import pyxel as px
import const as G_, common_func as comf
import item, rune, skill


class Character:
    def __init__(self, move_type:int, address:list, image_source:list, name:str, 
                 maxhp:int, di, level, movespeed):
        #引数で設定
        self.di = di # Dependency Injection
        self.level = level
        self.name = name #名前
        self.move_type = move_type #キャラの移動タイプ const.MoveType
        self.address = address #キャラのマップ上座標（Block）
        self.image_source = image_source #画像リソース情報
        self.movespeed = movespeed #移動速度　防具やデバフ、アイテム効果等で変化
        self.maxhp = maxhp #最大HP

        #デフォルト値
        self.direction = 0 #キャラの向き（CHARA_DIRのインデックス,0~3）
        self.image_position = 0 #スプライトのアニメーション用。0⇔1切替
        self.action_waittime = 4 #行動待ち時間を再設定する
        self.timer_action = 0 #行動時間タイマー
        self.timer_attack = 0 #攻撃時間タイマー
        self.timer_damaged = 0 #連続ダメージ防止兼ダメージエフェクト表示中タイマー
        self.timer_magicdamaged = 0 #連続ダメージ防止魔法ダメージエフェクト表示中タイマー
        self.timer_fire = 0 #デバフ（炎）タイマー
        self.effect_fire = None #デバフ効果

        self.timer_ice = 0 #デバフ（氷）タイマー
        self.effect_ice = None #デバフ効果
        self.timer_wind = 0 #デバフ（風）タイマー
        self.effect_wind = None #デバフ効果
        self.is_dead = False #死亡フラグ
        self.skill = {"a":None,"b":None,"x":None,"y":None} #装備中のスキルオブジェクト
        self.maxmp = 0 #最大MP

        self.gem = 0 #ジェム（お金）
        self.mana = 0 #マナ（経験値）
        if move_type != 0:
            self.reduce_element = {'fire':0, 'ice':0, 'wind':0, 'earth':0}

        #他パラメータから算出
        self.attack_waittime = G_.GAME_FPS*0.4 #攻撃待ち時間
        self.hp = maxhp #現在HP
        self.mp = self.maxmp #現在MP

    #行動速度（間隔）
    def set_action_waittime(self):
        return 4

    #攻撃速度（間隔）
    def set_attack_waittime(self):
        return G_.GAME_FPS*0.4

    #アドレス移動
    def move_address(self):
        if px.frame_count%16 in (0,1,2,3):
            self.image_position = 1 - self.image_position
        self.address = [self.address[0] + (G_.CHARA_DIR[self.direction][0]*(self.movespeed)),
                        self.address[1] + (G_.CHARA_DIR[self.direction][1]*(self.movespeed))]
        return True

    #ノックバックによる移動処理
    def move_knockback(self, move_length, target, direction):
        corners = [(-3,0), #左上
                   (3,0), #右上
                   (-3,6), #左下
                   (3,6), #右下
        ]
        match direction:
            case 0:
                offset1 = corners[2]
                offset2 = corners[3]
            case 1:
                offset1 = corners[0]
                offset2 = corners[2]
            case 2:
                offset1 = corners[1]
                offset2 = corners[3]
            case 3:
                offset1 = corners[0]
                offset2 = corners[0]

        rightlimit = G_.WND_MAIN[2]
        if target.move_type == 0 and target.user_scene in (70,75):
            rightlimit = px.width
        for _ in range(int(move_length)):
            destination = [target.address[0]+G_.CHARA_DIR[direction][0],\
                    target.address[1]+G_.CHARA_DIR[direction][1]]
            if target.move_type == 0:
                scene = target.user_scene
            else:
                scene = self.user_scene
            if scene == 30:
                fencesize = 10
            elif scene == 40:
                fencesize = 25
            elif scene in (70,75):
                fencesize = 8
            if target.address[0] <= fencesize and direction == 1:
                break
            if target.address[0] >= (rightlimit-fencesize) and direction == 2:
                break
            if target.address[1] <= fencesize and direction == 3:
                break
            if target.address[1] >= (G_.WND_MAIN[3]-fencesize) and direction == 0:
                break
            if target.move_type == 0:
                if target.user_scene == 40:
                    layer = G_.TilemapIndex.OBSTACLE
                    checklist = [(2,0),(3,0),(4,0),(5,0),
                                (2,1),(3,1),(4,1),(5,1)]
                    checklist+= [(2,2),(3,2),(4,2),(5,2),
                                (2,3),(3,3),(4,3),(5,3)]
                    checklist+= [(2,4),(3,4),(4,4),(5,4),
                                (2,5),(3,5),(4,5),(5,5)]
                    checklist+= [(9,30),(10,30),
                                (9,31),(10,31)]

                    if comf.get_tileinfo(destination[0]+offset1[0],
                                         destination[1]+offset1[1],layer) in checklist:
                        break
                    if comf.get_tileinfo(destination[0]+offset2[0],
                                         destination[1]+offset2[1],layer) in checklist:
                        break
                elif target.user_scene in (70,75):
                    layer = 1
                    if comf.get_tileinfo(destination[0]+G_.CHARA_DIR[direction][0],
                                         destination[1]+G_.CHARA_DIR[direction][1],layer) == (8,1):
                        break
                    if comf.get_tileinfo(destination[0]+offset1[0],
                                         destination[1]+offset1[1],layer) == (8,1):
                        break
                    if comf.get_tileinfo(destination[0]+offset2[0],
                                         destination[1]+offset2[1],layer) == (8,1):
                        break
            target.address = destination

    #物理攻撃処理
    def proc_attack_physical(self, target, knockback_length:int=1):
        if target.move_type == 0:
            #対象が被ダメージから一定時間内は連続ダメージを受けない
            #無敵バフ時はダメージを受けない
            #階層開始直後は死なない
            if target.timer_damaged > 0 or target.is_buff[G_.BuffType.DIFLECT] or target.timer_invincible > 0:
                return 0

        attack = self.attack

        #ユーザキャラ固有のチェック
        is_critical = False
        eliteattack = 1
        if self.move_type == 0:
            #カテゴリ熟練度増加
            mast_nm = G_.ItemType.NAME[self.weapon.type_id]
            dc = 75 if self.mastery[mast_nm] < 150 else 50 if self.mastery[mast_nm] < 175 else 25
            if self.mastery[mast_nm]<200 and px.rndi(1,100) <= dc:
                self.mastery[mast_nm] += 0.01
            #クリティカル判定
            rune_effect1 = self.get_rune_effect(G_.RuneList.CRITICAL)
            crit_rate_bonus = 0 if rune_effect1 is None else rune_effect1[1]*100
            is_critical = True if px.rndi(1,10000) < (self.dexterity+self.luck+crit_rate_bonus) else False
            #パーク：MAXHP攻撃力UP
            rune_effect2 = None
            if self.hp >= self.maxhp:
                rune_effect2 = self.get_rune_effect(G_.RuneList.FULLPOW)
            attack = self.attack * (rune_effect2[1] if rune_effect2 is not None else 1)
            #パーク：エリートダメージUP
            rune_effect6 = self.get_rune_effect(G_.RuneList.ELITEATTACK)
            if target.is_elite and rune_effect6 is not None:
                eliteattack = rune_effect6[1]
                                
        #ダメージ計算（物理）
        if is_critical:
            #パーク：クリダメUP
            rune_effect3 = self.get_rune_effect(G_.RuneList.FATAL)
            perk_bonus = rune_effect3[1] if rune_effect3 is not None else 1
            damage = attack*2*perk_bonus
        else:
            damage = max(0,
                     int(px.rndf(attack*0.9,attack*1.2) - target.defend))
        damage *= eliteattack

        if target.move_type == 0:
            #パーク：エリートダメージDOWN
            rune_effect7 = target.get_rune_effect(G_.RuneList.CLEANSE)
            if self.is_elite and rune_effect7 is not None:
                damage //= rune_effect7[1]
            #パーク：ダメージ半減
            rune_effect8 = target.get_rune_effect(G_.RuneList.SOLID)
            if rune_effect8 is not None:
                damage *= rune_effect8[1]
            #ダメージ反射(バフとオプション)
            reflectionrate = 0
            if target.is_buff[G_.BuffType.REFLECT]:
                reflectionrate = list(item.ItemManager.get_skill_by_id("720").values())[0][G_.JsonSkill.VALUE]
            rune_effect = target.get_rune_effect(G_.RuneList.REFLECT)
            perk_bonus = rune_effect[1] if rune_effect is not None else 0
            reflectionrate += perk_bonus
            reflectdamage = damage * (reflectionrate/100)
            damage -= reflectdamage
            self.hp -= reflectdamage

        #ダメージ量に応じた成長計算
        if damage > 0:
            target.timer_damaged = G_.GAME_FPS
            self.grow_weapon()
            if is_critical:
                px.play(3, G_.SNDEFX["critical"], resume=True)
            else:
                px.play(3, G_.SNDEFX["damage"], resume=True)
            target.hp -= int(damage)
        else:
            target.timer_damaged = G_.GAME_FPS*0.5
            px.play(3, G_.SNDEFX["miss"], resume=True)
            if self.move_type == 0:
                upper = 80 if self.weapon.mastery > 50 else 32 if self.weapon.mastery > 30 else 8
                if px.rndi(1,upper) <= 4:
                    self.grow_weapon()

        if self.move_type == 0:
            #パーク：吸血
            rune_effect4 = self.get_rune_effect(G_.RuneList.DRAIN)
            if rune_effect4 is not None:
                if self.hp < self.maxhp:
                    self.hp = min(self.maxhp, self.hp+self.hp+max(1, damage * rune_effect4[1]))
            #パーク：ノックバック
            rune_effect5 = self.get_rune_effect(G_.RuneList.BACK)
            if rune_effect5 is not None:
                knockback_length = rune_effect5[1]
                self.move_knockback(knockback_length, target, self.direction)

        return int(damage)

    #魔法攻撃処理
    def proc_attack_skill(self, skill_, target, knockback_length=1):
        reducedamage = 1
        if target.move_type == 0:
            #対象が被ダメージから一定時間内は連続ダメージを受けない
            #無敵バフ時はダメージを受けない
            #階層開始直後は死なない
            if target.timer_magicdamaged > 0 or target.is_buff[G_.BuffType.DIFLECT] or target.timer_invincible > 0:
                return 0
            #腕輪によるダメージ減衰
            if target.shield.type_id == G_.ItemType.BUNGLE:
                reducedamage = 0.666
            #パーク：四属性耐性
            regist_bonus = [G_.RuneList.RDCFIRE,G_.RuneList.RDCICE,
                            G_.RuneList.RDCWIND,G_.RuneList.RDCEARTH,9999]
            rune_effect = target.get_rune_effect(regist_bonus[skill_.model.element_type])
            if rune_effect is not None:
                reducedamage /= rune_effect[1]



        #ノックバック関連処理
        if skill_.model.id == "721": 
            knockback_length = 32
            self.move_knockback(knockback_length, target, self.direction)
        #属性減衰率取得
        elemental_reduce = 1 if skill_.model.element_type is None else\
                1 - (target.get_elemental_reduce(target, skill_.model.element_type)/100)

        eliteattack = 1
        try:
            if skill_.model.element_type == G_.ElementType.NONE:
                arcdiv = self.arcane
                wep = self.attack*(0.75 if self.weapon.type_id == G_.ItemType.AXE else 1)+self.arcane
                typebonus = skill_.model.value*100
            else:
                arcdiv = 1
                wep = 1
                typebonus = skill_.model.value
            arc = self.arcane/arcdiv
            val = skill_.model.value
            basevalue = arc * val * wep + typebonus
            
            #パーク：エリートダメージUP
            rune_effect6 = self.get_rune_effect(G_.RuneList.ELITEATTACK)
            if target.is_elite and rune_effect6 is not None:
                eliteattack = rune_effect6[1]
        except AttributeError:
            basevalue = self.arcane * skill_.model.value + (
                self.attack if skill_.model.element_type == G_.ElementType.NONE else 0)

        damage = px.rndf(basevalue*0.9, basevalue*1.1) * elemental_reduce * reducedamage
        #アサシネイトでの即死効果判定
        if skill_.model.id == "722":
            if self.move_type == 0:
                if target.is_boss:
                    damage = self.attack*4
                elif target.tier*2 <= px.rndi(self.luck//16,self.luck//6):
                    damage = target.hp*2
            else:
                if target.level <= px.rndi(0,self.level):
                    damage = target.hp//2
        damage *= eliteattack

        if self.move_type == 0:
            #カテゴリ熟練度増加
            mast_nm = G_.ItemType.NAME[self.weapon.type_id]
            dc = 75 if self.mastery[mast_nm] < 150 else 50 if self.mastery[mast_nm] < 175 else 25
            if self.mastery[mast_nm]<200 and px.rndi(1,200) <= dc: #スキルでは上昇確率が半分
                self.mastery[mast_nm] += 0.01
            #パーク：属性ダメージUP
            rune_id = [rune_id for i,rune_id in enumerate((G_.RuneList.FIRE,G_.RuneList.ICE,
                                                        G_.RuneList.WIND,G_.RuneList.EARTH)) 
                                                        if i == skill_.model.element_type]
            if len(rune_id):
                rune_effect = self.get_rune_effect(rune_id[0])
                perk_bonus = rune_effect[1] if rune_effect is not None else 1
                damage *= perk_bonus
            #パーク：スキルダメージUP
            rune_effect = self.get_rune_effect(G_.RuneList.MASTER)
            perk_bonus = rune_effect[1] if rune_effect is not None else 1
            damage *= perk_bonus

        if target.move_type == 0:
            #パーク：エリートダメージDOWN
            rune_effect7 = target.get_rune_effect(G_.RuneList.CLEANSE)
            if self.is_elite and rune_effect7 is not None:
                damage //= rune_effect7[1]
            #パーク：ダメージ半減
            rune_effect8 = target.get_rune_effect(G_.RuneList.SOLID)
            if rune_effect8 is not None:
                damage *= rune_effect8[1]
            #ダメージ反射(バフとオプション)
            reflectionrate = 0
            if target.is_buff[G_.BuffType.REFLECT]:
                reflectionrate = list(item.ItemManager.get_skill_by_id("720").values())[0][G_.JsonSkill.VALUE]
            rune_effect = target.get_rune_effect(G_.RuneList.REFLECT)
            perk_bonus = rune_effect[1] if rune_effect is not None else 0
            reflectionrate += perk_bonus
            reflectdamage = damage * (reflectionrate/100)
            damage -= reflectdamage
            self.hp -= reflectdamage

        #ダメージ量に応じた成長計算
        if damage > 0:
            target.timer_magicdamaged = G_.GAME_FPS
            self.grow_weapon()
            px.play(3, G_.SNDEFX["damage"], resume=True)
            target.hp -= int(damage)
        else:
            target.timer_magicdamaged = G_.GAME_FPS*0.5
            px.play(3, G_.SNDEFX["miss"], resume=True)

        #デバフ抵抗判定
        if skill_.model.element_type != G_.ElementType.NONE:
            if target.move_type != 0 and (elemental_reduce <= 0 or target.is_boss): #ボスにはデバフ無効
                pass
            else:
                caster = px.rndi(1, int(self.arcane))
                register = px.rndi(1, int(target.arcane))
                if caster > register:
                    is_user = True if target.move_type == 0 else False
                    #ローブのデバフ耐性
                    if is_user and (target.armor.type_id == G_.ItemType.ROBE and px.rndi(1,100) > 50):
                        pass
                    else:
                        match skill_.model.element_type:
                            case G_.ElementType.FIRE:
                                if target.move_type == 0:
                                    getregist = target.get_rune_effect(G_.RuneList.ANTIBURN)
                                    if px.rndi(0,99) < (0 if getregist is None else getregist[1]):
                                        return int(damage)
                                addtime = int((caster * (px.rndi(2,12)/100) +0.5))
                                if is_user and target.armor.type_id == G_.ItemType.ROBE:
                                    addtime //= 2
                                target.timer_fire = min(100, target.timer_fire + addtime)
                                target.effect_fire = skill.debuff_burn
                            case G_.ElementType.ICE:
                                if target.move_type == 0:
                                    getregist = target.get_rune_effect(G_.RuneList.ANTISLOW)
                                    if px.rndi(0,99) < (0 if getregist is None else getregist[1]):
                                        return int(damage)
                                addtime = int((caster * (px.rndi(2,12)/100) +0.5))
                                if is_user and target.armor.type_id == G_.ItemType.ROBE:
                                    addtime //= 2
                                target.timer_ice = min(100, target.timer_ice + addtime)
                                if target.effect_ice is None: #減少効果は重複発動しない
                                    skill.debuff_slow(target)
                                    target.effect_ice = skill.debuff_slow
                            case G_.ElementType.WIND:
                                if target.move_type == 0:
                                    getregist = target.get_rune_effect(G_.RuneList.ANTIBIND)
                                    if px.rndi(0,99) < (0 if getregist is None else getregist[1]):
                                        return int(damage)
                                addtime = int((caster * (px.rndi(2,12)/100) +0.5))
                                if is_user and target.armor.type_id == G_.ItemType.ROBE:
                                    addtime //= 2
                                target.timer_wind = min(100, target.timer_wind + addtime)
                                if target.effect_wind is None: #減少効果は重複発動しない
                                    skill.debuff_bind(target)
                                    target.effect_wind = skill.debuff_bind
                            case G_.ElementType.EARTH:
                                if target.move_type == 0:
                                    getregist = target.get_rune_effect(G_.RuneList.ANTIKNOCK)
                                    if px.rndi(0,99) < (0 if getregist is None else getregist[1]):
                                        return int(damage)
                                knocklength = self.arcane//100+16
                                if is_user and target.armor.type_id == G_.ItemType.ROBE:
                                    knocklength //= 2
                                self.move_knockback(knocklength, target,skill_.direction)
        return int(damage)

    #オーバーライド用
    def grow_weapon(self):
        pass

    def get_elemental_reduce(self, target, skill_type):
        match skill_type:
            case G_.ElementType.FIRE:
                ret_val = target.reduce_element.get("fire")
            case G_.ElementType.ICE:
                ret_val = target.reduce_element.get("ice")
            case G_.ElementType.WIND:
                ret_val = target.reduce_element.get("wind")
            case G_.ElementType.EARTH:
                ret_val = target.reduce_element.get("earth")
            case G_.ElementType.NONE:
                ret_val = 0
        return ret_val

    #ユーザ・モンスター共通タイマー減算処理
    def common_timer_decrement(self):
        #カウンタ減算
        self.timer_action = max(0, self.timer_action-1)
        self.timer_attack = max(0, self.timer_attack -1)
        self.timer_damaged = max(0, self.timer_damaged-1)
        self.timer_magicdamaged = max(0, self.timer_magicdamaged-1)
        if px.frame_count%G_.GAME_FPS == 0:
            self.decrement_fire()
            self.decrement_ice()
            self.decrement_wind()
        return

    def decrement_fire(self, is_equip=False):
        if self.effect_fire is not None:
            if self.timer_fire > 0:
                if is_equip is False:
                    self.effect_fire(self)
                try:
                    dec = 2 if self.is_clear else 1
                except AttributeError:
                    dec = 1
                self.timer_fire = max(0, self.timer_fire-dec)
            if self.timer_fire == 0:
                self.effect_fire = None

    def decrement_ice(self, is_equip=False):
        if self.effect_ice is not None:
            if self.timer_ice > 0:
                if is_equip is False:
                    self.hp = int(self.hp - self.hp*0.001)
                try:
                    dec = 2 if self.is_clear else 1
                except AttributeError:
                    dec = 1
                self.timer_ice = max(0, self.timer_ice-dec)
            if self.timer_ice == 0:
                self.effect_ice = None
                try:
                    self.calc_movespeed()
                except AttributeError:
                    self.movespeed = self.defaultmovespeed

    def decrement_wind(self):
        if self.effect_wind is not None:
            if self.timer_wind > 0:
                try:
                    dec = 2 if self.is_clear else 1
                except AttributeError:
                    dec = 1
                self.timer_wind = max(0, self.timer_wind-dec)
            if self.timer_wind == 0:
                self.effect_wind = None
                self.attack_waittime = self.set_attack_waittime()

    def update(self):
        raise NotImplementedError

    def draw_damage_effect(self):
        if self.timer_damaged%5 in (1,3):
            px.circ(*self.address, 9, px.COLOR_WHITE)
        if self.timer_magicdamaged%5 in (2,4):
            px.circ(*self.address, 9, px.COLOR_RED)


class UserCharacter(Character):
    def __init__(self, di, move_type, address, image_source, name, 
                 strength, dexterity, agility, intelligence, vitality, luck):
        #引数から設定
        super().__init__(move_type, address, image_source, name, 0, di, 0, 0)
        self.di.user = self #DI登録
        self.defaulthp = 100
        self.defaultmp = 10
        self.defaultparam = {"str":strength, "dex":dexterity, "agl":agility,
                             "int":intelligence, "vit":vitality, "lck":luck}
        
        #デフォルト値（キャラ作成後に初期化されない値）
        self.is_clear = False #NG+データフラグ
        self.mana_drain_rate = 100 #単位％　取得マナのexp化割合
        self.mastery = {"wand":100.0, "sword":100.0, "spear":100.0, "axe":100.0} #武器種の熟練度　全武器に有効
        self.food = 1000
        self.weapon = None #装備中のオブジェクト
        self.armor = None #装備中のオブジェクト
        self.shield = None #装備中のオブジェクト
        self.perk_list = set() #取得済パークのID
        self.skill_list = set() #取得済スキルのID
        self.skillbook = {"a":None,"b":None,"x":None,"y":None} #割当スキル(_dict_skill->SkillModel
        self.rune_effects = dict() #パーク、アビリティ、ルーンによる能力向上効果のIDと累積値
        self.user_scene = G_.GameState.TITLE
        self.defaultevade = {"gauge_max":100,
                             "gauge":100,
                             "cost":30,
                             "speed":2.0,
                             "range":48,
                             "recover_delay":G_.GAME_FPS//2,
                             }
        self.reset_param()
        self.set_evade_param()

        #キャラ選択に応じた初期パラメータ＆装備
        if self.name == "戦士型":
            self.char_type = 0
            equip_list = [160,240,340]
        elif self.name == "魔法使い型":
            self.char_type = 1
            equip_list = [100,200,300]
            default_skill_list = ["701","703"]
            button_list = ["x","y"]
            for i,skill_id in enumerate(default_skill_list):
                skill_dict = item.ItemManager.get_skill_by_id(skill_id)
                self.skillbook[button_list[i]] = skill.SkillModel(self.di,
                                                                  [list(skill_dict.keys())[0],
                                                                   list(skill_dict.values())[0]],
                                                                   self)
                self.skill_list.add(skill_id)
        elif self.name == "バランス型":
            self.char_type = 2
            equip_list = [140,220,320]

        self.equip_id = []
        for item_id in equip_list:
            self.equip_id.append(item.ItemManager.create_item(item_id, G_.ItemStatus.EQUIP))
        for id in self.equip_id:
            self.equip_item(id)

        self.reset_state()

        self.prev_hp = self.maxhp
        han = "0123456789"
        zen = "０１２３４５６７８９"
        self.h2z = str.maketrans(han,zen)

    def __getstate__(self):
        """pickle保存時: 不要なオブジェクトを除外"""
        # common_funcの関数で di, image_*, *_window, *_menu を削除
        return comf.get_clean_state(self)

    def resume(self, di):
        """ロード後の復帰処理"""
        self.di = di
        self.reset_param()
        self.reset_state()

    def reset_param(self):
        '''拠点帰還後のキャラクターパラメータの初期化'''
        self.level = 0
        self.bonusparam = {"str":0, "dex":0, "agl":0, "int":0, "vit":0, "lck":0}
        self.is_bonus = [0,0,0,0,0,0,0,0,0,0,0] #ボーナス効果中値 const.BonusType
        self.movespeed = 4
        self.calc_maxhp()
        self.calc_maxmp()
        self.hp = self.maxhp
        self.mp = self.maxmp
        self.mana = {"exp":0,"stock":0,"stockmax":self.di.base.stock_mana_max} #マナの取得量
        self.nowlevel_exp = 0
        self.is_evasion = False #回避中フラグ
        self.is_safeescape = False #翼の長靴による安全脱出
        self.is_buff = [False,False,False,False,False,False,False] #バフ効果中フラグ const.BuffType
        self.key = 0 #鍵　青宝箱を開ける
        self.food = 0
        self.mattock = 0 #鶴嘴　障害物を壊す
        self.score = 0 #プレイスコア
        self.timer_item = [0,0,0,0,0,0,0] #砂時計、隠れ蓑、紅玉石、飲み薬、天馬の羽、守り札
        for skill in self.skillbook.values():
            if skill is not None:
                skill.timer_recast=0

    def reset_state(self):
        '''ユーザテンポラリ情報の初期化（階層移動時の処理と共通）'''
        self.direction = 0
        self.weapon.is_attacking = False
        self.weapon.motion_counter = 0
        self.weapon.hitlist.clear()
        for skill in self.skillbook.values():
            if skill is not None:
                skill.clear_activeskill()
        self.is_evasion = False
        self.evade["timer"] = 0
        self.evade["recover_wait"] = 0
        self.evade["gauge"] = self.evade["gauge_max"]
        self.timer_action = 0
        self.timer_attack = 0
        self.timer_damaged = 0
        self.timer_magicdamaged = 0
        self.timer_invincible = 0
        self.timer_fire = 0 #デバフ（炎）タイマー
        self.effect_fire = None #デバフ効果
        self.timer_ice = 0 #デバフ（氷）タイマー
        self.effect_ice = None #デバフ効果
        self.timer_wind = 0 #デバフ（風）タイマー
        self.effect_wind = None #デバフ効果
        self.timer_food = 8 * G_.GAME_FPS

        self.image_position = 0
        armor = item.ItemManager.get_item(self.equip_id[1])
        self.image_source = [self.direction, armor.type_id%4*16, 16,16]
        self.is_dead = False
        self.is_use_item = False

        self.mp = self.maxmp
        self.calc_movespeed()
        self.action_waittime = self.set_action_waittime()
        self.attack_waittime = self.set_attack_waittime()
        self.popupdamage = [] # [ [damage,counter],... ]

    def user_levelup(self):
        '''道中のキャラクターレベルアップ'''
        i = self.level
        while True:
            need_exp = (i+1)**2*100 + self.nowlevel_exp
            if need_exp < self.mana["exp"]:
                self.nowlevel_exp = need_exp
                i+=1
            else:
                break
        for _ in range(i - self.level):
            self.level += 1
            px.play(0, G_.SNDEFX["lvup"], resume=True)
            if self.di.flg.is_levelup is False:
                self.di.app.notice_window.message_text = self.di.flg.notice_rule(G_.FlagNotice.LEVELUP)
            bonusbox = [["str","vit"],["int","lck"],["dex","agl"]]
            self.bonusparam = {dic_[0]:dic_[1]+2 
                               if dic_[0] in bonusbox[self.char_type] else dic_[1] 
                               for dic_ in 
                               {key:val+px.rndi(1,3) for key,val 
                                in self.bonusparam.items()}.items()}
            self.calc_maxhp()
            self.calc_maxmp()
            self.mp = min(self.maxmp, self.mp+self.maxmp//4)
            if self.hp < self.maxhp:
                self.hp = min(self.maxhp, int(self.hp+self.maxhp*0.08))
            self.set_evade_param()

    def set_rune_effect(self, rune:list):
        '''パーク一覧及びルーン効果一覧への設定'''
        val = self.rune_effects.get(rune[0],[0,0])[1]
        self.rune_effects[rune[0]] = (rune[1][G_.JsonRune.FUNC_EFX],
                                        val+rune[1][G_.JsonRune.VALUE])
        match rune[0]:
            case G_.RuneList.VITAL.value:
                self.calc_maxhp()
            case G_.RuneList.DASH.value:
                self.calc_movespeed()
        self.set_evade_param()

    def remove_rune_effect(self, rune:list):
        '''ルーン効果一覧からの削除'''
        current_data = self.rune_effects.get(rune[0], [0, 0])
        val = current_data[1]
        remaining_val = val - rune[1][G_.JsonRune.VALUE]
        
        # 修正: 浮動小数点の誤差を考慮し、0以下なら削除とする
        if remaining_val <= 0.0001: 
            self.rune_effects.pop(rune[0], None) # None指定でエラー回避
        else:
            # 関数ポインタ等は更新せず、値だけ更新でも良いが、元の実装通り上書きでOK
            self.rune_effects[rune[0]] = (rune[1][G_.JsonRune.FUNC_EFX], remaining_val)
            
        self.set_evade_param()

    def get_rune_effect(self, rune_id):
        '''ルーン効果一覧から効果値の取得'''
        rune_effect = self.rune_effects.get(rune_id.value)
        return (None if rune_effect is None else [getattr(rune, rune_effect[0]),rune_effect[1]])

    def set_evade_param(self):
        self.evade = {"gauge_max":self.defaultevade["gauge_max"],
                      "gauge":self.defaultevade["gauge"],
                      "cost":self.defaultevade["cost"],
                      "speed":self.defaultevade["speed"],
                      "range":self.defaultevade["range"],
                      "timer":0,
                      "recover_delay":self.defaultevade["recover_delay"],
                      "recover_wait":0}
        recover_rate = self.get_rune_effect(G_.RuneList.HIGAIN)
        recover_rate_bonus = 1 if recover_rate is None else recover_rate[1]
        self.evade["recover_rate"] = 1.15*(self.agility/100)*recover_rate_bonus

        range_ = self.rune_effects.get(G_.RuneList.LONGDASH.value)
        if range_:
            self.evade["range"] = self.defaultevade["range"] * range_[1]
        gauge_max = self.rune_effects.get(G_.RuneList.STAMINA.value)
        if gauge_max:
            self.evade["gauge_max"] = self.defaultevade["gauge_max"] * gauge_max[1]
        cost = self.rune_effects.get(G_.RuneList.RDCEVADE.value)
        if cost:
            self.evade["cost"] = self.defaultevade["cost"] * cost[1]
        recover_delay = self.rune_effects.get(G_.RuneList.REDUCTION.value)
        if recover_delay:
            self.evade["recover_delay"] = self.defaultevade["recover_delay"] * recover_delay[1]

    @property
    def inventory_max(self):
        #パーク効果
        perk = self.get_rune_effect(G_.RuneList.CARGO)
        if perk is None:
            pval = 0
        else:
            pval = perk[1]
        return 8*(3+pval)+8

    @property
    def strength(self):
        #パーク効果
        perk = self.get_rune_effect(G_.RuneList.STR)
        if perk is None:
            pval = 0
        else:
            pval = perk[1]
        return (self.defaultparam["str"]+self.bonusparam["str"])+pval

    @property
    def dexterity(self):
        #パーク効果
        perk = self.get_rune_effect(G_.RuneList.DEX)
        if perk is None:
            pval = 0
        else:
            pval = perk[1]
        return (self.defaultparam["dex"]+self.bonusparam["dex"])+pval

    @property
    def agility(self):
        #パーク効果
        perk = self.get_rune_effect(G_.RuneList.AGL)
        if perk is None:
            pval = 0
        else:
            pval = perk[1]
        return (self.defaultparam["agl"]+self.bonusparam["agl"])+pval

    @property
    def intelligence(self):
        #パーク効果
        perk = self.get_rune_effect(G_.RuneList.INT)
        if perk is None:
            pval = 0
        else:
            pval = perk[1]
        return (self.defaultparam["int"]+self.bonusparam["int"])+pval

    @property
    def vitality(self):
        #パーク効果
        perk = self.get_rune_effect(G_.RuneList.CON)
        if perk is None:
            pval = 0
        else:
            pval = perk[1]
        return (self.defaultparam["vit"]+self.bonusparam["vit"])+pval

    @property
    def luck(self):
        #パーク効果
        perk = self.get_rune_effect(G_.RuneList.LUK)
        if perk is None:
            pval = 0
        else:
            pval = perk[1]
        return (self.defaultparam["lck"]+self.bonusparam["lck"])+pval

    def calc_maxhp(self):
        rune_effect = self.get_rune_effect(G_.RuneList.VITAL)
        if rune_effect is not None:
            bonus_rate = rune_effect[1]
        else:
            bonus_rate = 1
        bonus_rate2 = 1+(self.is_bonus[G_.BonusType.MAXHP])/100
            
        self.maxhp = int((self.defaulthp+self.vitality+(self.level*self.vitality*10))
                         *bonus_rate*bonus_rate2)

    def calc_maxmp(self):
        self.maxmp = int(self.defaultmp+(self.level*(self.intelligence/16))+(self.intelligence/6))

    @property
    def inventory(self):
        return item.ItemManager.get_item_by_state(G_.ItemStatus.BUGGAGE)

    def buff_effect(self, id):
        match id:
            case G_.BuffType.TIMESTOP:
                pass    
            case G_.BuffType.HIDDEN:
                pass    
            case G_.BuffType.POWERUP:
                pass    
            case G_.BuffType.ARCANEUP:
                pass    
            case G_.BuffType.SPEEDUP:
                self.calc_movespeed()
            case G_.BuffType.DIFLECT:
                pass    
            case G_.BuffType.REFLECT:
                pass    
 
    #移動速度算出
    def calc_movespeed(self):
        #バフ効果
        agiup = 2 if self.is_buff[G_.BuffType.SPEEDUP] else 0
        #パーク：移動速度UP
        rune_effect = self.get_rune_effect(G_.RuneList.DASH)
        agiup += rune_effect[1] if rune_effect is not None else 0

        self.movespeed = self.armor.movespeed + agiup
        if self.timer_ice > 0:
            self.movespeed = self.movespeed//2

    @property
    def reduce_element(self):
        #属性ダメージカット
        regist_bonus = []
        for rune_id in (G_.RuneList.RDCFIRE,G_.RuneList.RDCICE,
                        G_.RuneList.RDCWIND,G_.RuneList.RDCEARTH):
            rune_effect = self.get_rune_effect(rune_id)
            if rune_effect is None:
                regist_bonus.append(0)
            else:
                regist_bonus.append(rune_effect[1])

        bonus_rate = 1+(self.is_bonus[G_.BonusType.REDUCEALL])/100
        val = (self.vitality/10)*bonus_rate
        val_fire = min(99.99,val + self.is_bonus[G_.BonusType.REGISTFIRE] + regist_bonus[0])
        val_ice = min(99.99,val + self.is_bonus[G_.BonusType.REGISICE] + regist_bonus[1])
        val_wind = min(99.99,val + self.is_bonus[G_.BonusType.REGISTWIND] + regist_bonus[2])
        val_earth = min(99.99,val + self.is_bonus[G_.BonusType.REGISTEARTH] + regist_bonus[3])
        return {'fire':val_fire,'ice':val_ice,'wind':val_wind,'earth':val_earth}

    @property
    def attack(self):
        buffbonus = 2 if self.is_buff[G_.BuffType.POWERUP] else 1
        bonus = 1 + self.is_bonus[G_.BonusType.ATTACK]/100
        type_name = G_.ItemType.NAME[self.weapon.type_id]
        rune_effect1 = None
        #パーク：武器マスタリ
        match self.weapon.type_id:
            case G_.ItemType.WAND:
                perk_no = G_.RuneList.WAND
            case G_.ItemType.SWORD:
                perk_no = G_.RuneList.SWORD
            case G_.ItemType.SPEAR:
                perk_no = G_.RuneList.SPEAR
            case G_.ItemType.AXE:
                perk_no = G_.RuneList.AXE
        rune_effect1 = self.get_rune_effect(perk_no)
        if rune_effect1 is not None:
            basevalue = rune_effect1[0](self.di, self.weapon, rune_effect1[1])
        else:
            basevalue = self.weapon.value
        #パーク：攻撃力UP
        rune_effect2 = self.get_rune_effect(G_.RuneList.ATTACK)
        perk_bonus = (100+rune_effect2[1])/100 if rune_effect2 is not None else 1
        return int((basevalue*self.mastery[type_name]/100+self.weapon.mastery/10)
                   *max(1,(self.weapon.mastery+self.strength)/90)
                   *perk_bonus*bonus*buffbonus)                

    @property
    def defend(self):
        bonus = 1 + self.is_bonus[G_.BonusType.DEFEND]/100
        rune_effect = None
        #パーク：防具マスタリ
        match self.armor.type_id:
            case G_.ItemType.ROBE:
                perk_no = G_.RuneList.ROBE
            case G_.ItemType.LEATHER:
                perk_no = G_.RuneList.LEATHER
            case G_.ItemType.CHAIN:
                perk_no = G_.RuneList.CHAIN
            case G_.ItemType.PLATE:
                perk_no = G_.RuneList.PLATE

        rune_effect = self.get_rune_effect(perk_no)
        if rune_effect is not None:
            basevalue_armor = rune_effect[0](self.di, self.armor, rune_effect[1])
        else:
            basevalue_armor = self.armor.value

        #パーク：盾マスタリ
        match self.shield.type_id:
            case G_.ItemType.BUNGLE:
                perk_no = G_.RuneList.BUNGLE
            case G_.ItemType.ROUND:
                perk_no = G_.RuneList.ROUND
            case G_.ItemType.KITE:
                perk_no = G_.RuneList.KITE
            case G_.ItemType.TOWER:
                perk_no = G_.RuneList.TOWER

        rune_effect1 = self.get_rune_effect(perk_no)
        if rune_effect1 is not None:
            basevalue_shield = rune_effect1[0](self.di, self.shield, rune_effect1[1])
        else:
            basevalue_shield = self.shield.value

        #パーク：防御UP
        rune_effect = self.get_rune_effect(G_.RuneList.DEFEND)
        perk_bonus = (100+rune_effect[1])/100 if rune_effect is not None else 1

        return int((basevalue_armor+(self.vitality/100)
                    +basevalue_shield+(self.dexterity/100))*perk_bonus*bonus)

    @property
    def arcane(self):
        buffbonus = 2 if self.is_buff[G_.BuffType.ARCANEUP] else 1
        wandbonus = self.weapon.value/2*(self.mastery["wand"]/100) if self.weapon.type_id == G_.ItemType.WAND else 0
        bonus = 1 + self.is_bonus[G_.BonusType.ARCANE]/100 + (1 if wandbonus else 0)
        
        #パーク：魔力UP
        rune_effect = self.get_rune_effect(G_.RuneList.ARCANE)
        perk_bonus = (100+rune_effect[1])/100 if rune_effect is not None else 1

        return int(((self.intelligence/8+wandbonus)+(self.level**1.756))*perk_bonus*bonus*buffbonus)

    #アイテム装備処理
    def equip_item(self, item_uuid):
        new_equip_item = item.ItemManager.get_item(item_uuid)
        item_type = new_equip_item.type_id
        #武器
        if item_type in (0,1,2,3):
            self.equip_id[0] = item_uuid
            self.weapon = new_equip_item
        #防具
        elif item_type in (4,5,6,7):
            self.equip_id[1] = item_uuid
            self.armor = new_equip_item
            #防具を装備した場合は見た目と移動速度が変化する（ダメージ減衰は攻撃ルーチン内で処理）
            self.image_source[1] = item_type%4*16
            self.calc_movespeed()
        #盾
        elif item_type in (8,9,10,11):
            self.equip_id[2] = item_uuid
            self.shield = new_equip_item

    #熟練度上昇
    def grow_exp(self, exp):
        bonus = 3 if self.is_clear else 1
        if exp < 255:
            if exp < 48:
                exp += 1.28 * bonus
            elif exp < 64:
                exp += 0.64 * bonus
            elif exp < 80:
                exp += 0.32 * bonus
            elif exp < 96:
                exp += 0.16 * bonus
            elif exp < 112:
                exp += 0.08 * bonus
            elif exp < 128:
                exp += 0.04 * bonus
            elif exp < 144:
                exp += 0.02 * bonus
            elif exp < 160:
                exp += 0.01 * bonus
            else:
                if px.rndi(64,128) >= exp//2:
                    exp += 0.01 * bonus
            exp = min(255,exp)
        return exp

    #武器熟練上昇
    def grow_weapon(self):
        self.weapon.mastery = self.grow_exp(self.weapon.mastery)

    def mana_division(self, mana):
        '''取得マナを分配率に応じて経験値とストックに振り分け'''
        getexp = max(1,int(mana * self.mana_drain_rate/100))
        stockmana = mana - getexp
        self.mana["exp"] += getexp
        self.mana["stock"] = min(self.mana["stockmax"], self.mana["stock"] + stockmana)
        return getexp

    #入力キーチェック
    def check_inputkey(self):
        #攻撃中、回避中は何もできない
        if self.timer_attack > 0 or self.is_evasion:
            return None
        _return_code = None
        btn = comf.get_button_state()
    #タイマーに関係なく実行できる操作(ただしボス戦中は魔法選択のみ、呼び出し元で制御)
        #方向転換は最優先
        if btn["u"]:
            self.direction = _return_code = 3
        elif btn["l"]:
            self.direction = _return_code  = 1
        elif btn["d"]:
            self.direction = _return_code  = 0
        elif btn["r"]:
            self.direction = _return_code  = 2

        #長押し要求操作は優先
        if btn["L"]:
            skill_index = ""
            if btn["a"] and self.skillbook["a"] is not None:
                skill_index = "a"
            elif btn["b"] and self.skillbook["b"] is not None:
                skill_index = "b"
            elif btn["x"] and self.skillbook["x"] is not None:
                skill_index = "x"
            elif btn["y"] and self.skillbook["y"] is not None:
                skill_index = "y"

            if skill_index:
                self.skillbook[skill_index].cast_skill()
            if self.timer_action>0:
                return
        #メニュー表示
        elif btn["b"]:
            _return_code =  7
    #攻撃タイマー中は攻撃不可
        #攻撃
        elif btn["a"]:
            self.weapon.is_attacking = True
            #パーク：攻撃速度UP
            rune_effect = self.get_rune_effect(G_.RuneList.HASTE)
            perk_bonus = rune_effect[1] if rune_effect is not None else 1
            attack_speed = self.weapon.attack_speed / perk_bonus# * perk_bonus
            self.timer_attack = int(G_.GAME_FPS//19
                                    + (self.attack_waittime
                                        * attack_speed
                                        * ((100-self.is_bonus[G_.BonusType.ATTACKSPEED])*0.01))
                                        * self.shield.rate_attackspeed / perk_bonus)
            self.weapon.motion_frames = self.timer_attack
            _return_code = 4
        else:
            #回避
            if btn["x"]:
                #回避不可条件チェック（回避中、ゲージ不足）
                if self.is_evasion or self.evade["gauge"]<self.evade["cost"]:
                    return
                self.evade["gauge"] = max(0, self.evade["gauge"]-self.evade["cost"])
                self.evade["timer"] = self.evade["range"] // self.evade["speed"] // self.movespeed
                self.evade["recover_wait"] = self.evade["recover_delay"]
                self.is_evasion = True

                _return_code =  5
            if self.timer_action>0:
                return
            #アイテム使用
            elif btn["y"]:
                if self.mattock and self.di.app.game_state in (G_.GameState.DUNGEON,
                                                               G_.GameState.DUNGEON_CAVE,
                                                               G_.GameState.DUNGEON_MAZE):
                    self.is_use_item = True
                else:
                    px.play(3, G_.SNDEFX["miss"], resume=True)
                _return_code =  6
            elif self.timer_attack > 0 or self.is_evasion:
                return _return_code
            else:
                #移動は攻撃タイマ―中も不可
                to_dir = 9
                if btn["u"]:
                    to_dir = 3
                elif btn["l"]:
                    to_dir = 1
                elif btn["d"]:
                    to_dir = 0
                elif btn["r"]:
                    to_dir = 2
                if to_dir != 9:
                    self.direction = to_dir
                    _return_code =  self.direction

        if _return_code in (0,1,2,3):
            self.timer_action += self.action_waittime

        return _return_code

    def evasion(self):
        if self.evade["timer"] <= 0:
            self.is_evasion = False
            return
        self.move_address(self.user_scene, int(self.movespeed*self.evade["speed"]+self.is_bonus[G_.BonusType.EVADELENGTH]//5) )

    #ユーザ専用カウンタ減算
    def user_timer_decrement(self):
        self.common_timer_decrement()
        self.timer_invincible = max(0, self.timer_invincible-1)
        self.timer_food = max(0, self.timer_food-1)
        #MP回復
        recv_mp_rate = 2 if self.armor.type_id == G_.ItemType.ROBE else 1
        recv_mp = ((self.intelligence/16+self.level/64)/(G_.GAME_FPS*1.5)) * recv_mp_rate
        self.mp = min(self.maxmp, self.mp+recv_mp)
        #回避処理
        self.evade["timer"] = max(0, self.evade["timer"]-1)
        self.evade["recover_wait"] = max(0, self.evade["recover_wait"]-1)
        if self.evade["recover_wait"] <= 0:
            self.evade["gauge"] = min(self.evade["gauge_max"],
                                      self.evade["gauge"]+self.evade["recover_rate"])
        #アイテムタイマー減算
        for i,t in enumerate(self.timer_item):
            self.timer_item[i] = max(0, t-1)

        if px.frame_count%G_.GAME_FPS == G_.GAME_FPS//2:
            if self.get_rune_effect(G_.RuneList.EXTING) is not None:
                self.decrement_fire(True)
            if self.get_rune_effect(G_.RuneList.WARMTH) is not None:
                self.decrement_ice(True)
            if self.get_rune_effect(G_.RuneList.BREEZE) is not None:
                self.decrement_wind()

    # def move_address(self, scene:int=0, move_length:int=1):
    def move_address(self, scene:int=0, move_length:int=1, box=None):
        self.image_position = 1 - self.image_position
        if scene == 40:
            layer = G_.TilemapIndex.OBSTACLE
            checklist = [(2,0),(3,0),(4,0),(5,0),
                         (2,1),(3,1),(4,1),(5,1)]
            checklist+= [(2,2),(3,2),(4,2),(5,2),
                         (2,3),(3,3),(4,3),(5,3)]
            checklist+= [(2,4),(3,4),(4,4),(5,4),
                         (2,5),(3,5),(4,5),(5,5)]
            checklist+= [(9,30),(10,30),
                         (9,31),(10,31)]
            checktype = None
        elif scene in (70,75):
            layer = 1
            checklist = [(8,1)]
            checktype = None

        for _ in range(move_length):
            destination = [self.address[0] + (G_.CHARA_DIR[self.direction][0]),
                           self.address[1] + (G_.CHARA_DIR[self.direction][1])]
            if comf.check_hit_tile(self, layer, checklist, checktype):
                break
            #宝箱開錠判定実行
            prev_address = self.address.copy()
            self.address = destination
            if box is not None:
                if box.is_placed and box.is_opened is False:
                    if self.di.app.pick_treasurebox(box) is False:
                        self.address = prev_address
            # self.address = destination
        return None

    def update(self):
        if self.is_dead:
            self.gem = 0
            self.mana["exp"] = 0

        self.image_source[0] = self.direction*32 + 16*self.image_position

        #食料消費と回復（フィールドとダンジョンのみ）
        if self.user_scene in (30,40) and self.timer_food <= 0:
            #パーク：食糧消費間隔増加
            rune_effect = self.get_rune_effect(G_.RuneList.FUELEFF)
            perk_bonus = rune_effect[1] if rune_effect is not None else 1

            self.timer_food = 5 * G_.GAME_FPS * perk_bonus
            item.func_effect_item31(self)

        for key,skill in self.skillbook.items():
            if skill is not None:
                skill.update()

        #タイマーアイテム効果消失
        if self.is_buff[G_.BuffType.TIMESTOP] and self.timer_item[G_.BuffType.TIMESTOP] == 0:
            self.is_buff[G_.BuffType.TIMESTOP] = False
            self.di.message_manager.add_message(f"{G_.BUFF_DESC[G_.BuffType.TIMESTOP]} 効果終了", px.COLOR_ORANGE)
        if self.is_buff[G_.BuffType.HIDDEN] and self.timer_item[G_.BuffType.HIDDEN] == 0:
            self.is_buff[G_.BuffType.HIDDEN] = False
            self.di.message_manager.add_message(f"{G_.BUFF_DESC[G_.BuffType.HIDDEN]} 効果終了", px.COLOR_ORANGE)
        if self.is_buff[G_.BuffType.POWERUP] and self.timer_item[G_.BuffType.POWERUP] == 0:
            self.is_buff[G_.BuffType.POWERUP] = False
            self.di.message_manager.add_message(f"{G_.BUFF_DESC[G_.BuffType.POWERUP]} 効果終了", px.COLOR_ORANGE)
        if self.is_buff[G_.BuffType.ARCANEUP] and self.timer_item[G_.BuffType.ARCANEUP] == 0:
            self.is_buff[G_.BuffType.ARCANEUP] = False
            self.di.message_manager.add_message(f"{G_.BUFF_DESC[G_.BuffType.ARCANEUP]} 効果終了", px.COLOR_ORANGE)
        if self.is_buff[G_.BuffType.SPEEDUP] and self.timer_item[G_.BuffType.SPEEDUP] == 0:
            self.is_buff[G_.BuffType.SPEEDUP] = False
            self.di.message_manager.add_message(f"{G_.BUFF_DESC[G_.BuffType.SPEEDUP]} 効果終了", px.COLOR_ORANGE)
            self.calc_movespeed()
            self.action_waittime = self.set_action_waittime()
        if self.is_buff[G_.BuffType.DIFLECT] and self.timer_item[G_.BuffType.DIFLECT] == 0:
            self.is_buff[G_.BuffType.DIFLECT] = False
            self.di.message_manager.add_message(f"{G_.BUFF_DESC[G_.BuffType.DIFLECT]} 効果終了", px.COLOR_ORANGE)
        if self.is_buff[G_.BuffType.REFLECT] and self.timer_item[G_.BuffType.REFLECT] == 0:
            self.is_buff[G_.BuffType.REFLECT] = False
            self.di.message_manager.add_message(f"{G_.BUFF_DESC[G_.BuffType.REFLECT]} 効果終了", px.COLOR_ORANGE)

        if self.is_evasion:
            self.evasion()
            return

        #攻撃モーション
        if self.weapon.is_attacking:
            self.weapon.update()

        #ポップアップダメージ更新（ボス戦のみ）
        if self.user_scene in (G_.GameState.BOSSBATTLE,G_.GameState.LASTBOSS) and self.prev_hp != self.hp:
            damage = f"{abs(int(self.prev_hp-self.hp)):,}"
            dmgcol = 30 if self.prev_hp>self.hp else 28
            self.popupdamage.append([damage.translate(self.h2z),0,dmgcol])
            self.prev_hp = self.hp

    def draw(self):
        for key,skill in self.skillbook.items():
            if skill is not None:
                skill.draw()

        if self.is_dead:
            return

        if self.is_use_item:
            px.play(3, G_.SNDEFX["item"], resume=True)
            px.cls(7)
            self.is_use_item = False

        #隠れ蓑用スプライト
        if self.timer_item[G_.BuffType.HIDDEN] > 0:
            imagesource_type = item.func_effect_item12(self)
        else:
            imagesource_type = self.image_source[1]

        #攻撃モーションスプライト
        x,y = self.address[0]-8, self.address[1]-8
        if self.weapon.is_attacking:
            px.blt(x, y, G_.IMGIDX["CHAR"],
                128+self.direction*16,imagesource_type, self.image_source[2],self.image_source[3],
                colkey=3)
        else:
            chasize = 2 if self.user_scene == G_.GameState.BASE else 1
            px.blt(x, y, G_.IMGIDX["CHAR"],
                self.image_source[0],imagesource_type,
                self.image_source[2],self.image_source[3],
                colkey=3, scale = chasize)
        self.draw_damage_effect()

        #武器攻撃モーション
        if self.weapon.is_attacking:
            if self.weapon.motion_counter == 1:
                px.play(3, G_.SNDEFX["attack"], resume=True)
            self.weapon.func_attackmotion(self.weapon, *self.address, self.direction)

        if self.user_scene == G_.GameState.BASE:
            return

        #戦闘情報
        if self.user_scene in (G_.GameState.DUNGEON,G_.GameState.BOSSBATTLE,G_.GameState.LASTBOSS):
            xoffset = 0 if self.user_scene == G_.GameState.DUNGEON else px.width-G_.WND_MAIN[2]
            #回避エフェクト
            if self.is_evasion:
                px.blt(x, y, G_.IMGIDX["CHIP"],*G_.ImageAddress.EVASION, colkey=px.COLOR_BLACK)
            #回避ゲージ
            gaugelength = 32*(self.evade["gauge_max"]/100)
            evadebar = self.evade["gauge"]/self.evade["gauge_max"]*gaugelength #現在値比率
            px.rect(self.address[0]-gaugelength//2,self.address[1]+9, gaugelength, 2, 24) #下地
            px.rect(self.address[0]-gaugelength//2,self.address[1]+9, evadebar, 2, 27) #現在値
            #MPゲージ
            mpbar = self.mp/self.maxmp*100 #現在値比率
            px.rect(2,px.height-G_.ImageAddress.MPBAR[3]-2+4, 100, 12, 24) #下地
            px.rect(2,px.height-G_.ImageAddress.MPBAR[3]-2+4, mpbar, 12, 1) #現在値
            px.text(2+32,px.height-G_.ImageAddress.MPBAR[3]-2+3+4,"Magic Point",px.COLOR_WHITE)
            px.blt(2,px.height-G_.ImageAddress.MPBAR[3]-2,G_.IMGIDX["CHIP"],
                   *G_.ImageAddress.MPBAR,colkey=px.COLOR_BLACK)
            #スキルボタン
            px.blt(230+xoffset,G_.WND_MAIN[3]-G_.ImageAddress.BUTTON["ang"][3]-2,
                   G_.IMGIDX["CHIP"],*G_.ImageAddress.BUTTON["ang"],colkey=px.COLOR_BLACK)
            px.blt(246+xoffset,G_.WND_MAIN[3]-G_.ImageAddress.BUTTON["bng"][3]-2,
                   G_.IMGIDX["CHIP"],*G_.ImageAddress.BUTTON["bng"],colkey=px.COLOR_BLACK)
            px.blt(262+xoffset,G_.WND_MAIN[3]-G_.ImageAddress.BUTTON["xng"][3]-2,
                   G_.IMGIDX["CHIP"],*G_.ImageAddress.BUTTON["xng"],colkey=px.COLOR_BLACK)
            px.blt(278+xoffset,G_.WND_MAIN[3]-G_.ImageAddress.BUTTON["yng"][3]-2,
                   G_.IMGIDX["CHIP"],*G_.ImageAddress.BUTTON["yng"],colkey=px.COLOR_BLACK)
            for key,skill in self.skillbook.items():
                if skill:
                    size = int(12-skill.timer_recast/skill.recast_time*12)
                    match key:
                        case "a":
                            px.blt(230+xoffset,
                                   G_.WND_MAIN[3]-G_.ImageAddress.BUTTON["ang"][3]-2+12-size,
                                   G_.IMGIDX["CHIP"],
                                   G_.ImageAddress.BUTTON["a"][0],
                                   G_.ImageAddress.BUTTON["a"][1]+14-size,
                                   G_.ImageAddress.BUTTON["a"][2],size,
                                   colkey=px.COLOR_BLACK)
                        case "b":
                            px.blt(246+xoffset,G_.WND_MAIN[3]-G_.ImageAddress.BUTTON["bng"][3]-2+12-size, G_.IMGIDX["CHIP"],
                                   G_.ImageAddress.BUTTON["b"][0],
                                   G_.ImageAddress.BUTTON["b"][1]+14-size,
                                   G_.ImageAddress.BUTTON["b"][2],size,
                                   colkey=px.COLOR_BLACK)
                        case "x":
                            px.blt(262+xoffset,G_.WND_MAIN[3]-G_.ImageAddress.BUTTON["xng"][3]-2+12-size, G_.IMGIDX["CHIP"],
                                   G_.ImageAddress.BUTTON["x"][0],
                                   G_.ImageAddress.BUTTON["x"][1]+14-size,
                                   G_.ImageAddress.BUTTON["x"][2],size,
                                   colkey=px.COLOR_BLACK)
                        case "y":
                            px.blt(278+xoffset,G_.WND_MAIN[3]-G_.ImageAddress.BUTTON["yng"][3]-2+12-size, G_.IMGIDX["CHIP"],
                                   G_.ImageAddress.BUTTON["y"][0],
                                   G_.ImageAddress.BUTTON["y"][1]+14-size,
                                   G_.ImageAddress.BUTTON["y"][2],size,
                                   colkey=px.COLOR_BLACK)
            #マナ瓶
            if self.mana["stockmax"]>0:
                flask = self.mana["stock"]/self.mana["stockmax"]*14
                px.rect(G_.WND_MAIN[2]-G_.ImageAddress.MANAPOT[2]-2+1+xoffset,
                        G_.WND_MAIN[3]-G_.ImageAddress.MANAPOT[3]-2+4+(14-flask),36,flask,19)
                px.blt(G_.WND_MAIN[2]-G_.ImageAddress.MANAPOT[2]-2+xoffset,
                       G_.WND_MAIN[3]-G_.ImageAddress.MANAPOT[3]-2,G_.IMGIDX["CHIP"],
                       *G_.ImageAddress.MANAPOT,colkey=px.COLOR_BLACK)
                if self.mana["stock"]==self.mana["stockmax"]:
                    px.text(G_.WND_MAIN[2]-G_.ImageAddress.MANAPOT[2]+11+xoffset,
                            G_.WND_MAIN[3]-G_.ImageAddress.MANAPOT[3]-1+11,"FULL",px.frame_count%16)
            #バフ状況
            for i,buff in enumerate(self.timer_item):
                if buff:
                    if i == 6:
                        px.blt((16+4)*i,0,G_.IMGIDX["CHIP"],*G_.ImageAddress.ITEM[35],
                            colkey=px.COLOR_BLACK,scale=0.5)
                    else:
                        px.blt((16+4)*i,0,G_.IMGIDX["CHIP"],*G_.ImageAddress.ITEM[i+13+7],
                            colkey=px.COLOR_BLACK,scale=0.5)
                    px.text((16+4)*i+12,5,f"{buff//G_.GAME_FPS:<3}",px.COLOR_WHITE)
            #能力ボーナス状況
            for i,bonus in enumerate(self.is_bonus):
                if bonus:
                    px.blt(192+(16+4)*i+xoffset,0,G_.IMGIDX["CHIP"],*G_.ImageAddress.ITEM[i+13],
                           colkey=px.COLOR_BLACK,scale=0.5)
                    px.text(192+(16+4)*i+12+xoffset,5,f"{bonus:>3}",px.COLOR_WHITE)
        #ボス戦時のみダメージポップアップ   
        if self.user_scene in (G_.GameState.BOSSBATTLE,G_.GameState.LASTBOSS):
            for i,dmg in enumerate(self.popupdamage):
                px.text(self.address[0]-G_.JP_FONT.text_width(dmg[0])//2,
                        self.address[1]-self.image_source[3]//2-(dmg[1]*2),
                        dmg[0], dmg[2], G_.JP_FONT)
                self.popupdamage[i][1] += 1
            self.popupdamage = [[dmg,cnt,col] for dmg,cnt,col in self.popupdamage if cnt < G_.GAME_FPS*0.75]
                