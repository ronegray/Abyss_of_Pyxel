import pyxel as px
import pickle
import gzip
from pathlib import Path
import const as G_
import common_func as comf
import menu, item, sound
import hashlib


class Commands:
    def __init__(self, x=0, y=0):
        self.msg_window = None
        self.data = None
        self.is_finished = False
        self.is_disp_finished = False
        self.message = []
        
    def keycheck(self):
        btn = comf.get_button_state()
        if btn["a"]:
            px.play(3,G_.SNDEFX["pi"], resume=True)
            return True
        if btn["b"]:
            return False
        return None
    
    def update(self):
        self.is_finished = True
        return self.keycheck()
    
    def draw(self):
        raise NotImplementedError
    
    def exec(self):
        raise NotImplementedError


class CommandSkipOpeningandTutrial(Commands):
    def __init__(self, di, x=0, y=0):
        self.di = di # Dependency Injection
        super().__init__(x, y)
    
    def exec(self):
        if not self.is_finished:
            self.di.flg.clear_all_flags()
            self.di.app.game_state = self.di.user.user_scene = G_.GameState.PREPARE_GAME
            self.is_finished = True
        if self.keycheck() != None:
            return True        
        return None

    def draw(self):
        pass


class CommandUpgrade(Commands):
    def __init__(self, di,  target_func:str, cost:int):
        self.di = di # Dependency Injection
        self.target_func = target_func
        self.cost = cost
        super().__init__()

    def exec(self):
        if not self.is_finished:
            if self.di.base.stock_gem >= self.cost:
                self.di.base.base_level[self.target_func] += 1
                self.di.base.stock_gem -= self.cost
                if G_.ConfigManager.LANGUAGE == G_.LanguageType.JAPANESE:
                    e2j = {"storage":"倉庫", "alchemy":"錬金", "ritual":"儀式", "shop":"売買", "backdoor":"隧道", "discover":"探索","upgrade":"拡張"}
                    targetname = e2j[self.target_func]
                self.di.base.information_window.message_text = [f"{targetname}のレベルが{self.di.base.base_level[self.target_func]}になった"]
                if self.target_func == "ritual":
                    self.di.user.reset_param()
                if self.target_func == "shop":
                    self.di.base.delete_garbage_shopitem()
                    self.di.base.generate_shop_items()
                px.play(2,G_.SNDEFX["lvup"],resume=True)
            else:
                self.di.base.information_window.message_text = [f"ジェムが足りません"]
            self.di.base.is_notice = True
            self.is_finished = True

            self.di.base.update_storage_max()
            self.di.base.update_basemenu()
            self.di.base.base_mainmenu.menu_window.height = ((1+1)+(self.di.base.base_mainmenu.menu_shape[1]*2))*G_.CHIP_PIXEL 

            self.command_instance = CommandSave(0,0, self.di.app, 0)
            self.command_instance.exec()

        if self.keycheck() != None:
            return True
        
        return None

    def draw(self):
        pass


class CommandIdentify(Commands):
    def __init__(self, di,  target_item:str, cost:int):
        self.di = di # Dependency Injection
        self.target_item = target_item
        self.cost = cost
        super().__init__()

    def exec(self):
        if not self.is_finished:
            if self.di.base.stock_gem >= self.cost:
                self.di.base.stock_gem -= self.cost
                px.play(1, G_.SNDEFX["identify"], resume=True) # SEは適宜
                self.target_item.is_identified = True
                self.target_item.update_name()
                self.di.base.information_window.message_text = [f"鑑定の結果・・・アイテムは",
                                                            f"{self.target_item.name}　だった"]
            else:
                self.di.base.information_window.message_text = [f"ジェムが足りません"]

            self.di.base.is_notice = True
            self.is_finished = True
            self.command_instance = CommandSave(0,0, self.di.app, 0)
            self.command_instance.exec()

        if self.is_finished:
            return False

        if self.keycheck() != None:
            return True
        
        return None

    def update(self):
        return True

    def draw(self):
        pass


