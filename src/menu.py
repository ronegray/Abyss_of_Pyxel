import pyxel as px
from pathlib import Path
from datetime import datetime
import const as G_
import common_func as comf
import command, item, skill


class Window:
    def __init__(self, x:int, y:int, width:int, height:int, window_type:int=0, close_timer:int=300):
        self.x = x if x + width <= px.width else px.width - width
        self.y = y
        self.width = width
        self.height= height
        self.window_type = window_type #0:待機メッセージ 1:一時メッセージ
        self.close_timer = close_timer
        self.close_counter = 0
        self.message_text = []

    def update(self):
        btn = comf.get_button_state()
        match self.window_type:
            case 0:
                if btn["a"]:
                    px.play(3,G_.SNDEFX["pi"], resume=True)
                    return False
                if btn["b"]:
                    return False
            case 1:
                if self.close_counter >= self.close_timer:
                    self.close_counter = 0
                    return False
                elif self.close_counter >= self.close_timer//2:
                    if btn["a"] or btn["b"]:
                        px.play(3,G_.SNDEFX["pi"], resume=True)
                        self.close_counter = 0
                        return False
                else:
                    self.close_counter += 1
        return True

    def draw(self):
        chip_cnt_w = self.width  // G_.CHIP_PIXEL 
        chip_cnt_h = self.height // G_.CHIP_PIXEL

        #枠線
        for Ypos in range(chip_cnt_h):
            for Xpos in range(chip_cnt_w):
                #四隅
                if Ypos == 0 and Xpos == 0:
                    px.blt(self.x, self.y, G_.IMGIDX["CHIP"],
                            0, 240, G_.CHIP_PIXEL,G_.CHIP_PIXEL, colkey=0) #左上
                elif Ypos == 0 and Xpos == chip_cnt_w-1:
                    px.blt(self.x + self.width - G_.CHIP_PIXEL, self.y, G_.IMGIDX["CHIP"],
                            8, 240, G_.CHIP_PIXEL,G_.CHIP_PIXEL, colkey=0) #右上
                elif Ypos == chip_cnt_h-1 and Xpos == 0:
                    px.blt(self.x, self.y + self.height - G_.CHIP_PIXEL, G_.IMGIDX["CHIP"],
                            0, 248, G_.CHIP_PIXEL,G_.CHIP_PIXEL, colkey=0) #左下
                elif Ypos == chip_cnt_h-1 and Xpos == chip_cnt_w-1:
                    px.blt(self.x + self.width - G_.CHIP_PIXEL, self.y + self.height - G_.CHIP_PIXEL,
                           G_.IMGIDX["CHIP"], 8, 248,  G_.CHIP_PIXEL,G_.CHIP_PIXEL, colkey=0) #右下
                #枠線
                elif Ypos == 0: #上端
                    px.blt(self.x + (Xpos*G_.CHIP_PIXEL), self.y, G_.IMGIDX["CHIP"],
                           16, 248, G_.CHIP_PIXEL,G_.CHIP_PIXEL, colkey=0)
                elif Xpos == 0: #左端
                    px.blt(self.x, self.y + (Ypos*G_.CHIP_PIXEL), G_.IMGIDX["CHIP"],
                           16, 240, G_.CHIP_PIXEL,G_.CHIP_PIXEL, colkey=0)
                elif Ypos == chip_cnt_h-1: #下端
                    px.blt(self.x + (Xpos*G_.CHIP_PIXEL), self.y + self.height - G_.CHIP_PIXEL, G_.IMGIDX["CHIP"],
                           24, 248, G_.CHIP_PIXEL,G_.CHIP_PIXEL, colkey=0 )
                elif Xpos == chip_cnt_w-1: #右端
                    px.blt(self.x + self.width - G_.CHIP_PIXEL, self.y + (Ypos*G_.CHIP_PIXEL), G_.IMGIDX["CHIP"],
                           24, 240, G_.CHIP_PIXEL,G_.CHIP_PIXEL, colkey=0 )
                #塗りつぶし
                else:
                    pass
                    px.blt(self.x + (Xpos*G_.CHIP_PIXEL), self.y + (Ypos*G_.CHIP_PIXEL), G_.IMGIDX["CHIP"],
                           32, 240, G_.CHIP_PIXEL,G_.CHIP_PIXEL )

        if self.close_counter >= self.close_timer//2:
            if px.frame_count//8%2 == 0:
                px.blt(self.x+self.width//2-4,
                    self.y+self.height-5, G_.IMGIDX["CHIP"],
                    35,248, 5,8, colkey=0, rotate=90)

    # @classmethod
    def drawText(self, x:int, y:int, text_list:list):
        for i, text in enumerate(text_list):
            px.text(x, y + (i*16+2), text, px.COLOR_WHITE, font=G_.JP_FONT)
        return

    def drawTextColor(self, x:int, y:int, text_list:list):
        for i, data in enumerate(text_list):
            px.text(x, y + (i*16+2), data[0], data[1], font=G_.JP_FONT)
        return

    def add_message(self, message_text):
        self.message_text.append(message_text)
        while len(self.message_text) > 3:
            self.message_text.pop(0)

    def draw_message(self):
        for i, text in enumerate(self.message_text):
            px.text(self.x+8, self.y+8 + (i*16+2), text, px.COLOR_WHITE, font=G_.JP_FONT)
        return
    

