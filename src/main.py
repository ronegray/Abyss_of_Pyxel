import pyxel as px
# --- 影付きフォント用モンキーパッチ ---
_original_text_func = px.text
def shadowed_text(x, y, s, col, font=None):
    shadow_color = 45
    # 影
    _original_text_func(x+1, y + 1, s, shadow_color, font)
    # 本文 
    _original_text_func(x, y, s, col, font)
px.text = shadowed_text

import const as G_
import common_func as comf, drawevent as evt
import base, character, dungeon, sound, message, item, menu, monster, command


class InstanceReferenceManager:
    '''DI用オブジェクト参照保持クラス'''
    def __init__(self, app):
        self.app:App = app
        self.flg:GameFlags = GameFlags()
        self.user:character.UserCharacter = None
        self.base:base.Base = None
        self.dungeon:dungeon.Floor = None
        self.monster_manager:monster.MonsterManager = None
        self.message_manager:message.comf = None
        self.menu:menu.Menu = None


class GameFlags:
    '''フラグデータ'''
    def __init__(self):
        #単体フラグ
        self.is_first = False
        self.is_newgame = False
        self.is_ritual = False
        self.is_skipOpening = None
        #v1.5.0 add
        self.is_clearbonus = False

        self.is_spawner = False
        self.is_elite = False
        self.is_revive = False        
        self.is_noticed_all = False
        self.is_attack = False
        self.is_lock = False
        self.is_evade = False
        self.is_menu = False
        self.is_mattock = False
        self.is_skill = False
        self.is_before_boss = False
        self.is_levelup = False
        self.is_escape = False
        self.is_mastery = False
        self.is_bluechest = False
        self.is_getskill = False

        self.is_storage = False
        self.is_alchemy = False
        self.is_ritual2 = False
        self.is_shop = False
        self.is_backdoor = False
        #フラグ辞書
        #魔法属性
        self.is_element = [False for _ in G_.ElementType]
        #装備品
        type_id_list =[]
        for categoryid in (G_.ItemType.CATEGORY_WEAPON,
                            G_.ItemType.CATEGORY_ARMOR,
                            G_.ItemType.CATEGORY_SHIELD):
            type_id_list += [type_id for type_id in G_.ItemType.get_items_in_category(categoryid)]
        self.is_equiptype = {str(type_id):False for type_id in type_id_list}
        #消費アイテム
        id_list = [id_ for id_ in item.ItemManager.get_item_id_by_category(G_.ItemType.CATEGORY_CONSUME)]
        self.is_consume = {str(id_):False for id_ in id_list}

    # v1.5.0
    def fix_flags(self):
        '''古いセーブデータに存在しない属性を補完する'''
        if not hasattr(self, "is_clearbonus"):
            self.is_clearbonus = False

    def clear_all_flags(self):
        for name, value in vars(self).items():
            # 単体フラグ（None含む）
            if isinstance(value, bool) or value is None:
                if name not in ("is_first","is_newgame","is_ritual"):
                    setattr(self, name, True)
            # list フラグ
            elif isinstance(value, list):
                for i in range(len(value)):
                    value[i] = True
            # tuple フラグ（再生成）
            elif isinstance(value, tuple):
                setattr(self, name, tuple(True for _ in value))
            # dict フラグ
            elif isinstance(value, dict):
                for k in value.keys():
                    value[k] = True
            else:
                pass  # 想定外型は無視

    def notice_rule(self, flg_notice_id):
        notice_message = ""
        if self.is_spawner is False and flg_notice_id == G_.FlagNotice.KILL_MONSTER:
            notice_message = "　　スポナーから湧く魔物を倒せばマナ(EXP)を吸収できる\nスポナーは様々な武具が入った宝箱を落とす"
            self.is_spawner = True
        elif self.is_lock is False and flg_notice_id == G_.FlagNotice.LOCK_DOOR:
            notice_message = "　　初めて訪れた部屋は封鎖されている\n全ての敵を倒せば封鎖を解除出来る"
            self.is_lock = True
        elif self.is_elite is False and flg_notice_id == G_.FlagNotice.POP_ELITE:
            notice_message = "スポナーは極稀に強力なエリートモンスターに変化する\n強力なぶんレア度の高いアイテムを隠し持っている"
            self.is_elite = True
        elif self.is_revive is False and flg_notice_id == G_.FlagNotice.REVIVE_SPAWNER:
            notice_message = "スポナーは極稀に復活することがある"
            self.is_revive = True
        elif self.is_before_boss is False and flg_notice_id == G_.FlagNotice.TO_BOSS:
            notice_message = "10階層毎に強敵が待ち構えている\n一度退いて体制を整えるのも作戦だ"
            self.is_before_boss = True
        elif self.is_levelup is False and flg_notice_id == G_.FlagNotice.LEVELUP:
            notice_message = "マナを吸収してレベルが上がると、ＨＰやＭＰの他、\nタイプに応じて能力値がランダムに上昇する"
            self.is_levelup = True
        elif self.is_escape is False and flg_notice_id == G_.FlagNotice.ESCAPE:
            notice_message = "エスケープでの脱出も一度は経験しておくべきだ\n持ち帰った情報を元に近道の開発が可能になる"
            self.is_escape = True
        elif self.is_mastery is False and flg_notice_id == G_.FlagNotice.MASTERY:
            notice_message = "同じ武器を使い続ける程攻撃能力が上がっていく\nアイテム固有熟練度と自身の習熟度はパラメータで確認できる"
            self.is_mastery = True
        elif self.is_bluechest is False and flg_notice_id == G_.FlagNotice.BLUECHEST:
            notice_message = "鍵の掛かった青い宝箱からしか入手できない\n特別なアイテムが幾つか存在する"
            self.is_bluechest = True
        elif self.is_storage is False and flg_notice_id == G_.FlagNotice.STORAGE:
            notice_message = "倉庫：拡張毎に容量が８増える"
            self.is_storage = True
        elif self.is_alchemy is False and flg_notice_id == G_.FlagNotice.ALCHEMY:
            notice_message = "錬金工房：Lv1 鑑定 Lv2 秘紋石結合 Lv3 秘紋石解除\n以降拡張毎に秘紋石解除の成功確率が上昇"
            self.is_alchemy = True
        elif self.is_ritual2 is False and flg_notice_id == G_.FlagNotice.RITUAL:
            notice_message = "儀式祭壇：拡張毎にマナ瓶の容量が増える　儀式：能力獲得 \n吸収率：迷宮内での成長に充てるマナ スキル：ボタン割当"
            self.is_ritual2 = True
        elif self.is_shop is False and flg_notice_id == G_.FlagNotice.SHOP:
            notice_message = "商品売買：拡張毎に高価な物が販売されるようになる"
            self.is_shop = True
        elif self.is_backdoor is False and flg_notice_id == G_.FlagNotice.BACKDOOR:
            notice_message = "迷宮近道：拡張毎に到達できる階層が深くなる\n（最深ボス討伐階層+近道Lv　ただし到達済階層迄）"
            self.is_backdoor = True
        elif self.is_getskill is False and flg_notice_id == G_.FlagNotice.GETSKILL:
            notice_message = "スキルを獲得したらボタン設定を忘れずにな！\n開発者？ってぇのもしょっちゅう忘れるって聞くぜ！"
            self.is_getskill = True

        return [notice_message]


