import pyxel as px
import uuid
from random import choice as random_choice
import const as G_
import common_func as comf

def notice_item(item_info, flg):
    notice_message = ""
    category = G_.ItemType.get_category(item_info.type_id)
    if category in (G_.ItemType.CATEGORY_WEAPON,G_.ItemType.CATEGORY_ARMOR,
                    G_.ItemType.CATEGORY_SHIELD):
        if flg.is_equiptype[str(item_info.type_id)] is False:
            flg.is_equiptype[str(item_info.type_id)] = True
            notice_message = f"{G_.ITEM_TYPE_NAME[item_info.type_id]}：\n{G_.ITEM_TYPE_DESC[item_info.type_id]}"
    elif category == G_.ItemType.CATEGORY_CONSUME:
        if flg.is_consume[str(item_info.id)] is False:
            flg.is_consume[str(item_info.id)] = True
            notice_message = f"{item_info.basename}：\n{ItemManager.get_item_info(item_info.id)[G_.JsonItem.DESC]}"
    return [notice_message]


#アイテム使用（取得即時効果の場合もここ）
def use_item(item_info, user):
    if item_info.type_id == G_.ItemType.INSTANT:
        if item_info.id == "16":
            if user.hp >= user.maxhp:
                px.play(3, G_.SNDEFX["miss"], resume=True)
                return 1
            user.hp = min(user.maxhp, user.hp+int(user.maxhp/3))
        elif item_info.id == "20":
            user.hp = user.maxhp*2
        elif item_info.id == "23":
            user.is_bonus[G_.BonusType.REGISTFIRE] += 10
        elif item_info.id == "24":
            user.is_bonus[G_.BonusType.REGISICE] += 10
        elif item_info.id == "25":
            user.is_bonus[G_.BonusType.REGISTWIND] += 10
        elif item_info.id == "26":
            user.is_bonus[G_.BonusType.REGISTEARTH] += 10
        else:
            user.is_bonus[int(item_info.id)]+=10
            if item_info.id == "6":
                user.calc_maxhp()
        return
    elif item_info.type_id == G_.ItemType.TIMER:
        buffid = int(item_info.id)-7
        if user.is_buff[buffid] is False:
            user.is_buff[buffid] = True
            user.buff_effect(buffid)
            if item_info.id == "11":
                user.calc_movespeed()

        #パーク：バフ時間UP
        rune_effect = user.get_rune_effect(G_.RuneList.SUSTAIN)
        perk_bonus = rune_effect[1] if rune_effect is not None else 1

        user.timer_item[buffid] = min(255*G_.GAME_FPS,
                                      user.timer_item[buffid]+(G_.BUFFTIME*perk_bonus)) #重複取得で効果延長

        user.di.message_manager.add_message(
                f"{G_.BUFF_DESC[buffid]} {user.timer_item[buffid]//G_.GAME_FPS}s",px.COLOR_CYAN)


#アイテム取得
def pick_item(item_uuid:str, num_item:int, user):
    px.play(3, G_.SNDEFX["pick"], resume=True)
    item_info = ItemManager.get_item(item_uuid)
    item_category = G_.ItemType.get_category(item_info.type_id)
    if item_category in (G_.ItemType.CATEGORY_WEAPON,G_.ItemType.CATEGORY_ARMOR,
                         G_.ItemType.CATEGORY_SHIELD,G_.ItemType.CATEGORY_RUNE):
        #インベントリがいっぱいだと持てない
        if len(user.inventory) >= user.inventory_max:
            if ItemManager.get_state(item_uuid) == G_.ItemStatus.CHEST:
                ItemManager.update_state(item_uuid, G_.ItemStatus.DROP)
        else:
            ItemManager.update_state(item_uuid, G_.ItemStatus.BUGGAGE)
        return item_info

    if item_info.type_id in (G_.ItemType.INSTANT,G_.ItemType.TIMER):
        use_item(item_info, user)
        return item_info
    else:
        match item_info.id:
            case "13":
                user.is_safeescape = True
            case "14":
                user.key += 5
            case "15":
                user.mattock += 1
            case "17":
                user.gem += num_item
            case "18":
                user.food += num_item
            case "19":
                user.key += 1
            case "21":
                user.score += num_item
            case "22":
                user.mana_division(num_item)
        ItemManager.remove_item(item_uuid)
        return item_info


