import pyxel as px
import const as G_
import common_func as comf

class MessageManager:
    MESSAGE_LINE_MAX = 19
    def __init__(self, di):
        self.di = di #Dependency Injection
        self.di.message_manager = self
        self.message_list = []
        self.timer_message = 0

    def __getstate__(self):
        """pickle保存時: 不要なオブジェクトを除外"""
        # common_funcの関数で di, image_*, *_window, *_menu を削除
        return comf.get_clean_state(self)

    def resume(self, di):
        """ロード後の復帰処理"""
        self.di = di

    def update(self):
        self.timer_message += 1

    def clear_message(self):
        self.message_list.clear()

    def add_message(self, message_text:str, textcolor:int=px.COLOR_WHITE):
        self.message_list.append([self.timer_message, message_text, textcolor])
        while len(self.message_list) > self.MESSAGE_LINE_MAX:
            self.message_list.pop(0)

    def countdown_message(self):
        self.update()
        for i,msg in enumerate(self.message_list):
            if self.timer_message - msg[0] > 5*G_.GAME_FPS:
                self.message_list.pop(i)

    def get_message(self, index:int):
        return self.message_list[index]
    
    def draw_window(self):
        px.bltm(G_.WND_MESG[0],G_.WND_MESG[1], 7, 
                0,G_.WND_MESG[1], G_.WND_MESG[2],G_.WND_MESG[3], colkey=7)
        
        #角は画像反転で描画
        px.blt(G_.WND_MESG[0], G_.WND_MESG[1], 0,
                96,0, 8,8, colkey=7)
        px.blt(G_.WND_MESG[0]+G_.WND_MESG[2]-8, G_.WND_MESG[1], 0,
                96,0, -8,8, colkey=7)
        px.blt(G_.WND_MESG[0], G_.WND_MESG[1]+G_.WND_MESG[3]-8, 0,
                96,0, 8,-8, colkey=7)
        px.blt(G_.WND_MESG[0]+G_.WND_MESG[2]-8, G_.WND_MESG[1]+G_.WND_MESG[3]-8, 0,
                96,0, -8,-8, colkey=7)

    def draw_message(self):
        #メッセージエリア枠線描画
        self.draw_window()
        line = 4
        for msgdata in self.message_list:
            px.text(G_.WND_MESG[0]+5,G_.WND_MESG[1]+line, msgdata[1], msgdata[2], G_.SMALLFONT)
            line += 11

    