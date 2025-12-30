import pyxel as px
import const as G_
import common_func as comf
import character, item, skill

class MonsterManager:
    def __init__(self, di, map_address:tuple, depth_level:int):
        self.di = di #Dependency Injection
        self.di.monster_manager = self
        self.ref_user = di.user #ユーザインスタンスへの参照
        self.message_manager = di.message_manager #メッセージ管理インスタンスへの参照
        self.mobgroup = [] #出現アドレス,グループID,モンスターID,モンスターオブジェクトのリスト
        self.red_treasure_list = [] #宝箱オブジェクト(出現マップアドレス、設置済フラグ、開封済フラグ、出現アドレス、アイテムID、個数)のリスト
        self.mobgroup_index = 0

        self.monster_list = comf.read_json(f"assets/data/tier{di.dungeon.floor_tier}.json")
        stage_monster_id_list = comf.generate_random_iterater(
                min(self.monster_list)[0],max(self.monster_list)[0]+1,len(self.monster_list)
            )
        for address in map_address:
            try:
                mobid = 3 if depth_level == 1 else next(stage_monster_id_list)
            except StopIteration:
                stage_monster_id_list = comf.generate_random_iterater(
                        min(self.monster_list)[0],max(self.monster_list)[0]+1,len(self.monster_list)
                    )
                mobid = next(stage_monster_id_list)
            self.mobgroup.append([address, 0, mobid, None, None])
            self.red_treasure_list.append(None)

        for i,_ in enumerate(self.mobgroup):
            self.mobgroup_index = i
            self.spawn_monster(depth_level)

    def spawn_monster(self, depth_level, treasure_id=None):
        mobs = self.mobgroup[self.mobgroup_index]
        monsters = []
        try:
            mobdata = [mobdata for mobdata in self.monster_list if mobdata[0] == mobs[2]][0]
        except IndexError:
            print(f"list={self.monster_list}\nmobs={mobs}")

        if mobs[4] is None:
            freeaddress = self.di.dungeon.rooms[self.di.dungeon.rooms_structure.index(self.mobgroup[self.mobgroup_index][0])].get_random_free_pixel_address()
            self.generate_spawner(mobs, mobdata, freeaddress)
        elif mobs[4].is_dead or mobs[4].is_elite:
            return

        #スポナーの周囲８マスに沸く
        c = mobs[4].address
        address_list = ([c[0]-16,c[1]],[c[0]+16,c[1]],[c[0],c[1]+16],[c[0],c[1]-16],
                        [c[0]-16,c[1]+16],[c[0]+16,c[1]-16],[c[0]+16,c[1]+16],[c[0]-16,c[1]-16])

        if px.rndi(0,G_.ELITE_RATE) < depth_level:
            if self.di.flg.is_elite is False:
                self.di.app.notice_window.message_text = self.di.flg.notice_rule(G_.FlagNotice.POP_ELITE)
            groupid = px.rndi(0,3)
            mobs[4] = Monster(self.di, depth_level, mobdata[G_.JsonMonster.TIER],
                                    mobdata[G_.JsonMonster.NAME],
                                    mobdata[G_.JsonMonster.IMAGESOURCE], c,
                                    *mobdata[G_.JsonMonster.DATA][groupid], is_elite=True)
        else:
            groupid = px.rndi(0,3)
            for i in range(px.rndi(1,8)):
                monsters.append(Monster(self.di, depth_level, mobdata[G_.JsonMonster.TIER],
                                        mobdata[G_.JsonMonster.NAME],
                                        mobdata[G_.JsonMonster.IMAGESOURCE], address_list[i],
                                        *mobdata[G_.JsonMonster.DATA][groupid]))
        if mobs[3]:
            mobs[3] += monsters
        else:
            mobs[3] = monsters

        return

    def generate_spawner(self, mobs, mobdata, freeaddress):
        name = "スポナー"
        image_source = G_.ImageAddress.SPAWNER
        parameter = mobdata[G_.JsonMonster.DATA][0].copy()
        parameter[G_.JsonMonster.MAXHP] *= 1.5 if self.di.flg.is_first else 3
        parameter[G_.JsonMonster.MOVETYPE] = 4
        parameter[G_.JsonMonster.MOVESPEED] = 0
        level = self.di.dungeon.depth_level
        mobs[4] = Monster(self.di, level, mobdata[G_.JsonMonster.TIER],
                          name, image_source, [freeaddress["x"],freeaddress["y"]],
                          *parameter)
        return

    def get_living_monsters(self):
        return (sum([1 for mob in self.mobgroup[self.mobgroup_index][3] if mob.is_dead is False])+
                (0 if self.mobgroup[self.mobgroup_index][4].is_dead else 1)
        )

    def get_spawner_state(self):
        return self.mobgroup[self.mobgroup_index][4].is_dead

    def revive_spawner(self):
        if self.di.flg.is_revive is False:
            self.di.app.notice_window.message_text = self.di.flg.notice_rule(G_.FlagNotice.REVIVE_SPAWNER)
        self.mobgroup[self.mobgroup_index][4].is_dead = False
        self.mobgroup[self.mobgroup_index][4].is_elite = False
        self.mobgroup[self.mobgroup_index][4].timer_fire = 0
        self.mobgroup[self.mobgroup_index][4].timer_ice = 0
        self.mobgroup[self.mobgroup_index][4].timer_wind = 0
        self.mobgroup[self.mobgroup_index][4].hp = self.mobgroup[self.mobgroup_index][4].maxhp

    def set_mobgroup_index(self, now_view):
        for i,data in enumerate(self.mobgroup):
            if data[0] == tuple(now_view):
                self.mobgroup_index = i
                break

    def update(self):
        for i, mob in enumerate(self.mobgroup[self.mobgroup_index][3]):
            if mob.is_dead:
                pass
            elif mob.hp < 0:
                mob.is_dead = True
            else:
                mob.update(self.ref_user)

        mob = self.mobgroup[self.mobgroup_index][4]
        if mob.is_dead:
            pass
        elif mob.hp < 0:
            mob.is_dead = True
            #パーク：赤宝箱レア度UP
            is_divine = True if self.di.user.get_rune_effect(G_.RuneList.DIVINE) is not None else False
            self.red_treasure_list[self.mobgroup_index] = \
                    (item.TreasureBox(self.mobgroup[self.mobgroup_index][0],[0,0],
                                      self.di.app.depth_level, mob.is_elite, is_divine))
            self.red_treasure_list[self.mobgroup_index].address = mob.address
        else:
            mob.update(self.ref_user)

        if  self.mobgroup[self.mobgroup_index][4].is_dead:
            if self.red_treasure_list[self.mobgroup_index].map_address == self.mobgroup[self.mobgroup_index][0]:
                if self.red_treasure_list[self.mobgroup_index].is_placed is False:
                    self.red_treasure_list[self.mobgroup_index].is_placed = True

    def draw(self, scene):
        if self.red_treasure_list[self.mobgroup_index] is not None and\
                self.red_treasure_list[self.mobgroup_index].map_address == self.mobgroup[self.mobgroup_index][0]:
            self.red_treasure_list[self.mobgroup_index].draw()

        for mob in self.mobgroup[self.mobgroup_index][3]:
            if mob.is_dead:                
                if mob.dead_dither > 0:
                    px.dither(mob.dead_dither)
                    px.blt(mob.address[0]-8, mob.address[1]-8, G_.IMGIDX["MOB"], 
                        mob.image_source[0] + 16*mob.image_position, mob.image_source[1],
                        mob.image_source[2] * mob.image_mirror, mob.image_source[3], colkey=3)
                    px.dither(1)
                    mob.dead_dither -= 0.025
            else:
                mob.draw(scene)
        mob = self.mobgroup[self.mobgroup_index][4]
        if mob.is_dead:                
            if mob.dead_dither > 0:
                px.dither(mob.dead_dither)
                px.blt(mob.address[0]-8, mob.address[1]-8, G_.IMGIDX["CHIP"], 
                    *G_.ImageAddress.SPAWNER, colkey=3)
                px.dither(1)
                mob.dead_dither -= 0.025
        else:
            mob.draw(scene)