class App():
    #アプリケーション固有情報初期化
    def init_app(self):
        px.init(G_.WND_MAIN[2]+G_.WND_SIDE[2], G_.WND_MAIN[3],
                title=G_.APP_NAME, fps=G_.GAME_FPS, quit_key=px.KEY_NONE)
        G_.JP_FONT = px.Font(G_.FONTFILE)
        G_.SMALLFONT = px.Font(G_.SMALLFONT)
        px.load(G_.ASSET_FILE, exclude_images=True, exclude_tilemaps=True)
        px.images[0].load(0, 0, "assets/image/0.chip.bmp")
        px.images[1].load(0, 0, "assets/image/1.chara.bmp")

        item.ItemManager.load_json()
        self.di = InstanceReferenceManager(self)
        self.di.base = base.Base(self.di)
        self.message_manager = message.MessageManager(self.di)
        self.depth_level = 0
        self.next_level = 1
        self.is_skip_level = False
        self.volume = 5

        self.build_window_frame()

    #ゲーム実行状況リセット
    def reset_parameter(self):
        self.message_window = menu.Window(16,px.height//2-12, px.width-(16*2),8*(1+2*5+1), 1,150)
        self.notice_window = menu.Window(16,px.height//2-12, px.width-(16*2),8*6, 1,150)
        self.notice_window.message_text = [""]
        self.message_manager.message_list = []
        self.background_drawer = None
        self.is_menu = False
        self.is_gameover = False
        self.counter = 0
        self.eventstep = 0
        self.is_nextstage = False
        self.is_nextlevel = False
        self.depth_level = 0
        self.next_level = self.next_level if self.is_skip_level else 1
        self.is_skip_level = False
        self.flavor_no = None
        self.is_emergency = False
        self.emergeny_counter = 0

    #熟練度アップ情報更新
    def update_levelup_info(self):
        self.now_user_exp = {
            "weapon":self.user.weapon.mastery,
            "level":self.user.level,
            "wand":self.user.mastery["wand"],
            "sword":self.user.mastery["sword"],
            "spear":self.user.mastery["spear"],
            "axe":self.user.mastery["axe"],
        }

    #熟練度アップ情報生成
    def reset_levelup_info(self):
        self.update_levelup_info()
        self.prev_user_exp = self.now_user_exp.copy()
        self.levelup_effects = []

    #熟練度アップチェック・表示オブジェクト生成
    def check_levelup(self):
        for i, (key, val) in enumerate(self.now_user_exp.items()):
            if int(val // 10) > int(self.prev_user_exp[key] // 10):
                self.levelup_effects.append({
                    "x": self.user.address[0]-12+i*3,
                    "y": self.user.address[1]-7-i,
                    "color": G_.LEVELUP_COLOR[0][i],
                    "type": G_.LEVELUP_COLOR[1][i],
                    "frame": 0,
                })
            self.prev_user_exp[key] = val

    #サブウインドウフレーム用タイルマップ生成
    def build_window_frame(self):
        layer = 7
        comf.fill_tilemap(layer, (31,31), G_.WND_SIDE[2]//8,G_.WND_SIDE[3]//8)
        #ステータスエリア
        size = [G_.WND_STAT[2]//8, G_.WND_STAT[3]//8]
        i = 0
        for y in range(size[1]):
            for x in range(size[0]):
                if y == 0 or y == size[1]-1:
                    px.tilemaps[layer].pset(x, y, (8+i,0))
                    i = 1 - i
                elif x == 0 or x == size[0]-1:
                    px.tilemaps[layer].pset(x, y, (8+i,0))
            i = 1 - i
        #メッセージエリア
        size2 = [G_.WND_MESG[2]//8,G_.WND_MESG[3]//8]
        for y in range(size2[1]):
            for x in range(size2[0]):
                if y == 0:
                    px.tilemaps[layer].pset(x, size[1]+ y, (11,0))
                elif y == size2[1]-1:
                    px.tilemaps[layer].pset(x, size[1]+ y, (15,0))
                elif x == 0:
                    px.tilemaps[layer].pset(x, size[1]+ y, (10,0))
                elif x == size2[0]-1:
                    px.tilemaps[layer].pset(x, size[1]+ y, (16,0))

    #ユーザキャラ情報初期化
    def init_user(self,index:int=9):
        if isinstance(self.user, character.UserCharacter):
            self.user.reset_state()
        else:
            match index:
                case 0:
                    self.user = character.UserCharacter(
                            self.di, 0, [G_.WND_MAIN[2]//4,G_.WND_MAIN[3]//4],[0,0,16,16],
                            "戦士型",40,20,20,10,35,15)
                case 1:
                    self.user = character.UserCharacter(
                            self.di,0, [G_.WND_MAIN[2]//4,G_.WND_MAIN[3]//4],[0,0,16,16],
                            "魔法使い型",10,15,15,50,10,40)
                case 2:
                    self.user = character.UserCharacter(
                            self.di, 0, [G_.WND_MAIN[2]//4,G_.WND_MAIN[3]//4],[0,0,16,16],
                            "バランス型",20,30,30,20,20,20)

    def prepare_nextlevel(self):
        '''次のLEVELを更新してダンジョンフロアを構築'''
        self.reset_display() #画面揺れの中途半端な残存をクリア
        self.reset_play_parameter()
        #デバッグ：指定フロアテスト用
        # self.depth_level = 89 if self.depth_level<10 else 1
        # self.depth_level = 9
        self.depth_level += self.next_level
        self.user.score += (self.depth_level-1)**2
        if self.depth_level%10 == 0:
            self.is_boss = True
            self.prepare_bossbattle()
            return
        self.generate_dungeon()

    def generate_dungeon(self):
        '''ダンジョン生成およびアイテム配置、モンスター生成と配置'''
        self.dungeon = dungeon.Floor(self.di, self.depth_level)
        #モンスター生成（ダンジョン）
        self.dungeon.monsters = monster.MonsterManager(self.di, self.dungeon.rooms_structure,
                                                       self.depth_level)

    #プレイ中の状態パラメタの初期化
    def reset_play_parameter(self):
        self.is_skip_update = False
        self.is_onstair = False
        self.is_onshop = False
        self.shop_index = 0
        self.dungeon_index = 0
        self.is_boss = False
        self.user_hp_window = None
        self.boss_hp_window = None

    #タイトル画面描画準備
    def prepare_title(self):
        self.reset_display() #画面揺れの中途半端な残存をクリア
        # px.dither(1)
        px.cls(0)
        self.user = None
        self.reset_parameter()
        self.depth_level = 0
        px.images[2].cls(0)
        item.ItemManager.clear_item()
        self.game_state = G_.GameState.TITLE
        self.menu = self.di.menu = menu.MenuTitle(self.game_state, self)
        self.menu.image_data = px.Image.from_image("assets/image/title.bmp")
        sound.load_sounds(self.game_state)

    #Pyxel アプリケーション起動
    def __init__(self):
        self.init_app()
        self.prepare_title()
        px.run(self.update, self.draw)

    #モンスター死亡時のメッセージと報酬獲得
    def kill_monster(self, mob):
        if self.di.flg.is_spawner is False:
            self.notice_window.message_text = self.di.flg.notice_rule(G_.FlagNotice.KILL_MONSTER)
        self.message_manager.add_message(f"{mob.name}撃退")
        self.user.score += int(mob.level + mob.tier*10)
        #パーク：取得マナアップ
        rune_effect = self.user.get_rune_effect(G_.RuneList.MANAUP)
        perk_bonus = 1+rune_effect[1] if rune_effect is not None else 1
        getexp = self.user.mana_division(mob.mana*perk_bonus)
        #パーク：取得ジェムアップ
        rune_effect = self.user.get_rune_effect(G_.RuneList.GEMUP)
        perk_bonus = 1+rune_effect[1] if rune_effect is not None else 1
        getgold = int(mob.gem)*perk_bonus

        self.user.gem += getgold
        self.message_manager.add_message(f"M{int(getexp): >7,}/ G{int(getgold): >7,}")
        self.user.user_levelup()

    #物理攻撃処理
    def attack_physical(self, mobgroup):
        #パーク：攻撃範囲拡大
        rune_effect1 = self.user.get_rune_effect(G_.RuneList.OVERRANGE)
        rangebonus = 0 if rune_effect1 is None else rune_effect1[1]
        #パーク：攻撃速度UP
        rune_effect = self.user.get_rune_effect(G_.RuneList.HASTE)
        perk_bonus = rune_effect[1] if rune_effect is not None else 1
        attack_speed = self.user.weapon.attack_speed / perk_bonus# * perk_bonus
        #斧の振り調整
        if self.user.weapon.type_id == 3 and \
                self.user.weapon.motion_counter > self.user.weapon.motion_frames//2:
            return

        _attackrange_weapon = self.user.weapon.func_attackrange(*self.user.address,self.user.direction)
        is_hit_weapon = False

        #物理攻撃実行中の処理
            #画面内全モンスターに対する処理

        for _attackrange in _attackrange_weapon: #武器の攻撃判定は複数ボックスで構成の場合あり
            #パーク：攻撃範囲拡大
            if _attackrange[2]>_attackrange[3]:
                _attackrange[2] += rangebonus
                _attackrange[3] += rangebonus//2
            elif _attackrange[2]<_attackrange[3]:
                _attackrange[2] += rangebonus//2
                _attackrange[3] += rangebonus
            else:
                _attackrange[2] += rangebonus//2
                _attackrange[3] += rangebonus//2

            for mob in mobgroup:
                if mob.is_dead or mob.is_warp or mob in self.user.weapon.hitlist:
                    continue                    
                if comf.check_collision_hitbox(*_attackrange, *mob.address,
                                               mob.image_source[2]-mob.image_source[2]//10,
                                               mob.image_source[3]-mob.image_source[3]//10):
                    is_hit_weapon = True
                    
                if is_hit_weapon:
                    damage = self.user.proc_attack_physical(mob)
                    self.user.weapon.hitlist.append(mob)
                    if damage > 0:
                        self.message_manager.add_message(f"攻撃！ {damage}", 10)
                        if not mob.is_dead and mob.hp < 0:
                            self.kill_monster(mob)
                    elif damage <= 0:
                        self.message_manager.add_message(f"防御された…", 12)
                is_hit_weapon = False

    def attack_skill(self, mobgroup, skill):#, treasure):
        _attackrange_skill = skill.model.func_attackrange(*skill.address, skill.direction)
        is_hit_skill = False
        #魔法攻撃実行中の処理
            #画面内全モンスターに対する処理
        for _attackrange in _attackrange_skill:
            # #デバッグ：攻撃範囲チェック用
            # if G_.IS_DEBUG:
            #     px.rect(_attackrange[0]-_attackrange[2]//2,_attackrange[1]-_attackrange[3]//2,
            #             *_attackrange[2:], px.COLOR_RED)
            #     px.flip()
            for mob in mobgroup:
                if mob.is_dead or mob.is_warp or mob in skill.hitlist:
                    continue
                if comf.check_collision_hitbox(*_attackrange, *mob.address,
                                               mob.image_source[2]-mob.image_source[2]//10,
                                               mob.image_source[3]-mob.image_source[3]//10):
                    is_hit_skill = True

                if is_hit_skill:
                    damage = self.user.proc_attack_skill(skill, mob)
                    skill.hitlist.append(mob)
                    if damage > 0:
                        self.message_manager.add_message(f"{skill.model.name}！ {damage}", 10)
                    elif damage <= 0:
                        self.message_manager.add_message(f"抵抗された…", 12)
                    if not mob.is_dead and mob.hp <= 0:
                        self.kill_monster(mob)
                    #魔法が命中したらインスタンスは消える
                    if mob.timer_magicdamaged <= 0: 
                        skill = None
                        return
                is_hit_skill = False

    #宝箱の開錠・内容入手
    def pick_treasurebox(self, box):
        if comf.check_collision_hitbox(self.user.address[0], self.user.address[1]+2,
                                       *G_.HitboxSize.MIDDLE,
                                       box.address[0],box.address[1],*G_.HitboxSize.SAME):
            if box.challenge_open(self.depth_level, self.user.dexterity):
                if len(self.user.inventory)>=self.user.inventory_max:
                    item.ItemManager.update_state(box.item_uuid, G_.ItemStatus.DROP)
                    self.message_manager.add_message("これ以上　持てない！")
                    return True
                if self.di.flg.is_first is False:
                    self.notice_window.message_text = item.notice_item(item.ItemManager.get_item(box.item_uuid), self.di.flg)
                self.message_manager.add_message("宝箱を開錠した", 3)
                num_text = "" if box.num_item == 1 else " "+box.num_item
                self.message_manager.add_message(
                        f"{item.ItemManager.get_item(box.item_uuid).name}{num_text}入手")
                item.pick_item(box.item_uuid, box.num_item, self.user)
                return True
            return False


    #ボス戦準備
    def prepare_bossbattle(self):
        self.reset_display() #画面揺れの中途半端な残存をクリア
        self.is_boss = False
        comf.fill_tilemap(1, (8,1), (G_.WND_MAIN[2]+G_.WND_SIDE[2])//8, G_.WND_MAIN[3]//8)
        comf.fill_tilemap(1, (9,1), 56,41, 1,10)
        BOSS_LIST = comf.read_json("assets/data/boss.json")

        now_tier = self.depth_level//10 - 1
        is_elite = False
        if now_tier >= len(BOSS_LIST):
            now_tier = px.rndi(0,len(BOSS_LIST)-1)
            is_elite = True
        self.boss = monster.BossMonster(self.di, self.depth_level,
                                        *BOSS_LIST[now_tier][1:], is_elite)

        if self.di.flg.is_first:
            px.images[2].load(0,0,f"assets/image/boss{now_tier}u.bmp")
        elif is_elite:
            px.images[2].load(0,0,f"assets/image/boss{now_tier}u.bmp")
        else:
            px.images[2].load(0,0,f"assets/image/boss{now_tier}.bmp")
        self.user.address = [24,256]
        self.user.timer_item[G_.BuffType.TIMESTOP] = 0
        self.user.timer_item[G_.BuffType.HIDDEN] = 0
        self.user.timer_item[G_.BuffType.DIFLECT] = 0
        self.user.prev_hp = self.user.hp
        self.user_hp_window = menu.Window((px.width//2-160)//2,16, 160,48, 9)
        self.boss_hp_window = menu.Window(px.width//2+(px.width//2-160)//2,16, 160,48, 9)
        self.background_drawer = dungeon.Floor.draw_boss_stage
        self.game_state = self.user.user_scene = G_.GameState.LASTBOSS if self.depth_level == 100 else G_.GameState.BOSSBATTLE

        if G_.IS_DEBUG:
            return
        #一度倒したボスは出現しない
        if self.di.base.defeated_boss >= self.depth_level:
            self.boss.is_gone = True
            self.boss.name = "もぬけの空"
            self.boss.hp = 0
            sound.load_sounds(G_.GameState.TITLE)
        else:
            sound.load_sounds(self.game_state)

    #共通更新処理１（複数フレーム継続処理）
    def update_phase1(self, area):
        #更新中に毎フレーム行う処理
            #メッセージ消去カウントダウン
            self.message_manager.countdown_message()
            #ユーザ情報更新（タイマー減算）
            self.user.user_timer_decrement()
        #継続動作の処理（主に当たり判定　
            #物理攻撃処理
            if self.user.weapon.is_attacking:
                self.attack_physical(area.monsters.mobgroup[area.monsters.mobgroup_index][3])
                self.attack_physical([area.monsters.mobgroup[area.monsters.mobgroup_index][4]])
            #魔法攻撃処理
            for skill in self.user.skillbook.values():
                if skill is not None and skill.active_skills:
                    for active_skill in skill.active_skills:
                        self.attack_skill(area.monsters.mobgroup[area.monsters.mobgroup_index][3], active_skill)
                        self.attack_skill([area.monsters.mobgroup[area.monsters.mobgroup_index][4]], active_skill)
            #ルーム封鎖解放
            if area.now_room.is_defeat is False and \
                    area.monsters.get_living_monsters() == 0:
                area.now_room.is_defeat = True


    #共通更新処理２（キー入力反応）
    def update_phase2(self, area):    
        #入力キーチェック（関数内で処理するものもあり）
        _return_code = self.user.check_inputkey()
        #移動時はタイルチェック
        if _return_code in (0,1,2,3):
            #宝箱情報（攻撃時の当たり判定が発生する為ここで取得）
            box = None
            if self.game_state not in (G_.GameState.BOSSBATTLE,G_.GameState.LASTBOSS) and\
                    area.monsters.red_treasure_list[area.monsters.mobgroup_index] is not None:
                box = area.monsters.red_treasure_list[area.monsters.mobgroup_index]
            self.user.move_address(self.game_state, int(self.user.movespeed),box)
        elif _return_code == 8:                    
            pass
            # #ボタン同時押しでスキル発動
        elif self.game_state in (G_.GameState.DUNGEON,
                                 G_.GameState.DUNGEON_CAVE,
                                 G_.GameState.DUNGEON_MAZE):
            if _return_code == 7:
                self.menu = self.di.menu  = menu.Menu(10,10, [1,4], G_.MENU_ITEM, 6, parent=self, user=self.user)
                px.play(3, [G_.SNDEFX["po"]], resume=True)
                self.game_state = G_.GameState.MENU
            elif _return_code == 6:
                if self.user.is_use_item is False:
                    self.message_manager.add_message("鶴嘴は使えない", 8)
                else:
                    for obstacle in self.dungeon.now_room.obstacles:
                        if obstacle.is_placed is False:
                            continue
                        if comf.check_collision_hitbox(obstacle.address["x"],obstacle.address["y"],
                                                    *G_.HitboxSize.SAME,
                                                    self.user.address[0]
                                                    +G_.CHARA_DIR[self.user.direction][0]*8,
                                                    self.user.address[1]
                                                    +G_.CHARA_DIR[self.user.direction][1]*8,
                                                    2,2):
                            obstacle.is_placed = False
                            px.play(3,G_.SNDEFX["item"],resume=True)
                            #パーク：鶴嘴消費率DOWN
                            rune_effect = self.user.get_rune_effect(G_.RuneList.TOUGH)
                            bonus = 0 if rune_effect is None else (rune_effect[1]+self.user.luck//50)
                            if px.rndi(0,99) >= bonus:
                                self.user.mattock -= 1
                            obstacle.update_virtual_tilemap()
                            break
                    self.user.is_use_item = False
    #その他ユーザ状態更新
        self.user.update()
        self.update_levelup_info()
        self.check_levelup()
        #レベルアップ表示関連
        for eff in self.levelup_effects:
            eff["frame"] += 1
            eff["y"] -= 0.2  # 上に浮く
        self.levelup_effects = [e for e in self.levelup_effects if e["frame"] < G_.GAME_FPS]
    #ステージ状態更新（主にモンスターの行動）
        if self.user.user_scene == G_.GameState.DUNGEON:
            area.update(self.game_state)
        else:
            self.boss.update(self.user)
        #モンスター行動の結果死亡した
        if self.user.hp <= 0:
            self.user.hp = 0
            self.user.is_dead = True
            self.di.base.deathdrop_id = {"weapon":self.user.weapon.id,
                                         "armor":self.user.armor.id,
                                         "shield":self.user.shield.id}
            for item_info in self.user.inventory:
                item.ItemManager.remove_item(item_info[0])

    #Pyxel Update処理
    def update(self):
        try:
            if self.notice_window.message_text[0]:
                if self.notice_window.update() is False:
                    self.notice_window.message_text = [""]
                return
            match self.game_state:
            #タイトル画面
                case G_.GameState.TITLE:
                    self.menu.update()
                    return
            #タイプ選択
                case G_.GameState.SELECTCHARA:
                    if not self.menu.update():
                        self.message_window = menu.Window(16,224,G_.WND_MAIN[2]+G_.WND_SIDE[2]-32,48, 1,50)
                        px.images[2].cls(0)
                        px.dither(0)
                        self.counter = 0
                        self.user.is_clear = self.is_clear_user
                        px.dither(1)
                        self.menu = self.di.menu  = menu.MenuNameEntry()
                        self.game_state = self.user.user_scene = G_.GameState.NAMEENTRY
                    return
            #名前入力
                case G_.GameState.NAMEENTRY:
                    if not self.menu.update():
                        self.user.name = self.menu.input_name_string
                        self.game_state = self.user.user_scene = G_.GameState.OPENING
                        self.message_window = menu.Window(32,224,px.width-64,8*(1+(2*5)+1), 1,50)
                        self.command_instance = command.CommandSkipOpeningandTutrial(self.di,
                                                                                     px.width//4,
                                                                                     px.height//2)
                        self.menu = menu.MenuYesNo(24,px.height*0.4,["オープニングとチュートリアルをスキップしますか？"],self.command_instance,self)
                        self.di.flg.is_first = True
                        self.di.flg.is_newgame = True
                    return
            #オープニング
                case G_.GameState.OPENING:
                    if self.di.flg.is_skipOpening is None:
                        if self.menu.update() is False:
                            self.di.flg.is_skipOpening = False
                    elif self.di.flg.is_skipOpening is False:
                        next_ = self.message_window.update()
                        if self.is_nextstage:
                            self.counter = 0
                            self.game_state = self.user.user_scene = G_.GameState.PREPARE_GAME
                        elif next_ is False:
                            self.message_window.close_counter = 0
                            self.eventstep += 1
                        return
            #拠点準備
                case G_.GameState.PREPARE_BASE:
                    self.reset_display() #画面揺れの中途半端な残存をクリア
                    self.di.flg.is_newgame = False
                    item.ItemManager.garbage_correct()
                    self.di.base.update_max_level()
                    self.di.base.return_base()
                    #余り食糧と鍵の売却
                    if self.di.user.food > 0:
                        self.di.base.stock_gem += self.di.user.food//10
                    if self.di.user.key > 0:
                        self.di.base.stock_gem += self.di.user.key*100
                    self.di.user.reset_param()
                    self.di.user.reset_state()

                    self.command_instance = command.CommandSave(0,0, self, 0)
                    self.command_instance.exec()
                    self.command_instance = None

                    self.game_state = self.user.user_scene = G_.GameState.BASE
                    sound.load_sounds(self.game_state)
            #拠点
                case G_.GameState.BASE:
                    self.di.base.update()
                    self.user.update()
            #ゲームメイン準備
                case G_.GameState.PREPARE_GAME:
                    px.stop()
                    px.sounds[4].mml("t85 Q66 o2 @0 v127 @ENV1 @ENV1{100,10,50} L16 dead ee<g>d8 ead ee<ga> dead ee<a g8g8g4.r2")
                    px.sounds[5].mml("t85 Q66 o2 @2 v127 @ENV2 @ENV2{80,12,30} L16 dead ee<g>d8 ead ee<ga> dead ee<a g8g8g4.r2")
                    px.sounds[6].mml("t85 Q66 o2 @0 v127 Y5 @ENV1 @ENV1{100,10,50} L16 dead ee<g>d8 ead ee<ga> dead ee<a g8g8g4.r2")
                    px.sounds[7].mml("t85 Q20 o9 @3 v40 L16 cgcg cgcQ50a8 Q20cgc gcgc gcgc gcg<<<<<Q80g4rrrrrrr")
                    px.musics[0].set([4],[5],[6],[7])
                    if G_.IS_DEBUG is False:
                        px.playm(0,loop=False)

                    self.reset_parameter()
                    self.user.reset_state()
                    self.reset_levelup_info()
                    self.di.base.delete_garbage_shopitem()
                    self.prepare_nextlevel()

                    if self.di.flg.is_first:
                        self.user.food = 1000
                    else:
                        foodcost = self.user.defaulthp if self.di.base.stock_gem >= self.user.defaulthp else self.di.base.stock_gem
                        self.user.food = foodcost*10
                        self.di.base.stock_gem -= foodcost

                    #パーク：開始時HP2倍（探索開始時のみ）
                    rune_effect = self.user.get_rune_effect(G_.RuneList.GIANT)
                    if rune_effect is not None:
                        self.user.hp = self.user.maxhp * rune_effect[1]
                    self.user.prev_hp = self.user.hp

                    #v1.2.0追加
                    if self.depth_level > 100:
                        # self.user.mattock = self.depth_level//100 + (self.depth_level-100)//50
                        self.user.mattock = 1 + (self.depth_level-100)//50

                    if self.game_state != G_.GameState.PREPARE_GAME:
                        return

                    #開始直後にいきなり死なない（ボス戦遷移時は発動しない）
                    if G_.IS_DEBUG is False:
                        self.user.timer_invincible = G_.GAME_FPS*(self.depth_level//10+1)
                    px.images[2].cls(0)
                    px.images[2].load(0, 0, f"assets/image/tier{self.di.dungeon.floor_tier}.bmp")
                    self.game_state = self.user.user_scene = G_.GameState.STARTFLOOR
                    self.image_keydisp = px.Image.from_image("assets/image/keydisp.bmp")
                    return
            #次フロア準備
                case G_.GameState.PREPARE_NEXTFLOOR:
                    px.stop()
                    px.sounds[4].mml("t85 Q66 o2 @0 v127 @ENV1 @ENV1{100,10,50} L16 dead ee<g> dead ee<g>d<g")
                    px.sounds[5].mml("t85 Q66 o2 @2 v127 @ENV2 @ENV2{80,12,30} L16 dead ee<g> dead ee<g>d<g")
                    px.sounds[6].mml("t85 Q66 o2 @0 v127 Y5 @ENV1 @ENV1{100,10,50} L16 dead ee<g> dead ee<g>d<g")
                    px.sounds[7].mml("t85 Q20 o9 @3 v40 L16 cgcg cgfQ30g8 Q20gcg cgcg")
                    px.musics[0].set([4],[5],[6],[7])
                    if G_.IS_DEBUG is False:
                        px.playm(0,loop=False)
                    
                    self.user.reset_state()

                    self.prepare_nextlevel()
                    if self.game_state != G_.GameState.PREPARE_NEXTFLOOR:
                        return
                    #開始直後にいきなり死なない（ボス戦除く）
                    self.user.timer_invincible = G_.GAME_FPS*(self.depth_level//20+1)

                    px.images[2].cls(0)
                    px.images[2].load(0, 0, f"assets/image/tier{self.di.dungeon.floor_tier}.bmp")
                    self.game_state = self.user.user_scene = G_.GameState.STARTFLOOR
                    return
            #ステージ開始
                case G_.GameState.STARTFLOOR:
                    if self.flavor_no is None:
                        self.flavor_no = px.rndi(0,99)
                    self.dungeon.now_room_pos = 0, 0
                    self.dungeon.monsters.set_mobgroup_index(
                            self.dungeon.now_room_pos)
                    self.background_drawer = self.dungeon.draw

                    if px.play_pos(0) is None:
                        self.game_state = self.user.user_scene = G_.GameState.DUNGEON
                        match self.dungeon.floortype:
                            case "room":
                                sound.load_sounds(G_.GameState.DUNGEON)
                            case "cave":
                                sound.load_sounds(G_.GameState.DUNGEON_CAVE)
                            case "maze":
                                sound.load_sounds(G_.GameState.DUNGEON_MAZE)
                        self.flavor_no = None
                    return
            #ダンジョン
                case 40:
                    #Notification
                    if self.di.flg.is_noticed_all is False:
                        if self.di.flg.is_attack is False and self.depth_level == 1:
                            self.notice_window.message_text = [G_.BUTTON_DESC[0]]
                            self.di.flg.is_attack = True
                        elif self.di.flg.is_skill is False and self.depth_level == 1:
                            self.notice_window.message_text = [G_.BUTTON_DESC[4]]
                            self.di.flg.is_skill = True
                        elif self.di.flg.is_lock is False and self.depth_level == 2:
                            self.notice_window.message_text = self.di.flg.notice_rule(G_.FlagNotice.LOCK_DOOR)
                        elif self.di.flg.is_evade is False and self.depth_level == 3:
                            self.notice_window.message_text = [G_.BUTTON_DESC[2]]
                            self.di.flg.is_evade = True
                        elif self.di.flg.is_menu is False and self.depth_level == 4:
                            self.notice_window.message_text = [G_.BUTTON_DESC[1]]
                            self.di.flg.is_menu = True
                        elif self.di.flg.is_mattock is False and self.depth_level == 5:
                            self.notice_window.message_text = [G_.BUTTON_DESC[3]]
                            self.di.flg.is_mattock = True
                        elif self.di.flg.is_mastery is False and self.depth_level == 8:
                            self.notice_window.message_text = self.di.flg.notice_rule(G_.FlagNotice.MASTERY)
                        elif self.di.flg.is_escape is False and self.depth_level == 12:
                            self.notice_window.message_text = self.di.flg.notice_rule(G_.FlagNotice.ESCAPE)
                    #更新状況に関わらず毎フレーム実行する処理
                        #現時点で無し
                    #処理待ちによる更新のスキップ
                    if self.is_skip_update: #処理待ち中は更新スキップフラグON
                        return
                    #共通更新処理１
                    self.update_phase1(self.dungeon)
                    #共通更新処理２
                    self.update_phase2(self.dungeon)

                    #階層移動準備（100Fのボスは必ず一度は倒さないと先に進めない）
                    if self.dungeon.is_nextlevel:
                        self.next_level = self.dungeon.now_room.stair.next_level
                        if (self.depth_level+self.next_level >= 100 and
                            self.next_level > 1 and
                            self.di.base.reached_max_level <= 100
                            ):
                                self.depth_level = 99
                                self.next_level = 0
                        # v1.5.0
                        elif self.depth_level == 999:
                            self.depth_level = 1000
                            self.next_level = 0
                        elif self.depth_level+self.next_level >= 1000:
                            if (self.next_level > 1 and 
                                self.di.base.reached_max_level < 1000):
                                self.depth_level = 999
                                self.next_level = 0
                            else:
                                self.depth_level = 1000
                                self.next_level = 0
                        self.game_state = self.user.user_scene = G_.GameState.PREPARE_NEXTFLOOR
                    return
            #メニュー
                case 60:
                    self.reset_display() #画面揺れの中途半端な残存をクリア
                    if self.menu.update() is False:

                        self.menu = None
                        self.game_state = self.user.user_scene
                    return
            #ボス戦 #ラスボス戦
                case G_.GameState.BOSSBATTLE | G_.GameState.LASTBOSS:
                    self.user.timer_invincible = 0
                    #処理待ちによる更新のスキップ
                    if self.is_skip_update: #処理待ち中は更新スキップフラグON
                        return
                    if self.boss.is_gone:
                        self.message_window = menu.Window(64,64, px.width-64-64,
                                                            px.height-64-64, 1, 150)
                        self.game_state = self.user.user_scene = G_.GameState.STAGECLEAR
                        return
                    if self.user.is_dead:
                        self.message_window = None
                        self.game_state = G_.GameState.GAMEOVER
                        return
                    if self.boss.is_dead:
                        for skill in self.user.skillbook.values():
                            if skill is not None:
                                skill.clear_activeskill()
                        self.user.weapon.is_attacking = False
                        if self.boss.is_broken:
                            self.game_state = self.user.user_scene = G_.GameState.ENDING \
                                    if self.game_state == G_.GameState.LASTBOSS \
                                        else G_.GameState.STAGECLEAR
                            self.message_window = menu.Window(64,64, px.width-64-64,
                                                              px.height-64-64, 1, 150)
                            sound.load_sounds(self.game_state)
                            return
                        elif self.boss.is_defeat:
                            if px.play_pos(3) is None:
                                self.boss.is_broken = True
                            return
                        else:
                            self.counter += 1
                            return
                    #更新状況に関わらず毎フレーム実行する処理
                        #現時点で無し
                    #処理待ちによる更新のスキップ
                    if self.is_skip_update: #処理待ち中は更新スキップフラグON
                        self.is_skip_update = self.message_window.update()
                        return
                    #共通更新処理１
                    #メッセージ消去カウントダウン
                    self.message_manager.countdown_message()
                    #ユーザ情報更新（タイマー減算）
                    self.user.user_timer_decrement()
                #継続動作の処理（主に当たり判定　
                    #宝箱情報（攻撃時の当たり判定が発生する為ここで取得）
                    box = None
                    #物理攻撃処理
                    if self.user.weapon.is_attacking:
                        self.attack_physical([self.boss])
                    #魔法攻撃処理
                    for skill in self.user.skillbook.values():
                        if skill is not None and skill.active_skills:
                            for active_skill in skill.active_skills:
                                self.attack_skill([self.boss], active_skill)
                    if self.boss.hp < 0:
                        self.boss.is_dead = True
                        self.counter = 0
                        return
                    #共通更新処理２
                    self.update_phase2(None)
                    return
            #ステージクリアイベント
                case G_.GameState.STAGECLEAR:
                    next_ = self.message_window.update()
                    if self.is_nextstage:
                        if self.di.base.defeated_boss < self.depth_level:
                            self.di.base.defeated_boss = self.depth_level
                            if self.di.flg.is_first is False:
                                divnum = 2 if self.depth_level <= 100 else 4
                                self.user.defaultparam = {key:param+self.depth_level//divnum
                                                          for key,param
                                                          in self.user.defaultparam.items()}
                                self.user.defaulthp += self.depth_level*10
                                self.user.defaultmp += self.depth_level//2
                                self.user.score += self.depth_level**2*100
                            else:
                                self.di.base.defeated_boss = 5
                                self.user.score += self.depth_level**2*50
                                self.di.base.reached_max_level = self.depth_level = 0
                        # v1.5.0
                        if self.depth_level == 1000 and self.di.flg.is_clearbonus is False:
                            item.ItemManager.create_item("969",G_.ItemStatus.STORAGE)
                            item.ItemManager.create_item("969",G_.ItemStatus.STORAGE)
                            item.ItemManager.create_item("969",G_.ItemStatus.STORAGE)
                            item.ItemManager.create_item("921",G_.ItemStatus.STORAGE)
                            item.ItemManager.create_item("921",G_.ItemStatus.STORAGE)
                            item.ItemManager.create_item("921",G_.ItemStatus.STORAGE)
                            item.ItemManager.create_item("957",G_.ItemStatus.STORAGE)
                            item.ItemManager.create_item("957",G_.ItemStatus.STORAGE)
                            item.ItemManager.create_item("957",G_.ItemStatus.STORAGE)
                            self.di.flg.is_clearbonus = True
                            #クリア時点データの退避用セーブ
                            cmd = command.CommandSave(0,0,self,1,False)
                            cmd.set_max_datano()
                            self.user.reset_state()
                            cmd.exec()
                        if self.di.flg.is_first or self.depth_level==1000:
                            px.stop()
                            px.play(3, G_.SNDEFX["special"])
                            while px.play_pos(3) is not None:
                                pass
                            self.game_state = self.user.user_scene = G_.GameState.PREPARE_BASE
                        else:
                            btn = comf.get_button_state()
                            if btn["L"]:
                                px.stop()
                                px.play(3, G_.SNDEFX["special"])
                                while px.play_pos(3) is not None:
                                    pass
                                self.game_state = self.user.user_scene = G_.GameState.PREPARE_BASE
                                if self.depth_level >= 100:
                                    self.depth_level += 1 #ワープ先をボス部屋の次にするため
                            elif btn["R"]:
                                self.next_level = 1
                                self.game_state = self.user.user_scene = G_.GameState.PREPARE_NEXTFLOOR

                        self.di.flg.is_first = False
                        self.di.base.is_defeat_or_die = True
                    elif next_ is False:
                        self.message_window.close_counter = 0
                        self.eventstep += 1
                    return
            #エンディング1（メッセージウインドウ）
                case G_.GameState.ENDING:
                    next_ = self.message_window.update()
                    if self.is_nextstage:
                        self.game_state = 91
                        self.counter = 1
                        if self.di.base.defeated_boss < self.depth_level:
                            self.di.base.defeated_boss = self.depth_level
                            if self.di.flg.is_first is False:
                                self.user.defaultparam = {key:param+self.depth_level//3
                                                          for key,param
                                                          in self.user.defaultparam.items()}
                                self.user.defaulthp += self.depth_level*10
                    elif next_ is False:
                        self.message_window.close_counter = 0
                        self.eventstep += 1
                    return
            #エンディング2（テキストスクロール準備）
                case 91:
                    self.counter -= 0.01
                    if self.counter < 0:
                        self.stars = []
                        self.spawn_timer = 0
                        self.ending_messages = comf.read_json("assets/data/messages.json")
                        self.scroll_y = G_.WND_MAIN[3]
                        px.dither(1)
                        self.game_state = 92
                    return
            #エンディング3（テキストスクロール、スタッフロール）
                case 92:
                    # 流れ星生成
                    self.spawn_timer -= 1
                    if self.spawn_timer <= 0:
                        self.stars.append(evt.ShootingStar())
                        self.spawn_timer = px.rndi(5, 15)
                    # 流れ星更新
                    self.stars = [s for s in self.stars if not s.update()]
                    # メッセージスクロール
                    if self.scroll_y > -(G_.GAME_FPS*24):
                        self.scroll_y -= 0.2
                    #エンディングスキップ
                    if self.scroll_y < 200 and self.counter <= 0:
                        to_state = comf.get_button_state()
                        if to_state["a"] or to_state["b"]:
                            self.counter = 1
                    if abs(self.scroll_y) >= (G_.GAME_FPS*23) or abs((1-self.counter/(G_.GAME_FPS*8)))<=0:
                        px.dither(1)
                        px.stop()
                        px.play(3,G_.SNDEFX["special"])
                        while px.play_pos(3) is not None:
                            pass
                        px.dither(1)
                        self.user.score += 1000000
                        self.game_state = self.user.user_scene = G_.GameState.PREPARE_BASE
                    elif self.counter >= 1:
                        self.counter += 1
                    return
            #ゲームオーバー
                case G_.GameState.GAMEOVER:
                    if self.is_gameover:
                        if self.message_window.update() is False:
                            self.di.base.is_defeat_or_die = True
                            self.user.gem //= 2
                            self.user.mana["stock"] //= 2
                            if self.di.flg.is_first:
                                self.di.base.reached_max_level = self.depth_level = 0
                            self.game_state = self.user.user_scene = G_.GameState.PREPARE_BASE
                    else:
                        if self.user.user_scene in (30,40):
                            menuwidth = G_.WND_MAIN[2]//4-12
                        else:
                            menuwidth = (G_.WND_MAIN[2]+G_.WND_SIDE[2])//4-12
                        self.message_window = menu.Window(menuwidth, G_.WND_MAIN[3]//2+16,
                                                            (1+12*2+1)*G_.CHIP_PIXEL, (1+2*3+1)*G_.CHIP_PIXEL, 1, 300)
                        self.is_gameover = True
                        self.counter = px.frame_count
                    return
        except Exception as e:
            comf.error_message(["",f"更新処理で予期せぬ例外が発生しました","",f"情報：",f"{e}",""])
            self.prepare_title()

    #ユーザステータスウインドウ描画
    def draw_status(self):
        #サブウインドウ枠線描画
        px.bltm(G_.WND_STAT[0],G_.WND_STAT[1], 7, 
            0,G_.WND_STAT[1], G_.WND_STAT[2],G_.WND_STAT[3], colkey=7)
        _draw_data = [
            f"{self.user.name}",
            f"{int(self.user.hp):>14,}",
            f"{int(self.user.food):>14,}",
            f"{int(self.user.mana["exp"]):>14,}",
            f"{int(self.user.gem):>14,}",
            f"{int(self.user.score):>14,}",
        ]
        px.blt(G_.WND_SIDE[0]+10, G_.WND_SIDE[1]+11 + 1*13, 0, *G_.ImageAddress.MINIHEART, 0)
        px.blt(G_.WND_SIDE[0]+10, G_.WND_SIDE[1]+11 + 2*13, 0, *G_.ImageAddress.MINIFOOD, 0)
        px.blt(G_.WND_SIDE[0]+10, G_.WND_SIDE[1]+11 + 3*13, 0, *G_.ImageAddress.MINIEXP, 0)
        px.blt(G_.WND_SIDE[0]+10, G_.WND_SIDE[1]+11 + 4*13, 0, *G_.ImageAddress.MINIGOLD, 0)
        px.blt(G_.WND_SIDE[0]+10, G_.WND_SIDE[1]+11 + 5*13, 0, *G_.ImageAddress.MINISCORE, 0)
        for i, text in enumerate(_draw_data):
            if i == 0:
                px.text(G_.WND_SIDE[0]+10, G_.WND_SIDE[1]+9 + i*13, text, 7, font=G_.JP_FONT)
            else:
                px.text(G_.WND_SIDE[0]+22, G_.WND_SIDE[1]+8 + i*13, text, 7, font=G_.JP_FONT)

        px.blt(G_.WND_SIDE[0]+10, G_.WND_SIDE[1]+11 + 6*13, 0, *G_.ImageAddress.MINILEVEL, 0)
        px.text(G_.WND_SIDE[0]+18, G_.WND_SIDE[1]+8 + 6*13, f"{self.depth_level:>4,}", 7, font=G_.JP_FONT)
        px.blt(G_.WND_SIDE[0]+44, G_.WND_SIDE[1]+11 + 6*13, 0, *G_.ImageAddress.MINIKEY, 0)
        px.text(G_.WND_SIDE[0]+53, G_.WND_SIDE[1]+8 + 6*13, f"{self.user.key:>3}", 7, font=G_.JP_FONT)
        px.blt(G_.WND_SIDE[0]+79, G_.WND_SIDE[1]+11 + 6*13, 0, *G_.ImageAddress.MINIMATTOCK, 0)
        px.text(G_.WND_SIDE[0]+88, G_.WND_SIDE[1]+8 + 6*13, f"{self.user.mattock:>3}", 7, font=G_.JP_FONT)
        if self.user.timer_fire > 0:
            px.blt(G_.WND_SIDE[0]+10, G_.WND_SIDE[1]+11 + 7*13, 0, 56+(0*8),232, 8,8, 0)
            px.text(G_.WND_SIDE[0]+18, G_.WND_SIDE[1]+8 + 7*13, f"{self.user.timer_fire}s", 7, font=G_.JP_FONT)
        if self.user.timer_ice > 0:
            px.blt(G_.WND_SIDE[0]+44, G_.WND_SIDE[1]+11 + 7*13, 0, 56+(1*8),232, 8,8, 0)
            px.text(G_.WND_SIDE[0]+53, G_.WND_SIDE[1]+8 + 7*13, f"{self.user.timer_ice}s", 7, font=G_.JP_FONT)
        if self.user.timer_wind > 0:
            px.blt(G_.WND_SIDE[0]+79, G_.WND_SIDE[1]+11 + 7*13, 0, 56+(2*8),232, 8,8, 0)
            px.text(G_.WND_SIDE[0]+88, G_.WND_SIDE[1]+8 + 7*13, f"{self.user.timer_wind}s", 7, font=G_.JP_FONT)

    #スクロール方向算出
    def get_scroll_direction(self, offset):
        scroll_dir = 9
        if self.user.address[0] < offset:
            scroll_dir = 1
        elif self.user.address[0] > G_.WND_MAIN[2] - offset:
            scroll_dir = 2
        elif self.user.address[1] < offset:
            scroll_dir = 3
        elif self.user.address[1] > G_.WND_MAIN[2] - offset:
            scroll_dir = 0
        return scroll_dir

    #ボス戦描画
    def draw_bossbattle(self):
        #背景描画共通呼び出し
        self.background_drawer()
        #HPウインドウ
        self.user_hp_window.draw()
        self.user_hp_window.drawText(self.user_hp_window.x+16, self.user_hp_window.y+8,
                                        [self.user.name, f"{int(self.user.hp):>15,}"])
        self.boss_hp_window.draw()
        self.boss_hp_window.drawText(self.boss_hp_window.x+16, self.boss_hp_window.y+8,
                                        [self.boss.name,f"{int(self.boss.hp):>15,}"])
        self.user.draw()
        if self.boss.is_gone is False:
            self.boss.draw()
        #ボス死亡時エフェクト
        if self.boss.is_dead and self.boss.is_defeat is False:
            self.boss.is_defeat = evt.defeat_boss(self.boss, self.counter)

    #共通描画処理
    def draw_common(self):
        #背景・モンスター描画共通呼び出し
        self.background_drawer()
        #大ダメージエフェクト
        if self.is_emergency:
            self.is_skip_update = True
            if self.emergeny_counter > G_.GAME_FPS//2:
                self.is_skip_update = False
                self.is_emergency = False
                self.emergeny_counter = 0
                px.camera()
            else:
                if self.emergeny_counter%6 in (0,1,2):
                    px.dither(0.5)
                    px.rect(0,0,px.width,px.height,px.COLOR_RED)
                    px.dither(1)
                px.camera(px.rndi(-8,8),px.rndi(-8,8))
                self.emergeny_counter += 1

        #ユーザ死亡時は拠点へ連行
        if self.user.is_dead:
            self.game_state = G_.GameState.GAMEOVER
        self.user.draw()
        #レベルアップ頭上テキスト
        for eff in self.levelup_effects:
            col = eff["color"] if px.frame_count%8 < 6 else 7
            _original_text_func(int(eff["x"]), int(eff["y"]), f"{eff["type"]}UP", col)
        self.draw_status()
        self.message_manager.draw_message()

    #Pyxel draw処理
    def draw(self):
        try:
            if self.notice_window.message_text[0]:
                self.notice_window.draw()
                self.notice_window.draw_message()
                if str(self.notice_window.message_text[0]).startswith("　　スポナー"):
                    px.blt(self.notice_window.x+10, self.notice_window.y+6,
                           G_.IMGIDX["CHIP"],*G_.ImageAddress.SPAWNER, colkey=3)
                elif str(self.notice_window.message_text[0]).startswith("　　初めて訪れた部屋"):
                    px.blt(self.notice_window.x+10, self.notice_window.y+6,
                           G_.IMGIDX["CHIP"],*G_.ImageAddress.DOOR, colkey=0)
                return

            match self.game_state:
            #タイトル画面
                case G_.GameState.TITLE:
                    if self.menu.is_newgame:
                        if self.menu.cnt <= 0:
                            px.dither(1)
                            self.menu = self.di.menu  = menu.MenuSelectCharacter(self.init_user)
                            self.game_state = G_.GameState.SELECTCHARA
                            sound.load_sounds(self.game_state)
                    self.menu.draw( )
            #キャラ選択
                case G_.GameState.SELECTCHARA:
                    self.menu.draw()
            #名前入力
                case G_.GameState.NAMEENTRY:
                    self.menu.draw()
            #オープニング
                case G_.GameState.OPENING:
                    px.cls(0)
                    if self.di.flg.is_skipOpening is None:
                        self.menu.draw()
                    elif self.di.flg.is_skipOpening is False:
                        px.blt(0,-px.height//5, self.di.base.image_base, 0,0,self.di.base.image_base.width,self.di.base.image_base.height, colkey=0, scale=0.5)
                        self.is_nextstage = evt.opening(self.message_window, self.eventstep)
                        self.message_window.draw()
                        self.message_window.draw_message()
            #フィールド準備
                case G_.GameState.STARTFLOOR:
                    pox_x = px.width/2 - 16*9/2 #16ドットx9文字の半分を画面幅の半分から減算
                    pos_y = px.height/3
                    lv_0xx = self.depth_level//100
                    lv_x0x = self.depth_level//10%10
                    lv_xx0 = self.depth_level%10
                    px.cls(0)
                    #LEVEL:
                    px.blt(pox_x,pos_y,G_.IMGIDX["CHIP"], *G_.ImageAddress.LEVEL, colkey=px.COLOR_BLACK)
                    px.blt(pox_x+16,pos_y,G_.IMGIDX["CHIP"], G_.ImageAddress.LEVEL[0]+16,
                           *G_.ImageAddress.LEVEL[1:], colkey=px.COLOR_BLACK)
                    px.blt(pox_x+32,pos_y,G_.IMGIDX["CHIP"], G_.ImageAddress.LEVEL[0]+32,
                           *G_.ImageAddress.LEVEL[1:], colkey=px.COLOR_BLACK)
                    px.blt(pox_x+48,pos_y,G_.IMGIDX["CHIP"], G_.ImageAddress.LEVEL[0]+16,
                           *G_.ImageAddress.LEVEL[1:], colkey=px.COLOR_BLACK)
                    px.blt(pox_x+64,pos_y,G_.IMGIDX["CHIP"], *G_.ImageAddress.LEVEL, colkey=px.COLOR_BLACK)
                    px.blt(pox_x+80,pos_y,G_.IMGIDX["CHIP"], G_.ImageAddress.LEVEL[0]+48,
                           *G_.ImageAddress.LEVEL[1:], colkey=px.COLOR_BLACK)
                    #floor no.
                    px.blt(pox_x+96,pos_y,G_.IMGIDX["CHIP"], G_.ImageAddress.LEVELNUM[0]+16*lv_0xx,
                           *G_.ImageAddress.LEVEL[1:], colkey=px.COLOR_BLACK)
                    px.blt(pox_x+112,pos_y,G_.IMGIDX["CHIP"], G_.ImageAddress.LEVELNUM[0]+16*lv_x0x,
                           *G_.ImageAddress.LEVEL[1:], colkey=px.COLOR_BLACK)
                    px.blt(pox_x+128,pos_y,G_.IMGIDX["CHIP"], G_.ImageAddress.LEVELNUM[0]+16*lv_xx0,
                           *G_.ImageAddress.LEVEL[1:], colkey=px.COLOR_BLACK)

                    if self.di.flg.is_newgame and self.depth_level == 1:                    
                        px.blt((px.width-self.image_keydisp.width)//2,(px.height-self.image_keydisp.height)//2,
                            self.image_keydisp, 0,0,self.image_keydisp.width,self.image_keydisp.height,
                                colkey=0,scale=2)
                        px.text(166,32,"※Xinputキー配置の表示です",px.COLOR_WHITE,G_.JP_FONT)
                        px.text(160,72,"十字パッド：移動",px.COLOR_WHITE,G_.JP_FONT)
                        px.text(160,108+32*1,"Ａ：決定・攻撃",px.COLOR_WHITE,G_.JP_FONT)
                        px.text(160,108+32*2,"Ｂ：キャンセル・メニュー表示",px.COLOR_WHITE,G_.JP_FONT)
                        px.text(160,108+32*3,"Ｘ：回避",px.COLOR_WHITE,G_.JP_FONT)
                        px.text(160,108+32*4,"Ｙ：鶴嘴を使用",px.COLOR_WHITE,G_.JP_FONT)
                        px.text(160,108+32*5,"Ｌ：押しながらＡＢＸＹで設定スキル発動",px.COLOR_WHITE,G_.JP_FONT)
                    else:
                        hint_message1 = hint_message2 = ""
                        if self.depth_level == 21: self.flavor_no = 6
                        match self.flavor_no:
                            case 0:
                                hint_message1 = "画面右下のボタンアイコンはスキルを設定すると活性化し"
                                hint_message2 = "スキル使用時はクールタイムの表示になる"
                            case 1:
                                hint_message1 = "迷宮で死亡すると装備品以外の持ち物を全て失い、"
                                hint_message2 = "瓶に貯めたマナや獲得したジェムも半減する"
                            case 2:
                                hint_message1 = "鶴嘴はここぞという時の為に残しておくべきだ"
                                hint_message2 = "壁に囲まれて進めない時は諦めるしかないのだから"
                            case 3:
                                hint_message1 = "敵が強くて勝てない時は、少し手前の階層まで戻って"
                                hint_message2 = "強力なアイテムを狙ってみてはどうだろう"
                            case 4:
                                hint_message1 = "ｘゅぃ・・・ぅｍ・・・"
                                hint_message2 = "　・・・・・・・・ﾄｰ"
                            case 5:
                                hint_message1 = "器用で幸運な程、クリティカルしやすくなる"
                                hint_message2 = "相手の防御を無視して攻撃力の倍の打撃を与える"
                            case 6:
                                hint_message1 = "術の攻撃が厳しい時には腕輪が役に立つ"
                                hint_message2 = "防御力は心許ないが、魔法の威力を抑え込む"
                            case 7:
                                hint_message1 = "スキル攻撃は防御力を無視したダメージを与える"
                                hint_message2 = "ただし火氷風土の術は属性軽減率で弱められる"
                            case 8:
                                hint_message1 = "武器熟練度は別のアイテムには引き継がれないが"
                                hint_message2 = "自身の習熟度は武器種が揃えば効果を発揮する"
                            case 9:
                                hint_message1 = "同じアイテムでもランクに応じて性能が上がる"
                                hint_message2 = "ランクは売買の価格にも影響する"
                            case 10:
                                hint_message1 = "未鑑定状態のアイテムは装備できない"
                                hint_message2 = "買取価格も基本価格をもとに算出される"
                            case 11:
                                hint_message1 = "伝説に謳われる程の高ランクアイテムが存在する"
                                hint_message2 = "凄まじい能力を秘めているに違いない"
                            case 12:
                                hint_message1 = "RARE以上の装備品には能力が付与されている"
                                hint_message2 = "鑑定してみればどんな能力か分かるだろう"
                            case 13:
                                hint_message1 = "一部のアイテムは青い宝箱からしか入手出来ない"
                                hint_message2 = "希少な品を失わないように注意したい"
                            case 14:
                                hint_message1 = "RARE以上の装備品には秘紋石のスロットがある"
                                hint_message2 = "高級な秘紋石は低い等級のスロットには使えない"
                            case 15:
                                hint_message1 = "秘紋石は能力に応じた品でなければ使えない"
                                hint_message2 = "適切でない装備品には付けられない"
                            case 16:
                                hint_message1 = "もｘｘたあ"
                                hint_message2 = "ｘぷらｘずｘ・・・"
                            case 17:
                                hint_message1 = "COxTxA x DExTxx"
                                hint_message2 = "AxxNUx"
                            case 18:
                                hint_message1 = "秘紋石の抽出には細心の注意が必要だ"
                                hint_message2 = "石の等級が高い程繊細で壊れやすい"
                            case 19:
                                hint_message1 = "秘紋石の抽出には高度な技術が必要だ"
                                hint_message2 = "錬金工房に投資してレベルをあげるとよい"
                            case 20:
                                hint_message1 = "結合する秘紋石は倉庫に入っていたって構いやしない"
                                hint_message2 = "きっと倉庫に貯まるはずだから"
                            case 21:
                                hint_message1 = "秘紋石と結合するアイテムはインベントリに"
                                hint_message2 = "持っておく必要がある"
                            case 22:
                                hint_message1 = "巨大な敵を倒せば夥しい量のマナを浴びるだろう"
                                hint_message2 = "魂まで届いたマナは、肉体の飛躍的な強化を促す"
                            case 23:
                                hint_message1 = "必ず食糧が落ちている階層がある"
                                hint_message2 = "注意して探索すれば餓死は防げるかも知れない"
                            case 24:
                                hint_message1 = "秘紋石は、その辺に落ちているような代物ではない"
                                hint_message2 = "必ず迷宮の青い宝箱に安置されている"
                            case 25:
                                hint_message1 = "装備品のスロットは、実に様々な状態をとる"
                                hint_message2 = "同じ品同じランクでさえ数も等級も異なるのだ"
                            case 26:
                                hint_message1 = "深層の大部屋に繋がる魔法陣は無いという"
                                hint_message2 = "探索の為には近道の開発が欠かせないだろう"
                            case 27:
                                hint_message1 = "瀕死の危機に陥った時は、脱出するのも手だ"
                                hint_message2 = "全アイテムを失うよりは・・・"
                            case 28:
                                hint_message1 = "死亡するとジェムと瓶に貯めたマナを半分失う"
                                hint_message2 = "死の淵に立たされた時は脱出すべきだろう"
                            case 29:
                                hint_message1 = "怪しげに光る、ワープ階段には注意した方がいい"
                                hint_message2 = "ワープ先の階層が、勝てる敵ばかりとは限らない"
                            case 30:
                                hint_message1 = "インベントリ等アイテムの一覧表示メニューでは"
                                hint_message2 = "LRキーでアイテム種類による絞り込み表示が可能"
                            case 31:
                                hint_message1 = "拠点での作業では各所で自動セーブされる"
                                hint_message2 = "守護神の力が及ばない迷宮内ではセーブが出来ない"
                            case 32:
                                hint_message1 = "商人達が未鑑定で売る商品には気を付けろ"
                                hint_message2 = "値段に見合った品という保証はない"
                            case 33:
                                hint_message1 = "ワハハ！コゾウ！！"
                                hint_message2 = "ヒッカカッカッカッタナハハハ！"
                            case 34:
                                hint_message1 = "敵の魔法攻撃発動はＸＹ軸の重なりが条件だ"
                                hint_message2 = "敵と座標軸を合わせるな！"
                            case 35:
                                hint_message1 = "脱出時のアイテム遺失率は、翼の長靴か"
                                hint_message2 = "高ランクの能力で低減する事が可能だ"
                            case 36:
                                hint_message1 = "拠点の開発には様々な意見があろう　しかし"
                                hint_message2 = "祭壇、近道、錬金、これらの重要性は疑う余地がない"
                            case 37:
                                hint_message1 = "魔法によるデバフ効果を受けた時は、次の階へ飛び込めば"
                                hint_message2 = "理由はさておき、デバフ効果が解除される"
                            case 38:
                                hint_message1 = "・・・こｘが？"
                                hint_message2 = "・・・・・・あのおんｘの？"
                            case 39:
                                hint_message1 = "時折、階層に不相応な敵が現れることがある"
                                hint_message2 = "弱ければ幸運を喜べばいいが、強ければ・・・諦めも肝心"
                            case 40:
                                hint_message1 = "迷宮は一つ形に留まらず、訪れる度に姿を変える"
                                hint_message2 = "道具無しには乗り越えられない姿を見せる事もある"
                            case 41:
                                hint_message1 = "頑健な肉体には魔法も通じにくい"
                                hint_message2 = "健康な肉体には健全な精神が宿るというもの"
                            case 99:
                                hint_message1 = ""
                                hint_message2 = ""
                        text_width = G_.JP_FONT.text_width(hint_message1)
                        px.text(px.width//2 - text_width // 2, pos_y+128, hint_message1,
                                7, font=G_.JP_FONT)
                        text_width = G_.JP_FONT.text_width(hint_message2)
                        px.text(px.width//2 - text_width // 2, pos_y+144, hint_message2,
                                7, font=G_.JP_FONT)
            #拠点
                case G_.GameState.PREPARE_BASE:
                    px.cls(0)
                    return
                case G_.GameState.BASE:
                    self.di.base.draw()
            #ダンジョン
                case 40:
                    #マップ切替
                    _scroll_offset = 8
                    scroll_dir = self.get_scroll_direction(_scroll_offset)
                    if scroll_dir in (0,1,2,3):
                        self.is_skip_update = True
                        self.dungeon.move_room(scroll_dir)
                        if self.dungeon.now_room.is_defeat is False:
                            door_offset = 16
                        else:
                            door_offset = 0
                        match scroll_dir:
                            case 0:
                                self.user.address = [self.user.address[0], _scroll_offset]
                            case 1:
                                self.user.address = [G_.WND_MAIN[2] - _scroll_offset, self.user.address[1]]
                            case 2:
                                self.user.address = [_scroll_offset, self.user.address[1]]
                            case 3:
                                self.user.address = [self.user.address[0], G_.WND_MAIN[3] - _scroll_offset]
                        self.user.address[0] += G_.CHARA_DIR[self.user.direction][0]*door_offset
                        self.user.address[1] += G_.CHARA_DIR[self.user.direction][1]*door_offset
                        self.is_skip_update = False
                        self.background_drawer()
                    #共通描画処理
                    self.draw_common()
            #メニュー
                case 60|66:
                    #共通描画処理
                    self.draw_common()
                    self.menu.draw()
            #ボス戦 #ラスボス戦
                case G_.GameState.BOSSBATTLE|G_.GameState.LASTBOSS:
                    self.draw_bossbattle()
                    if self.boss.is_gone:
                        return
                    if self.boss.is_anger_event:
                        self.is_skip_update = True
                        if evt.anger_boss(self.counter):
                            self.boss.is_anger_event = False
                            if self.user.is_clear:
                                px.images[2].cls(0)
                                px.images[2].load(0, 0, f"assets/image/stage{self.depth_level//10}u.bmp")
                                self.boss.hp = self.boss.maxhp
                                self.boss.movespeed += 1
                                self.boss.attack *= 1.2
                                self.boss.defend *= 1.1
                            sound.load_sounds(self.game_state)
                            self.counter = 0
                            self.is_skip_update = False
                            return
                        else:
                            self.counter += 1
                        return
            #ステージクリアイベント
                case G_.GameState.STAGECLEAR:
                    if self.di.flg.is_first:
                        self.is_nextstage = evt.interlude_first(self.message_window, self.eventstep)
                    elif self.boss.is_gone:
                        # v1.5.0
                        if self.depth_level == 1000:
                            skipstep = 3 if self.di.flg.is_clearbonus else 2
                            self.is_nextstage = evt.interlude_end(self.message_window, self.eventstep+skipstep)
                        else:
                            self.is_nextstage = evt.interlude_silence(self.message_window, self.eventstep)
                        px.blt(px.width//2-16,px.height-16,G_.IMGIDX["CHIP"],
                               *G_.ImageAddress.DIAGRAM[:2],
                               (1 if px.frame_count/G_.GAME_FPS%2==0 else -1)*G_.ImageAddress.DIAGRAM[2],
                               G_.ImageAddress.DIAGRAM[3],
                               colkey=px.COLOR_BLACK,scale=1+(px.frame_count/30%4-1)/10)
                    elif self.depth_level == 1000:
                        self.is_nextstage = evt.interlude_end(self.message_window, self.eventstep)
                    else:
                        self.is_nextstage = evt.interlude(self.message_window, self.eventstep)
                    self.message_window.draw()
                    self.message_window.draw_message()
            #エンディング1（メッセージウインドウ）
                case G_.GameState.ENDING:
                    self.is_nextstage = evt.ending(self.message_window, self.eventstep)
                    self.message_window.draw()
                    self.message_window.draw_message()
                    if self.message_window.close_counter >= self.message_window.close_timer//2:
                        if self.is_nextstage is False and px.frame_count//8%2 == 0:
                            px.blt(self.message_window.x+self.message_window.width//2-4,
                                self.message_window.y+self.message_window.height-5, G_.IMGIDX["CHIP"],
                                35,248, 5,8, colkey=0, rotate=90)
            #エンディング2（テキストスクロール準備）
                case 91:
                    px.dither(self.counter)
                    px.cls(0)
                    #背景描画共通呼び出し
                    self.background_drawer()
                    #HPウインドウ
                    self.user_hp_window.draw()
                    self.user_hp_window.drawText(self.user_hp_window.x+8, self.user_hp_window.y+8,
                                                [self.user.name, f"{self.user.hp:>11,}"])
                    self.boss_hp_window.draw()
                    self.boss_hp_window.drawText(self.boss_hp_window.x+8, self.boss_hp_window.y+8,
                                                [self.boss.name,f"{self.boss.hp:>11,}"])
                    #キャラクター描画
                    self.user.draw()
                    self.boss.draw()
                    self.message_window.draw()
                    self.message_window.draw_message()

            #エンディング3（テキストスクロール、スタッフロール）
                case 92:
                    px.cls(0)
                    if self.counter >= 1:
                        px.dither(1-self.counter/(G_.GAME_FPS*8))
                    # 流れ星
                    for s in self.stars:
                        s.draw()
                    # メッセージ（中央寄せ、日本語対応）
                    y = self.scroll_y
                    for line in self.ending_messages:
                        text_w = G_.JP_FONT.text_width(line)
                        px.text(px.width//2 - text_w // 2, int(y), line, 7, font=G_.JP_FONT)
                        if self.scroll_y < 1400:
                            y += 48  # 行間
                    if self.scroll_y <= 200:
                        px.text(426,324,"skip", 13)
            #ゲームオーバー
                case 99:
                    if isinstance(self.message_window, menu.Window):
                        if evt.gameover(self.user, self.counter, self.message_window):
                            self.message_window.draw()
                            self.message_window.draw_message()

        except Exception as e:
            comf.error_message(["",f"描画処理で予期せぬ例外が発生しました","",f"情報：",f"{e}",""])
            self.prepare_title()

    def reset_display(self):
        px.dither(1)
        px.camera()
        px.pal()

#******アプリケーション実行******#
if __name__ == "__main__":
    App()