import pyxel as px
import const as G_, common_func as comf
import menu, item, sound, command

class Base:
    '''拠点クラス'''
    STORAGE_DEFAULT_SIZE = 8

    def __init__(self, di):
        self.di = di
        
        # --- 数値・フラグ等の単純データの初期化 ---
        self.stock_mana = 0
        self.stock_gem = 0
        self.base_level = {"storage":1, "alchemy":0, "ritual":0, "shop":1, "backdoor":0, "discover":1, "upgrade":1, "quit":1}
        self.deathdrop_id = {"weapon":None, "armor":None, "shield":None}
        self.reached_max_level = 1
        self.score_max = 0 
        self.is_defeat_or_die = False
        self.is_returned = False
        self.defeated_boss = 0
        self.shop_item_list = []
        self.base_menu_itemlist = []
        self.is_notice = False
        self.ritual_window = None
        self.cmd = False
        self.is_finish_tutrial = False
        self.eventstep = 0

        # --- 依存関係のある処理 ---
        self.update_storage_max()
        self.update_basemenu_list() # リストデータを作成
        
        # --- 画像とUIの生成（共通メソッド呼び出し） ---
        self.set_image()
        self._init_ui_objects() # ★ここで生成

    def _init_ui_objects(self):
        """
        UIインスタンスの生成・再生成を行う共通メソッド
        __init__ と resume の両方から呼ばれる
        """
        # WindowやMenuの生成処理をここに集約
        self.information_window = menu.Window(*G_.WND_INFO)
        self.basestate_window = menu.Window(*G_.WND_BASE)
        self.userstate_window = menu.Window(*G_.WND_USTA)
        self.ritual_window = None

        # update_basemenu_listで作られた self.base_menu_itemlist を使用
        self.base_mainmenu = menu.MenuBaseMain(
            self.di, 8, 8, [1, len(self.base_menu_itemlist)],
            self.base_menu_itemlist, 2
        )

    def __getstate__(self):
        """pickle保存時: 不要なオブジェクトを除外"""
        # common_funcの関数で di, image_*, *_window, *_menu を削除
        return comf.get_clean_state(self)

    def resume(self, di):
        """ロード後の復帰処理"""
        self.di = di
        
        # --- 画像とUIの再構築 ---
        self.set_image()      # 画像読み込み
        
        # self.base_menu_itemlist 等の単純データはpickleから復元されているため
        # そのままUI生成メソッドを呼べばOKです
        self._init_ui_objects() # ★ここで再生成

    def set_image(self):
        self.image_base = px.Image.from_image("assets/image/base.bmp")

    @property
    def stock_mana_max(self):
        match self.base_level["ritual"]:
            case 0:
                return 0
            case 1:
                return 3300
            case 2:
                return 29700
            case 3:
                return 89500
            case 4:
                return 194000
            case 5:
                return 498000
            case 6:
                return 960000
            case 7:
                return 1580000
            case 8:
                return 2890000
            case 9:
                return 6160000
            case 10:
                return 9999999

    @property
    def storage(self):
        return item.ItemManager.get_item_by_state(G_.ItemStatus.STORAGE)

    def update_storage_max(self):
        self.storage_max = self.STORAGE_DEFAULT_SIZE * self.base_level["storage"] + 8

    def return_base(self):
        '''拠点帰還時の処理'''
        #ダンジョン活動結果の反映
        if self.is_defeat_or_die and self.di.flg.is_ritual is False:
            pass
        else:
            if self.di.user.gem:
                self.stock_gem += self.di.user.gem
                self.di.user.gem = 0
                self.di.app.notice_window.message_text = ["　　持ち帰ったジェムを資産庫に保管した"]
            if self.di.user.mana["stock"]:
                self.stock_mana += self.di.user.mana["stock"]
                self.di.user.mana["stock"] = 0
                self.di.app.notice_window.message_text += ["　　　　瓶に貯めたマナを祭壇に捧げ注ぎ込んだ"]

        self.score_max = max(self.di.user.score, self.score_max)
        self.base_level["discover"] = min(11,self.defeated_boss//10+1)

        self.update_basemenu()
        self.generate_shop_items()

        #メニューのリセット
        self.base_mainmenu = menu.MenuBaseMain(self.di, 8,8,[1,len(self.base_menu_itemlist)],self.base_menu_itemlist,2)

    def generate_shop_items(self, count=8):
        """base_level["shop"] に基づいてアイテムリストを生成する"""
        if self.base_level["shop"] == 0:
            return
        shop_level = self.base_level["shop"]*10 + (2 if self.base_level["shop"]==10 else 1)
        for _ in range(count):
            # item.ItemManagerを直接呼び出す
            category = px.rndi(G_.ItemType.CATEGORY_WEAPON,G_.ItemType.CATEGORY_SHIELD)
            new_item = item.ItemManager.create_randomitem(shop_level,category,False,
                                                          G_.ItemStatus.SHOP)
            new_item_obj =  item.ItemManager.get_item(new_item)
            if new_item_obj.rank == G_.ItemRank.COMMON:
                new_item_obj.update_rank(G_.ItemRank.UNCOMMON)
            if new_item_obj.rank >= G_.ItemRank.RARE:
                if px.rndi(0,9) >= new_item_obj.rank+3:
                    new_item_obj.is_identified = True
                    new_item_obj.update_name()
            self.shop_item_list.append(new_item)

    def delete_garbage_shopitem(self):
        item.ItemManager.garbage_correct()
        self.shop_item_list.clear()

    def update_basemenu_list(self):
        self.base_menu_itemlist = [["inventory"]]
        self.base_menu_itemlist += [[func[0]] for func in self.base_level.items()
                                   if func[1] > 0]
        if G_.ConfigManager.LANGUAGE == G_.LanguageType.JAPANESE:
            e2j = {"inventory":"荷物","storage":"倉庫", "alchemy":"錬金", "ritual":"儀式",
                   "shop":"売買","backdoor":"近道", "discover":"探索",
                   "upgrade":"拡張","quit":"終了"}
            tmp = [[e2j[listitem[0]]] for listitem in self.base_menu_itemlist]
            self.base_menu_itemlist = tmp
    
    def update_basemenu(self):
        self.update_basemenu_list()
        self.base_mainmenu.menu_shape = [1,len(self.base_menu_itemlist)]
        self.base_mainmenu.menu_items = self.base_menu_itemlist

    def update_max_level(self):
        self.reached_max_level = max(self.reached_max_level, self.di.app.depth_level)

    def update(self):
        #パラメータ表示
        btn=comf.get_button_state()
        if btn["S"]:
            self.cmd = command.CommandStatus(54,20,self.di.user)
        if isinstance(self.cmd,command.CommandStatus):
            if self.cmd.update() is False:
                self.cmd = None
            return
        #守護神メッセージ
        if isinstance(self.ritual_window,menu.Window):
            next_ = self.ritual_window.update()
            if self.is_finish_tutrial:
                self.di.flg.is_ritual = True
                self.base_level["ritual"] = 1
                self.di.user.mana_drain_rate = 50
                self.di.user.mana["stockmax"] = self.stock_mana_max
                self.stock_mana = 180
                self.update_basemenu()
                self.base_mainmenu = menu.MenuBaseMain(self.di, 8,8,[1,len(self.base_menu_itemlist)],self.base_menu_itemlist,2)
                self.ritual_window = None
                sound.load_sounds(G_.GameState.BASE)
            elif next_ is False:
                self.ritual_window.close_counter = 0
                self.eventstep += 1
            return
        if self.di.flg.is_ritual is False and self.is_defeat_or_die:
            self.ritual_window = menu.Window(px.width//2-160,20, 320,
                                                px.height-40, 1, 150)
            sound.load_sounds(G_.GameState.RITUAL)
        #キャラスプライト足踏み
        if px.frame_count%32 == 0:
            self.di.user.image_position = 1 - self.di.user.image_position
        #メイン更新ロジック呼び出し
        if self.base_mainmenu.update() is False:
            self.information_window.update()
            self.userstate_window.update()

    def draw_state(self):
        self.basestate_window.draw()
        state = [
            " [拠点情報]",
            "最大到達深度",f"{min(1000,self.reached_max_level): 5,}",
            "最大スコア",f"{min(9999999999,int(self.score_max)): 13,}",
            "倉庫保管状況",f"{len(self.storage): >5}/{self.storage_max: >5}",
            "総資産",f"{min(9999999999,int(self.stock_gem)): 13,}",
            "奉納済マナ",f"{min(9999999999,int(self.stock_mana)): 13,}",
        ]
        self.basestate_window.drawText(self.basestate_window.x + 8,
                                       self.basestate_window.y + 8, state)

    def draw(self):
        px.cls(0)
        px.blt(0,0,self.image_base, 0,0,
               self.image_base.width, self.image_base.height, colkey=px.COLOR_BLACK)
        #守護神メッセージ時は他の情報を抑止
        if isinstance(self.ritual_window,menu.Window):
            self.is_finish_tutrial = self.tutrial(self.ritual_window, self.eventstep)
            self.base_mainmenu.draw()
            self.ritual_window.draw()
            self.ritual_window.drawText(self.ritual_window.x+16,self.ritual_window.y+10,self.ritual_window.message_text)
            return
        #メイン描画ロジック
        px.text(1,1, "F1/start : parameter",px.COLOR_WHITE)
        for i,[name,funclevel] in enumerate(self.base_level.items()):
            if name == "upgrade":
                continue
            if funclevel:
                px.blt(*G_.ImageAddress.BASE_FUNC[i][:2],G_.IMGIDX["CHIP"],
                       *G_.ImageAddress.BASE_FUNC[i][2:],colkey=px.COLOR_BLACK)
        if isinstance(self.cmd,command.CommandStatus):
            self.cmd.draw(0)
            return
        match self.base_mainmenu.menu_items[self.base_mainmenu.cursor_position[1]][0]:
            case "inventory"|"荷物":
                i = 6
            case "storage"|"倉庫":
                i = 0
            case "alchemy"|"錬金":
                i = 1
            case "ritual"|"儀式":
                i = 2
            case "shop"|"売買":
                i = 3
            case "backdoor"|"近道":
                i = 4
            case "discover"|"探索":
                i = 5
            case "upgdrade"|"拡張":
                i = 6
            case "quit"|"終了":
                i = 6
            case _:
                i = None
        if i is not None:
            self.di.user.address = [G_.ImageAddress.BASE_FUNC[i][0]+16,
                                    G_.ImageAddress.BASE_FUNC[i][1]+32]
        self.di.user.draw()

        self.userstate_window.draw()
        self.userstate_window.message_text = [f"最大HP：{self.di.user.maxhp: >9,}",
                                              f"攻撃力：{self.di.user.attack: >9,}",
                                              f"防御力：{self.di.user.defend: >9,}",
                                              f"魔力　：{self.di.user.arcane: >9,}"]
        self.userstate_window.draw_message()

        self.draw_state()
        self.base_mainmenu.draw()

        if self.di.base.is_notice:
            self.information_window.draw()
            self.information_window.draw_message()

    def tutrial(self, window, step):
        match step:
            case 0:
                if self.score_max >= 5000:
                    youare = ["幻の迷宮を越えし者","真の迷宮に挑む資格"]
                else:
                    youare = ["迷宮の闇に斃れし者","探索者としての見所"]
                window.message_text = [f"{youare[0]}よ　私はこの地の守護神",
                                        "",
                                        "迷宮で得た力が失われた事に気付きましたか？",
                                        "迷宮を出ると、マナは空へ散り行き失われます",
                                        "",
                                        f"貴方には{youare[1]}がありそうです",
                                        "貴方にマナを汲み取る器を授けましょう",
                                        "この瓶でマナを持ち帰り、我が祭壇に捧げるのです",
                                        "",
                                        "身に宿したマナの散逸を防ぐ事は出来ませんが",
                                        "私に力が戻れば貴方に貸し与える事が出来ます",
                                        "",
                                        "自身にどれ程マナを吸収し、瓶にどれ程注ぐのか",
                                        "祭壇で吸収率を決めるとよいでしょう",
                                        "",
                                        "迷宮で命の危機に瀕しても、私がここへ連れ戻します",
                                        "安心しておいきなさい"]
            case 1:
                window.message_text = ["この都市を拠点として活動するならば",
                                        "施設の『拡張』を覚えておきなさい",
                                        "高度な機能の解放や効果を向上させられます",
                                        "",
                                        "まず貴方がすべきことは",
                                        "要らない荷物の処分でしょうか",
                                        "",
                                        "『商店』で売却するか『倉庫』で預けるのです",
                                        "",
                                        "『祭壇』で儀式を行い、捧げたマナを用いれば",
                                        "迷宮探索に役立つ力を得られます",
                                        "",
                                        "『探索』で再び迷宮に挑む事が出来ます",
                                        "強敵を倒す事で、更なる道が示されます",
                                        "",
                                        "あなたの活躍に期待していますよ",
                                        ""]
            case 2:
                window.message_text = ["くくくくくくくく・・・・・",
                                       "おろかなニンゲンの傀儡が手に入ったわ",
                                        "",
                                        "容易く欲に染まる愚かな種よ",
                                        "我が神へ捧げる星の力を掘り起こすがいい",
                                        "",
                                        "キサマ等はそのために生み出された",
                                        "神の僕、いや道具に過ぎないのだから",
                                        "ふはははははははははははは",
                                        "",
                                        "憎きは星の守り人を気取るやつらよ",
                                        "汚らわしい追われし者の分際で",
                                        "",
                                        "だがまあよい",
                                        "力の散る地上では何もできまいに",
                                        "",
                                        "穴倉の底で指を咥えて眺めているがよい"]
                for _ in range(4):
                    px.flip()
                return True
        return False