class CommandCombineRune(Commands):
    def __init__(self, di, equip_tuple, slot_info, rune_tuple):
        self.di = di
        self.equip_uuid, self.equip_obj = equip_tuple
        self.slot_type = slot_info["type"]
        self.rune_uuid, self.rune_obj = rune_tuple
        super().__init__()

    def exec(self):
        if not self.is_finished:
            # 1. ルーンの状態更新 (BUGGAGE -> RUNESLOT)
            item.ItemManager.update_state(self.rune_uuid, G_.ItemStatus.RUNESLOT) # 要const定義
            
            # 2. 装備品のスロットに追加
            self.equip_obj.rune_slot.attach_rune(self.slot_type, self.rune_uuid)
            
            # 3. もし装備中なら、Userに効果を適用
            # 装備中のカテゴリIDと一致するか確認
            category = G_.ItemType.get_category(self.equip_obj.type_id)
            # categoryはWeapon:1, Armor:2, Shield:3に対応、equip_idリストはindex 0,1,2
            equip_idx = category - 1
            if 0 <= equip_idx < 3:
                if self.di.user.equip_id[equip_idx] == self.equip_uuid:
                    # 装備中なので効果適用
                    effect_data = [[key, rune] for key, rune 
                                   in item.ItemManager.get_rune_by_id(self.rune_obj.id).items()][0]
                    self.di.user.set_rune_effect(effect_data)

            self.di.base.information_window.message_text = ["結合が完了した"]
            self.di.base.is_notice = True
            
            px.play(1, G_.SNDEFX["gain"], resume=True) # SEは適宜
            self.is_finished = True
            
            # セーブ
            self.command_instance = CommandSave(0,0, self.di.app, 0)
            self.command_instance.exec()
            
        if self.keycheck() != None:
            return True
        return None
    
    def draw(self):
        pass


class CommandExtractRune(Commands):
    def __init__(self, di, equip_tuple, slot_info, success_rate):
        self.di = di
        self.equip_uuid, self.equip_obj = equip_tuple
        self.slot_type = slot_info["type"]
        self.slot_index = slot_info["index"]
        self.rune_uuid = slot_info["rune"]
        self.success_rate = success_rate
        super().__init__()

    def exec(self):
        if not self.is_finished:
            # 1. スロットから外す
            self.equip_obj.rune_slot.detach_rune(self.slot_type, self.slot_index)
            
            # 2. 装備中なら効果削除
            category = G_.ItemType.get_category(self.equip_obj.type_id)
            equip_idx = category - 1
            rune_obj = item.ItemManager.get_item(self.rune_uuid)
            
            if 0 <= equip_idx < 3:
                if self.di.user.equip_id[equip_idx] == self.equip_uuid:
                    effect_data = [[key, rune] for key, rune 
                                   in item.ItemManager.get_rune_by_id(rune_obj.id).items()][0]
                    self.di.user.remove_rune_effect(effect_data)

            # 3. 成功判定
            if px.rndi(1, 100) <= self.success_rate:
                # 成功: BUGGAGEへ
                item.ItemManager.update_state(self.rune_uuid, G_.ItemStatus.BUGGAGE)
                self.di.base.information_window.message_text = ["抽出に成功した"]
                px.play(1, G_.SNDEFX["pick"], resume=True)
            else:
                # 失敗: GARBAGEへ
                item.ItemManager.update_state(self.rune_uuid, G_.ItemStatus.GARBAGE)
                self.di.base.information_window.message_text = ["抽出に失敗し、秘紋石は砕け散った…"]
                px.play(1, G_.SNDEFX["shattered"], resume=True) # SE要定義

            self.di.base.is_notice = True
            self.is_finished = True
            
            # セーブ
            self.command_instance = CommandSave(0,0, self.di.app, 0)
            self.command_instance.exec()

        if self.keycheck() != None:
            return True
        return None

    def draw(self):
        pass