class Monster(character.Character):
    def __init__(self, di, level, tier, name, image_source, address,
                 maxhp, attack, defend, arcane, action_waittime, movespeed,
                 reduce_fire, reduce_ice, reduce_wind, reduce_earth,
                 mana, move_type, skill_id, is_elite=False):
        super().__init__(move_type, address, image_source,
                         name, maxhp, di, level, movespeed)

        self.level = -0.5 if self.di.flg.is_first else level-1
        levelup_rate = 1 + (self.level-1)/100 + level/500 
        #深層補正
        adjust_hp,adjust_atk,adjust_def,adjust_exp = self.abyssal_adjustment(tier)

        hilvlhpadj = level if level < 500 else 251+level//2 if level < 700 else level//2
        self.maxhp = int(self.maxhp*levelup_rate*adjust_hp*(1.006932**hilvlhpadj))
        self.hp = self.maxhp
        self.mp = 0
        self.skillbook = {}
        if skill_id is not None:
            skill_dict = item.ItemManager.get_skill_by_id(str(skill_id))
            self.skillbook["a"] = skill.SkillModel(self.di,
                                                   [list(skill_dict.keys())[0],
                                                    list(skill_dict.values())[0]], self)
            self.mp = int(self.level+1*10)+arcane+list(skill_dict.values())[0][G_.JsonSkill.COST]

        self.di = di
        self.action_waittime = action_waittime
        self.movespeed = self.defaultmovespeed = movespeed
        self.reduce_element = {'fire':min(100,reduce_fire+(0.05*self.level)),
                               'ice':min(100,reduce_ice+(0.05*self.level)),
                               'wind':min(100,reduce_wind+(0.05*self.level)),
                               'earth':min(100,reduce_earth+(0.05*self.level))}
        #モンスター専用属性
        self.tier = tier
        self.mana = int(mana * levelup_rate * adjust_exp)

        self.skill_id = skill_id
        self.is_boss = False
        self.is_warp = False
        self.is_elite = is_elite
        self.warp_counter = 0
        self.image_mirror = 1
        self.dead_dither = 1
        self.is_hitattack = False

        #所持金算出
        self.gem = max(px.rndi(1,10), int((tier**2 + self.level//10) * px.rndi(1,11) + self.level))
        #モンスターの場合は算出ではなく指定値
        self.attack = int(attack * levelup_rate)*adjust_atk+self.level
        self.defend = 0 if self.di.flg.is_first else int(defend * levelup_rate)*adjust_def+self.level
        self.arcane = int((arcane if self.level<=100 else 1000) * levelup_rate +self.level/10)
        #エリート補正
        if self.is_elite:
            elitepower = 5
            self.maxhp *= elitepower
            self.attack *= elitepower
            self.defend *= elitepower
            self.arcane *= elitepower
            self.mana *= elitepower
            self.gem *= elitepower

            self.action_waittime -= 1
            self.move_type = G_.MoveType.TRACE

    def abyssal_adjustment(self, tier):
        adjust_hp = adjust_atk = adjust_def = adjust_exp = 1
        if self.level >= 100:
            match tier:
                case 0:
                    adjust_hp = 654
                    adjust_atk = 302
                    adjust_def = 2424.2
                    adjust_exp = 365.2
                case 1:
                    adjust_hp = 297.2
                    adjust_atk = 192.8
                    adjust_def = 1784
                    adjust_exp = 60.8
                case 2:
                    adjust_hp = 163.5
                    adjust_atk = 63.4
                    adjust_def = 558.3
                    adjust_exp = 28.1
                case 3:
                    adjust_hp = 54.5
                    adjust_atk = 25.3
                    adjust_def = 21.1
                    adjust_exp = 25.5
                case 4:
                    adjust_hp = 25.3
                    adjust_atk = 10.9
                    adjust_def = 335.7
                    adjust_exp = 12.2
                case 5:
                    adjust_hp = 10
                    adjust_atk = 11
                    adjust_def = 198.1
                    adjust_exp = 5.8
                case 6:
                    adjust_hp = 8.1
                    adjust_atk = 10
                    adjust_def = 57.2
                    adjust_exp = 5.3
                case 7:
                    adjust_hp = 5.1
                    adjust_atk = 3.9
                    adjust_def = 45
                    adjust_exp = 3.9
                case 8:
                    adjust_hp = 2
                    adjust_atk = 1.6
                    adjust_def = 3
                    adjust_exp = 2
        return [adjust_hp,adjust_atk,adjust_def,adjust_exp]

    def calc_distance(self, ref_user):
        diff_x = ref_user.address[0] - self.address[0]
        diff_y = ref_user.address[1] - self.address[1]
        threshold = self.image_source[2]*0.75
        return [diff_x, diff_y, threshold]

    def trace_target(self, ref_user):
        diff_x, diff_y, threshold = self.calc_distance(ref_user)
        dx = -1 if diff_x <= -threshold else 1 if diff_x >= threshold else 0
        dy = +3 if diff_y <= -threshold else -3 if diff_y >= threshold else 0
        dir = 5 + dx + dy  # テンキー配置の位置を表す
        # 斜めにいる場合 → ランダムに縦横へ寄せる
        match dir:
            case 1: dir = 4 if px.rndi(0,1) == 0 else 2
            case 3: dir = 6 if px.rndi(0,1) == 0 else 2
            case 7: dir = 4 if px.rndi(0,1) == 0 else 8
            case 9: dir = 6 if px.rndi(0,1) == 0 else 8
        # テンキー方向 → Python版 direction に変換
        dir_map = {2:0, 4:1, 6:2, 8:3}
        if dir in dir_map:
            self.direction = dir_map[dir]
        else:
            # 重なっている場合 → より差分の大きい軸で方向を決定
            if abs(diff_x) > abs(diff_y):
                self.direction = 2 if diff_x > 0 else 1  # 右 or 左
            elif abs(diff_y) > 0:
                self.direction = 0 if diff_y > 0 else 3  # 下 or 上
            else:
                # 完全に同座標 → デフォルトで下を向く（安全策）
                self.direction = 0

    def flee_target(self, ref_user):
        diff_x, diff_y, threshold = self.calc_distance(ref_user)
        dx = -1 if diff_x <= -threshold else 1 if diff_x >= threshold else 0
        dy = +3 if diff_y <= -threshold else -3 if diff_y >= threshold else 0
        dir = 5 - dx - dy  # 追尾の逆
        # 斜め方向なら、前フレームの向きを避けて縦横を選択
        match dir:
            case 1: dir = 4 if px.rndi(0,1) == 1 else 2
            case 3: dir = 6 if px.rndi(0,1) == 1 else 2
            case 7: dir = 4 if px.rndi(0,1) == 1 else 8
            case 9: dir = 6 if px.rndi(0,1) == 1 else 8
        # テンキー方向 → Python版 direction に変換
        dir_map = {2:0, 4:1, 6:2, 8:3}
        if dir in dir_map:
            self.direction = dir_map[dir]

    #詠唱後魔法の独立更新処理
    def skillupdate(self, ref_user):
        self.skillbook["a"].update()
        if self.skillbook["a"].active_skills:
            for active_skill in self.skillbook["a"].active_skills:
                _attackrange_skill = active_skill.model.func_attackrange(*active_skill.address,
                                                                    active_skill.direction)
                for _attackrange in _attackrange_skill:
                    if ref_user.is_evasion or ref_user in active_skill.hitlist:
                        continue
                    if comf.check_collision_hitbox(*_attackrange,
                                                   *ref_user.address, *G_.HitboxSize.MIDDLE):
                        damage = self.proc_attack_skill(active_skill, ref_user)
                        if damage>=ref_user.maxhp/3:
                            self.di.app.is_emergency = True
                        active_skill.hitlist.append(ref_user)
                        if damage > 0:
                            self.di.message_manager.add_message(f"被害 {damage}", 8)
                        elif damage == 0:
                            self.di.message_manager.add_message(f"レジスト成功！", 3)
                        if active_skill.model.id in ("704","705","706","707"): #魔法が命中したらインスタンスは消える
                            active_skill = None
                            return

    def update(self, ref_user):
        if self.is_dead:
            return
        if self.timer_attack == 0:
            self.is_hitattack = False
        
        self.common_timer_decrement()

        #詠唱呪文のインスタンス削除はインスタンス外部から実行
        if self.skillbook.get("a") is not None:
            self.skillupdate(ref_user)

        #砂時計、隠れ蓑によるモンスター移動ロジックの一時変更
        if ref_user.timer_item[G_.BuffType.TIMESTOP] > 0:
            return
        elif ref_user.timer_item[G_.BuffType.HIDDEN] > 0:
            movetype = 1
            self.is_warp = False
        else:
            movetype = self.move_type

        if self.timer_action > 0:
            return
        else:
            if self.timer_attack > 0:
                return
            elif self.is_warp or ref_user.is_evasion or self.is_hitattack:
                pass
            elif comf.check_collision_hitbox(*self.address,*G_.HitboxSize.MIDDLE,
                                             *ref_user.address,*G_.HitboxSize.MIDDLE):
                if ref_user.timer_damaged == 0:
                    if ref_user.timer_item[G_.BuffType.HIDDEN] <= 0: #砂時計の場合は処理がここまで来ない
                        damage = self.proc_attack_physical(ref_user)
                        if damage>=ref_user.maxhp/3:
                            self.di.app.is_emergency = True
                        self.is_hitattack = True
                        if damage:
                            self.di.message_manager.add_message(f"被害 {damage}", 8)
                        else:
                            self.di.message_manager.add_message(f"ガード成功！", 3)
                        return
            if self.skill_id is not None and\
                ref_user.timer_item[G_.BuffType.HIDDEN] <= 0 and\
                self.mp >= self.skillbook["a"].cost and\
                self.skillbook["a"].timer_recast <= 0 and\
                px.rndi(4, 24) == 24:
                if self.is_warp: #ワープ中は当然魔法を撃たない
                    pass
                elif (self.address[0]-4 <= ref_user.address[0] <= self.address[0]+4) or\
                        (self.address[1]-4 <= ref_user.address[1] <= self.address[1]+4):
                    self.trace_target(ref_user)
                    self.skillbook["a"].cast_skill()
                    return

        is_moved = False
        match movetype:
            case 1:
                tmpRnd = px.rndi(0,4)
                if tmpRnd == 4:
                    return
                else:
                    self.direction = tmpRnd
                    is_moved = True
            case 2:
                    self.trace_target(ref_user)
                    is_moved = True
            case 3:
                    self.flee_target(ref_user)
                    is_moved = True
            case 4:
                self.trace_target(ref_user) 
                self.image_position = px.frame_count%32//16
            case 5:
                self.image_position = px.frame_count%32//16
                self.warp_counter = max(0, self.warp_counter - 1)
                if self.warp_counter < self.action_waittime*16:
                    self.is_warp = True
                else:
                    self.is_warp = False
                if self.warp_counter == 0:
                    self.address = [px.rndi(20,G_.WND_MAIN[2]-20),px.rndi(20,G_.WND_MAIN[3]-20)]
                    self.timer_action = self.action_waittime
                    self.warp_counter = self.action_waittime*64
            case _:
                pass

        if is_moved:
            if ref_user.user_scene == 30:
                fencesize = 10
            elif ref_user.user_scene == 40:
                fencesize = 25
            is_blocked = self.check_fence(fencesize) #フェンス（柵）より外には移動しない
            if is_blocked:
                diff_x = self.address[0] - ref_user.address[0]
                diff_y = self.address[1] - ref_user.address[1]
                match movetype:
                    case 1:
                        self.direction = self.direction + 1 if self.direction != 3 else 0
                    case 2:
                        match self.direction:
                            case 0|3:
                                self.direction = 2 if diff_x > 0 else 1
                            case 1|2:
                                self.direction = 0 if diff_y > 0 else 3
                        if self.check_fence(fencesize):
                            return
                    case 3:
                        # 本来の方向に進めないので「ユーザから遠ざかる反対方向」を再計算
                        match self.direction:
                            case 0: self.direction = 3 if px.rndi(0,1) == 0 else 1 if diff_x < 0 else 2
                            case 1: self.direction = 2 if px.rndi(0,1) == 0 else 3 if diff_y < 0 else 0
                            case 2: self.direction = 1 if px.rndi(0,1) == 0 else 3 if diff_y < 0 else 0
                            case 3: self.direction = 0 if px.rndi(0,1) == 0 else 1 if diff_x < 0 else 2
                        if self.check_fence(fencesize):
                            return
                    # case 4:
                    #   移動しない為このケースは不要
                    # case 5:
                    #   通常移動ロジック内でフェンス内のみ移動する為このケースは不要
            self.move_address()
            self.timer_action = self.action_waittime

    def check_fence(self, fencesize):
        if (self.address[0] <= fencesize and self.direction == 1) or \
        (self.address[0] >= (G_.WND_MAIN[2]-fencesize) and self.direction == 2) or \
        (self.address[1] <= fencesize and self.direction == 3) or \
        (self.address[1] >= (G_.WND_MAIN[3]-fencesize) and self.direction == 0):
            return True
        return False

    def draw(self,scene=None):
        if self.skillbook.get("a") is not None:
            self.skillbook["a"].draw()

        if self.is_warp:
            return

        self.draw_damage_effect()
        if self.direction == 2:
            self.image_mirror = -1
        elif self.direction == 1:
            self.image_mirror = 1
        else:
            self.image_mirror = self.image_mirror

        ImageIndex = G_.IMGIDX["MOB"]
        r=0
        if self.name == "スポナー":
            self.image_position = 0
            ImageIndex = G_.IMGIDX["CHIP"]
            r = px.frame_count%60*6

        scale_ = 1
        if self.is_elite:
            px.pal(7,10)
            px.blt(self.address[0]-8, self.address[1]-8, G_.IMGIDX["CHIP"], 
                *G_.ImageAddress.SPAWNER, colkey=3, rotate = px.frame_count%60*9, scale=1.5)
            px.pal()
            scale_ = 1.4
        px.blt(self.address[0]-8, self.address[1]-8, ImageIndex, 
            self.image_source[0] + 16*self.image_position, self.image_source[1],
            self.image_source[2] * self.image_mirror, self.image_source[3],
            colkey=3, scale=scale_, rotate=r)

        if self.timer_fire>0:
            px.blt(self.address[0]-12, self.address[1]+4, G_.IMGIDX["CHIP"],
                    56,232, 8,8, colkey=0)
        if self.timer_ice>0:
            px.blt(self.address[0]-4, self.address[1]+4, G_.IMGIDX["CHIP"],
                    64,232, 8,8, colkey=0)
        if self.timer_wind>0:
            px.blt(self.address[0]+4, self.address[1]+4, G_.IMGIDX["CHIP"],
                    72,232, 8,8, colkey=0)

        # if G_.IS_DEBUG:
        #     px.text(self.address[0]-8,self.address[1]-10,f"HP:{self.hp}",19)
        #     px.text(self.address[0]-8,self.address[1]-4,f"AT:{self.attack}",24)
        #     px.text(self.address[0]-8,self.address[1]+2,f"DF:{self.defend}",19)
        #     px.text(self.address[0]-8,self.address[1]+8,f"AR:{self.arcane}",24)


class BossMonster(Monster):
    def __init__(self, di, level, tier, name, image_source, address,
                 maxhp, attack,defend,arcane, action_waittime,movespeed,
                 reduce_fire, reduce_ice, reduce_wind, reduce_earth,
                 mana,move_type,skill_id, is_elite):
        super().__init__(di, level, tier, name, image_source, address,
                         maxhp, attack,defend,arcane, action_waittime,movespeed,
                         reduce_fire, reduce_ice, reduce_wind, reduce_earth,
                         mana,move_type,skill_id, False)
        self.is_elite = is_elite    
        self.is_anger = False
        self.is_anger_event = False
        self.is_boss = True
        self.is_defeat = False
        self.is_broken = False
        self.is_gone = False
        self.is_special = False
        self.timer_special = (self.tier+6)*G_.GAME_FPS
        self.func_special_action = getattr(self, f"special_act_tier{tier}")

        if is_elite:
            powuprate = 1+((self.level)/1000)
            self.maxhp = int(self.maxhp*powuprate)
            self.hp = self.maxhp
            self.attack *= powuprate
            self.defend *= powuprate
            self.arcane *= powuprate
            self.name = "深"+self.name
        self.mp = 9999999999

        self.popupdamage = [] # [ [damage,counter],... ]
        self.prev_hp = self.hp
        han = "0123456789"
        zen = "０１２３４５６７８９"
        self.h2z = str.maketrans(han,zen)

    def abyssal_adjustment(self, tier):
        adjust_hp = adjust_atk = adjust_def = adjust_exp = 1
        if self.level >= 110:
            match tier:
                case 0:
                    adjust_hp = 500
                    adjust_atk = 200
                    adjust_def = 1000
                    adjust_exp = 21333
                case 1:
                    adjust_hp = 200
                    adjust_atk = 90
                    adjust_def = 300
                    adjust_exp = 1067
                case 2:
                    adjust_hp = 100
                    adjust_atk = 50
                    adjust_def = 160
                    adjust_exp = 213
                case 3:
                    adjust_hp = 60
                    adjust_atk = 20
                    adjust_def = 80
                    adjust_exp = 71
                case 4:
                    adjust_hp = 30
                    adjust_atk = 15
                    adjust_def = 40
                    adjust_exp = 21
                case 5:
                    adjust_hp = 15
                    adjust_atk = 8
                    adjust_def = 20
                    adjust_exp = 9
                case 6:
                    adjust_hp = 5
                    adjust_atk = 4
                    adjust_def = 8
                    adjust_exp = 6
                case 7:
                    adjust_hp = 2
                    adjust_atk = 2
                    adjust_def = 4
                    adjust_exp = 3
                case 8:
                    adjust_def = 2
                    adjust_exp = 2
        return [adjust_hp,adjust_atk,adjust_def,adjust_exp]

    def update(self, ref_user):
        if self.is_dead:
            return

        #HP半減で怒りモード
        if self.hp <= self.maxhp//2 and self.is_anger is False:
            self.action_waittime -= 1
            self.movespeed += 1
            self.is_anger = True
            self.is_anger_event = True

        self.common_timer_decrement()
        self.timer_special -= 1
        #ボスにデバフは効かない
        self.timer_fire = 0
        self.timer_ice = 0
        self.timer_wind = 0

        if self.skillbook.get("a") is not None:
            self.skillupdate(ref_user)

        #難易度調整の為　5秒に一度短時間硬直
        if px.frame_count%(G_.GAME_FPS*5) < G_.GAME_FPS//4:
            return

        if self.timer_action > 0:
            return
        else:
            if self.timer_attack > 0:
                return
            elif comf.check_collision_hitbox(*self.address,self.image_source[2]-4,
                                             self.image_source[3]-4,
                                             *ref_user.address,15,15):
                if ref_user.timer_damaged == 0:
                    self.proc_attack_physical(ref_user, 8)
                    return

        if self.is_special:
            self.func_special_action()
        elif self.timer_special <= 0:
            self.is_special = True
            self.timer_special = (self.tier+6)*G_.GAME_FPS

        self.trace_target(ref_user)

        #フェンス（柵）より外には移動しない
        fencesize = 40
        if (self.address[0] <= fencesize and self.direction == 1) or \
        (self.address[0] >= (G_.WND_MAIN[2]+G_.WND_SIDE[2]-fencesize) and self.direction == 2) or \
        (self.address[1] <= fencesize and self.direction == 3) or \
        (self.address[1] >= (G_.WND_MAIN[3]+G_.WND_SIDE[3]-fencesize) and self.direction == 0):
            diff_x = self.address[0] - ref_user.address[0]
            diff_y = self.address[1] - ref_user.address[1]
            match self.direction:
                case 0|3:
                    self.direction = 2 if diff_x > 0 else 1
                case 1|2:
                    self.direction = 0 if diff_y > 0 else 3
            if self.check_fence(fencesize):
                return

        self.move_address()
        self.timer_action = self.action_waittime

        #ポップアップダメージ更新
        if self.prev_hp != self.hp:
            damage = f"{int(self.prev_hp-self.hp):,}"
            self.popupdamage.append([damage.translate(self.h2z),0])
            self.prev_hp = self.hp

    def special_act_tier0(self):
        if self.level < 9:
            return
        self.movespeed = 5 if self.is_anger else 4
        if self.timer_special < 5*G_.GAME_FPS:
            self.movespeed = 3 if self.is_anger else 2
            self.is_special = False

    def special_act_tier1(self):
        self.address[0] = max(G_.WND_BOSS[0]+16,
                              min(G_.WND_BOSS[0]+G_.WND_BOSS[2]-16,
                                  self.address[0]+G_.CHARA_DIR[self.direction][0]*64))
        self.address[1] = max(G_.WND_BOSS[1]+16,
                              min(G_.WND_BOSS[1]+G_.WND_BOSS[3]-16,
                                  self.address[1]+G_.CHARA_DIR[self.direction][1]*64))
        self.is_special = False

    def special_act_tier2(self):
        self.movespeed = 0
        if self.skillbook["a"].timer_recast == 0:
            self.skillbook["a"].cast_skill()
        else:
            self.movespeed = 4 if self.is_anger else 3
            self.is_special = False

    def special_act_tier3(self):
        self.movespeed = 6
        if self.timer_special < (self.tier+1)*G_.GAME_FPS:
            self.movespeed = 1
            self.is_special = False

    def special_act_tier4(self):
        if self.skillbook["a"].timer_recast == 0:
            self.skillbook["a"].cast_skill()
        else:
            self.is_special = False

    def special_act_tier5(self):
        self.action_waittime = 1 if self.is_anger else 2
        if self.timer_special < 4*G_.GAME_FPS:
            self.action_waittime = 4 if self.is_anger else 5
            self.is_special = False

    def special_act_tier6(self):
        if self.skillbook["a"].timer_recast == 0:
            self.skillbook["a"].cast_skill()
        else:
            self.is_special = False

    def special_act_tier7(self):
        self.movespeed = 0
        tmp_address = self.address.copy()
        match self.direction:
            case G_.Direction.FRONT:
                rndirange = [[G_.WND_BOSS[0]+32,G_.WND_BOSS[2]-32],
                             [G_.WND_BOSS[1]+32,self.address[1]]]
            case G_.Direction.BACK:
                rndirange = [[G_.WND_BOSS[0]+32,G_.WND_BOSS[2]-32],
                             [self.address[1],G_.WND_BOSS[3]-32]]
            case G_.Direction.LEFT:
                rndirange = [[G_.WND_BOSS[0]+32,self.address[0]],
                             [G_.WND_BOSS[1]+32,G_.WND_BOSS[3]-32]]
            case G_.Direction.RIGHT:
                rndirange = [[self.address[0],G_.WND_BOSS[2]-32],
                             [G_.WND_BOSS[1]+32,G_.WND_BOSS[3]-32]]

        self.address[0] = px.rndi(*rndirange[0])
        self.address[1] = px.rndi(*rndirange[1])
        if self.skillbook["a"].timer_recast == 0:
            self.skillbook["a"].cast_skill()
        else:
            if px.frame_count%16 == 0:
                self.movespeed = 3 if self.is_anger else 2
                self.is_special = False
        self.address = tmp_address.copy()

    def special_act_tier8(self):
        self.movespeed = 0
        if self.skillbook["a"].timer_recast == 0 and px.rndi(1,100) > 50:
            self.skillbook["a"].cast_skill()
        else:
            if px.frame_count%32 == 0:
                self.movespeed = 3 if self.is_anger else 2
                self.is_special = False
            self.is_special = False

    def special_act_tier9(self):
        if self.skillbook["a"].timer_recast == 0:
            self.skillbook["a"].cast_skill()
        else:
            self.is_special = False

    def draw(self):
        if self.skillbook.get("a") is not None:
            self.skillbook["a"].draw()

        if self.timer_damaged%5 in (1,3):
            px.circ(*self.address, 34, 7)
        if self.timer_magicdamaged%5 in (2,4):
            px.circ(*self.address, 34, 8)

        if self.direction == 2:
            self.image_mirror = -1
        elif self.direction == 1:
            self.image_mirror = 1
        else:
            self.image_mirror = self.image_mirror

        if self.is_dead and self.is_defeat:
            px.blt(self.address[0]-32, self.address[1], G_.IMGIDX["MOB"],
                    self.image_source[0], self.image_source[3]*2,
                    self.image_source[2], self.image_source[3]//2, colkey=3)
        else:
            if self.di.flg.is_first and px.frame_count%4 == 0:
                return
            if self.is_special and px.frame_count%4==0:
                px.circ(*self.address, self.image_source[3]//2, 30)
            px.blt(self.address[0]-32, self.address[1]-32, G_.IMGIDX["MOB"], 
                self.image_source[0], self.image_source[1] + 64*(px.frame_count%64//32),
                self.image_source[2] * self.image_mirror, self.image_source[3], colkey=3)
            for i,dmg in enumerate(self.popupdamage):
                px.text(self.address[0]-G_.JP_FONT.text_width(dmg[0])//2,
                        self.address[1]-self.image_source[3]//2-(dmg[1]*2),
                        dmg[0], 24, G_.JP_FONT)
                self.popupdamage[i][1] += 1
            self.popupdamage = [[dmg,cnt] for dmg,cnt in self.popupdamage if cnt < G_.GAME_FPS*0.75]
                