class Menu:
    rofs    = 4 #文字出力 行間(pixel)
    fw,fh   = 12, 13 #フォント幅高
    rowpad  = 2 #オブジェクト上下間調整
    _padding_left = 2

    def __init__(self, x:int, y:int, menulist_shape:list, menu_items:list,
                 menutext_length:int=6, menu_type:int=0, parent=None, user=None):
        self.user = user
        self.parent = parent
        self.menu_items = menu_items     #メニュー項目文字列
        self.menu_shape = menulist_shape    #メニュー項目個数　横,縦
        self.menutext_length = menutext_length      #メニュー項目文字長
        self.menu_type = menu_type       #メニュー種別 
        self.cursor_position = [0,0]     #メニューカーソル選択位置
        self.cursor_address = [0,0]     #メニューカーソル描画アドレス
        self.selectitem_text = ""        #選択メニューの文字列
        _window_width = ((1+1+1) + (1+1+self.menutext_length*2)*self.menu_shape[0])*G_.CHIP_PIXEL
        _window_height = ((1+1)+ (self.menu_shape[1]*2))*G_.CHIP_PIXEL 
        if (x + _window_width) > px.width:
            x = px.width - _window_width
        self.menu_window = Window(x, y, _window_width, _window_height, 2)
        self.submenu_instance = ""
        self.is_submenu = False
        self.msg_window = ""
        self.is_msg_window = False
        self.answerYN = 0 #MenuYesNoからのリターン
        self.command_instance = None
        self.is_command = False
        self.message_text = ""
        self.is_close_me = False

    def chkCmdRtn(self):
        flgTmp = self.command_instance.update()
        if flgTmp is not None:
            if isinstance(self.command_instance, command.CommandBuy):
                return False
            elif isinstance(self.command_instance, command.CommandIdentify):
                return False
            else:
                self.is_command = False
                if isinstance(self.parent, Menu):
                    self.parent.is_close_me = True
                return False
        return True

    def update(self):
        if self.is_close_me:
            if isinstance(self.parent, Menu):
                self.parent.is_close_me = True
            return False

        if self.is_command:
            return self.chkCmdRtn()
       
        #サブメニュー表示中
        if self.is_submenu:
            self.is_submenu = self.submenu_instance.update()
            return True
        if self.is_msg_window:
            self.is_msg_window = self.msg_window.update()
            return True
        btn = comf.get_button_state()
        #キャンセル
        if btn["b"]:
            return False
        #決定
        if btn["a"]:
            px.play(3,G_.SNDEFX["pi"], resume=True)

            self.selectitem_text = self.menu_items[self.cursor_position[1] % self.menu_shape[1]] [self.cursor_position[0] % self.menu_shape[0]]
            _subwindow_x, _subwindow_y = self.cursor_address[0], self.cursor_address[1] + G_.CHIP_PIXEL + 4
            match self.menu_type:
                #フィールドメニュー
                case 0:
                    match self.cursor_position:
                        case [0,0]: #パラメータ
                            self.command_instance = command.CommandStatus(_subwindow_x, _subwindow_y, self.user)
                            self.is_command = True
                        case [0,1]: #インベントリ
                            self.submenu_instance = MenuInventory(self, self.user)
                            self.is_submenu = True
                        case [0,2]: #エスケープ
                            if self.user.is_safeescape:
                                msg = ["安全に拠点へ帰還します","[低確率でインベントリのアイテムを遺失]"]
                            else:
                                msg = ["迷宮から逃げ出します","[逃走中に高確率でインベントリのアイテムを遺失]"]
                            self.command_instance = command.CommandEscape(self.parent.di)
                            self.submenu_instance = MenuYesNo(_subwindow_x, _subwindow_y, msg, self.command_instance, self)
                            self.is_submenu = True
                        case [0,3]: #ロード
                            self.command_instance = command.CommandLoad(0,0,self.parent, 0)
                            self.submenu_instance = MenuYesNo(_subwindow_x, _subwindow_y,
                                                            ["探索前のデータからやり直しますか？"],
                                                            self.command_instance, self)
                            self.is_submenu = True
                    return True
                #キャラ選択メニュー
                case 1:
                    return self.menuCharaSelect()
                #商店メニュー
                case 2:
                    return self.menuShop()
                #タイトルメニュー
                case 3:
                    return self.menuTitle()
                #名前入力メニュー
                case 4:
                    return self.menuNameEntry()
                #装備アイテム選択メニュー
                case 5:
                    return self.menuSelectItem()
                #データセーブメニュー
                case 6:
                    return self.menuSave()
                #データロードメニュー
                case 7:
                    return self.menuLoad()
                case G_.MenuType.INVENTORY:
                    return self.menuInventory()
                case G_.MenuType.INVENTORYSUB:
                    return self.menuInventorySub()
                case G_.MenuType.BASEMAIN:
                    return self.menuBaseMain()
                case G_.MenuType.BASESTORAGE:
                    return self.menuBaseStorage()
                case G_.MenuType.STORESTORAGE:
                    return self.menuStoreStorage()
                case G_.MenuType.GETSTORAGE:
                    return self.menuGetStorage()
                case G_.MenuType.BASEALCHEMY:
                    return self.menuBaseAlchemy()
                case G_.MenuType.IDENTIFY:
                    return self.menuIdentify()
                case G_.MenuType.BASERITUAL:
                    return self.menuBaseRitual()
                case G_.MenuType.GETPERK:
                    return self.menuGetPower()
                case G_.MenuType.EQUIPSKILL:
                    return self.menuEquipSkill()
                case G_.MenuType.BASESHOP:
                    return self.menuBaseShop()
                case G_.MenuType.SHOPSELL:
                    return self.menuShopSell()
                case G_.MenuType.SHOPSELLALL:
                    return self.menuShopSellAll()
                case G_.MenuType.BASEBACKDOOR:
                    return self.menuBaseBackdoor()
                case G_.MenuType.BASEDISCOVER:
                    return self.menuBaseDiscover()
                case G_.MenuType.BASEUPGRADE:
                    return self.menuBaseUpgrade()
                case _:
                    raise SystemError

            return True
        
        self.moveCursor()

        return True

    def moveCursor(self):
        if px.btnp(px.KEY_W,0,G_.GAME_FPS//5) or px.btnp(px.GAMEPAD1_BUTTON_DPAD_UP,0,G_.GAME_FPS//5) or px.btnp(px.KEY_UP,0,G_.GAME_FPS//5):
            self.cursor_position[1] = (self.cursor_position[1]-1)%self.menu_shape[1]
        if px.btnp(px.KEY_A,0,G_.GAME_FPS//5) or px.btnp(px.GAMEPAD1_BUTTON_DPAD_LEFT,0,G_.GAME_FPS//5) or px.btnp(px.KEY_LEFT,0,G_.GAME_FPS//5):
            self.cursor_position[0] = (self.cursor_position[0]-1)%self.menu_shape[0]
        if px.btnp(px.KEY_S,0,G_.GAME_FPS//5) or px.btnp(px.GAMEPAD1_BUTTON_DPAD_DOWN,0,G_.GAME_FPS//5) or px.btnp(px.KEY_DOWN,0,G_.GAME_FPS//5):
            self.cursor_position[1] = (self.cursor_position[1]+1)%self.menu_shape[1]
        if px.btnp(px.KEY_D,0,G_.GAME_FPS//5) or px.btnp(px.GAMEPAD1_BUTTON_DPAD_RIGHT,0,G_.GAME_FPS//5) or px.btnp(px.KEY_RIGHT,0,G_.GAME_FPS//5):
            self.cursor_position[0] = (self.cursor_position[0]+1)%self.menu_shape[0]

    def draw(self):
        self.drawMenu()

        if self.is_command:
            self.command_instance.draw(self.cursor_address)

        if self.is_submenu:
            self.submenu_instance.draw()

        if self.is_msg_window:
            self.msg_window.draw()
            self.msg_window.drawText(self.cursor_address[0]+8,self.cursor_address[1]+16,
                                     self.message_text)

    def drawMenu(self):
        #メニューウインドウ枠表示
        self.menu_window.draw()
        #メニュー項目文字表示
        for row in range(self.menu_shape[1]):
            for col in range(self.menu_shape[0]):
                for i,_str in enumerate(self.menu_items[row][col]):

                    px.text(self.menu_window.x+(1+((1+1)*col+(self.menutext_length*2)*col)+(1+1+i*2))*G_.CHIP_PIXEL,
                            self.menu_window.y+(1 + row*2)*G_.CHIP_PIXEL,
                            _str, px.COLOR_WHITE, G_.JP_FONT)

        #メニューカーソル表示
        #初期状態
        self.cursor_address = [self.menu_window.x + 
                               #メニュー枠+余白+(カーソル位置(項目n番目)ｘ項目長x2)*チップサイズ(8)
                               (1+(((1)*(self.cursor_position[0]+1)+self.cursor_position[0]+(self.menutext_length*2)*self.cursor_position[0])))
                               *G_.CHIP_PIXEL - 2,
                               self.menu_window.y +
                               (1+(1+(self.cursor_position[1]*2)))*G_.CHIP_PIXEL - 5]
        px.blt(*self.cursor_address, G_.IMGIDX["CHIP"], 32,248, G_.CHIP_PIXEL,G_.CHIP_PIXEL, colkey=0)


class MenuYesNo(Menu):
    def __init__(self, x, y, msg:list, command_instance, parent):
        super().__init__(x + 2*G_.CHIP_PIXEL, y + (len(msg)*2+1)*G_.CHIP_PIXEL , [1,2],  [["はい"],["いいえ"]], 4, 3)
        self.address = [x,y]
        _textlength = 0
        for texts in msg:
            _textlength = max(len(texts),_textlength)
        _msg_window_width = (_textlength*2+2)*G_.CHIP_PIXEL
        if x + _msg_window_width > px.width:
            x = px.width - _msg_window_width
        self.message_window  = Window(x, y, _msg_window_width, (len(msg)*2+2)*G_.CHIP_PIXEL, 0)
        self.message = msg
        self.command_instance     = command_instance
        self.parent = parent

    def update(self):
        if self.is_command:
            return self.chkCmdRtn()
        btn = comf.get_button_state()
        if btn["a"]:
            px.play(3,G_.SNDEFX["pi"], resume=True)
            match self.cursor_position[1] % self.menu_shape[1]:
                case 0:
                    self.command_instance.exec()
                    self.is_command = True
                case 1:
                    return False
            return True
        if btn["b"]:
            if self.is_command:
                return True
            else:
                return False

        self.moveCursor()
        return True

    def draw(self):
        if self.is_command:
            self.command_instance.draw()
        else:
            self.message_window.draw()
            self.message_window.drawText(self.address[0]+8,self.address[1]+8, self.message)
            self.drawMenu()


class MenuNameEntry(Menu):
    def __init__(self):
        self.name_chars = comf.read_json("assets/data/letter.json")
        super().__init__(px.width//2-(376//2), 16, [11,9],  self.name_chars[0], 1 , 4)
        self.prefix     = "名前　：　"
        self.input_name_string  = ""
        self.name_window  = Window(px.width//2 - (G_.CHIP_PIXEL*(8+5)*2)//2,
                                      px.height//1.5, G_.CHIP_PIXEL*(8+5)*2, G_.CHIP_PIXEL*5, 0)
        self.name_string = [self.prefix + self.input_name_string]
        self.msg_window2 = None
        self.is_msg_window2 = False
        self.msg2_string = []
        self.keep_corsor = [0,0]
        self.is_need_redraw = True

    def update(self):
        if self.is_msg_window2:
            self.is_msg_window2 = self.msg_window2.update()
            return True
        btn = comf.get_button_state()
        if btn["a"]:
            self.is_need_redraw = True
            px.play(3,G_.SNDEFX["pi"], resume=True)
            self.selMnu = self.menu_items[self.cursor_position[1]][self.cursor_position[0]]
            match self.selMnu:
                case "ED":
                    if len(self.input_name_string) <= 0:
                        if isinstance(self.msg_window2, Window):
                            del self.msg_window2
                        self.msg_window2 = Window(32,px.height//2-16,
                                                    px.width-64,((1+1+(1*2))*G_.CHIP_PIXEL), 1,90)
                        self.is_msg_window2 = True
                        self.msg2_string = ["名前が入力されていません"]
                        return True
                    else:
                        return False
                case "片":
                    self.menu_items = self.name_chars[1]
                    return True
                case "英":
                    self.menu_items = self.name_chars[2]
                    return True
                case "平":
                    self.menu_items = self.name_chars[0]
                    return True
            tmpStr = self.input_name_string + self.selMnu
            if len(tmpStr) > 8:
                self.msg_window2 = Window(32,px.height//2-16,
                                            px.width-64,((1+1+(1*2))*G_.CHIP_PIXEL), 1, 90)
                self.is_msg_window2 = True
                self.msg2_string = ["名前の文字数は８文字が上限です"]
                px.play(3, G_.SNDEFX["don"], resume=True)
                return True
            else:
                self.input_name_string += self.selMnu
        if btn["b"]:
            tmpStr = self.input_name_string[:-1]
            self.input_name_string = tmpStr
            return True
        if btn["S"]:
            self.cursor_position = [self.menu_shape[0]-1,self.menu_shape[1]-1]
        self.name_string = [self.prefix + self.input_name_string]
        self.moveCursor()

        return True

    def draw(self):
        self.drawMenu() #文字一覧はここで
        self.name_window.draw() #入力名はここ
        self.name_window.drawText(self.name_window.x+8,
                                    self.name_window.y+12, self.name_string)
        px.text(px.width//2-(7*10),px.height-14,"キャンセルボタンで一文字削除　StartボタンでEDへカーソル移動",
                px.COLOR_GRAY,G_.SMALLFONT)
        if self.is_msg_window2:
            self.msg_window2.draw() #エラーメッセージ用
            self.msg_window2.drawText(self.msg_window2.x+40, self.msg_window2.y+8, self.msg2_string)
        self.is_need_redraw = False


class MenuSelectCharacter(Menu):
    def __init__(self, func_init_user):
        self.func_init_user = func_init_user
        self.item_list = []
        self.itemlist_index = 0
        self.count_push_left = 0
        self.count_push_right = 0
        self.spritedir = [0,1,2,3,6,7,4,5]
        #タイプ、タイプ名、説明、スプライトアドレス(縦位置)
        self.item_list = [[0,[G_.CharaType.NAME[G_.CharaType.POWER]],
                           ["筋力が高く物理戦闘が得意だが、反面知性や運が低い",
                            "そのためクリティカルやスキル威力は期待薄",
                            "高い頑健により属性攻撃の減衰率にも秀でている",
                            "",
                            "初期装備の斧は遅いが高威力・広範囲の攻撃",
                            "中装と合わせて力で押し切る戦士系タイプ",
                            "",
                            "初期装備：斧、中装、中盾",],2,
                            [" 初期ＨＰ：１３５　　初期ＭＰ：５",
                             " 筋力　　：４０　　　器用　　：２０　　　敏捷　：２０",
                             " 知性　　：１０　　　頑健　　：３５　　　幸運　：１５"],"中"],
                          [1,[G_.CharaType.NAME[G_.CharaType.SKILL]],
                           ["知性と幸運が極端に高く、他は軒並み最低レベル",
                            "スキル威力やＭＰの量・回復速度は高い",
                            "高い幸運による迷宮探索時の恩恵は計り知れない",
                            "",
                            "初期装備の杖は魔力を高める唯一の武器種",
                            "スキルを駆使して戦うテクニカルなタイプ",
                            "",
                            "初期装備：杖、衣服、腕輪",],0,
                            [" 初期ＨＰ：１１０　　初期ＭＰ：２５",
                             " 筋力　　：１０　　　器用　　：１５　　　敏捷　：１５",
                             " 知性　　：５０　　　頑健　　：１０　　　幸運　：４０"],"高"],
                          [2,[G_.CharaType.NAME[G_.CharaType.SPEED]],
                           ["器用と敏捷が高めだが明確に得意と言える分野もない",
                            "回避能力とクリティカル率の成長には期待できるか",
                            "器用な分赤宝箱を開けるスピードは速い",
                            "",
                            "初期装備の槍は随一の攻撃距離を誇る",
                            "軽装でのヒット＆アウェイに向いたタイプ",
                            "",
                            "初期装備：槍、軽装、小盾",],1,
                            [" 初期ＨＰ：１２０　　初期ＭＰ：１０",
                             " 筋力　　：２０　　　器用　　：３０　　　敏捷　：３０",
                             " 知性　　：２０　　　頑健　　：２０　　　幸運　：２０"],"低"],
        ]
        super().__init__(0,0, [1,13], self.item_list[self.itemlist_index], 20, 2)#, user=user)
        self.menu_window.x = px.width//2 - self.menu_window.width//2
        self.menu_window.y = 24
        self.message_window = Window(self.menu_window.x, self.menu_window.y+self.menu_window.height,
                                     self.menu_window.width, (1+3*2+1)*G_.CHIP_PIXEL, 0)

    def remap_item(self):
        self.menu_items = self.item_list[self.itemlist_index]

    def moveCursor(self):
        if px.btnp(px.KEY_A) or px.btnp(px.GAMEPAD1_BUTTON_DPAD_LEFT) or px.btnp(px.KEY_LEFT):
            self.itemlist_index = (self.itemlist_index-1)%3
            self.remap_item()
            self.count_push_left = 1
        if px.btnp(px.KEY_D) or px.btnp(px.GAMEPAD1_BUTTON_DPAD_RIGHT) or px.btnp(px.KEY_RIGHT):
            self.itemlist_index = (self.itemlist_index+1)%3
            self.remap_item()
            self.count_push_right = 1

    def menuCharaSelect(self):
        self.command_instance = command.CommandCharaSelect(self.message_window.x, self.message_window.y,
                                                           self.itemlist_index, self.func_init_user)
        self.submenu_instance = MenuYesNo(self.menu_window.x+16, self.menu_window.height//2 + G_.CHIP_PIXEL*3,
                                          [f"{self.menu_items[1][0]}　で　よろしいですか？"], self.command_instance,
                                          self)
        self.is_submenu = True
        return True

    def update(self):
        #サブメニュー表示中
        if self.is_submenu:
            self.is_submenu = self.submenu_instance.update()
            if self.submenu_instance.is_command:
                return False
            return True
        btn = comf.get_button_state()
        #キャンセル
        if btn["b"]:
            px.play(3,G_.SNDEFX["miss"], resume=True)
            return True
        #決定
        if btn["a"]:
            px.play(3,G_.SNDEFX["pi"], resume=True)

            self.menuCharaSelect()
            self.is_submenu = True

            return True
        
        self.moveCursor()

        return True

    def draw(self):
        self.drawMenu()
        #左右キーで別リスト展開
        px.blt(self.menu_window.x-(4+16),self.menu_window.y+self.menu_window.height//2,
               G_.IMGIDX["CHIP"], 200,240,-16,16,0)
        px.blt(self.menu_window.x+self.menu_window.width+4,self.menu_window.y+self.menu_window.height//2,
               G_.IMGIDX["CHIP"], 200,240,16,16,0)
        #左右キー押下時はカーソルを一瞬巨大化
        if self.count_push_left:
            px.blt(self.menu_window.x-24,self.menu_window.y+self.menu_window.height//2,
                   G_.IMGIDX["CHIP"], 200,240,-16,16,px.COLOR_BLACK, scale=2.0)
            self.count_push_left = (self.count_push_left+1)%3
        if self.count_push_right:
            px.blt(self.menu_window.x+self.menu_window.width+9,
                   self.menu_window.y+self.menu_window.height//2,G_.IMGIDX["CHIP"],
                   200,240,16,16,px.COLOR_BLACK, scale=2.0)
            self.count_push_right = (self.count_push_right+1)%3
 
        if self.is_submenu:
            self.submenu_instance.draw()

    def drawMenu(self):
        px.cls(0)
        #メニューウインドウ枠表示
        self.menu_window.draw()
        #メニュー項目表示
        header = [str(self.menu_items[1][0])]
        self.menu_window.drawText(self.menu_window.x
                                  +self.menu_window.width//2
                                  -G_.JP_FONT.text_width(str(header))//2
                                  +6,
                                  self.menu_window.y+4, header)

        px.blt(self.menu_window.x+self.menu_window.width//2-8, self.menu_window.y+48,
               G_.IMGIDX["CHAR"],
               self.spritedir[px.frame_count//32%8]*16, self.menu_items[3]*16,16,16,
               colkey=px.COLOR_BLACK,scale=4.0)
        self.menu_window.drawText(self.menu_window.x+8, self.menu_window.y+90,
                                  self.menu_items[2])
        self.message_window.draw()
        self.message_window.drawText(self.message_window.x+8,self.message_window.y+8,self.menu_items[4])


class MenuSavedata(Menu):
    def __init__(self, x, y, app, menu_type):
        slotname = [["データ１"],["データ２"],["データ３"],["データ４"],]
        for i in range(4):
            path = Path(px.user_data_dir("moq",G_.APP_NAME)+f"savedata{i}.bin")
            if path.exists() is False:
                filedate = "0000/00/00 00:00:00"
            else:
                filedate = f"{datetime.fromtimestamp(path.stat().st_mtime):%Y/%m/%d %H:%M:%S}"
            slotname[i][0] = f"{slotname[i][0]}　{filedate}"

        super().__init__(x, y, [1,4], slotname, 11, menu_type)
        self.app = app
        self.dataslot = 0

    def select_dataslot(self):
        self.dataslot = self.cursor_position[1] % self.menu_shape[1]

    def drawMenu(self):
        #メニューウインドウ枠表示
        self.menu_window.draw()
        #メニュー項目文字表示
        for row in range(self.menu_shape[1]):
            px.text(self.menu_window.x + 3 * G_.CHIP_PIXEL,
                    self.menu_window.y+(1 + row*2)*G_.CHIP_PIXEL,
                    self.menu_items[row][0], px.COLOR_WHITE, G_.JP_FONT)
        #メニューカーソル表示
        #初期状態
        self.cursor_address = [self.menu_window.x + 
                               #メニュー枠+余白+(カーソル位置(項目n番目)ｘ項目長x2)*チップサイズ(8)
                               (1+(((1)*(self.cursor_position[0]+1)+self.cursor_position[0]+(self.menutext_length*2)*self.cursor_position[0])))
                               *G_.CHIP_PIXEL - 2,
                               self.menu_window.y +
                               (1+(1+(self.cursor_position[1]*2)))*G_.CHIP_PIXEL - 5]
        px.blt(*self.cursor_address, G_.IMGIDX["CHIP"], 32,248, G_.CHIP_PIXEL,G_.CHIP_PIXEL, colkey=0)


class MenuLoad(Menu):
    def __init__(self, x, y, app):
        super().__init__(x, y, app, 7)

    def menuLoad(self):
        self.dataslot = 0
        self.command_instance = command.CommandLoad(0,0,self.app, self.dataslot)
        self.submenu_instance = MenuYesNo(self.cursor_address[0],
                                          self.cursor_address[1] + G_.CHIP_PIXEL + 2,
                                          ["データをロードしますか？"], self.command_instance, self)
        self.is_submenu = True
        return True


class MenuTitle(Menu):
    def __init__(self, now_scene, app):
        x,y = 0,0
        menushape = [1,2]
        menuitem = [["ニューゲーム"],["データをロード"]]
        menulen = 8
        super().__init__(x,y, menushape, menuitem, menulen, 0)
        self.menu_window.x,self.menu_window.y = (px.width-self.menu_window.width)//2,(px.height-self.menu_window.height)-16
        self.app = app
        self.now_scene = now_scene
        self.is_newgame = False
        self.cnt = 1
        self.logocnt = 0
        self.is_finished = False
        self.is_keydisp = False
        self.image_keydisp = px.Image.from_image("assets/image/keydisp.bmp")
        self.image_logo = px.Image.from_image("assets/image/AoP_logo.bmp")

    def update(self):
        if self.is_newgame:
            return
        
        if self.is_finished:
            if self.command_instance.update() is not None:
                self.command_instance = None
                self.is_command = self.is_finished = False
                return False

        if self.is_finished is False and self.is_command:
            self.command_instance.exec()
            self.is_finished = True
            if self.command_instance.is_nofile:
                return False
            else:
                return True
        
        if self.is_finished == False:
            btn = comf.get_button_state()
            if btn["a"]:
                if self.is_keydisp:
                    self.is_keydisp = False
                    return False
                px.play(3,G_.SNDEFX["pi"], resume=True)
                cursor_pos = self.cursor_position[1] % self.menu_shape[1]
                if cursor_pos == 0:
                    self.is_finished = self.is_newgame = True
                    self.app.is_clear_user = False
                    return True
                else:
                    match cursor_pos:
                        case 0:
                            self.is_finished = self.is_newgame = True
                            self.app.is_clear_user = True
                        case _:
                            self.command_instance = command.CommandLoad(0,0, self.app, cursor_pos-1)
                            self.is_command = True
                return True
            if btn["b"]:
                self.is_keydisp = False
                return False
            if btn["S"]:
                self.is_keydisp = True
                return False
            if px.btnp(px.KEY_A,15,15) or px.btnp(px.GAMEPAD1_BUTTON_DPAD_LEFT,15,15) or px.btnp(px.KEY_LEFT,15,15):
                if self.app.volume >0:
                    self.app.volume -= 1
                    for ch in px.channels:
                        ch.gain /= 2 
            if px.btnp(px.KEY_D,15,15) or px.btnp(px.GAMEPAD1_BUTTON_DPAD_RIGHT,15,15) or px.btnp(px.KEY_RIGHT,15,15):
                if self.app.volume <7:
                    self.app.volume += 1
                    for ch in px.channels:
                        ch.gain *= 2
        self.moveCursor()

        return None

    def draw(self):
        if self.is_keydisp:
            px.blt((px.width-self.image_keydisp.width)//2,(px.height-self.image_keydisp.height)//2,
                   self.image_keydisp, 0,0,self.image_keydisp.width,self.image_keydisp.height,
                    colkey=0, scale=2)
            px.text(166,32,"※Xinputキー表示(SwithではABとXYが逆)",px.COLOR_WHITE,G_.JP_FONT)
            px.text(160,72,"十字パッド：移動",px.COLOR_WHITE,G_.JP_FONT)
            px.text(160,108+32*1,"Ａ：決定・攻撃",px.COLOR_WHITE,G_.JP_FONT)
            px.text(160,108+32*2,"Ｂ：キャンセル・メニュー表示",px.COLOR_WHITE,G_.JP_FONT)
            px.text(160,108+32*3,"Ｘ：回避",px.COLOR_WHITE,G_.JP_FONT)
            px.text(160,108+32*4,"Ｙ：鶴嘴を使用",px.COLOR_WHITE,G_.JP_FONT)
            px.text(160,108+32*5,"Ｌ：押しながらＡＢＸＹで設定スキル発動",px.COLOR_WHITE,G_.JP_FONT)
            return
            
        if self.is_newgame:
            if self.cnt > 0:
                px.dither(self.cnt)
                self.cnt -= 0.01
            else:
               self.app.is_menu = False
               px.dither(1)

        px.cls(0)
        px.blt((px.width-self.image_data.width)//2,8, self.image_data, 0, 0, self.image_data.width, self.image_data.height)

        px.dither(self.logocnt)
        px.blt((px.width-self.image_logo.width)//2,px.height*0.1, self.image_logo,
               0, 0, self.image_logo.width, self.image_logo.height, colkey=9)
        px.dither(1)
        self.logocnt = min(0.9,self.logocnt+0.003)

        self.drawMenu()

        appver = f"ver.{G_.APP_VERSION}"
        px.text(px.width-(len(appver)*px.FONT_WIDTH)-1, px.height-8, appver, px.COLOR_GRAY)
        px.text(2, px.height-13, f"F1/Startキーで操作表示／左右キーで音量調節(0<<<7):{self.app.volume}", px.COLOR_GRAY, G_.SMALLFONT)

        if self.is_command:
            self.command_instance.draw()
            if self.command_instance.is_nofile:
                self.is_newgame = False
                self.cnt = 1


class MenuInventory(Menu):
    def __init__(self, parent, user):
        x, y = 11,11
        self.user = user
        self.item_list = []
        self.itemlist_index = 0
        # --- 追加: 絞り込み機能用初期化 ---
        self.filter_cursor = 0 # 現在の絞り込みインデックス
        self.filter_types = G_.INVENTORY_FILTER_TYPES # 絞り込み対象リスト
        # ------------------------------
        self.messege_window = Window(G_.WND_MAIN[0], G_.WND_MAIN[3]//2-(1+2+1)*G_.CHIP_PIXEL,
                                     G_.WND_MAIN[2], (1+2+1)*G_.CHIP_PIXEL, 0)
        self.is_push_left = 0
        self.is_push_right = 0

        self.list_rows = 8
        menutext_length = 9
        self.generate_item_list()
        super().__init__(x, y, [1,len(self.item_list[self.itemlist_index])],
                         self.item_list[self.itemlist_index], menutext_length,
                         G_.MenuType.INVENTORY, user=user)
        self.info_window = Window(x+self.menu_window.width+8, parent.menu_window.y, 128,256, 0)
        self.equip_window = Window(self.info_window.x+self.info_window.width,
                                   self.info_window.y, 128,256, 0)
        self.desc_window = Window(self.info_window.x,self.info_window.y+self.info_window.height,
                                  248,40, 0)
        self.change_target_item()
        self.userstate_window = Window(*G_.WND_USTA)
        # --- 追加: 絞り込み状態表示用ウィンドウ ---
        # アイテムリストの下に配置。高さは文字高さ+余白で24px程度確保
        self.filter_window = Window(self.menu_window.x,
                                    self.menu_window.y + self.menu_window.height-4,
                                    self.menu_window.width, 24, 0)

    # --- 追加: 共通フィルタリング処理 ---
    def _get_filtered_list(self, raw_list):
        """渡されたリストを現在のfilter_cursorに基づいてフィルタリングして返す"""
        target_type = self.filter_types[self.filter_cursor]
        
        if target_type is None:
            return raw_list
        
        # タプル(uuid, obj)の形式を想定してフィルタリング
        return [item_ for item_ in raw_list if item_[1].type_id == target_type]
    # ----------------------------------

    def generate_item_list(self):
        tmplist = item.ItemManager.get_item_by_state(G_.ItemStatus.BUGGAGE)
        # --- 追加: フィルタリング適用 ---
        tmplist = self._get_filtered_list(tmplist)
        # ----------------------------

        self.inventory_count = len(tmplist)
        if self.inventory_count <= 0:
            # self.item_list = [["何も　持っていない"]]
            # 絞り込み結果が0件の場合は表示を変える
            if self.filter_cursor == 0:
                self.item_list = [["何も　持っていない"]]
            else:
                self.item_list = [["該当なし"]] # フィルタリングで何もない場合
        else:
            self.item_list = [tmplist[i:i+self.list_rows]
                               for i in range(0, self.inventory_count, self.list_rows)]

        # ページインデックスが範囲外にならないよう補正
        if self.itemlist_index >= len(self.item_list):
            self.itemlist_index = len(self.item_list) - 1
        self.menu_shape = [1,len(self.item_list[self.itemlist_index])]

    def update(self):
# 1. 割り込み状態（サブメニュー、メッセージ、終了処理中）なら親クラスに任せて終わる
        #    これにより、サブメニュー操作中に勝手に裏で絞り込みが変わるのを防ぎます
        if self.is_submenu or self.is_msg_window or self.is_close_me or self.is_command:
            return super().update()

        # 2. L/Rキーの独自処理
        is_change_filter = False
        
        if px.btnp(px.KEY_L) or px.btnp(px.GAMEPAD1_BUTTON_LEFTSHOULDER):
            px.play(3, G_.SNDEFX["pi"], resume=True)
            self.filter_cursor = (self.filter_cursor - 1) % len(self.filter_types)
            is_change_filter = True

        if px.btnp(px.KEY_R) or px.btnp(px.GAMEPAD1_BUTTON_RIGHTSHOULDER):
            px.play(3, G_.SNDEFX["pi"], resume=True)
            self.filter_cursor = (self.filter_cursor + 1) % len(self.filter_types)
            is_change_filter = True

        if is_change_filter:
            self.generate_item_list() # リスト再生成
            self.remap_itemlist()     # 画面表示更新
            self.change_target_item() # カーソル位置の情報更新
            return True               # 処理を行ったのでここで終了

        # 3. それ以外（カーソル移動、Aボタン決定、Bボタンキャンセル）は親クラスの標準機能を使う
        #    これで大量のコードコピーを回避できます
        return super().update()

    def moveCursor(self):
        if px.btnp(px.KEY_W,20,10) or px.btnp(px.GAMEPAD1_BUTTON_DPAD_UP,20,10) or px.btnp(px.KEY_UP,20,10):
            self.cursor_position[1] = (self.cursor_position[1]-1)%self.menu_shape[1]
        if px.btnp(px.KEY_S,20,10) or px.btnp(px.GAMEPAD1_BUTTON_DPAD_DOWN,20,10) or px.btnp(px.KEY_DOWN,20,10):
            self.cursor_position[1] = (self.cursor_position[1]+1)%self.menu_shape[1]
        if len(self.item_list) > 1:
            if px.btnp(px.KEY_A) or px.btnp(px.GAMEPAD1_BUTTON_DPAD_LEFT) or px.btnp(px.KEY_LEFT):
                self.itemlist_index = (self.itemlist_index-1)%len(self.item_list)
                self.remap_itemlist()
                self.is_push_left = 1
            if px.btnp(px.KEY_D) or px.btnp(px.GAMEPAD1_BUTTON_DPAD_RIGHT) or px.btnp(px.KEY_RIGHT):
                self.itemlist_index = (self.itemlist_index+1)%len(self.item_list)
                self.remap_itemlist()
                self.is_push_right = 1

        self.change_target_item()

    def change_target_item(self):
        self.target_item = self.item_list[self.itemlist_index][self.cursor_position[1]]

    def remap_itemlist(self):
        self.menu_items = self.item_list[self.itemlist_index]
        self.menu_shape[1] = len(self.menu_items)
        self.cursor_position = [0,0]

    def menuInventory(self):
        self.userstate_window.update()
        if self.selectitem_text not in ("何","該"):
            self.submenu_instance = MenuInventorySub(self.cursor_address[0],
                                                     self.cursor_address[1] + G_.CHIP_PIXEL + 2,
                                                     self, self.user)
            self.is_submenu = True
        else:
            px.play(3,G_.SNDEFX["miss"],resume=True)
        return True

    def draw_filter(self):
        # 絞り込み状態ウィンドウの描画
        self.filter_window.draw()

        # 1. 絞り込み状態ウィンドウの描画
        self.filter_window.draw()
        
        # --- 状態リストのインデックス計算 ---
        prev_idx = (self.filter_cursor - 1) % len(self.filter_types)
        next_idx = (self.filter_cursor + 1) % len(self.filter_types)
        
        def get_type_name(idx):
            t = self.filter_types[idx]
            typename = "全て" if t is None else G_.ITEM_TYPE_NAME[t]
            padding = 3-len(typename)
            typename = " "*padding+typename+" "*padding 
            # return "全て" if t is None else G_.ITEM_TYPE_NAME[t]
            return typename

        prev_name = get_type_name(prev_idx)
        curr_name = "< "+get_type_name(self.filter_cursor)+" >"
        next_name = get_type_name(next_idx)

        # --- 各種座標計算 ---
        # 中央座標
        center_x = self.filter_window.x + self.filter_window.width // 2
        center_y = self.filter_window.y + 6
        
        # テキスト幅（中央の現在の状態を基準にする）
        curr_w = G_.JP_FONT.text_width(curr_name)
        
        # 2. テキスト描画
        # 現在の状態（中央・白）
        px.text(center_x - curr_w // 2, center_y, curr_name, px.COLOR_WHITE, G_.JP_FONT)
        
        # Lボタン
        icon_l_x = self.filter_window.x + 4
        icon_y = self.filter_window.y + 8
        px.blt(icon_l_x, icon_y, G_.IMGIDX["CHIP"],
               *G_.ImageAddress.BUTTON["L"], px.COLOR_BLACK)
        # 前の状態（グレー）
        px.text(icon_l_x+16+4, center_y+1, prev_name, px.COLOR_GRAY, G_.SMALLFONT)

        # Rボタン
        icon_r_x = self.filter_window.x + self.filter_window.width - 4 - 16
        px.blt(icon_r_x, icon_y, G_.IMGIDX["CHIP"],
               *G_.ImageAddress.BUTTON["R"], px.COLOR_BLACK)
        # 後の状態（グレー）
        px.text(icon_r_x-(G_.JP_FONT.text_width(next_name))-4, center_y+1, next_name, px.COLOR_GRAY, G_.SMALLFONT)

    def draw(self):
        #メニュー本体描画
        self.drawMenu()
        # 絞り込み状態ウィンドウの描画
        self.draw_filter()

        def draw_info_user(self):
            self.userstate_window.draw()
            self.userstate_window.message_text = [f"最大HP：{self.user.maxhp: >9,}",
                                                f"攻撃力：{self.user.attack: >9,}",
                                                f"防御力：{self.user.defend: >9,}",
                                                f"魔力　：{self.user.arcane: >9,}"]
            self.userstate_window.draw_message()
            if self.is_submenu:
                self.submenu_instance.draw()

        if self.inventory_count == 0:
            # (ステータス描画などは必要に応じて実行)
            draw_info_user(self)
            return

        #カーソルアイテム詳細描画
        self.drawInfo(self.info_window, self.target_item)
        item_category = G_.ItemType.get_category(self.target_item[1].type_id)
        if item_category in (G_.ItemType.CATEGORY_WEAPON,
                             G_.ItemType.CATEGORY_ARMOR,
                             G_.ItemType.CATEGORY_SHIELD):
            self.drawInfo(self.equip_window,
                        [self.user.equip_id[item_category-1],
                        item.ItemManager.get_item(self.user.equip_id[item_category-1])],
                        True)

        #カーソルアイテム説明表示
        self.desc_window.draw()
        if self.target_item[1].is_identified:
            if self.target_item[1].type_id == G_.ItemType.RUNE:
                idx_desc = G_.JsonRune.DESC
            else:
                idx_desc = G_.JsonItem.DESC
            px.text(self.desc_window.x+8,self.desc_window.y+8,
                    f"{str(item.ItemManager.get_item_info(self.target_item[1].id)[idx_desc]).replace("\n","")}",
                    px.COLOR_WHITE, G_.SMALLFONT)
        else:
            px.text(self.desc_window.x+8,self.desc_window.y+8,
                    "未鑑定の"+self.target_item[1].name,
                    px.COLOR_WHITE, G_.SMALLFONT)

        #装備品は左右キーで別リスト展開
        scale_right = scale_left = 1
        if self.is_push_left:
            scale_left = 2
            self.is_push_left = (self.is_push_left+1)%(self.menu_shape[0]+1)
        if self.is_push_right:
            scale_right = 2
            self.is_push_right = (self.is_push_right+1)%(self.menu_shape[0]+1)
        px.blt(self.menu_window.x-8,
               self.menu_window.y+self.menu_window.height//2-8,
               G_.IMGIDX["CHIP"], *G_.ImageAddress.BIGARROW[:2],-16,16,
               colkey=px.COLOR_BLACK, scale=scale_left)
        px.blt(self.menu_window.x+self.menu_window.width-8,
               self.menu_window.y+self.menu_window.height//2-8,
               G_.IMGIDX["CHIP"], *G_.ImageAddress.BIGARROW,
               colkey=px.COLOR_BLACK, scale=scale_right)

        draw_info_user(self)
    
    def drawInfo(self, target_window, target_item, is_equip=False):
        target_window.draw()
        if is_equip:
            px.text(target_window.x+8,target_window.y+8,
                    f"＜装備中アイテム＞",
                    px.COLOR_WHITE, G_.SMALLFONT)
        px.text(target_window.x+8,target_window.y+8+(16*3),
                f"種別　　：{G_.ITEM_TYPE_NAME[target_item[1].type_id]}",
                px.COLOR_WHITE, G_.SMALLFONT)

        if target_item[1].is_identified:
            px.text(target_window.x+8,target_window.y+8+(16*4),
                    f"基本価格：{target_item[1].price:>7,}",
                    px.COLOR_WHITE, G_.SMALLFONT)
            px.text(target_window.x+5,target_window.y+8+(16*1), target_item[1].name,
                    G_.ItemRank.COLOR[target_item[1].rank], G_.SMALLFONT)
            px.text(target_window.x+8,target_window.y+8+(16*2),
                    f"[ {G_.ItemRank.NAME[target_item[1].rank]} ]",
                    G_.ItemRank.COLOR[target_item[1].rank], G_.SMALLFONT)
            if target_item[1].type_id != G_.ItemType.RUNE:
                px.text(target_window.x+8,target_window.y+8+(16*5),
                        f"基礎性能：{target_item[1].value:>7,}",
                        px.COLOR_WHITE, G_.SMALLFONT)
                if G_.ItemType.get_category(target_item[1].type_id) == G_.ItemType.CATEGORY_WEAPON:
                    px.text(target_window.x+8,target_window.y+8+(16*6),
                            f"熟練度　：{target_item[1].mastery:>6,.2f}%",
                            px.COLOR_WHITE, G_.SMALLFONT)
                if target_item[1].rune_slot is not None:
                    px.text(target_window.x+8,target_window.y+8+(16*7),
                            f"固定能力：{target_item[1].rune_slot.ability.basename}",
                            G_.ItemRank.COLOR[target_item[1].rune_slot.ability.rank], G_.SMALLFONT)
                    desc = item.ItemManager.get_item_info(target_item[1].rune_slot.ability.id)[G_.JsonRune.DESC]
                    px.text(target_window.x+12,target_window.y+8+(16*8)-4, f"{desc}",
                            G_.ItemRank.COLOR[target_item[1].rune_slot.ability.rank], G_.SMALLFONT)

                    px.text(target_window.x+8,target_window.y+8+(16*10),
                            f"追加能力：",px.COLOR_WHITE, G_.SMALLFONT)
                    
                    slot_list=[]
                    slot_names = {"low":"低級", "mid":"中級", "hi":"高級"}
                    h = 0
                    for stype in ["low", "mid", "hi"]:
                        max_s = target_item[1].rune_slot.max_slots[stype]
                        current_runes = target_item[1].rune_slot.runes[stype]
                        for i in range(max_s):
                            rune_uuid = current_runes[i] if i < len(current_runes) else None
                            if rune_uuid:
                                rune_obj = item.ItemManager.get_item(rune_uuid)
                                rune_color = G_.ItemRank.COLOR[rune_obj.rank]
                                disp = f"［{slot_names[stype]}］{rune_obj.basename}"
                            else:
                                disp = f"［{slot_names[stype]}］未設定"
                                rune_color = px.COLOR_WHITE
                            px.text(target_window.x+8,target_window.y+8+(16*(11+h)),
                                    disp, rune_color, G_.SMALLFONT)
                            h+=1
        else:
            px.text(target_window.x+5,target_window.y+8, target_item[1].name,
                    px.COLOR_GRAY, G_.SMALLFONT)
            px.text(target_window.x+8,target_window.y+8+(16*1),
                    "<未鑑定>",
                    px.COLOR_GRAY, G_.SMALLFONT)
            Estimated = "産廃レベル" if target_item[1].price<1000 else (
                        "安っぽい" if target_item[1].price<10000 else (
                        "よく見かける" if target_item[1].price<100000 else (
                        "見た目高そう" if target_item[1].price<1000000 else (
                        "超高級品"))))
            px.text(target_window.x+8,target_window.y+8+(16*4),
                    f"概算価値：{Estimated}",
                    px.COLOR_GRAY, G_.SMALLFONT)

    def drawMenu(self):
        #メニューウインドウ枠表示
        self.menu_window.draw()
        px.rect(self.menu_window.x+self.menu_window.width-8-(4*3)-3,self.menu_window.y,
                (4*3)+3,8,px.COLOR_NAVY)
        px.text(self.menu_window.x+self.menu_window.width-8-(4*3)-1,self.menu_window.y,
                f"{self.itemlist_index+1}/{len(self.item_list)}",px.COLOR_WHITE)

        #メニュー項目文字表示
        for row in range(self.menu_shape[1]):
            if self.inventory_count == 0:
                px.text(self.menu_window.x+(1+1+1)*G_.CHIP_PIXEL,
                        self.menu_window.y+(1 + row*2)*G_.CHIP_PIXEL, self.menu_items[row],
                        px.COLOR_WHITE, G_.JP_FONT)
            else:
                _padding = " "*(19-(len(self.menu_items[row][1].name)*2))
                _str = f"{self.menu_items[row][1].name}"

                color = G_.ItemRank.COLOR[self.menu_items[row][1].rank] if self.menu_items[row][1].is_identified else px.COLOR_GRAY
                px.text(self.menu_window.x+(1+1+1)*G_.CHIP_PIXEL,
                        self.menu_window.y+(1 + row*2)*G_.CHIP_PIXEL, _str,
                        color, G_.JP_FONT)
        #メニューカーソル表示
        self.cursor_address = [self.menu_window.x + 
                               #メニュー枠+余白+(カーソル位置(項目n番目)ｘ項目長x2)*チップサイズ(8)
                               (1+(((1)*(self.cursor_position[0]+1)+self.cursor_position[0]+(self.menutext_length*2)*self.cursor_position[0])))
                               *G_.CHIP_PIXEL - 2,
                               self.menu_window.y +
                               (1+(1+(self.cursor_position[1]*2)))*G_.CHIP_PIXEL - 5]
        px.blt(*self.cursor_address, G_.IMGIDX["CHIP"], 32,248, G_.CHIP_PIXEL,G_.CHIP_PIXEL, colkey=0)


class MenuInventorySub(Menu):
    def __init__(self, x, y, parent, user):
        super().__init__(x, y, [1,2], [["装備"],["捨てる"]], 6, G_.MenuType.INVENTORYSUB,
                         parent, user)
    
    def menuInventorySub(self):
        match self.cursor_position[1]%len(self.menu_items):
            #装備
            case 0:
                submenu_x = self.cursor_address[0]
                submenu_y = self.cursor_address[1] + G_.CHIP_PIXEL + 2
                if self.parent.target_item[1].is_identified is False:
                    self.msg_window = Window(submenu_x, submenu_y,
                                             G_.WND_MAIN[2]-(16*2),G_.CHIP_PIXEL*2*2)
                    self.message_text = ["未鑑定アイテムは装備できない"]
                    self.is_msg_window = True
                    return True
                #対象アイテムの装備カテゴリを取得
                item_category = G_.ItemType.get_category(self.parent.target_item[1].type_id)
                if item_category not in (G_.ItemType.CATEGORY_WEAPON,
                                     G_.ItemType.CATEGORY_ARMOR,
                                     G_.ItemType.CATEGORY_SHIELD):
                    self.msg_window = Window(submenu_x, submenu_y,
                                            G_.WND_MAIN[2]-(16*2),G_.CHIP_PIXEL*2*2)
                    self.message_text = ["このアイテムは装備できない"]
                    self.is_msg_window = True
                    return True

                # --- [1] 現在装備中のアイテムを外す処理 ---
                now_equip = item.ItemManager.get_item(self.user.equip_id[item_category-1])
                item.ItemManager.update_state(self.user.equip_id[item_category-1], G_.ItemStatus.BUGGAGE)
                
                if now_equip and now_equip.rune_slot:
                    # 1-A. 固有アビリティ(Ability)の減算
                    # 辞書からリスト形式 [key, val] を取り出して渡す
                    ability_effects = [[key, rune] for key, rune in item.ItemManager.get_rune_by_id(now_equip.rune_slot.ability.id).items()]
                    if ability_effects:
                        self.user.remove_rune_effect(ability_effects[0])

                    # 1-B. 装着済みルーン(Socket Items)の減算
                    for slot_type in ["low", "mid", "hi"]:
                        for rune_uuid in now_equip.rune_slot.runes[slot_type]:
                            rune_obj = item.ItemManager.get_item(rune_uuid)
                            if rune_obj:
                                rune_effects = [[key, rune] for key, rune in item.ItemManager.get_rune_by_id(rune_obj.id).items()]
                                if rune_effects:
                                    self.user.remove_rune_effect(rune_effects[0])

                # --- [2] 新しいアイテムを装備する処理 ---
                item.ItemManager.update_state(self.parent.target_item[0], G_.ItemStatus.EQUIP)
                target_obj = self.parent.target_item[1]

                if target_obj and target_obj.rune_slot:
                    # 2-A. 固有アビリティ(Ability)の加算
                    ability_effects = [[key, rune] for key, rune in item.ItemManager.get_rune_by_id(target_obj.rune_slot.ability.id).items()]
                    if ability_effects:
                        self.user.set_rune_effect(ability_effects[0])

                    # 2-B. 装着済みルーン(Socket Items)の加算
                    for slot_type in ["low", "mid", "hi"]:
                        for rune_uuid in target_obj.rune_slot.runes[slot_type]:
                            rune_obj = item.ItemManager.get_item(rune_uuid)
                            if rune_obj:
                                rune_effects = [[key, rune] for key, rune in item.ItemManager.get_rune_by_id(rune_obj.id).items()]
                                if rune_effects:
                                    self.user.set_rune_effect(rune_effects[0])
                self.user.equip_item(self.parent.target_item[0])

            #捨てる
            case 1:
                item.ItemManager.update_state(self.parent.target_item[0], G_.ItemStatus.DROP)
                item.ItemManager.get_item(self.parent.target_item[0]).address = {
                    "x":self.user.address[0]+
                    G_.CHARA_DIR[self.user.direction][0]*16+
                    G_.CHARA_DIR[self.user.direction][0]*px.rndi(1,8),
                    "y":self.user.address[1]+
                    G_.CHARA_DIR[self.user.direction][1]*16+
                    G_.CHARA_DIR[self.user.direction][1]*px.rndi(1,8)
                }
                if self.parent.cursor_position[1] == 0:
                    if len(self.parent.item_list[self.parent.itemlist_index]) == 1:
                        if self.parent.itemlist_index == 0:
                                self.parent.is_close_me = True
                                return
                        else:
                            self.parent.itemlist_index -= 1 
                            self.parent.cursor_position[1] = self.parent.list_rows-1
                else:
                    self.parent.cursor_position[1] -= 1
            case _:
                return
        self.parent.generate_item_list()
        self.parent.menu_items = self.parent.item_list[self.parent.itemlist_index]
        if len(self.parent.menu_items) <= self.parent.cursor_position[1]:
            self.parent.cursor_position[1] = len(self.parent.menu_items)-1
        self.parent.change_target_item()


class MenuBaseMain(Menu):
    def __init__(self, di, x, y, menulist_shape, menu_items, menutext_length = 6, parent=None):
        self.di = di # Dependency Injection
        super().__init__(x, y, menulist_shape, menu_items, menutext_length, G_.MenuType.BASEMAIN, parent, self.di.user)

    def menuBaseMain(self):
        self.di.base.is_notice = False
        submenu_x, submenu_y = self.cursor_address[0], self.cursor_address[1] + G_.CHIP_PIXEL + 2
        match self.selectitem_text:
            case "inventory"|"荷物":
                self.submenu_instance = MenuInventory(self, self.di.user)
                self.is_submenu = True
            case "storage"|"倉庫":
                self.submenu_instance = MenuBaseStorage(self.di, submenu_x-10,16)
                self.is_submenu = True
            case "alchemy"|"錬金":
                self.submenu_instance = MenuBaseAlchemy(self.di, submenu_x,submenu_y)
                self.is_submenu = True
            case "ritual"|"儀式":
                self.submenu_instance = MenuBaseRitual(self.di, submenu_x,submenu_y)
                self.is_submenu = True
            case "shop"|"売買":
                self.submenu_instance = MenuBaseShop(self.di, submenu_x,submenu_y)
                self.is_submenu = True
            case "backdoor"|"近道":
                self.submenu_instance = MenuBaseBackdoor(self.di, submenu_x,submenu_y)
                self.is_submenu = True
            case "discover"|"探索":
                self.submenu_instance = MenuBaseDiscover(self.di, submenu_x,submenu_y)
                self.is_submenu = True
            case "upgrade"|"拡張":
                self.submenu_instance = MenuBaseUpgrade(self.di, submenu_x,submenu_y)
                self.is_submenu = True
            case "quit"|"終了":
                self.command_instance = command.CommandSave(0,0, self.di.app, 0, True)
                self.command_instance.exec()
                px.quit()
            case _:
                pass

    def moveCursor(self):
        super().moveCursor()  
        match self.menu_items[self.cursor_position[1]][0]:
            case "inventory"|"荷物":
                self.di.base.information_window.message_text=["荷物：　手荷物の確認、装備や廃棄"]
                self.di.base.is_notice = True
            case "storage"|"倉庫":
                self.di.base.information_window.message_text=[f"倉庫(Lv{self.di.base.base_level["storage"]})：　倉庫にアイテムを保管する、または取り出す"]
                self.di.base.is_notice = True
            case "alchemy"|"錬金":
                self.di.base.information_window.message_text=[f"錬金工房(Lv{self.di.base.base_level["alchemy"]})：　錬金術でアイテムを鑑定できる","秘密の紋章が刻まれた石でアイテムに特殊な力を付与できる","秘紋石の抽出には錬金工房のレベルが関わってくる"]
                self.di.base.is_notice = True
            case "ritual"|"儀式":
                self.di.base.information_window.message_text=[f"儀式祭壇(Lv{self.di.base.base_level["ritual"]})：　祭壇で儀式を行い、マナと引き換えに様々な力を得る","得た力は永続的に効果を発揮する","スキルはボタンに割り当てないと使えない"]
                self.di.base.is_notice = True
            case "shop"|"売買":
                self.di.base.information_window.message_text=[f"商品売買(Lv{self.di.base.base_level["shop"]})：　ランダムに入荷されるアイテムの購入","またはアイテムの売却が出来る"]
                self.di.base.is_notice = True
            case "backdoor"|"近道":
                self.di.base.information_window.message_text=[f"迷宮近道(Lv{self.di.base.base_level["backdoor"]})：　到達済階層に向かう近道の整備","開発が進む程、到達済階層の近くまで行ける"]
                self.di.base.is_notice = True
            case "discover"|"探索":
                self.di.base.information_window.message_text=[f"迷宮探索(Lv{self.di.base.base_level["discover"]})：　ダンジョン探索に向かう","倒したボスの部屋へ転移可能（次の階層から開始）"]
                self.di.base.is_notice = True
            case "upgrade"|"拡張":
                self.di.base.information_window.message_text=["拠点拡張：　拠点の機能を整備・拡張する","実施の為には条件があり、","実際の整備・拡張にはジェムその他が必要になる"]
                self.di.base.is_notice = True
            case "quit"|"終了":
                self.di.base.information_window.message_text=["ゲーム終了：　現在のデータを保存してゲームを終了する"]
                self.di.base.is_notice = True
            case _:
                pass


class MenuBaseStorage(Menu):
    def __init__(self, di, x, y, parent=None, user=None):
        self.di = di
        menulist_shape = [1,2]
        menu_items = [["保管する"],["取り出す"],["装備する"]]
        menutext_length = 4
        menu_type = G_.MenuType.BASESTORAGE
        super().__init__(x, y, menulist_shape, menu_items, menutext_length, menu_type,
                         di.base.base_mainmenu, di.user)

    def menuBaseStorage(self):
        match self.cursor_position[1]:
            case 0:
                self.submenu_instance = MenuStoreStorage(self.di)
                self.is_submenu = True
            case 1:
                self.submenu_instance = MenuGetStorage(self.di)
                self.is_submenu = True
        return True


class MenuStoreStorage(MenuInventory):
    def __init__(self, di):
        self.di = di
        x,y = self.di.base.base_mainmenu.menu_window.x,self.di.base.base_mainmenu.menu_window.y
        basemenu = self.di.base.base_mainmenu
        user = self.di.user
        super().__init__(basemenu, user)
        self.menu_type = G_.MenuType.STORESTORAGE

    def menuStoreStorage(self):
        if self.selectitem_text not in ("何","該"):
            if len(self.di.base.storage) >= self.di.base.storage_max:
                self.di.base.information_window.add_message("倉庫がいっぱいだ")
                self.di.base.is_notice = True
                return
            #指定装備カテゴリの現在装備中アイテムのステータスを所持中に変更
            item.ItemManager.update_state(self.target_item[0], G_.ItemStatus.STORAGE)
            if self.cursor_position[1] == 0:
                if len(self.item_list[self.itemlist_index]) == 1:
                    if self.itemlist_index == 0:
                            self.is_close_me = True
                            return
                    else:
                        self.itemlist_index -= 1 
                        self.cursor_position[1] = 7
            else:
                self.cursor_position[1] -= 1
                px.play(3,G_.SNDEFX["miss"],resume=True)
            self.generate_item_list()
            self.menu_items = self.item_list[self.itemlist_index]
            self.change_target_item()

        self.command_instance = command.CommandSave(0,0, self.di.app, 0)
        self.command_instance.exec()
        return True


class MenuGetStorage(MenuInventory):
    def __init__(self, di):
        self.di = di
        x,y = self.di.base.base_mainmenu.menu_window.x,self.di.base.base_mainmenu.menu_window.y
        basemenu = self.di.base.base_mainmenu
        user = self.di.user
        super().__init__(basemenu, user)
        self.menu_type = G_.MenuType.GETSTORAGE

    def generate_item_list(self):
        list_rows = 8
        tmplist = item.ItemManager.get_item_by_state(G_.ItemStatus.STORAGE)
        tmplist = self._get_filtered_list(tmplist)
        self.inventory_count = len(tmplist)
        if self.inventory_count <= 0:
            # 絞り込み結果が0件の場合は表示を変える
            if self.filter_cursor == 0:
                self.item_list = [["何も　持っていない"]]
            else:
                self.item_list = [["該当なし"]] # フィルタリングで何もない場合
        else:
            self.item_list = [tmplist[i:i+list_rows]
                               for i in range(0, self.inventory_count, list_rows)]

        # ページインデックスの補正
        if self.itemlist_index >= len(self.item_list):
            self.itemlist_index = max(0, len(self.item_list) - 1)
        self.menu_shape = [1,len(self.item_list[self.itemlist_index])]

    def menuGetStorage(self):
        if len(self.di.user.inventory) >= self.di.user.inventory_max:
            self.di.base.information_window.add_message("これ以上　持てない")
            self.di.base.is_notice = True
            return
        if self.selectitem_text not in ("何","該"):
            #指定装備カテゴリの現在装備中アイテムのステータスを所持中に変更
            item.ItemManager.update_state(self.target_item[0], G_.ItemStatus.BUGGAGE)
            if self.cursor_position[1] == 0:
                if len(self.item_list[self.itemlist_index]) == 1:
                    if self.itemlist_index == 0:
                            self.is_close_me = True
                            return
                    else:
                        self.itemlist_index -= 1 
                        self.cursor_position[1] = 7
            else:
                px.play(3,G_.SNDEFX["miss"],resume=True)
                self.cursor_position[1] -= 1
            self.generate_item_list()
            self.menu_items = self.item_list[self.itemlist_index]
            self.change_target_item()
        self.command_instance = command.CommandSave(0,0, self.di.app, 0)
        self.command_instance.exec()
        return True


class MenuBaseAlchemy(Menu):
    def __init__(self, di, x, y):
        self.di = di # Dependency Injection
        self.func_level = self.di.base.base_level["alchemy"]
        menulist_shape = [1, min(3,self.func_level)]
        entrylevel = [["アイテムの鑑定"],["秘紋石の結合"],["秘紋石の抽出"]]
        menu_items = entrylevel[:self.func_level]
        menutext_length = 8
        menu_type = G_.MenuType.BASEALCHEMY
        super().__init__(x, y, menulist_shape, menu_items, menutext_length, menu_type)

    def menuBaseAlchemy(self):
        self.di.base.is_notice = False
        match self.cursor_position[1]:
            case 0:
                self.submenu_instance = MenuIdentify(self.di)
                self.is_submenu = True
            case 1: # 結合
                self.submenu_instance = MenuSelectSocketItem(self.di, is_extract=False)
                self.is_submenu = True
            case 2: # 抽出
                self.submenu_instance = MenuSelectSocketItem(self.di, is_extract=True)
                self.is_submenu = True
        return True


# 結合/抽出対象の装備品を選択するメニュー
class MenuSelectSocketItem(MenuInventory):
    def __init__(self, di, is_extract=False):
        self.di = di
        self.is_extract = is_extract
        basemenu = self.di.base.base_mainmenu
        user = self.di.user
        super().__init__(basemenu, user)
        self.menu_type = G_.MenuType.INVENTORY
        self.need_refresh = False

    def update(self):
        # コマンド実行中（セーブなど）のチェック
        if self.is_command:
            return self.chkCmdRtn()
       
        # サブメニュー（スロット選択）表示中
        if self.is_submenu:
            # サブメニューの更新処理
            self.is_submenu = self.submenu_instance.update()
            
            # サブメニューから戻ってきた場合
            if self.is_submenu is False:
                # ★修正: 抽出が行われた場合のみ再生成する
                if self.need_refresh:
                    # カーソル位置を記憶しておく
                    last_index = self.itemlist_index
                    
                    self.generate_item_list() # 内部で index=0 にリセットされる
                    
                    # カーソル位置を復元（リスト範囲外なら末尾に合わせる）
                    if last_index >= len(self.item_list):
                        self.itemlist_index = len(self.item_list) - 1
                    else:
                        self.itemlist_index = last_index
                    
                    self.remap_itemlist()
                    self.change_target_item()
                    
                    # フラグを戻す
                    self.need_refresh = False
            return True

        # 以下、通常の操作処理（Menuクラスのupdateを参考に記述）
        btn = comf.get_button_state()
        # キャンセル（Bボタン）
        if btn["b"]:
            return False
            
        # 決定（Aボタン）
        if btn["a"]:
            px.play(3, G_.SNDEFX["pi"], resume=True)
            # 決定時の処理（menuInventoryメソッド）を実行
            return self.menuInventory()
        
        # カーソル移動
        self.moveCursor()
        
        return True

    def generate_item_list(self):
        # 装備品かつスロット持ちを抽出
        # 対象: BUGGAGE(手荷物) + EQUIP(装備中)
        bag_items = item.ItemManager.get_item_by_state(G_.ItemStatus.BUGGAGE)
        equip_items = item.ItemManager.get_item_by_state(G_.ItemStatus.EQUIP)
        all_items = bag_items + equip_items
        
        target_item_list = []
        for item_ in all_items:
            obj = item_[1]
            if obj.is_identified and obj.rune_slot is not None:
                has_rune = any(len(obj.rune_slot.runes[k]) > 0 for k in ["low","mid","hi"])
                if self.is_extract:
                    if has_rune: target_item_list.append(item_)
                else:
                    # 結合モード：スロット枠自体は必ずあるため対象とする
                    target_item_list.append(item_)
        
        self.inventory_count = len(target_item_list)
        if self.inventory_count <= 0:
            self.item_list = [["対象アイテムがない"]]
        else:
            self.list_rows = 8
            self.item_list = [target_item_list[i:i+self.list_rows]
                               for i in range(0, self.inventory_count, self.list_rows)]
        
        self.itemlist_index = 0
        self.menu_shape = [1,len(self.item_list[self.itemlist_index])]

    def menuInventory(self): # オーバーライド
        if self.selectitem_text in ("何","該"):
            px.play(3,G_.SNDEFX["miss"],resume=True)
            return True
        if self.item_list == [["対象アイテムがない"]]:
            px.play(3,G_.SNDEFX["miss"],resume=True)
            return True

        if not self.target_item[1].is_identified:
            px.play(3,G_.SNDEFX["miss"],resume=True)
            self.di.base.information_window.message_text = ["未鑑定品は加工できない"]
            self.di.base.is_notice = True
            return True

        # スロット選択メニューへ
        self.submenu_instance = MenuSelectSocketSlot(self.di, self.target_item, self.is_extract, self)
        self.is_submenu = True
        return True

    def draw_filter(self):
        #ソケットアイテム選択では絞り込みしない
        return


# 装備品の特定スロットを選択するメニュー
class MenuSelectSocketSlot(Menu):
    def __init__(self, di, target_item_tuple, is_extract, parent_menu):
        self.di = di
        self.target_item_tuple = target_item_tuple # [uuid, obj]
        self.target_obj = target_item_tuple[1]
        self.is_extract = is_extract
        self.parent_menu = parent_menu
        
        self.slot_list = [] # [{"type":"low", "index":0, "rune":uuid/None, "disp":str}]
        self.create_slot_list()
        
        menu_items = [[slot["disp"]] for slot in self.slot_list]
        x = parent_menu.info_window.x+8
        y = parent_menu.info_window.y+8
        super().__init__(x, y, [1, len(menu_items)], menu_items, 12, 0)

    def create_slot_list(self):
        self.slot_list = []
        # Low, Mid, Hi の順で走査
        slot_names = {"low":"低級", "mid":"中級", "hi":"高級"}
        
        for stype in ["low", "mid", "hi"]:
            max_s = self.target_obj.rune_slot.max_slots[stype]
            current_runes = self.target_obj.rune_slot.runes[stype]
            
            for i in range(max_s):
                rune_uuid = current_runes[i] if i < len(current_runes) else None
                
                if self.is_extract:
                    if rune_uuid:
                        rune_obj = item.ItemManager.get_item(rune_uuid)
                        disp = f"[{slot_names[stype]}] {rune_obj.name}"
                        self.slot_list.append({"type":stype, "index":i, "rune":rune_uuid, "disp":disp})
                else: # Combine
                    if rune_uuid:
                        rune_obj = item.ItemManager.get_item(rune_uuid)
                        disp = f"［{slot_names[stype]}］{rune_obj.name}"
                        self.slot_list.append({"type":stype, "index":i, "rune":rune_uuid, "disp":disp})
                    else:
                        disp = f"［{slot_names[stype]}］空きスロット"
                        self.slot_list.append({"type":stype, "index":i, "rune":None, "disp":disp})

    def update(self):
        if self.is_command:
            return self.chkCmdRtn()
        if self.is_submenu:
            self.is_submenu = self.submenu_instance.update()
            # サブメニューから戻ったらリスト更新（結合/抽出後）
            if not self.is_submenu:
                self.create_slot_list()
                self.menu_items = [[slot["disp"]] for slot in self.slot_list]
                if not self.menu_items: self.menu_items = [["結合ルーンなし"]]
                self.menu_shape = [1, len(self.menu_items)]
                # カーソル位置補正
                if self.cursor_position[1] >= len(self.menu_items):
                    self.cursor_position[1] = len(self.menu_items) - 1
            return True

        btn = comf.get_button_state()
        if btn["b"]: return False
        if btn["a"]:
            if not self.slot_list: return True
            target_slot = self.slot_list[self.cursor_position[1]]
            
            if self.is_extract:
                if len(self.di.user.inventory) >= self.di.user.inventory_max:
                    px.play(3, G_.SNDEFX["miss"], resume=True)
                    self.di.base.information_window.message_text = ["鞄がいっぱいで抽出できない"]
                    self.di.base.is_notice = True
                    return True
                # 抽出処理へ
                self.do_extract(target_slot)
                self.parent_menu.need_refresh = True
            else:
                # 結合処理へ
                if target_slot["rune"] is not None:
                    px.play(3, G_.SNDEFX["miss"], resume=True)
                    # 既に埋まっている
                    return True
                self.do_combine(target_slot)
            return True
        
        self.moveCursor()
        return True

    def do_combine(self, target_slot):
        # 結合可能なルーンを選択するメニューを開く
        req_rank = self.target_obj.rune_slot.get_slot_req_rank(target_slot["type"])
        self.submenu_instance = MenuSelectRune(self.di, req_rank, self.target_item_tuple, target_slot)
        self.is_submenu = True

    def do_extract(self, target_slot):
        rune_obj = item.ItemManager.get_item(target_slot["rune"])
        # 成功率計算: 高ランクほど破損しやすい。錬金レベルで緩和
        # 破損率 = (Rank+1)*15 - (AlchemyLv * 5)
        # Rank0(Common)=15%※ただし該当なし, Rank5(Legend)=90%
        break_prob = rune_obj.rank * 15 - (self.di.base.base_level["alchemy"] * 5)
        break_prob = max(5, min(95, break_prob)) # 5%~95%に制限
        success_rate = 100 - break_prob

        msg = [f"{rune_obj.name}を抽出します", f"成功率: {success_rate}%"]
        
        self.command_instance = command.CommandExtractRune(self.di, self.target_item_tuple, target_slot, success_rate)
        self.submenu_instance = MenuYesNo(self.cursor_address[0],
                                          self.cursor_address[1]+G_.CHIP_PIXEL*2,
                                          msg, self.command_instance, self)
        self.is_submenu = True


# 結合用ルーン選択メニュー
class MenuSelectRune(MenuInventory):
    def __init__(self, di, req_rank, target_equip_tuple, target_slot_info):
        self.di = di
        self.req_rank = req_rank
        self.target_equip_tuple = target_equip_tuple
        self.target_slot_info = target_slot_info
        
        basemenu = self.di.base.base_mainmenu
        user = self.di.user
        # ウィンドウ位置調整
        super().__init__(basemenu, user)

    def generate_item_list(self):
        bag_items = item.ItemManager.get_item_by_state(G_.ItemStatus.BUGGAGE)
        store_items = item.ItemManager.get_item_by_state(G_.ItemStatus.STORAGE)
        all_items = bag_items + store_items
        #ルーン結合可能な対象タイプの選択
        match G_.ItemType.get_category(self.target_equip_tuple[1].type_id):
            case G_.ItemType.CATEGORY_WEAPON:
                apply = G_.RuneApply.WEAPON
            case G_.ItemType.CATEGORY_ARMOR:
                apply = G_.RuneApply.ARMOR
            case G_.ItemType.CATEGORY_SHIELD:
                apply = G_.RuneApply.SHIELD

        runes = []
        for item_ in all_items:
            if item_[1].type_id == G_.ItemType.RUNE and item_[1].is_identified:
                if (item_[1].category & apply) != 0:
                    if item_[1].rank <= self.req_rank:
                        runes.append(item_)

        self.inventory_count = len(runes)

        if not runes:
            self.item_list = [["条件に合う秘紋石がない"]]
        else:
            self.list_rows = 6
            self.item_list = [runes[i:i+self.list_rows] for i in range(0, len(runes), self.list_rows)]
        
        self.itemlist_index = 0
        self.menu_shape = [1, len(self.item_list[0])]

    def menuInventory(self):
        if self.selectitem_text in ("何","該"):
            px.play(3,G_.SNDEFX["miss"],resume=True)
            return True
        if self.item_list == [["条件に合う秘紋石がない"]]:
            px.play(3,G_.SNDEFX["miss"],resume=True)
            return True

        target_rune_tuple = self.target_item
        
        self.command_instance = command.CommandCombineRune(
            self.di, self.target_equip_tuple, self.target_slot_info, target_rune_tuple)
            
        self.submenu_instance = MenuYesNo(self.cursor_address[0], self.cursor_address[1]+G_.CHIP_PIXEL*2,
                                          [f"{target_rune_tuple[1].name}を", "結合しますか？"],
                                          self.command_instance, self)
        self.is_submenu = True
        return True


class MenuIdentify(MenuInventory):
    def __init__(self, di):
        self.di = di
        basemenu = self.di.base.base_mainmenu
        user = self.di.user
        super().__init__(basemenu, user)
        self.menu_type = G_.MenuType.IDENTIFY

    def generate_item_list(self):
        bug_items = item.ItemManager.get_item_by_state(G_.ItemStatus.BUGGAGE)
        store_items = item.ItemManager.get_item_by_state(G_.ItemStatus.STORAGE)
        tmplist = [[uuid_,obj] for uuid_,obj in bug_items+store_items if obj.is_identified is False]
        tmplist = self._get_filtered_list(tmplist)

        self.inventory_count = len(tmplist)
        if self.inventory_count <= 0:
            # 絞り込み結果が0件の場合は表示を変える
            if self.filter_cursor == 0:
                self.item_list = [["何も　持っていない"]]
            else:
                self.item_list = [["該当なし"]] # フィルタリングで何もない場合
        else:
            self.item_list = [tmplist[i:i+self.list_rows]
                               for i in range(0, self.inventory_count, self.list_rows)]
        # ページインデックスが範囲外にならないよう補正
        if self.itemlist_index >= len(self.item_list):
            self.itemlist_index = len(self.item_list) - 1
        self.menu_shape = [1,len(self.item_list[self.itemlist_index])]

    def menuIdentify(self):
        self.di.base.is_notice = False
        if self.selectitem_text not in ("何","該"):
            if self.target_item[1].is_identified:
                self.di.base.information_window.message_text = ["アイテムは既に鑑定済だ"]
                self.di.base.is_notice = True
        else:
            px.play(3,G_.SNDEFX["miss"],resume=True)
            return True

        if self.di.base.is_notice:
            return True
        cost = self.target_item[1].price // 4
        self.command_instance = command.CommandIdentify(self.di, self.target_item[1], cost)
        self.submenu_instance = MenuYesNo(self.cursor_address[0],
                                          self.cursor_address[1]+G_.CHIP_PIXEL+2,
                                          [f"ジェムが{cost:,}必要だ"], self.command_instance, self)
        self.is_submenu = True

        return True
    
    def drawInfo(self, target_window, target_item, is_equip=False):
        if is_equip:
            return
        super().drawInfo(target_window, target_item)

class MenuBaseRitual(Menu):
    def __init__(self, di, x, y):
        self.di = di # Dependency Injection
        self.func_level = self.di.base.base_level["ritual"]
        menulist_shape = [1, 3]
        menu_items = [["儀式を行う"],["マナ吸収率変更"],["スキルの設定"]]
        menutext_length = 8
        menu_type = G_.MenuType.BASERITUAL
        super().__init__(x, y, menulist_shape, menu_items, menutext_length, menu_type)

    def menuBaseRitual(self):
        subwindow_x, subwindow_y = self.cursor_address[0], self.cursor_address[1]+G_.CHIP_PIXEL+2
        match self.cursor_position[1]:
            case 0:
                self.submenu_instance = MenuGetPower(self.di, subwindow_x, subwindow_y, self)
                self.is_submenu = True
            case 1:
                self.submenu_instance = MenuSetManaDrainRate(self.di, subwindow_x, subwindow_y)
                self.is_submenu = True
            case 2:
                self.submenu_instance = MenuEquipSkill(self.di, subwindow_x, subwindow_y, self)
                self.is_submenu = True
        return True


class MenuGetPower(Menu):
    def __init__(self, di, x, y, parent):
        self.di = di
        self.parent_menu = parent
        self.user = parent.di.user
        self.item_list = []
        self.itemlist_index = 0
        self.rune_dict = {}
        self.messege_window = Window(G_.WND_MAIN[0], G_.WND_MAIN[3]//2-(1+2+1)*G_.CHIP_PIXEL,
                                     G_.WND_MAIN[2], (1+2+1)*G_.CHIP_PIXEL, 0)
        self.is_push_left = 0
        self.is_push_right = 0
        menutext_length = 6
        self.generate_item_list()
        super().__init__(x, y, [1,len(self.item_list[self.itemlist_index])],
                         self.item_list[self.itemlist_index], menutext_length,
                         G_.MenuType.GETPERK, user=self.user)
        self.info_window = Window(x+self.menu_window.width+16,
                                  y+self.cursor_address[1]+16, 11*16,48, 0)
        self.change_target_item()

    def generate_item_list(self):
        list_rows = 8
        self.rune_dict = {rune_id:rune for rune_id, rune
                   in item.ItemManager.get_rune_by_rank(self.parent_menu.func_level).items()
                   if (rune[G_.JsonRune.TYPE] & G_.RuneType.PERK) != 0
                    and rune_id not in self.user.perk_list}
        skill_dict = {skill_id:skill for skill_id, skill
                   in item.ItemManager.get_skill_by_rank(self.parent_menu.func_level).items()
                   if skill_id not in self.user.skill_list}
        self.rune_dict.update(skill_dict)
        self.rune_count = len(self.rune_dict)
        if self.rune_count <= 0:
            self.item_list = [["得られる力は無い"]]
        else:
            tmplist = list(self.rune_dict.items())
            self.item_list = [tmplist[i:i+list_rows]
                               for i in range(0, self.rune_count, list_rows)]
        self.itemlist_index = self.itemlist_index if self.itemlist_index < len(self.item_list) else len(self.item_list)-1
        self.menu_shape = [1,len(self.item_list[self.itemlist_index])]

    def moveCursor(self):
        if px.btnp(px.KEY_W,20,10) or px.btnp(px.GAMEPAD1_BUTTON_DPAD_UP,20,10) or px.btnp(px.KEY_UP,20,10):
            self.cursor_position[1] = (self.cursor_position[1]-1)%self.menu_shape[1]
        if px.btnp(px.KEY_S,20,10) or px.btnp(px.GAMEPAD1_BUTTON_DPAD_DOWN,20,10) or px.btnp(px.KEY_DOWN,20,10):
            self.cursor_position[1] = (self.cursor_position[1]+1)%self.menu_shape[1]
        if len(self.item_list) > 1:
            if px.btnp(px.KEY_A) or px.btnp(px.GAMEPAD1_BUTTON_DPAD_LEFT) or px.btnp(px.KEY_LEFT):
                self.itemlist_index = (self.itemlist_index-1)%(len(self.item_list))
                self.remap_itemlist()
                self.is_push_left = 1
            if px.btnp(px.KEY_D) or px.btnp(px.GAMEPAD1_BUTTON_DPAD_RIGHT) or px.btnp(px.KEY_RIGHT):
                self.itemlist_index = (self.itemlist_index+1)%(len(self.item_list))
                self.remap_itemlist()
                self.is_push_right = 1

        #メニューカーソル表示
        self.cursor_address = [self.menu_window.x + 
                               #メニュー枠+余白+(カーソル位置(項目n番目)ｘ項目長x2)*チップサイズ(8)
                               (1+(((1)*(self.cursor_position[0]+1)+self.cursor_position[0]+(self.menutext_length*2)*self.cursor_position[0])))
                               *G_.CHIP_PIXEL - 2,
                               self.menu_window.y +
                               (1+(1+(self.cursor_position[1]*2)))*G_.CHIP_PIXEL - 5]
        self.info_window.y = self.cursor_address[1]
        self.change_target_item()

    def change_target_item(self):
        self.target_item = self.item_list[self.itemlist_index][self.cursor_position[1]]
        self.di.base.is_notice = False

    def remap_itemlist(self):
        self.menu_items = self.item_list[self.itemlist_index]
        self.menu_shape[1] = len(self.menu_items)
        self.cursor_position = [0,0]

    def menuGetPower(self):
        if self.item_list == [["得られる力は無い"]]:
            px.play(3,G_.SNDEFX["miss"],resume=True)
            return
        if self.target_item[1][G_.JsonRune.RANK] == G_.ItemRank.COMMON:
            cost = 60
        else:
            basecost = 10
            hirate = 0.5 if self.target_item[1][G_.JsonRune.RANK] >= G_.ItemRank.LEGEND else 1
            cost = int(basecost**(self.target_item[1][G_.JsonRune.RANK]+1)*(7-self.target_item[1][G_.JsonRune.RANK])*0.9*hirate)
        if self.target_item[1][G_.JsonRune.TYPE_ID] == G_.ItemType.SKILL:
            cost //= 2
        self.command_instance = command.CommandGetPerk(self.di, self.target_item, cost)
        self.submenu_instance = MenuYesNo(self.cursor_address[0],
                                          self.cursor_address[1]+G_.CHIP_PIXEL+2,
                [f"祭壇のマナが{cost:,}必要だ"],
                self.command_instance, self)
        self.is_submenu = True

        return True

    def draw(self):
        #メニュー本体描画
        self.drawMenu()
        if self.rune_count == 0:
            return
        #カーソルアイテム詳細描画
        self.drawInfo(self.info_window, self.target_item)
        #装備品は左右キーで別リスト展開
        scale_right = scale_left = 1
        if self.is_push_left:
            scale_left = 2
            self.is_push_left = (self.is_push_left+1)%(self.menu_shape[0]+1)
        if self.is_push_right:
            scale_right = 2
            self.is_push_right = (self.is_push_right+1)%(self.menu_shape[0]+1)
        px.blt(self.menu_window.x-8,
               self.menu_window.y+self.menu_window.height//2-8,
               G_.IMGIDX["CHIP"], *G_.ImageAddress.BIGARROW[:2],-16,16,
               colkey=px.COLOR_BLACK, scale=scale_left)
        px.blt(self.menu_window.x+self.menu_window.width-8,
               self.menu_window.y+self.menu_window.height//2-8,
               G_.IMGIDX["CHIP"], *G_.ImageAddress.BIGARROW,
               colkey=px.COLOR_BLACK, scale=scale_right)

        if self.is_submenu:
            self.submenu_instance.draw()

    def drawInfo(self, target_window, target_item):
        target_window.draw()
        if target_item[1][G_.JsonRune.TYPE_ID] == G_.ItemType.SKILL:
            recastphysic = 4 if target_item[1][G_.JsonSkill.ELEMENT] == G_.ElementType.NONE else 1
            recast_time = (target_item[1][G_.JsonSkill.RANK]+1)/2 * recastphysic
            description = f"{target_item[1][G_.JsonRune.DESC]}\n消費MP:{target_item[1][G_.JsonSkill.COST]} 再使用待機:{recast_time}秒"
        else:
            description = f"永続能力：\n{str(target_item[1][G_.JsonRune.DESC]).replace("\n","")}"
        px.text(target_window.x+8,target_window.y+6, description,
                G_.ItemRank.COLOR[target_item[1][2]], G_.SMALLFONT)

    def drawMenu(self):
        #メニューウインドウ枠表示
        self.menu_window.draw()
        #メニュー項目文字表示
        for row in range(self.menu_shape[1]):
            if self.rune_count == 0:
                px.text(self.menu_window.x+(1+1+1)*G_.CHIP_PIXEL,
                        self.menu_window.y+(1 + row*2)*G_.CHIP_PIXEL, self.menu_items[row],
                        px.COLOR_WHITE, G_.JP_FONT)
            else:
                _padding = " "*(19-(len(self.menu_items[row][1][1])*2))
                _str = f"{self.menu_items[row][1][1]}"

                px.text(self.menu_window.x+(1+1+1)*G_.CHIP_PIXEL,
                        self.menu_window.y+(1 + row*2)*G_.CHIP_PIXEL, _str,
                        G_.ItemRank.COLOR[self.menu_items[row][1][2]], G_.JP_FONT)
        px.blt(*self.cursor_address, G_.IMGIDX["CHIP"], 32,248,
               G_.CHIP_PIXEL,G_.CHIP_PIXEL, colkey=0)


class MenuSetManaDrainRate(Menu):
    """
    1〜99の数字を入力するためのメニュークラス。
    左右キーで桁を選択し、上下キーで数字を増減させる。
    """
    def __init__(self, di, x: int, y: int):
        self.di = di
        dummy_items = [[" ", " "]]
        menu_type = G_.MenuType.MANADRAINRATE
        super().__init__(x, y, [2, 1], dummy_items, menutext_length=4, menu_type=menu_type)
        self.menu_window.height += 16
        
        # 状態管理
        self.result_value = max(1, min(99, self.di.user.mana_drain_rate)) # 1〜99に制限
        self.is_finished = False # 呼び出し元に返すためのフラグ

    def update(self):
        """
        入力処理（キーボード操作）を記述
        """
        if self.is_finished:
            # 決定キーが押されて終了フラグが立ったらFalseを返して親メニューに戻る
            return False 

        # 現在の桁位置（0:十の位, 1:一の位）
        current_digit_index = self.cursor_position[0] 
        
        # --- 1. 桁位置の決定 (左右キー) ---
        # MenuクラスのmoveCursorを使わず、必要な左右キーの処理だけを記述
        if px.btnp(px.KEY_A) or px.btnp(px.GAMEPAD1_BUTTON_DPAD_LEFT) or px.btnp(px.KEY_LEFT):
            # 左移動
            px.play(3, G_.SNDEFX["pi"], resume=True) # SE流用
            # 2桁間で循環
            self.cursor_position[0] = (self.cursor_position[0] - 1) % self.menu_shape[0]
        if px.btnp(px.KEY_D) or px.btnp(px.GAMEPAD1_BUTTON_DPAD_RIGHT) or px.btnp(px.KEY_RIGHT):
            # 右移動
            px.play(3, G_.SNDEFX["pi"], resume=True) # SE流用
            # 2桁間で循環
            self.cursor_position[0] = (self.cursor_position[0] + 1) % self.menu_shape[0]

        # --- 2. 数字の増減 (上下キー) ---
        delta = 0
        if px.btnp(px.KEY_W) or px.btnp(px.GAMEPAD1_BUTTON_DPAD_UP) or px.btnp(px.KEY_UP):
            delta = 1 # 上キーで増加
        elif px.btnp(px.KEY_S) or px.btnp(px.GAMEPAD1_BUTTON_DPAD_DOWN) or px.btnp(px.KEY_DOWN):
            delta = -1 # 下キーで減少

        if delta != 0:
            px.play(3, G_.SNDEFX["pi"], resume=True) # SE流用
            
            if current_digit_index == 1:
                new_value = self.result_value + delta
            else:
                # 現在の値を桁ごとに分解
                digits = [self.result_value // 10, self.result_value % 10]
                
                # 選択中の桁の値を更新
                new_digit_value = digits[current_digit_index] + delta
                
                # 桁ごとの循環 (0-9)
                if new_digit_value < 0:
                    new_digit_value = 9
                elif new_digit_value > 9:
                    new_digit_value = 0
                
                digits[current_digit_index] = new_digit_value
                
                # 新しい値を再構築
                new_value = digits[0] * 10 + digits[1]

            if new_value == 0:
                if delta == 1:
                    new_value = 1
                elif delta == -1:
                    if current_digit_index == 0:
                        new_value = 1
                    elif current_digit_index == 1:
                        new_value = 99
            elif new_value == 100:
                new_value = 1
  
            self.result_value = new_value

        # --- 3. 決定キー/キャンセルキー ---
        btn = comf.get_button_state()
        if btn["a"]: # 決定キー (Aボタン)
            px.play(3, G_.SNDEFX["pi"], resume=True)
            self.di.user.mana_drain_rate = self.result_value
            self.is_finished = True
            return False # 親メニューに戻る
        if btn["b"]: # キャンセルキー (Bボタン)
            px.play(3, G_.SNDEFX["po"], resume=True)
            self.result_value = None # キャンセルの場合は結果をNoneとする
            self.is_finished = True
            return False # 親メニューに戻る

        self.command_instance = command.CommandSave(0,0, self.di.app, 0)
        self.command_instance.exec()

        return True # 継続

    def drawMenu(self):
        """
        数字とカーソルを描画
        """
        # 1. メニューウインドウ枠表示 (Menuクラスの機能流用)
        self.menu_window.draw()

        # 2. 2桁の数字を描画 (ゼロ埋め)
        display_text = f"{self.result_value:02d}"
        start_x = self.menu_window.x + G_.CHIP_PIXEL * 3
        start_y = self.menu_window.y + G_.CHIP_PIXEL + 2
        text_w = 16 # 1文字あたりの幅を仮に16pxと設定

        #選択中の桁位置を点滅
        if px.frame_count%4 < 2:
            px.dither(0.5)
            px.rect(start_x + self.cursor_position[0] * text_w-2, start_y+1, 9, 11, px.COLOR_GREEN)
            px.dither(1)
        for i, char in enumerate(display_text):
            # 数字の文字描画
            px.text(start_x + i * text_w, start_y, char, px.COLOR_WHITE, font=G_.JP_FONT)
        px.text(start_x+(i+1) * text_w, start_y+1, f"（指定可能範囲 1～99",
                px.COLOR_WHITE, G_.SMALLFONT)
        px.text(start_x + text_w-2, start_y+16, f"現在の設定値={self.di.user.mana_drain_rate}%", px.COLOR_WHITE, G_.SMALLFONT)


class MenuEquipSkill(Menu):
    def __init__(self, di, x, y, parent):
        self.di = di
        self.parent_menu = parent
        self.user = parent.di.user
        self.item_list = []
        self.itemlist_index = 0
        self.skill_dict = {}
        self.messege_window = Window(G_.WND_MAIN[0], G_.WND_MAIN[3]//2-(1+2+1)*G_.CHIP_PIXEL,
                                     G_.WND_MAIN[2], (1+2+1)*G_.CHIP_PIXEL, 0)
        self.is_push_left = 0
        self.is_push_right = 0
        menutext_length = 8
        self.generate_item_list()
        super().__init__(72, 4, [1,len(self.item_list[self.itemlist_index])],
                         self.item_list[self.itemlist_index], menutext_length,
                         G_.MenuType.EQUIPSKILL, user=self.user)
        self.info_window = Window(72+self.menu_window.width+16,
                                  y+self.cursor_address[1]+16, 12*16,48, 0)
        self.change_target_item()

    def generate_item_list(self):
        list_rows = 8
        self.skill_dict = {skill_id:skill for skill_id, skill
                           in item.ItemManager.get_skill().items()
                           if skill_id in self.user.skill_list and
                           skill_id not in self.user.skillbook}
        self.item_count = len(self.skill_dict)
        if self.item_count <= 0:
            self.item_list = [["覚えたスキルがない"]]
        else:
            tmplist = list(self.skill_dict.items())
            self.item_list = [tmplist[i:i+list_rows]
                               for i in range(0, self.item_count, list_rows)]
        self.itemlist_index = self.itemlist_index if self.itemlist_index < len(self.item_list) else len(self.item_list)-1
        self.menu_shape = [1,len(self.item_list[self.itemlist_index])]

    def moveCursor(self):
        if px.btnp(px.KEY_W,20,10) or px.btnp(px.GAMEPAD1_BUTTON_DPAD_UP,20,10) or px.btnp(px.KEY_UP,20,10):
            self.cursor_position[1] = (self.cursor_position[1]-1)%self.menu_shape[1]
        if px.btnp(px.KEY_S,20,10) or px.btnp(px.GAMEPAD1_BUTTON_DPAD_DOWN,20,10) or px.btnp(px.KEY_DOWN,20,10):
            self.cursor_position[1] = (self.cursor_position[1]+1)%self.menu_shape[1]
        if len(self.item_list) > 1:
            if px.btnp(px.KEY_A) or px.btnp(px.GAMEPAD1_BUTTON_DPAD_LEFT) or px.btnp(px.KEY_LEFT):
                self.itemlist_index = (self.itemlist_index-1)%(len(self.item_list))
                self.remap_itemlist()
                self.is_push_left = 1
            if px.btnp(px.KEY_D) or px.btnp(px.GAMEPAD1_BUTTON_DPAD_RIGHT) or px.btnp(px.KEY_RIGHT):
                self.itemlist_index = (self.itemlist_index+1)%(len(self.item_list))
                self.remap_itemlist()
                self.is_push_right = 1

        #メニューカーソル表示
        self.cursor_address = [self.menu_window.x + 
                               #メニュー枠+余白+(カーソル位置(項目n番目)ｘ項目長x2)*チップサイズ(8)
                               (1+(((1)*(self.cursor_position[0]+1)+self.cursor_position[0]+(self.menutext_length*2)*self.cursor_position[0])))
                               *G_.CHIP_PIXEL - 2,
                               self.menu_window.y +
                               (1+(1+(self.cursor_position[1]*2)))*G_.CHIP_PIXEL - 5]
        self.info_window.y = self.cursor_address[1]
        self.change_target_item()

    def change_target_item(self):
        self.target_item = self.item_list[self.itemlist_index][self.cursor_position[1]]

    def remap_itemlist(self):
        self.menu_items = self.item_list[self.itemlist_index]
        self.menu_shape[1] = len(self.menu_items)
        self.cursor_position = [0,0]

    def menuEquipSkill(self):
        if self.item_list == [["覚えたスキルがない"]]:
            px.play(3,G_.SNDEFX["miss"],resume=True)
            return True
        self.submenu_instance = MenuSelectSkill(self.di, self.target_item)
        self.is_submenu = True

        return True

    def draw(self):
        #メニュー本体描画
        self.drawMenu()
        if self.item_count == 0:
            return
        #カーソルアイテム詳細描画
        self.drawInfo(self.info_window, self.target_item)
        #装備品は左右キーで別リスト展開
        scale_right = scale_left = 1
        if self.is_push_left:
            scale_left = 2
            self.is_push_left = (self.is_push_left+1)%(self.menu_shape[0]+1)
        if self.is_push_right:
            scale_right = 2
            self.is_push_right = (self.is_push_right+1)%(self.menu_shape[0]+1)
        px.blt(self.menu_window.x-8,
               self.menu_window.y+self.menu_window.height//2-8,
               G_.IMGIDX["CHIP"], *G_.ImageAddress.BIGARROW[:2],-16,16,
               colkey=px.COLOR_BLACK, scale=scale_left)
        px.blt(self.menu_window.x+self.menu_window.width-8,
               self.menu_window.y+self.menu_window.height//2-8,
               G_.IMGIDX["CHIP"], *G_.ImageAddress.BIGARROW,
               colkey=px.COLOR_BLACK, scale=scale_right)

        if self.is_submenu:
            self.submenu_instance.draw()

    def drawInfo(self, target_window, target_item):
        target_window.draw()
        skillinfo = ""
        if target_item[1][G_.JsonRune.TYPE_ID] == G_.ItemType.SKILL:
            recastphysic = 4 if target_item[1][G_.JsonSkill.ELEMENT] == G_.ElementType.NONE else 1
            recast_time = (target_item[1][G_.JsonSkill.RANK]+1) * recastphysic
            skillinfo = f"\n消費ＭＰ：{target_item[1][G_.JsonSkill.COST]}　再使用時間：{recast_time}秒"
        px.text(target_window.x+8,target_window.y+6, target_item[1][G_.JsonRune.DESC]+skillinfo,
                G_.ItemRank.COLOR[target_item[1][2]], G_.SMALLFONT)

    def drawMenu(self):
        #メニューウインドウ枠表示
        self.menu_window.draw()
        #メニュー項目文字表示
        for row in range(self.menu_shape[1]):
            if self.item_count == 0:
                px.text(self.menu_window.x+(1+1+1)*G_.CHIP_PIXEL,
                        self.menu_window.y+(1 + row*2)*G_.CHIP_PIXEL, self.menu_items[row],
                        px.COLOR_WHITE, G_.JP_FONT)
            else:
                _padding = " "*(19-(len(self.menu_items[row][1][1])*2))
                _str = f"{self.menu_items[row][1][1]}"

                px.text(self.menu_window.x+(1+1+1)*G_.CHIP_PIXEL,
                        self.menu_window.y+(1 + row*2)*G_.CHIP_PIXEL, _str,
                        G_.ItemRank.COLOR[self.menu_items[row][1][2]], G_.JP_FONT)
        px.blt(*self.cursor_address, G_.IMGIDX["CHIP"], 32,248,
               G_.CHIP_PIXEL,G_.CHIP_PIXEL, colkey=0)


class MenuSelectSkill:
    def __init__(self, di, skill_info):
        self.di = di
        self.user = di.user
        self.skill_info = skill_info
        self.menu_window = Window(10,px.height//2-40, 80,80, 0)
        self.msg_window = Window(self.menu_window.x+self.menu_window.width+8,
                                 self.menu_window.y+8,
                                 8+6*16+8,32,0)
        self.cursor_position = [0,1]
        self.select_index = "a"

    def update(self):
        _pushed_button = comf.get_button_state()
        if _pushed_button["u"]:
            self.cursor_position = [0,-1]
            self.select_index = "y"
        elif _pushed_button["d"]:
            self.cursor_position = [0,1]
            self.select_index = "a"
        elif _pushed_button["l"]:
            self.cursor_position = [-1,0]
            self.select_index = "x"
        elif _pushed_button["r"]:
            self.cursor_position = [1,0]
            self.select_index = "b"
        elif _pushed_button["a"]:
            self.user.skillbook[self.select_index] = skill.SkillModel(self.di, self.skill_info, self.user)

            px.play(3, G_.SNDEFX["pi"], resume=True)
            self.command_instance = command.CommandSave(0,0, self.di.app, 0)
            self.command_instance.exec()
            return False
        elif _pushed_button["b"]:
            px.play(3, G_.SNDEFX["po"], resume=True)
            return False
        return True

    def draw(self):
        self.menu_window.draw()
        self.msg_window.draw()
        skillname = "未設定" if self.user.skillbook[self.select_index] is None\
                else self.user.skillbook[self.select_index].name

        self.msg_window.drawText(self.msg_window.x+8, self.msg_window.y+8,[skillname])
        #ボタンアイコン
        px.blt(self.menu_window.x+32, self.menu_window.y+8, G_.IMGIDX["CHIP"],
               *G_.ImageAddress.BUTTON["y"], colkey=0 )
        px.blt(self.menu_window.x+32, self.menu_window.y+56, G_.IMGIDX["CHIP"],
               *G_.ImageAddress.BUTTON["a"], colkey=0 )
        px.blt(self.menu_window.x+8, self.menu_window.y+32, G_.IMGIDX["CHIP"],
               *G_.ImageAddress.BUTTON["x"], colkey=0 )
        px.blt(self.menu_window.x+56, self.menu_window.y+32, G_.IMGIDX["CHIP"],
               *G_.ImageAddress.BUTTON["b"], colkey=0 )
        #カーソル
        px.blt(self.menu_window.x+40+self.cursor_position[0]*16-4,
               self.menu_window.y+40+self.cursor_position[1]*16-4,
               G_.IMGIDX["CHIP"], 80,232, 8,8, colkey=0)


class MenuBaseShop(Menu):
    def __init__(self, di, x, y):
        self.di = di # Dependency Injection
        self.func_level = self.di.base.base_level["shop"]
        menulist_shape = [1, 3]
        menu_items = [["購入する"],["売却する"],["全て売却する"]]
        menutext_length = 8
        menu_type = G_.MenuType.BASESHOP
        super().__init__(x, y, menulist_shape, menu_items, menutext_length, menu_type)
        self.sellprice_total = 0

    def calc_sellprice(self, target_item):
        sellprice = 0
        if target_item[1].is_identified:
            sellprice = target_item[1].price*(target_item[1].rank*3+1)
        else: #未鑑定品の価格はイメージに合わせた定額（価格でアイテムが識別できないよう）
            # sellprice = target_item[1].price
            if target_item[1].price<1000: #産廃レベル
                sellprice = 400
            elif target_item[1].price<10000: #安っぽい
                sellprice = 4000
            elif target_item[1].price<100000: #よく見かける
                sellprice = 40000
            elif target_item[1].price<1000000: #見た目高そう
                sellprice = 400000
            else: #超高級品
                sellprice = 800000
        sellprice//=4
        #パーク：買取額UP
        rune_effect = self.di.user.get_rune_effect(G_.RuneList.BONUS)
        sellprice *= rune_effect[1] if rune_effect is not None else 1

        return int(sellprice)

    def menuBaseShop(self):
        subwindow_x, subwindow_y = self.cursor_address[0], self.cursor_address[1]+G_.CHIP_PIXEL+2
        match self.cursor_position[1]:
            case 0:
                self.submenu_instance = MenuShopBuy(self.di, subwindow_x, subwindow_y, self)
                self.is_submenu = True
            case 1:
                self.submenu_instance = MenuShopSell(self.di)
                self.is_submenu = True
            case 2:
                if self.di.user.inventory:
                    self.sellprice_total = 0
                    for target_item in self.di.user.inventory:
                        self.sellprice_total += self.calc_sellprice(target_item)
                else:
                    self.msg_window = Window(subwindow_x,subwindow_y,8+(16*12)+8,32)
                    self.message_text = ["何もお持ちではないご様子ですが…"]
                    self.is_msg_window = True
                    return True

                self.message_window = Window(G_.WND_MAIN[0],
                                             G_.WND_MAIN[3]//2-(1+2+1)*G_.CHIP_PIXEL,
                                             G_.WND_MAIN[2], (1+2+1)*G_.CHIP_PIXEL, 0)
                self.command_instance = command.CommandSellAll(self.di, self.message_window,
                                                               self.sellprice_total)
                self.submenu_instance = MenuYesNo(self.cursor_address[0],
                                                self.cursor_address[1]+G_.CHIP_PIXEL+2,
                        [f"{int(self.sellprice_total):,}で買い取ります"],
                        self.command_instance, self)
                self.is_submenu = True
        return True


class MenuShopBuy(Menu):
    def __init__(self, di, x, y, parent):
        self.di = di
        self.parent_menu = parent
        self.user = parent.di.user
        self.item_list = []
        self.display_dict = {}
        self.message_window = Window(G_.WND_MAIN[0], G_.WND_MAIN[3]//2-(1+2+1)*G_.CHIP_PIXEL,
                                     G_.WND_MAIN[2], (1+2+1)*G_.CHIP_PIXEL, 0)
        menutext_length = 11
        menu_type = G_.MenuType.SHOPBUY
        self.generate_item_list()
        super().__init__(x, y, [1,len(self.item_list)],
                         self.item_list, menutext_length,
                         menu_type, user=self.di.user)
        self.info_window = Window(x+self.menu_window.width+2,
                                  y+self.cursor_address[1], 12*12,40, 0)
        self.change_target_item()
        #パーク：販売額DOWN
        rune_effect = self.di.user.get_rune_effect(G_.RuneList.DISCOUNT)
        self.pricerate = rune_effect[1] if rune_effect is not None else 1

    def generate_item_list(self):
        list_rows = 8
        self.item_count = len(self.di.base.shop_item_list)
        if self.item_count <= 0:
            self.item_list = ["商品がない"]
        else:
            self.item_list = [item.ItemManager.get_item(key) for key 
                              in self.di.base.shop_item_list]
        self.menu_shape = [1,len(self.item_list)]

    def moveCursor(self):
        if px.btnp(px.KEY_W,20,10) or px.btnp(px.GAMEPAD1_BUTTON_DPAD_UP,20,10) or px.btnp(px.KEY_UP,20,10):
            self.cursor_position[1] = (self.cursor_position[1]-1)%self.menu_shape[1]
        if px.btnp(px.KEY_S,20,10) or px.btnp(px.GAMEPAD1_BUTTON_DPAD_DOWN,20,10) or px.btnp(px.KEY_DOWN,20,10):
            self.cursor_position[1] = (self.cursor_position[1]+1)%self.menu_shape[1]

        #メニューカーソル表示
        self.cursor_address = [self.menu_window.x + 
                               #メニュー枠+余白+(カーソル位置(項目n番目)ｘ項目長x2)*チップサイズ(8)
                               (1+(((1)*(self.cursor_position[0]+1)+self.cursor_position[0]+(self.menutext_length*2)*self.cursor_position[0])))
                               *G_.CHIP_PIXEL - 2,
                               self.menu_window.y +
                               (1+(1+(self.cursor_position[1]*2)))*G_.CHIP_PIXEL - 5]
        self.change_target_item()

    def change_target_item(self):
        self.target_item = self.item_list[self.cursor_position[1]]

    def update(self):
        if self.is_command:
            return self.chkCmdRtn()
       
        #サブメニュー表示中
        if self.is_submenu:
            self.is_submenu = self.submenu_instance.update()
            if self.is_submenu is False:
                self.generate_item_list()
                self.menu_items = self.item_list
                if self.submenu_instance.is_command:
                    self.cursor_position[1] = self.cursor_position[1]-1 if self.cursor_position[1]>0 else 0
            return True

        btn = comf.get_button_state()
        #キャンセル
        if btn["b"]:
            return False
        #決定
        if btn["a"]:
            if self.item_list == ["商品がない"]:
                px.play(3,G_.SNDEFX["miss"],resume=True)
                return True
            px.play(3,G_.SNDEFX["pi"], resume=True)
            buyprice = self.target_item.price*(self.target_item.rank+1) if self.target_item.is_identified else (10**(self.parent_menu.func_level*(1-self.parent_menu.func_level*0.05))*self.parent_menu.func_level)
            self.command_instance = command.CommandBuy(self.di, self.message_window,
                                                       self.target_item, buyprice*self.pricerate)
            self.submenu_instance = MenuYesNo(self.cursor_address[0],
                                              self.cursor_address[1]+G_.CHIP_PIXEL+2,
                                              [f"そいつを買うかい？"],
                                              self.command_instance, self)
            self.is_submenu = True

            return True
        
        self.moveCursor()
        return True

    def draw(self):
        #メニュー本体描画
        self.drawMenu()
        if self.item_count == 0:
            return
        #カーソルアイテム詳細描画
        self.drawInfo(self.info_window, self.target_item)

        if self.is_submenu:
            self.submenu_instance.draw()

    def drawInfo(self, target_window, target_item):
        target_window.draw()
        price = target_item.price*(target_item.rank+1) if target_item.is_identified else (
            10**(self.parent_menu.func_level*(1-self.parent_menu.func_level*0.05))
            *self.parent_menu.func_level
        )
        px.text(target_window.x+8,target_window.y+8,
                f"Price:{int(price*self.pricerate): >15,}",
                px.COLOR_WHITE, G_.SMALLFONT)
        if target_item.is_identified:
            px.text(target_window.x+8,target_window.y+24,
                    f"{item.ItemManager.get_item_info(target_item.id)[G_.JsonItem.DESC]}",
                    px.COLOR_WHITE, G_.SMALLFONT)
        else:
            px.text(target_window.x+8,target_window.y+24,
                    f"未鑑定の為詳細不明",
                    px.COLOR_GRAY, G_.SMALLFONT)

    def drawMenu(self):
        #メニューウインドウ枠表示
        self.menu_window.draw()
        #メニュー項目文字表示
        for row in range(self.menu_shape[1]):
            if self.item_count == 0:
                px.text(self.menu_window.x+(1+1+1)*G_.CHIP_PIXEL,
                        self.menu_window.y+(1 + row*2)*G_.CHIP_PIXEL, str(self.menu_items[row]),
                        px.COLOR_WHITE, G_.JP_FONT)
            else:
                padding_ = " "*(4-(len(G_.ITEM_TYPE_NAME[self.menu_items[row].type_id])*2))
                _str = f"{padding_+G_.ITEM_TYPE_NAME[self.menu_items[row].type_id]}）{self.menu_items[row].name}"
                color = G_.ItemRank.COLOR[self.menu_items[row].rank] if self.menu_items[row].is_identified else px.COLOR_GRAY
                px.text(self.menu_window.x+(1+1+1)*G_.CHIP_PIXEL,
                        self.menu_window.y+(1 + row*2)*G_.CHIP_PIXEL, _str,
                        color, G_.JP_FONT)
        px.blt(*self.cursor_address, G_.IMGIDX["CHIP"], 32,248,
               G_.CHIP_PIXEL,G_.CHIP_PIXEL, colkey=0)


class MenuShopSell(MenuInventory):
    def __init__(self, di):
        self.di = di
        basemenu = self.di.base.base_mainmenu
        user = self.di.user
        self.message_window = Window(G_.WND_MAIN[0], G_.WND_MAIN[3]//2-(1+2+1)*G_.CHIP_PIXEL,
                                     G_.WND_MAIN[2], (1+2+1)*G_.CHIP_PIXEL, 0)
        super().__init__(basemenu, user)
        self.menu_type = G_.MenuType.SHOPSELL
        self.sellprice = 0

    def menuShopSell(self):
        if self.selectitem_text not in ("何","該"):
            self.sellprice = self.di.base.base_mainmenu.submenu_instance.calc_sellprice(self.target_item)
        else:
            px.play(3,G_.SNDEFX["miss"],resume=True)
            return True

        self.command_instance = command.CommandSell(self.di, self.message_window,
                                                    self.target_item,
                                                    self.sellprice)
        self.submenu_instance = MenuYesNo(self.cursor_address[0],
                                          self.cursor_address[1]+G_.CHIP_PIXEL+2,
                [f"{int(self.sellprice):,}で買い取ります"],
                self.command_instance, self)
        self.is_submenu = True

        return True


class MenuBaseBackdoor(Menu):
    """
    1〜99の数字を入力するためのメニュークラス。
    左右キーで桁を選択し、上下キーで数字を増減させる。
    """
    def __init__(self, di, x: int, y: int):
        self.di = di
        self.func_level = self.di.base.base_level["backdoor"]
        dummy_items = [[" ", " ", " "]]
        menu_type = G_.MenuType.BASEBACKDOOR
        super().__init__(x, y, [3, 1], dummy_items, menutext_length=3, menu_type=menu_type)
        
        # 状態管理
        self.max_assignable_level = min(self.di.base.reached_max_level,
                                        self.di.base.defeated_boss+self.func_level)
        self.result_value = max(1, min(999, max(1,self.max_assignable_level))) # 1〜99に制限
        self.is_finished = False # 呼び出し元に返すためのフラグ

    def update(self):
        """
        入力処理（キーボード操作）を記述
        """
        if self.is_finished:
            # 決定キーが押されて終了フラグが立ったらFalseを返して親メニューに戻る
            return False 

        # 現在の桁位置（0:十の位, 1:一の位）
        current_digit_index = self.cursor_position[0] 
        
        # --- 1. 桁位置の決定 (左右キー) ---
        # MenuクラスのmoveCursorを使わず、必要な左右キーの処理だけを記述
        if px.btnp(px.KEY_A) or px.btnp(px.GAMEPAD1_BUTTON_DPAD_LEFT) or px.btnp(px.KEY_LEFT):
            # 左移動
            px.play(3, G_.SNDEFX["pi"], resume=True) # SE流用
            # 2桁間で循環
            self.cursor_position[0] = (self.cursor_position[0] - 1) % self.menu_shape[0]
        if px.btnp(px.KEY_D) or px.btnp(px.GAMEPAD1_BUTTON_DPAD_RIGHT) or px.btnp(px.KEY_RIGHT):
            # 右移動
            px.play(3, G_.SNDEFX["pi"], resume=True) # SE流用
            # 2桁間で循環
            self.cursor_position[0] = (self.cursor_position[0] + 1) % self.menu_shape[0]

        # --- 2. 数字の増減 (上下キー) ---
        delta = 0
        if px.btnp(px.KEY_W) or px.btnp(px.GAMEPAD1_BUTTON_DPAD_UP) or px.btnp(px.KEY_UP):
            delta = 1 # 上キーで増加
        elif px.btnp(px.KEY_S) or px.btnp(px.GAMEPAD1_BUTTON_DPAD_DOWN) or px.btnp(px.KEY_DOWN):
            delta = -1 # 下キーで減少

        if delta != 0:
            px.play(3, G_.SNDEFX["pi"], resume=True) # SE流用
            
            # 現在の値を桁ごとに分解
            digits = [self.result_value // 100, self.result_value // 10 % 10, self.result_value % 10]
            
            # 選択中の桁の値を更新
            new_digit_value = digits[current_digit_index] + delta
            
            # 桁ごとの循環 (0-9)
            if new_digit_value < 0:
                new_digit_value = 9
            elif new_digit_value > 9:
                new_digit_value = 0
            
            digits[current_digit_index] = new_digit_value
            
            # 新しい値を再構築
            new_value = digits[0] * 100 + digits[1] * 10 + digits[2]
            
            # 全体の制約: 1〜99
            if new_value < 1:
                # 00になる場合は、最小値の1にする (例: 10で十の位を0にすると00になるため)
                new_value = 1 
            elif new_value > self.max_assignable_level:
                new_value = self.max_assignable_level

            self.result_value = new_value
        
        # --- 3. 決定キー/キャンセルキー ---
        btn = comf.get_button_state()
        if btn["a"]: # 決定キー (Aボタン)
            px.play(3, G_.SNDEFX["pi"], resume=True)
            # self.di.user.mana_drain_rate = self.result_value
            self.di.app.next_level = self.result_value
            self.di.app.is_skip_level = True if self.di.app.next_level > 1 else False
            self.di.app.game_state = self.di.user.user_scene = G_.GameState.PREPARE_GAME
            self.is_finished = True
            return False # 親メニューに戻る
        if btn["b"]: # キャンセルキー (Bボタン)
            px.play(3, G_.SNDEFX["po"], resume=True)
            self.result_value = None # キャンセルの場合は結果をNoneとする
            self.is_finished = True
            return False # 親メニューに戻る

        return True # 継続

    def drawMenu(self):
        """
        数字とカーソルを描画
        """
        # 1. メニューウインドウ枠表示 (Menuクラスの機能流用)
        self.menu_window.draw()

        # 2. 2桁の数字を描画 (ゼロ埋め)
        display_text = f"{self.result_value:03d}"
        start_x = self.menu_window.x + G_.CHIP_PIXEL * 3
        start_y = self.menu_window.y + G_.CHIP_PIXEL + 2
        text_w = 16 # 1文字あたりの幅を仮に16pxと設定

        #選択中の桁位置を点滅
        if px.frame_count%4 < 2:
            px.dither(0.5)
            px.rect(start_x + self.cursor_position[0] * text_w-2, start_y+1, 9, 11, px.COLOR_GREEN)
            px.dither(1)
        for i, char in enumerate(display_text):
            # 数字の文字描画
            px.text(start_x + i * text_w, start_y, char, px.COLOR_WHITE, font=G_.JP_FONT)
        px.text(start_x+(i+2) * text_w, start_y+1, f"（指定可能範囲 1～{self.max_assignable_level}",
                px.COLOR_WHITE, G_.SMALLFONT)


class MenuBaseDiscover(Menu):
    def __init__(self, di, x, y):
        self.di = di # Dependency Injection
        self.func_level = self.di.base.base_level["discover"]
        menulist_shape = [1, self.func_level]
        can_warp_floor = [[f"{i}階へ転移"]for i in range(1,self.func_level*10,10) if i > 1]
        entrylevel = [["ダンジョンへ進入"]] + can_warp_floor
        menu_items = entrylevel[:self.func_level]
        menutext_length = 8
        menu_type = G_.MenuType.BASEDISCOVER
        super().__init__(x, y, menulist_shape, menu_items, menutext_length, menu_type)

    def menuBaseDiscover(self):
        self.di.app.next_level = 1 if self.cursor_position[1]==0 else self.cursor_position[1]*10+1
        self.di.app.is_skip_level = True if self.di.app.next_level > 1 else False
        self.di.app.game_state = self.di.user.user_scene = G_.GameState.PREPARE_GAME
        return True


class MenuBaseUpgrade(Menu):
    def __init__(self, di, x, y):
        self.di = di # Dependency Injection
        menu_items = [["倉庫を増築"],["錬金工房の整備"]]
        if di.base.is_defeat_or_die:
            menu_items += [["祭壇の整飾"]]
        if di.base.score_max > G_.SHOP_SCORE:
            menu_items += [["商店へ投資"]]
        if di.base.is_returned and di.base.reached_max_level>9:
            menu_items += [["探索路の開発"]]
        menulist_shape = [1, len(menu_items)]
        menutext_length = 7
        menu_type = G_.MenuType.BASEUPGRADE
        super().__init__(x, y, menulist_shape, menu_items, menutext_length, menu_type)

    def menuBaseUpgrade(self):
        self.di.base.is_notice = False
        subwindow_x, subwindow_y = self.cursor_address[0], self.cursor_address[1]+G_.CHIP_PIXEL+2
        match self.menu_items[self.cursor_position[1]][0]:
            case "storage"|"倉庫を増築":
                if self.di.flg.is_storage is False:
                    self.di.app.notice_window.message_text = self.di.flg.notice_rule(G_.FlagNotice.STORAGE)
                if self.di.base.base_level["storage"] >= 14:
                    self.di.base.information_window.message_text = ["増築用のスペースがない"]
                    self.di.base.is_notice = True
                    px.play(2,G_.SNDEFX["miss"],resume=True)
                target = "storage"
            case "alchemy"|"錬金工房の整備":
                if self.di.flg.is_alchemy is False:
                    self.di.app.notice_window.message_text = self.di.flg.notice_rule(G_.FlagNotice.ALCHEMY)
                if self.di.base.base_level["alchemy"] >= 10:
                    self.di.base.information_window.message_text = ["整備状況はじゅうぶんだ"]
                    self.di.base.is_notice = True
                    px.play(2,G_.SNDEFX["miss"],resume=True)
                target = "alchemy"
            case "ritual"|"祭壇の整飾":
                if self.di.flg.is_ritual2 is False:
                    self.di.app.notice_window.message_text = self.di.flg.notice_rule(G_.FlagNotice.RITUAL)
                if self.di.base.is_defeat_or_die:
                    nextlvl = self.di.base.base_level["ritual"]+1
                    require = int(nextlvl**6*3*(nextlvl/2))
                    if self.di.base.base_level["ritual"] >= 10:
                        self.di.base.information_window.message_text = ["すでに完璧な調和を見せている"]
                        self.di.base.is_notice = True
                        px.play(2,G_.SNDEFX["miss"],resume=True)
                    elif require > self.di.base.stock_mana:
                        self.di.base.information_window.message_text = [f"マナをもっと奉納する必要がある\n\n　奉納済マナ要求値：{require:>10,}"]
                        self.di.base.is_notice = True
                        px.play(2,G_.SNDEFX["miss"],resume=True)
                else:
                    self.di.base.information_window.message_text = ["祭壇には神気が感じられない・・・"]
                    self.di.base.is_notice = True
                    px.play(2,G_.SNDEFX["miss"],resume=True)
                target = "ritual"
            case "shop"|"商店へ投資":
                if self.di.flg.is_shop is False:
                    self.di.app.notice_window.message_text = self.di.flg.notice_rule(G_.FlagNotice.SHOP)
                if self.di.base.base_level["shop"] >= 8:
                    self.di.base.information_window.message_text = ["これ以上の投資は不要らしい"]
                    self.di.base.is_notice = True
                    px.play(2,G_.SNDEFX["miss"],resume=True)
                require = ((self.di.base.base_level["shop"]+1)**2-2)*G_.SHOP_SCORE
                if  require > self.di.base.score_max:
                    self.di.base.information_window.message_text = [f"希少な品を集めるには名声が不足している\n\n　最大スコア要求値：{require:>10,}"]
                    self.di.base.is_notice = True
                    px.play(2,G_.SNDEFX["miss"],resume=True)
                target = "shop"
            case "backdoor"|"探索路の開発":
                if self.di.flg.is_backdoor is False:
                    self.di.app.notice_window.message_text = self.di.flg.notice_rule(G_.FlagNotice.BACKDOOR)
                if self.di.base.base_level["backdoor"] >= 9:
                    self.di.base.information_window.message_text = ["開発はもはや必要ないだろう"]
                    self.di.base.is_notice = True
                    px.play(2,G_.SNDEFX["miss"],resume=True)
                target = "backdoor"

        if self.di.base.is_notice:
            return True

        match self.di.base.base_level[target]:
            case 0:
                cost =  300
            case 1:
                cost =  2200
            case 2:
                cost =  11800
            case 3:
                cost =  32600
            case 4:
                cost =  94000
            case 5:
                cost =  217000
            case 6:
                cost =  457400
            case 7:
                cost =  1162000
            case 8:
                cost =  3689000
            case _:
                cost =  9999999 

        self.command_instance = command.CommandUpgrade(self.di, target, cost)
        self.submenu_instance = MenuYesNo(subwindow_x, subwindow_y,
                [f"Lv{self.di.base.base_level[target]} -> {self.di.base.base_level[target]+1}",
                 f"ジェムが{cost:,}必要だ"], self.command_instance, self)
        self.is_submenu = True

        return True