class CommandSell(Commands):
    def __init__(self, di, insW, iteminfo, cost):
        self.di = di # Dependency Injection
        self.messege_window=insW
        self.iteminfo = iteminfo
        self.cost = cost
        super().__init__()
        self.is_bought   = False

    def exec(self):
        if not self.is_finished:
            self.di.base.stock_gem += self.cost
            
            # 追加: 結合されているルーンもGARBAGEへ
            item.ItemManager.delete_attached_runes(self.iteminfo[0])
            item.ItemManager.update_state(self.iteminfo[0], G_.ItemStatus.GARBAGE)
            
            self.msg = ["今後ともごひいきに。"]
            px.play(2, G_.SNDEFX["buy"], resume=True)
            self.is_finished = True

    def draw(self):
        if self.is_finished:
            self.messege_window.draw()
            self.messege_window.drawText(self.messege_window.x +8 ,self.messege_window.y + 8, self.msg)
            self.is_disp_finished = True


class CommandSellAll(Commands):
    def __init__(self, di, insW, price):
        self.di = di # Dependency Injection
        self.messege_window=insW
        self.price = price
        super().__init__()
        self.is_bought   = False

    def exec(self):
        if not self.is_finished:
            self.di.base.stock_gem += self.price
            for sellitem in self.di.user.inventory:
                # 追加: 結合されているルーンもGARBAGEへ
                item.ItemManager.delete_attached_runes(sellitem[0])
                item.ItemManager.update_state(sellitem[0], G_.ItemStatus.GARBAGE)

            self.msg = ["今後ともごひいきに。"]
            px.play(2, G_.SNDEFX["buy"], resume=True)
            self.is_finished = True

    def draw(self):
        if self.is_finished:
            self.messege_window.draw()
            self.messege_window.drawText(self.messege_window.x +8 ,self.messege_window.y + 8, self.msg)
            self.is_disp_finished = True


class CommandGetPerk(Commands):
    def __init__(self, di,  target_item_list, cost):
        self.di = di # Dependency Injection
        self.target_rune_list = target_item_list
        self.cost = cost
        super().__init__()

    def exec(self):
        if not self.is_finished:
            if self.di.base.stock_mana >= self.cost:
                self.di.base.stock_mana -= self.cost
                if int(self.target_rune_list[0]) >= 900:
                    self.di.user.perk_list.add(self.target_rune_list[0])
                    self.di.user.set_rune_effect(self.target_rune_list)
                else:
                    self.di.user.skill_list.add(self.target_rune_list[0])
                    if self.di.flg.is_getskill is False:
                        self.di.app.notice_window.message_text = self.di.flg.notice_rule(G_.FlagNotice.GETSKILL)
                self.di.base.information_window.message_text = [f"新しい能力を取得した"]
                px.play(1, G_.SNDEFX["gain"], resume=True)
            else:
                self.di.base.information_window.message_text = [f"祭壇に捧げたマナが足りない"]

            self.di.base.is_notice = True
            self.is_finished = True
            self.command_instance = CommandSave(0,0, self.di.app, 0)
            self.command_instance.exec()

        if self.keycheck() != None:
            return True
        
        return None

    def draw(self):
        pass