#スポナー/エリートドロップ宝箱
class TreasureBox:
    def __init__(self, map_address, address, depth_level, is_elite=False, is_divine=False):
        self.map_address = map_address
        self.address = address
        category = px.rndi(G_.ItemType.CATEGORY_WEAPON, G_.ItemType.CATEGORY_SHIELD)
        self.item_uuid = ItemManager.create_randomitem(depth_level, category, is_elite,
                                                       G_.ItemStatus.CHEST, is_divine)
        self.num_item = 1
        self.rate_open = 0
        self.is_placed = False
        self.is_opened = False
        self.DifficultClass = depth_level**2*0.05+50
    
    def challenge_open(self, depth_level, dexterity):
        px.play(3,G_.SNDEFX["unlock"], resume=True)
        if px.rndf(0, self.DifficultClass) <= dexterity:
            openbonus = px.rndi(1,50-depth_level)
            self.rate_open += min(40,max(1,(dexterity/16 + openbonus)))
        if self.rate_open >= 100:
            self.is_opened = True
            return True
        return False

    def draw(self):
        if self.is_placed and self.is_opened is False:
            px.blt(self.address[0]-8,self.address[1]-8, 0,
                   G_.ImageAddress.REDCHEST[0]+16*(self.rate_open//45),
                   *G_.ImageAddress.REDCHEST[1:], colkey=0)


class ItemManager:
    _repos = {} # {uuid: {"state":str, "obj": Item}}
    _relay = []
    _dict_rune = {}
    _dict_skill = {}
    _dict_item = {}

    @classmethod
    def load_json(cls):
        cls.load_item()
        cls.load_rune()
        cls.load_skill()

    @classmethod
    def load_item(cls):
        cls._dict_item = {i:{str(item_[0]):item_[1:] for item_ in category_data}
                         for i,category_data in enumerate(comf.read_json("assets/data/item.json"))}

    @classmethod
    def load_rune(cls):
        cls._dict_rune = {str(rune[0]):rune[1:]
                          for rune in comf.read_json("assets/data/rune.json")}

    @classmethod
    def load_skill(cls):
        cls._dict_skill = {str(skill[0]):skill[1:]
                           for skill in comf.read_json("assets/data/skill.json")}

    @classmethod
    def get_item_id_by_category(cls, item_category):
        if item_category == G_.ItemType.RUNE:
            return cls._dict_rune
        elif item_category in (G_.ItemType.CATEGORY_CONSUME,
                               G_.ItemType.CATEGORY_WEAPON,
                               G_.ItemType.CATEGORY_ARMOR,
                               G_.ItemType.CATEGORY_SHIELD):
            return cls._dict_item[item_category]
        else:
            return None

    @classmethod
    def get_item_id_by_type(cls, item_type):
        dict_ = dict(**cls._dict_item[G_.ItemType.CATEGORY_CONSUME],
                     **cls._dict_item[G_.ItemType.CATEGORY_WEAPON],
                     **cls._dict_item[G_.ItemType.CATEGORY_ARMOR],
                     **cls._dict_item[G_.ItemType.CATEGORY_SHIELD],
                     **cls._dict_rune)
        return [item_id for item_id, item_info in dict_.items()
                if item_info[G_.JsonItem.TYPE_ID] == item_type]

    @classmethod
    def get_item_info(cls, item_id):
        dict_ = dict(**cls._dict_item[G_.ItemType.CATEGORY_CONSUME],
                     **cls._dict_item[G_.ItemType.CATEGORY_WEAPON],
                     **cls._dict_item[G_.ItemType.CATEGORY_ARMOR],
                     **cls._dict_item[G_.ItemType.CATEGORY_SHIELD],
                     **cls._dict_rune)
        return dict_.get(str(item_id))

    @classmethod
    def create_item(cls, item_id:int, initial_state:G_.ItemStatus=G_.ItemStatus.DROP):
        '''指定IDのアイテムを生成（装備品は最低ランク）'''
        item_uuid = str(uuid.uuid4())
        item_info = cls.get_item_info(item_id)
        match item_info[0]:
            case G_.ItemType.WAND|G_.ItemType.SWORD|G_.ItemType.SPEAR|G_.ItemType.AXE:
                item_ = Weapon(item_uuid, item_id, item_info)
            case G_.ItemType.ROBE|G_.ItemType.LEATHER|G_.ItemType.CHAIN|G_.ItemType.PLATE:
                item_ = Armor(item_uuid, item_id, item_info)
            case G_.ItemType.BUNGLE|G_.ItemType.ROUND|G_.ItemType.KITE|G_.ItemType.TOWER:
                item_ = Shield(item_uuid, item_id, item_info)
            case G_.ItemType.RUNE:
                item_ = Rune(item_uuid, item_id, item_info)
            case G_.ItemType.INSTANT|G_.ItemType.TIMER|G_.ItemType.STOCK|G_.ItemType.INCREASE|G_.ItemType.EX:
                item_ = Item(item_uuid, item_id, item_info)

        cls._repos[item_uuid] = {
            "state":initial_state,
            "obj":item_
        }
        return item_uuid

    @classmethod
    def create_randomitem(cls, depth_level, category=None, is_elite=False,
                          initial_state=G_.ItemStatus.DROP,is_divine=False):
        '''深度に応じたアイテムのランダム生成（カテゴリ指定可、CONSUMEのみType指定可）'''
        #カテゴリ指定がない場合はランダム
        item_type = ""
        if category is None:
            category = px.rndi(G_.ItemType.CATEGORY_CONSUME,G_.ItemType.CATEGORY_RUNE)
        elif category == G_.ItemType.CATEGORY_RUNE:
            item_type = G_.ItemType.RUNE
        elif category in (G_.ItemType.INSTANT,G_.ItemType.TIMER,G_.ItemType.STOCK,
                          G_.ItemType.INCREASE,G_.ItemType.EX):
            item_type = category
            category = G_.ItemType.CATEGORY_CONSUME
        if item_type == "":
            item_type_list = G_.ItemType.get_items_in_category(category)
            item_type = random_choice(item_type_list)

        #ランクの決定
        elitebonus = 1 if is_elite else 0 #エリートモンスタードロップのボーナス
        perkbonus = 2 if is_divine else 0 #赤宝箱レアUPパークのボーナス※重複しない
        maxrank = min(G_.ItemRank.ANCIENT, depth_level//10+1 +elitebonus +perkbonus)
        rank = min(G_.ItemRank.ANCIENT,
                   random_choice([i for i,num in enumerate(range(maxrank+1, 0, -1))
                                  for _ in range(num*num)][maxrank*2:]) +elitebonus +perkbonus)
        if rank == G_.ItemRank.ANCIENT:
            rank = G_.ItemRank.ANCIENT if px.rndi(perkbonus,7) == px.rndi(perkbonus,7) else G_.ItemRank.LEGEND
        #候補アイテムリストの生成
        if item_type == G_.ItemType.RUNE:
            rank = max(rank,3)
            candidate_list = [item_id for item_id, rune in cls._dict_rune.items()
                         if (rune[G_.JsonRune.TYPE] & G_.RuneType.RUNE) != 0
                         and rune[G_.JsonRune.RANK]<=rank]
        else:
            tmplist = [item_id for item_id, item_info in cls._dict_item[category].items() 
                       if item_info[G_.JsonItem.TYPE_ID]==item_type
                       and item_info[G_.JsonItem.RANK]<=rank]
            if len(tmplist)==0:
                tmplist = [item_id for item_id, item_info in cls._dict_item[category].items()
                           if item_info[G_.JsonItem.RANK]<=rank
                ]
            base = 8 if depth_level < 40 else 9 if depth_level < 90 else 10
            maxitem = min(max(depth_level//base+1,1),len(tmplist))
            if maxitem == 13 and depth_level < 150:
                maxitem = 12
            minitem = min(depth_level//16,len(tmplist)-1) if category in (
                    G_.ItemType.CATEGORY_WEAPON,
                    G_.ItemType.CATEGORY_ARMOR,
                    G_.ItemType.CATEGORY_SHIELD) else 0
            candidate_list = tmplist[minitem:maxitem]

        #アイテムの生成
        item_id = random_choice(candidate_list)
        item_uuid = cls.create_item(item_id, initial_state)

        #装備アイテムの場合はランクを更新
        item_ = cls.get_item(item_uuid)    
        if category in (G_.ItemType.CATEGORY_WEAPON,
                        G_.ItemType.CATEGORY_ARMOR,
                        G_.ItemType.CATEGORY_SHIELD):
            item_.update_rank(rank)
        return item_uuid

    @classmethod
    def get_item(cls, item_uuid: str):
        '''指定UUIDのアイテムオブジェクトを取得'''
        return cls._repos.get(item_uuid, {}).get("obj")

    @classmethod
    def get_state(cls, item_uuid: str):
        '''指定UUIDのアイテム状態を取得'''
        return cls._repos.get(item_uuid, {}).get("state")

    @classmethod
    def get_item_by_state(cls, state):
        '''指定状態のUUIDとオブジェクトのリストを取得'''
        return [[item_uuid, item_["obj"]] for item_uuid, item_ in cls._repos.items()
                if item_.get("state") == state ]

    @classmethod
    def get_rune(cls):
        return {rune_id:rune for rune_id,rune in cls._dict_rune.items()}

    @classmethod
    def get_rune_by_id(cls, target_rune_id):
        return {rune_id:rune for rune_id,rune in cls._dict_rune.items()
                if rune_id == target_rune_id}

    @classmethod
    def get_rune_by_rank(cls, rank):
        return {rune_id:rune for rune_id,rune in cls._dict_rune.items()
                if rune[G_.JsonRune.RANK] < rank}

    @classmethod
    def get_skill(cls):
        return {skill_id:skill for skill_id,skill in cls._dict_skill.items()}

    @classmethod
    def get_skill_by_id(cls, target_skill_id):
        return {skill_id:skill for skill_id,skill in cls._dict_skill.items()
                if skill_id == target_skill_id}

    @classmethod
    def get_skill_by_rank(cls, rank):
        return {skill_id:skill for skill_id,skill in cls._dict_skill.items()
                if skill[G_.JsonSkill.RANK] < rank}

    @classmethod
    def update_state(cls, item_uuid: str, new_state: str):
        if item_uuid in cls._repos:
            cls._repos[item_uuid]["state"] = new_state
            if new_state == G_.ItemStatus.DROP:
                address = {"x":px.rndf(16,G_.WND_MAIN[2]-16),"y":px.rndf(16,G_.WND_MAIN[3]-16)}
                cls._relay.append([item_uuid,1])
            else:
                address = {"x":0,"y":0}
            cls._repos[item_uuid]["obj"].address = address

    @classmethod
    def notice_relay(cls):
        response = []
        for info in cls._relay:
            response.append(info)
        cls._relay = []
        return response

    @classmethod
    def remove_item(cls, item_uuid: str):
        if item_uuid in cls._repos:
            del cls._repos[item_uuid]

    @classmethod
    def garbage_correct(cls):
        garbage_list = cls.get_item_by_state(G_.ItemStatus.DROP)
        garbage_list += cls.get_item_by_state(G_.ItemStatus.CHEST)
        garbage_list += cls.get_item_by_state(G_.ItemStatus.SHOP)
        garbage_list += cls.get_item_by_state(G_.ItemStatus.GARBAGE)
        for item_ in garbage_list:
            cls.remove_item(item_[0])
        cls._relay.clear()

    @classmethod
    def delete_attached_runes(cls, parent_item_uuid):
        parent_item = cls.get_item(parent_item_uuid)
        if parent_item and parent_item.rune_slot:
            for slot_type in ["low", "mid", "hi"]:
                for rune_uuid in parent_item.rune_slot.runes[slot_type]:
                    cls.update_state(rune_uuid, G_.ItemStatus.GARBAGE)

    @classmethod
    def clear_item(cls):
        cls._repos.clear()


class Item:
    def __init__(self, item_uuid:str, item_id:int, item_info:list):
        self.uuid = item_uuid
        self.id = item_id
        self.type_id, self.basename, self.price, self.value, self.rank = item_info[:5]
        self.rune_slot = None #ルーンスロット＝オプションソケット定義　装備品にのみ存在
        self.is_identified = True
        self.name = self.basename

    def update_rank(self, rank):
        if G_.ItemType.get_category(self.type_id) not in (G_.ItemType.CATEGORY_WEAPON,
                G_.ItemType.CATEGORY_ARMOR,G_.ItemType.CATEGORY_SHIELD):
            return
        self.rank = rank
        if self.rank > G_.ItemRank.UNCOMMON: #RARE以上は未鑑定
            self.is_identified = False 
            self.rune_slot = SlotModule(self, self.rank)
        self.update_name()
        self.value = max(int(self.value*(100+rank*5)/100), self.value+rank)

    def update_name(self):
        if self.is_identified is False:
            self.name = "不明な"+G_.ITEM_TYPE_NAME[self.type_id]
            return
        #ランクによる名付け
        rankname = G_.ItemRank.SHORTEN[self.rank]+":"
        if G_.ConfigManager.LANGUAGE == G_.LanguageType.JAPANESE:
            e2j = {"C:":"", "UC:":"特注の", "R:":"名品の", "SR:":"秘宝の",
                   "EX:":"究極の", "LG:":"伝説の","AN:":"神代の"}
            rankname = e2j[rankname]
        #オプションによる名付け
        abiname = ""
        if self.rune_slot is not None:
            abiname = self.rune_slot.ability.basename
        #名前の更新
        self.name = rankname + abiname + self.basename


class SlotModule:
    def __init__(self, parent, rank:int):
        self.parent_item = parent
        self.max_slots = {"low":0, "mid":0, "hi":0}
        self.runes = {"low":[], "mid":[], "hi":[]}
        self.define_ability(self.parent_item.type_id)
        self.init_slots(rank)
        
    def define_ability(self, item_type_id):
        if self.parent_item.rank < G_.ItemRank.RARE:
            return
        match G_.ItemType.get_category(item_type_id):
            case G_.ItemType.CATEGORY_WEAPON:
                apply = G_.RuneApply.WEAPON
            case G_.ItemType.CATEGORY_ARMOR:
                apply = G_.RuneApply.ARMOR
            case G_.ItemType.CATEGORY_SHIELD:
                apply = G_.RuneApply.SHIELD
        ability_list = [ability[0] for ability in ItemManager._dict_rune.items()
                        if (ability[1][G_.JsonRune.TYPE] & G_.RuneType.ABILITY) != 0
                        and (ability[1][G_.JsonRune.CATEGORY] & apply) != 0
                        and ability[1][G_.JsonRune.RANK] <= self.parent_item.rank]
        ability_id = random_choice(ability_list)
        self.ability = ItemManager.get_item(
                ItemManager.create_item(ability_id, G_.ItemStatus.ABILITY))

    def init_slots(self, rank):
        match rank:
            case G_.ItemRank.RARE:
                self.max_slots["low"] += 1
            case G_.ItemRank.SUPERRARE:
                maxval = 2
                if px.rndi(1,100) <= 25:
                    self.max_slots["mid"] += 1
                    maxval -= 1
                self.max_slots["low"] = maxval
            case G_.ItemRank.EXTREME:
                self.max_slots["mid"] += 1
                if px.rndi(1,100) <= 33:
                    self.max_slots["mid"] += 1
                else:
                    self.max_slots["low"] += 1
                if px.rndi(1,100) <= 5:
                    self.max_slots["low"] += 1
            case G_.ItemRank.LEGEND:
                maxval = 3
                if px.rndi(1,100) <= 90:
                    self.max_slots["hi"] += 1
                    maxval -= 1
                self.max_slots["mid"] = maxval
                if px.rndi(1,100) <= 5:
                    self.max_slots["low"] += 1
            case G_.ItemRank.ANCIENT:
                self.max_slots["hi"] += 1
                if px.rndi(1,100) <= 25:
                    self.max_slots["hi"] += 1
                else:
                    self.max_slots["mid"] += 1
                self.max_slots["mid"] += 1
                if px.rndi(1,100) <= 5:
                    self.max_slots["mid"] += 1
                else:
                    self.max_slots["low"] += 1


    # スロットのランク要件（このランク以下のルーンが必要）
    def get_slot_req_rank(self, slot_type):
        match slot_type:
            case "low": return G_.ItemRank.SUPERRARE
            case "mid": return G_.ItemRank.EXTREME
            case "hi":  return G_.ItemRank.ANCIENT
            case _: return 0

    # ルーン装着
    def attach_rune(self, slot_type, rune_uuid):
        if len(self.runes[slot_type]) < self.max_slots[slot_type]:
            self.runes[slot_type].append(rune_uuid)
            return True
        return False

    # ルーン取り外し
    def detach_rune(self, slot_type, index):
        if len(self.runes[slot_type]) > index:
            return self.runes[slot_type].pop(index)
        return None


class Rune(Item):
    def __init__(self, item_uuid, item_id, item_info):
        rune_info = [item_info[G_.JsonRune.TYPE_ID],
                     item_info[G_.JsonRune.NAME],
                     1000,
                     item_info[G_.JsonRune.VALUE],
                     item_info[G_.JsonRune.RANK],]
        super().__init__(item_uuid, item_id, rune_info)
        self.category = item_info[G_.JsonRune.CATEGORY]
        self.effect_type_id = None
        self.is_identified = False
        #ランクによる名付け
        match self.rank:
            case G_.ItemRank.RARE|G_.ItemRank.SUPERRARE: rankname = "低級"
            case G_.ItemRank.EXTREME: rankname = "中級"
            case G_.ItemRank.LEGEND|G_.ItemRank.ANCIENT: rankname = "高級"
            case _: rankname = "ありえない"
        self.name = rankname+G_.ITEM_TYPE_NAME[self.type_id]

    def update_name(self):
        if self.is_identified:
            self.name = self.basename+"の"+G_.ITEM_TYPE_NAME[self.type_id]


class Armor(Item):
    def __init__(self, item_uuid, item_id, item_info):
        super().__init__(item_uuid, item_id, item_info)
        self.movespeed = self.get_category_parameter(self.type_id)
        self.mastery = 0.01

    def get_category_parameter(self, item_type_id):
        match item_type_id:
            case 4:
                return 6
            case 5:
                return 5
            case 6:
                return 4
            case 7:
                return 3
            case _:
                raise IndexError


class Shield(Item):
    
    def __init__(self, item_uuid, item_id, item_info):
        super().__init__(item_uuid, item_id, item_info)
        self.rate_attackspeed = self.get_category_parameter(self.type_id)
        self.mastery = 0.01

    def get_category_parameter(self, item_type_id):
        match item_type_id:
            case 8:
                return 1
            case 9:
                return 1.2
            case 10:
                return 1.4
            case 11:
                return 1.7
            case _:
                raise IndexError


class Weapon(Item):
    def __init__(self, item_uuid, item_id, item_info):
        super().__init__(item_uuid, item_id, item_info)
        self.attack_speed, self.func_attackrange, self.func_attackmotion =\
            self.get_category_parameter(self.type_id)

        self.motion_counter = 0
        self.motion_frames = -1
        self.is_attacking = False
        self.mastery = 0.01
        self.hitlist = []

    def update(self):
        if self.is_attacking:
            self.motion_counter += 1
            if self.motion_counter > self.motion_frames:
                self.is_attacking = False
                self.motion_counter = 0
                self.hitlist = []

    def get_category_parameter(self, item_type_id):
        match item_type_id:
            case 0:
                return 0.1, range_type_0, motion_type_0
            case 1:
                return 0.35, range_type_1, motion_type_1
            case 2:
                return 0.7, range_type_2, motion_type_2
            case 3:
                return 1.4, range_type_3, motion_type_3
            case _:
                raise IndexError


def range_type_0(x, y, direction):
    dx1 = G_.CHARA_DIR[direction][0]*12
    dy1 = G_.CHARA_DIR[direction][1]*12
    w1 = 8
    h1 = 8
    return [[x+dx1,y+dy1, w1,h1]]


def motion_type_0(cls, x, y, direction):
    self = cls
    u, v = 0, 112
    w, h = 8, 16

    # 攻撃角度 = 45 × (現在フレーム / 最大フレーム)
    swing_angle = 45 * self.motion_counter // self.motion_frames

    if direction == 0:  # 下向き：左→下→右（270〜450）
        origin_x = x
        origin_y = y + 7
        base_angle = -130
        rotate_angle = base_angle - swing_angle
    elif direction == 1:  # 左向き：上→左→下（0〜180）
        origin_x = x - 7
        origin_y = y
        base_angle = -40
        rotate_angle = base_angle - swing_angle
    elif direction == 2:  # 右向き：下→右→上（180〜360）
        origin_x = x + 7
        origin_y = y
        base_angle = 40
        rotate_angle = base_angle + swing_angle
    elif direction == 3:  # 上向き：右→上→左（90〜270）
        origin_x = x
        origin_y = y - 7
        base_angle = -40
        rotate_angle = base_angle + swing_angle

    draw_x = origin_x - w // 2
    draw_y = origin_y - h // 2

    px.blt(draw_x, draw_y, G_.IMGIDX["CHIP"], u, v, w, h, colkey=15, rotate=rotate_angle)


def range_type_1(x, y, direction):
    dx1 = G_.CHARA_DIR[direction][0]*10
    dy1 = G_.CHARA_DIR[direction][1]*10
    w1 = 36 if dx1 == 0 else 12
    h1 = 36 if dy1 == 0 else 12

    dx2 = G_.CHARA_DIR[direction][0]*20
    dy2 = G_.CHARA_DIR[direction][1]*20
    w2 = 16 if dx2 == 0 else 8
    h2 = 16 if dy2 == 0 else 8

    return [[x+dx1,y+dy1, w1,h1],[x+dx2,y+dy2, w2,h2]]


def motion_type_1(cls, x, y, direction):
    self = cls
    u, v = 8, 112
    w, h = 8, 32

    # 攻撃角度 = 180 × (現在フレーム / 最大フレーム)
    swing_angle = 180 * self.motion_counter // self.motion_frames

    if direction == 0:  # 下向き：左→下→右（270〜450）
        origin_x = x
        origin_y = y + 5
        base_angle = -90
        rotate_angle = base_angle - swing_angle
    elif direction == 1:  # 左向き：上→左→下（0〜180）
        origin_x = x - 5
        origin_y = y
        base_angle = 0
        rotate_angle = base_angle - swing_angle
    elif direction == 2:  # 右向き：下→右→上（180〜360）
        origin_x = x + 5
        origin_y = y
        base_angle = 10
        rotate_angle = base_angle + swing_angle
    elif direction == 3:  # 上向き：右→上→左（90〜270）
        origin_x = x
        origin_y = y - 5
        base_angle = -90
        rotate_angle = base_angle + swing_angle

    draw_x = origin_x - w // 2
    draw_y = origin_y - h // 2

    px.blt(draw_x, draw_y, G_.IMGIDX["CHIP"], u, v, w, h, colkey=15, rotate=rotate_angle)


def range_type_2(x, y, direction):
    range_length = 64
    range_width = 10
    dx1 = G_.CHARA_DIR[direction][0]*(8+range_length//2)
    dy1 = G_.CHARA_DIR[direction][1]*(8+range_length//2)
    w1 = range_width if dx1 == 0 else range_length
    h1 = range_width if dy1 == 0 else range_length

    return [[x+dx1,y+dy1, w1,h1]]


def motion_type_2(cls, x, y, direction):
    self = cls
    u, v = 16, 112
    w, h = 8, 64

    # 攻撃突き出し距離
    if self.motion_counter <= self.motion_frames//3:
        thrust = int(64 * self.motion_counter / (self.motion_frames // 3))
    else:
        thrust = int(64 * (self.motion_frames - self.motion_counter) / (self.motion_frames * 2 // 3))   

    if direction == 0:  # 下向き：左→下→右（270〜450）
        draw_x = x - w // 2 - 5
        draw_y = y + 10 - h + thrust
        rotate_angle = 180
    elif direction == 1:  # 左向き：上→左→下（0〜180）
        draw_x = x - 8 - thrust + 24
        draw_y = y - h // 2 + 2
        rotate_angle = -90
    elif direction == 2:  # 右向き：下→右→上（180〜360）
        draw_x = x + 8 - w + thrust - 24
        draw_y = y - h // 2 + 2
        rotate_angle = 90
    elif direction == 3:  # 上向き：右→上→左（90〜270）
        draw_x = x - w // 2 + 5
        draw_y = y - 10 - thrust
        rotate_angle = 0

    px.blt(draw_x, draw_y, G_.IMGIDX["CHIP"], u, v, w, h, colkey=15, rotate=rotate_angle)


def range_type_3(x, y, direction):
    dx1 = G_.CHARA_DIR[direction][0]*10
    dy1 = G_.CHARA_DIR[direction][1]*10
    w1 = 52 if dx1 == 0 else 20
    h1 = 52 if dy1 == 0 else 20

    dx2 = G_.CHARA_DIR[direction][0]*24
    dy2 = G_.CHARA_DIR[direction][1]*24
    w2 = 32 if dx2 == 0 else 8
    h2 = 32 if dy2 == 0 else 8

    dx3 = G_.CHARA_DIR[direction][0]*30
    dy3 = G_.CHARA_DIR[direction][1]*30
    w3 = 16 if dx2 == 0 else 4
    h3 = 16 if dy2 == 0 else 4

    return [[x+dx1,y+dy1, w1,h1],[x+dx2,y+dy2, w2,h2],[x+dx3,y+dy3, w3,h3]]


def motion_type_3(cls, x, y, direction):
    self = cls
    u, v = 24, 112
    w, h = 8, 48

    # 攻撃角度 = 180 × (現在フレーム*2 / 最大フレーム) 振り終わりで硬直
    swing_angle = min(180, 180 * self.motion_counter*2 // self.motion_frames)

    if direction == 0:  # 下向き：左→下→右（270〜450）
        origin_x = x
        origin_y = y + 5
        base_angle = 100
        vector = -1
        rotate_angle = base_angle + swing_angle
    elif direction == 1:  # 左向き：上→左→下（0〜180）
        origin_x = x - 5
        origin_y = y
        base_angle = 10
        vector = -1
        rotate_angle = base_angle + swing_angle
    elif direction == 2:  # 右向き：下→右→上（180〜360）
        origin_x = x + 5
        origin_y = y
        base_angle = 10
        vector = 1
        rotate_angle = base_angle + swing_angle
    elif direction == 3:  # 上向き：右→上→左（90〜270）
        origin_x = x
        origin_y = y - 5
        base_angle = -80
        vector = 1
        rotate_angle = base_angle + swing_angle

    draw_x = origin_x - w // 2
    draw_y = origin_y - h // 2

    px.blt(draw_x, draw_y, G_.IMGIDX["CHIP"], u, v, w*vector, h, colkey=15, rotate=rotate_angle)


#描画処理のみ。モンスター動作変更系はMonsterクラスの処理内で定義
def func_effect_item11(user): #砂時計 (効果の描画のみ)
    if (user.timer_item[G_.BuffType.TIMESTOP]>G_.GAME_FPS*4\
         and px.frame_count//(G_.GAME_FPS*2)%2 == 0)\
        or (G_.GAME_FPS*4 > user.timer_item[G_.BuffType.TIMESTOP] > 0\
             and px.frame_count%16 in (0,1,2,3,4)):
        px.rectb(1,1, G_.WND_MAIN[2]-2,G_.WND_MAIN[2]-2, px.COLOR_GREEN)
        px.rectb(3,3, G_.WND_MAIN[2]-6,G_.WND_MAIN[2]-6, px.COLOR_LIME)


def func_effect_item12(user): #隠れ蓑
    imagesource_type = 112
    if user.timer_item[G_.BuffType.HIDDEN] <= 5*G_.GAME_FPS:
        if px.frame_count%16 in (0,1,2,3):
            imagesource_type = user.image_source[1]
    return imagesource_type


def func_effect_item31(user): #食料
    comsume = user.maxhp // 100
    #パーク：食糧消費減少
    rune_effect = user.get_rune_effect(G_.RuneList.RDCFOOD)
    perk_bonus = rune_effect[1] if rune_effect is not None else 1
    user.food = user.food - (comsume*perk_bonus)
    if user.food >= 0:
        if user.hp < user.maxhp:
            user.hp = min(user.maxhp, user.hp + comsume)
    else:
        user.di.message_manager.add_message("食糧不足で飢餓状態だ！",px.COLOR_RED)
        px.play(3,G_.SNDEFX["damage"],resume=True)
        user.hp -= user.maxhp // 20
        user.food = 0