class CommandStatus(Commands):
    def __init__(self, x, y, user):
        super().__init__(self)
        self.user = user
        windowwidth = 43
        self.param1_window = menu.Window(x, y, G_.CHIP_PIXEL*windowwidth,G_.CHIP_PIXEL*14,0)
        self.param2_window = menu.Window(x, self.param1_window.y+self.param1_window.height-5,
                                         G_.CHIP_PIXEL*windowwidth,G_.CHIP_PIXEL*8,0)
        self.param3_window = menu.Window(x, self.param2_window.y+self.param2_window.height-5,
                                         G_.CHIP_PIXEL*windowwidth,G_.CHIP_PIXEL*4,0)
        self.param4_window = menu.Window(x, self.param3_window.y+self.param3_window.height-5,
                                         G_.CHIP_PIXEL*windowwidth,G_.CHIP_PIXEL*14,0)

    def update(self):
        if not self.is_finished:
            equip_name = []
            for name in (self.user.weapon.name, self.user.armor.name, self.user.shield.name):
                strlen_ = len(name)*2
                equip_name.append(name + " " * (23 - strlen_))

            self.data1 = [
                f"レベル　：{self.user.level: >12}　　筋力：{self.user.strength:>5}　　 [属性軽減率]",
                f"最大ＨＰ：{self.user.maxhp: >12,}　　器用：{self.user.dexterity:>5}　　火術：{self.user.reduce_element['fire']:06.2f}%",
                f"最大ＭＰ：{self.user.maxmp: >12,}　　敏捷：{self.user.agility:>5}　　氷術：{self.user.reduce_element['ice']:06.2f}%",
                f"攻撃力　：{self.user.attack: >12,}　　知性：{self.user.intelligence:>5}　　風術：{self.user.reduce_element['wind']:06.2f}%",
                f"防御力　：{self.user.defend: >12,}　　頑健：{self.user.vitality:>5}　　土術：{self.user.reduce_element['earth']:06.2f}%",
                f"魔力　　：{self.user.arcane: >12,}　　幸運：{self.user.luck:>5}　　{
                    G_.CharaType.NAME[self.user.char_type]}",
            ]
            self.data2 = [
                f"武器　　： {G_.ITEM_TYPE_NAME[self.user.weapon.type_id]} ）{equip_name[0]} 熟練度 {self.user.weapon.mastery:06.2f}%",
                f"防具　　：{G_.ITEM_TYPE_NAME[self.user.armor.type_id]}）{equip_name[1]} 移動力 {self.user.movespeed}px/{self.user.action_waittime}f",
                f"盾　　　：{G_.ITEM_TYPE_NAME[self.user.shield.type_id]}）{equip_name[2]} 攻撃遅延度 {self.user.shield.rate_attackspeed:>1.1f}",
            ]
            self.data3 = [
                f"習熟度　：杖){self.user.mastery["wand"]-100:06.2f}% 剣){self.user.mastery["sword"]-100:06.2f}% 槍){self.user.mastery["spear"]-100:06.2f}% 斧){self.user.mastery["axe"]-100:06.2f}%",
                ]
            if len(self.user.rune_effects):
                runelist = ""
                icnt = 0
                for runename in [item.ItemManager.get_item_info(rune_id)[1]
                                for rune_id in sorted(self.user.rune_effects)]:
                    runelist += runename+"   "
                    icnt += 1
                    if icnt == 8:
                        runelist += "\n"
                        icnt = 0
                self.data4 = [f"{str(runelist)}"]
            self.is_finished = True
        return self.keycheck()

    def draw(self, P_adrCursor):
        if self.is_finished:
            self.param1_window.draw()
            self.param1_window.drawText(self.param1_window.x + 8 ,self.param1_window.y + 8, self.data1)
            self.param2_window.draw()
            self.param2_window.drawText(self.param2_window.x + 8 ,self.param2_window.y + 8, self.data2)
            self.param3_window.draw()
            self.param3_window.drawText(self.param3_window.x + 8 ,self.param3_window.y + 8, self.data3)
            if len(self.user.rune_effects):
                self.param4_window.draw()
                self.param4_window.drawText(self.param4_window.x + 8 ,self.param4_window.y + 8, self.data4)


class CommandInventory(Commands):
    def __init__(self, x, y, user):
        super().__init__(self)
        self.user = user
        self.data = []
        
        for item_uuid in self.user.inventory:
            obj = item.ItemManager.get_item(item_uuid)
            strlen_ = len(obj.name)*2
            name = obj.name + " " * (21 - strlen_)
            color_code = G_.ItemRank.COLOR[obj.rank] if obj.is_identified else px.COLOR_WHITE
            self.data.append([f"{name}",color_code])
        if len(self.data) == 0:
            self.data.append(["何も　持っていない", px.COLOR_WHITE])

        self.is_finished = True
        self.msg_window = menu.Window(x, y, G_.CHIP_PIXEL*23,G_.CHIP_PIXEL*(len(self.data)*2+2),0)

    def update(self):
        return self.keycheck()
    
    def draw(self, P_adrCursor):
        if self.is_finished:
            self.msg_window.draw()
            self.msg_window.drawTextColor(P_adrCursor[0] + 8 ,P_adrCursor[1] + 16, self.data)
 

class CommandEscape(Commands):
    def __init__(self, di):
        self.di = di # Dependency Injection
        super().__init__()

    def exec(self):
        if not self.is_finished:
            lost_rate = 10 if self.di.user.is_safeescape else 66
            #パーク：遺失率低下
            rune_effect = self.di.user.get_rune_effect(G_.RuneList.HOLD)
            lost_rate *= (1-rune_effect[1]/100) if rune_effect is not None else 1
            for item_ in self.di.user.inventory:
                if px.rndi(1,100) <= lost_rate:
                    item.ItemManager.delete_attached_runes(item_[0])
                    item.ItemManager.remove_item(item_[0])
            px.stop()
            px.play(3, G_.SNDEFX["run"])
            startframe = px.frame_count
            while px.play_pos(3) is not None:
                px.flip()
                if startframe + G_.GAME_FPS//2 < px.frame_count:
                    px.cls(0)
            self.di.base.is_returned = True
            self.di.app.game_state = self.di.user.user_state = G_.GameState.PREPARE_BASE
            self.is_finished = True

        if self.keycheck() != None:
            return True
        
        return None

    def draw(self):
        pass


class CommandQuit(Commands):
    def __init__(self):
        pass

    def exec(self):
        px.quit()


class CommandCharaSelect(Commands):
    def __init__(self, x, y, select_index, fnc_init_user):
        super().__init__(x,y)
        self.select_index = select_index
        self.fnc_init_user = fnc_init_user

    def exec(self):
        self.fnc_init_user(self.select_index)
        px.cls(0)
        return
    
    def draw(self):
        pass


class CommandBuy(Commands):
    def __init__(self, di, insW, iteminfo, cost):
        self.di = di # Dependency Injection
        self.messege_window=insW
        self.iteminfo = iteminfo
        self.cost = cost
        super().__init__()
        self.is_bought   = False

    def exec(self):
        if self.di.base.stock_gem <= self.cost:
            self.msg = ["所持金不足ですね。どうぞお引き取りを。"]
            self.is_finished = True
        if len(self.di.user.inventory) >= self.di.user.inventory_max:
            self.msg = ["持ち物がいっぱいみたいですね。"]
            self.is_finished = True

        if not self.is_finished:
            self.di.app.notice_window.message_text = item.notice_item(self.iteminfo, self.di.flg)
            iteminfo = item.pick_item(self.iteminfo.uuid, 1, self.di.user)

            self.di.base.stock_gem -= self.cost
            item.ItemManager.update_state(self.iteminfo.uuid,G_.ItemStatus.BUGGAGE)
            self.di.base.shop_item_list.remove(self.iteminfo.uuid)

            self.command_instance = CommandSave(0,0, self.di.app, 0)
            self.command_instance.exec()

            self.msg = ["お買い上げありがとうございます！"]
            px.play(2, G_.SNDEFX["buy"], resume=True)
            self.is_finished = True

        if self.keycheck() != None:
            return True
        
        return None

    def draw(self):
        if self.is_finished:
            self.messege_window.draw()
            self.messege_window.drawText(self.messege_window.x +8 ,self.messege_window.y + 8, self.msg)
            self.is_disp_finished = True


class CommandSave(Commands):
    def __init__(self, x, y, app, data_no:int, is_quit:bool=False):
        super().__init__(self)
        self.messege_window = menu.Window(16,88,px.width - (G_.CHIP_PIXEL*2*2),(1+1*2+1)*G_.CHIP_PIXEL,1)
        self.app = app
        self.data_no = data_no
        self.GameData = {}
        self.is_quit = is_quit

    def exec(self):
        if not self.is_finished:
            self.GameData["HEADER"] = G_.DATA_HEADER #不正データチェック用
            #ゲームの中核インスタンス
            self.GameData["flag"] = self.app.di.flg
            self.GameData["item"] = item.ItemManager._repos
            self.GameData["base"] = self.app.di.base
            self.GameData["user"] = self.app.user

            #Pickle時エラーチェック用
            #import test
            # print("Checking for leaks...")
            # leak_path = test_image.find_image_leak(self.GameData)
            # if leak_path:
            #     print(f"★画像リーク発見!: {leak_path}")
            # else:
            #     print("画像リークなし。安全です。")
            raw = pickle.dumps(self.GameData)
            self.GameData = None
            compressed = gzip.compress(raw)
            hash_value = hashlib.sha256(compressed).digest()  # 新形式: ハッシュ計算
            hashed_data = hash_value + compressed  # 新形式: ハッシュ + 圧縮データ
            path = Path(px.user_data_dir("moq",G_.APP_NAME)+f"savedata{self.data_no}.bin")
            with open(path, "wb") as f:
                f.write(G_.DATA_HEADER + hashed_data)

            if self.is_quit:
                px.stop()
                px.play(3, G_.SNDEFX["save"])
                
                while px.play_pos(3) is not None:
                    pass

    def draw(self, P_adrCursor=None):
        if self.is_finished:
            self.messege_window.draw()
            self.messege_window.drawText(self.messege_window.x + 8 ,self.messege_window.y + 8, ["セーブが完了しました"])


class CommandLoad(Commands):
    def __init__(self, x, y, app, data_no:int):
        super().__init__(self)
        self.messege_window = menu.Window(16,px.height//2-((1+1*2+1)*G_.CHIP_PIXEL)//2,
                                          px.width - (G_.CHIP_PIXEL*2*2),
                                          (1+1*2+1)*G_.CHIP_PIXEL,1)
        self.GameData  = {}
        self.app = app
        self.data_no = data_no
        self.is_nofile = False

    def exec(self):
        path = Path(px.user_data_dir("moq",G_.APP_NAME)+f"savedata{self.data_no}.bin")
        if path.exists() is False:
            self.is_nofile = True
            return False

        if not self.is_finished:
            self.app.reset_parameter()

            # 1. データの展開
            with open(path, "rb") as f:
                savedata = f.read()

            if not savedata.startswith(G_.DATA_HEADER):
                comf.error_message(["Invalid save data"])
                return False

            savedata_body = savedata[len(G_.DATA_HEADER):]  # HEADER除去後のデータ
            # 新形式（ハッシュ）試行
            hash_value = savedata_body[:32]  # SHA-256ハッシュ（32バイト）
            compressed = savedata_body[32:]
            if hashlib.sha256(compressed).digest() == hash_value:  # ハッシュ一致
                raw = gzip.decompress(compressed)
                self.GameData = pickle.loads(raw)
                if self.GameData["HEADER"] != G_.DATA_HEADER:
                    comf.error_message(["Invalid save data"])
                # 成功: 新形式ロード完了
            item.ItemManager._repos = self.GameData["item"]

            # 3. 【登録フェーズ】インスタンスをDIコンテナ(self.app.di)にすべてセットする
            # ※まだ resume は呼びません。互いに参照できるように先に配置だけ済ませます。
            self.app.di.flg = self.GameData["flag"]
            self.app.user = self.GameData["user"]
            self.app.di.user = self.app.user
            self.app.di.base = self.GameData["base"]
            self.GameData = None

            # 4. 【復帰フェーズ】diが整った状態で resume を呼ぶ
            # これで、resumeの中で `self.di.message_manager` 等を呼んでも安全です。
            self.app.user.resume(self.app.di)
            for button,skill in self.app.user.skillbook.items():
                if skill is not None:
                    skill.resume(self.app.di)
            self.app.di.base.resume(self.app.di)

            # 5.　【再開フェーズ】ゲーム状態を変更してプレイを再開
            self.app.game_state = self.app.user.user_scene = G_.GameState.BASE

            px.stop()
            px.cls(0)
            if px.play_pos(3) is None:
                px.play(3, G_.SNDEFX["load"])
                while px.play_pos(3) is not None:
                    pass
                px.flip()

            sound.load_sounds(self.app.game_state)

            self.is_finished = True
    
        return True

    def draw(self,P_adrcursor=None):
        if self.is_nofile:
            self.messege_window.draw()
            self.messege_window.drawText(self.messege_window.x + 8 ,self.messege_window.y + 8, ["データが存在しません"])
            self.is_disp_finished = True
            return
