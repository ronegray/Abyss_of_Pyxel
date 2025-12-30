import pyxel as px
import const as G_, common_func as comf
import item


class Skill:
    def __init__(self, skill, caster):
        pass
        self.model = skill
        self.address = caster.address
        self.direction = caster.direction
        if self.model.element_type == 4:
            if self.model.movespeed:
                self.timer_remain = G_.GAME_FPS*3
            else:
                self.timer_remain = 10
        elif self.model.movespeed:
            self.timer_remain = caster.arcane//10 + G_.GAME_FPS
        else:
            self.timer_remain = G_.GAME_FPS
        self.hitlist = []
        if self.model.id == "720":
            self.model.di.user.is_buff[G_.BuffType.REFLECT] = True
            self.model.di.user.timer_item[G_.BuffType.REFLECT] = G_.BUFFTIME
        if self.model.element_type == 4:
            px.play(3, G_.SNDEFX["critical"], resume=True)
        else:
            px.play(3, G_.SNDEFX["skill"], resume=True)

    #アドレス移動
    def move_address(self):
        self.address = [self.address[0] + (G_.CHARA_DIR[self.direction][0]*(self.model.movespeed)),
                        self.address[1] + (G_.CHARA_DIR[self.direction][1]*(self.model.movespeed))]
        return True

    def update(self):
        # 移動速度が定義されたスキルは投射型
        if self.model.movespeed:
            self.move_address()
        #持続時間
        self.timer_remain -= 1
        if self.model.id in ("708","709","710","711","712","713","714","715"):
            if self.timer_remain == G_.GAME_FPS//2:
                self.hitlist = []

    def draw(self):
        if self.model.palette is not None:
            for col in self.model.palette:
                px.pal(col[0],col[1])

        self.model.func_drawtype(self)

        #カラーパレットのリセット
        px.pal()


def range_type_S0(x, y, direction):
    dx1 = G_.CHARA_DIR[direction][0]
    dy1 = G_.CHARA_DIR[direction][1]
    w1 = 8
    h1 = 8
    return [[x+dx1,y+dy1, w1,h1]]

def range_type_S1(x, y, direction):
    dx1 = G_.CHARA_DIR[direction][0]
    dy1 = G_.CHARA_DIR[direction][1]
    w1 = 24
    h1 = 24
    return [[x+dx1,y+dy1, w1,h1]]

def draw_type_S0(skill):
    px.blt(skill.address[0]-skill.model.image_source[2]//2,
           skill.address[1]-skill.model.image_source[3]//2,
           G_.IMGIDX["CHIP"], *skill.model.image_source, colkey=0, rotate=px.frame_count%180)


def range_type_S2(x, y, direction):
    dx1 = G_.CHARA_DIR[direction][0]*12
    dy1 = G_.CHARA_DIR[direction][1]*12
    w1 = 32 if dx1 == 0 else 8
    h1 = 32 if dy1 == 0 else 8

    dx2 = G_.CHARA_DIR[direction][0]*20
    dy2 = G_.CHARA_DIR[direction][1]*20
    w2 = 48 if dx2 == 0 else 8
    h2 = 48 if dy2 == 0 else 8

    dx3 = G_.CHARA_DIR[direction][0]*36
    dy3 = G_.CHARA_DIR[direction][1]*36
    w3 = 64 if dx2 == 0 else 24
    h3 = 64 if dy2 == 0 else 24

    return [[x+dx1,y+dy1, w1,h1],[x+dx2,y+dy2, w2,h2],[x+dx3,y+dy3, w3,h3]]

def draw_type_S2(skill):
    for i, rect in enumerate(skill.model.func_attackrange(*skill.address, skill.direction)):
        if px.frame_count%3 != i:
            continue
        px.blt(rect[0]-(rect[2]//2),rect[1]-(rect[3]//2), G_.IMGIDX["CHIP"],
            *skill.model.image_source[:2],rect[2],rect[3], colkey=0)


def range_type_S3(x, y, direction):
    return [[px.width//2,px.height//2, px.width,px.height]]

def draw_type_S3(skill):
    areawidth = G_.WND_MAIN[2]+G_.WND_SIDE[2]
    for _ in range(5):
        a1 = px.rndi(-8,8)
        a2 = px.rndi(-8,8)
        a3 = px.rndi(-8,8)
        px.blt(px.rndi(0,areawidth), px.rndi(0,G_.WND_MAIN[3]),
                G_.IMGIDX["CHIP"], *skill.model.image_source[:2],a1,a1+8,colkey=0)
        px.blt(px.rndf(areawidth*0.33,areawidth*0.66),
                px.rndf(G_.WND_MAIN[3]*0.33,G_.WND_MAIN[3]*0.66),
                G_.IMGIDX["CHIP"], *skill.model.image_source[:2],a2,a2+8,colkey=0)
        px.blt(px.rndf(areawidth*0.475,areawidth*0.525),
                px.rndf(G_.WND_MAIN[3]*0.475,G_.WND_MAIN[3]*0.525),
                G_.IMGIDX["CHIP"], *skill.model.image_source[:2],a3,a3+8,colkey=0)


def range_type_S4(x, y, direction):
    dx1 = G_.CHARA_DIR[direction][0]*24
    dy1 = G_.CHARA_DIR[direction][1]*24
    w1 = 32
    h1 = 32
    return [[x+dx1,y+dy1, w1,h1]]

def draw_type_S4(skill):
    for rect in skill.model.func_attackrange(*skill.address, skill.direction):
        px.blt(rect[0]-(rect[2]//2),rect[1]-(rect[3]//2), G_.IMGIDX["CHIP"],
               *skill.model.image_source[:2],rect[2],rect[3],
               colkey=0, rotate=px.frame_count%90)


def range_type_S5(x, y, direction):
    dx1 = G_.CHARA_DIR[direction][0]
    dy1 = G_.CHARA_DIR[direction][1]
    w1 = 16 if dx1 == 0 else 8
    h1 = 16 if dy1 == 0 else 8
    return [[x+dx1,y+dy1, w1,h1]]

def draw_type_S5(skill):
    match skill.direction:
        case 0:
            angle = 180
        case 1:
            angle = -90
        case 2:
            angle = 90
        case 3:
            angle = 0
    px.blt(skill.address[0]-skill.model.image_source[2]//2,
           skill.address[1]-skill.model.image_source[3]//2,
           G_.IMGIDX["CHIP"], *skill.model.image_source, colkey=0, rotate=angle)


def range_type_S6(x, y, direction):
    dx1 = G_.CHARA_DIR[direction][0]*24
    dy1 = G_.CHARA_DIR[direction][1]*24
    # w1 = 64
    # h1 = 32
    w1 = 64 if dx1 == 0 else 32
    h1 = 64 if dy1 == 0 else 32
    return [[x+dx1,y+dy1, w1,h1]]

def draw_type_S6(skill):
    match skill.direction:
        case 0:
            angle = 180
        case 1:
            angle = -90
        case 2:
            angle = 90
        case 3:
            angle = 0
    rect = skill.model.func_attackrange(*skill.address, skill.direction)
    px.blt(rect[0][0]-skill.model.image_source[2]//2,
           rect[0][1]-skill.model.image_source[3]//2,
           G_.IMGIDX["CHIP"], *skill.model.image_source, colkey=0, rotate=angle)


def range_type_S7(x, y, direction):
    dx1 = G_.CHARA_DIR[direction][0]
    dy1 = G_.CHARA_DIR[direction][1]
    w1 = 96
    h1 = 96
    return [[x+dx1,y+dy1, w1,h1]]

def draw_type_S7(skill):
    angle = ((10-skill.timer_remain) * 36) % 360
    dx,dy = 24,-24
    c = px.cos(angle)
    s = px.sin(angle)
    rotated_dx = dx * c - dy * s
    rotated_dy = dx * s + dy * c
    target_center_x = skill.address[0] + rotated_dx
    target_center_y = skill.address[1] + rotated_dy
    draw_x = target_center_x - 24
    draw_y = target_center_y - 24
    px.blt(draw_x,draw_y, G_.IMGIDX["CHIP"], 
           *skill.model.image_source, colkey=0, rotate=angle)


def range_type_S8(x, y, direction):
    dx1 = G_.CHARA_DIR[direction][0]*10
    dy1 = G_.CHARA_DIR[direction][1]*10
    w1 = 36 if dx1 == 0 else 12
    h1 = 36 if dy1 == 0 else 12
    dx2 = G_.CHARA_DIR[direction][0]*20
    dy2 = G_.CHARA_DIR[direction][1]*20
    w2 = 16 if dx2 == 0 else 8
    h2 = 16 if dy2 == 0 else 8
    return [[x+dx1,y+dy1, w1,h1],[x+dx2,y+dy2, w2,h2]]

def draw_type_S8(skill):
    for rect in skill.model.func_attackrange(*skill.address, skill.direction):
        if px.rndi(0,7) < 5:
            px.blt(rect[0]-rect[2]//4,rect[1]-rect[3]//4, G_.IMGIDX["CHIP"],
                *skill.model.image_source[:2],rect[2]//2,rect[3]//2,
                colkey=0, scale=px.rndf(1.5,3))


def range_type_S9(x, y, direction):
    dx1 = G_.CHARA_DIR[direction][0]*16
    dy1 = G_.CHARA_DIR[direction][1]*16
    # w1 = 8
    # h1 = 16
    w1 = 8 if dx1 == 0 else 16
    h1 = 8 if dy1 == 0 else 16
    return [[x+dx1,y+dy1, w1,h1]]

def draw_type_S9(skill):
    match skill.direction:
        case 0:
            angle = 180
        case 1:
            angle = -90
        case 2:
            angle = 90
        case 3:
            angle = 0
    rect = skill.model.func_attackrange(*skill.address, skill.direction)
    px.blt(rect[0][0]-skill.model.image_source[2]//2,
           rect[0][1]-skill.model.image_source[3]//2,
           G_.IMGIDX["CHIP"], *skill.model.image_source, colkey=0, rotate=angle)


def range_type_none(x,y,direction):
    return [[x,y,0,0]]

def draw_type_none(skill):
    px.blt(skill.address[0]+px.rndi(-12,4),skill.address[1]+px.rndi(-12,4),G_.IMGIDX["CHIP"],
           *skill.model.image_source, colkey=0, rotate=px.rndi(0,360))
    px.blt(skill.address[0]+px.rndi(-10,2),skill.address[1]+px.rndi(-10,2),G_.IMGIDX["CHIP"],
           *skill.model.image_source, colkey=0, rotate=px.rndi(0,360))
    px.blt(skill.address[0]+px.rndi(-8,0),skill.address[1]+px.rndi(-8,0),G_.IMGIDX["CHIP"],
           *skill.model.image_source, colkey=0, rotate=px.rndi(0,360))


#デバフ効果
def debuff_burn(target):
    target.hp = int(target.hp - target.hp*0.02)


def debuff_slow(target):
    try:
        target.movespeed = target.movespeed //2
    except AttributeError:
        target.movespeed /= 2


def debuff_bind(target):
    target.attack_waittime *= 2


def debuff_recoil():
    #ノックバック
    pass


class SkillModel:
    def __init__(self, di, common_param, caster):
        self.di = di
        self.caster = caster
        self.id = common_param[0]
        self.name = common_param[1][G_.JsonSkill.NAME]
        self.value = common_param[1][G_.JsonSkill.VALUE]
        self.element_type = common_param[1][G_.JsonSkill.ELEMENT]
        self.cost = common_param[1][G_.JsonSkill.COST]
        self.func_efx = common_param[1][G_.JsonSkill.FUNC_EFX]
        self.desc = common_param[1][G_.JsonSkill.DESC]
        self.set_skill_param()
        recastphysic = 8 if self.element_type == G_.ElementType.NONE else 1
        self.recast_time = (common_param[1][G_.JsonSkill.RANK]+1) * G_.GAME_FPS/2 * recastphysic# * 2
        self.timer_recast = 0
        self.active_skills = []

    def set_skill_param(self):
        skill_param = globals()[self.func_efx]()
        self.func_effect = skill_param["func_effect"]
        self.func_attackrange = skill_param["func_attackrange"]
        self.func_drawtype = skill_param["func_drawtype"]
        self.movespeed = skill_param["movespeed"]
        self.image_source = skill_param["image_source"]
        self.palette = skill_param["palette"]

    def __getstate__(self):
        """pickle保存時: 不要なオブジェクトを除外"""
        # common_funcの関数で di, image_*, *_window, *_menu を削除
        return comf.get_clean_state(self)

    def resume(self, di):
        """ロード後の復帰処理"""
        self.di = di
        self.set_skill_param()

    def cast_skill(self):
        if self.timer_recast > 0:
            px.play(3, G_.SNDEFX["miss"], resume=True)
            self.di.message_manager.add_message("まだ使えない",px.COLOR_RED)
            return

        rune_effect = rune_effect1 = None
        if self.di.user == self.caster:
            rune_effect = self.di.user.get_rune_effect(G_.RuneList.ECONOM)
        costrate = 1 if rune_effect is None else rune_effect[1]
        if self.caster.mp >= self.cost/costrate:
            self.caster.mp -= self.cost/costrate
            recastrate = 1 if rune_effect1 is None else rune_effect1[1]
            self.timer_recast = self.recast_time*recastrate
            self.active_skills.append(Skill(self, self.caster))
            if self.caster.move_type == 0 and self.di.app.depth_level > 2:
                self.di.app.notice_window.message_text = self.notice_element()
        else:
            px.play(3, G_.SNDEFX["miss"], resume=True)
            self.di.message_manager.add_message("MPが足りない",px.COLOR_RED)

    def clear_activeskill(self):
        self.active_skills = []

    def notice_element(self):
        notice_message = ""
        if self.di.flg.is_element[self.element_type] is False:
            notice_message = G_.ELEMENT_DESC[self.element_type]
            self.di.flg.is_element[self.element_type] = True
        return [notice_message]

    def update(self):
        self.timer_recast = max(0, self.timer_recast - 1)
        if self.active_skills:
            for active in self.active_skills:
                active.update()
                if active.model.movespeed:
                    if self.di.user.user_scene in (G_.GameState.DUNGEON,
                                                   G_.GameState.DUNGEON_CAVE,
                                                   G_.GameState.DUNGEON_MAZE) :
                        if -(G_.CHIP_PIXEL*2)>active.address[0] or\
                                G_.WND_MAIN[2]+(G_.CHIP_PIXEL*2)<active.address[0] or\
                                -(G_.CHIP_PIXEL*2)>active.address[1] or\
                                G_.WND_MAIN[3]+(G_.CHIP_PIXEL*2)<active.address[1]:
                            active.timer_remain = 0
                    elif self.di.user.user_scene in (G_.GameState.BOSSBATTLE,
                                                     G_.GameState.LASTBOSS) :
                        if -(G_.CHIP_PIXEL*2)>active.address[0] or\
                             G_.WND_BOSS[0]+G_.WND_BOSS[2]+(G_.CHIP_PIXEL*2)<active.address[0] or\
                             G_.WND_BOSS[1]-(G_.CHIP_PIXEL*2)>active.address[1] or\
                             G_.WND_BOSS[1]+G_.WND_BOSS[3]+(G_.CHIP_PIXEL*2)<active.address[1]:
                            active.timer_remain = 0
        self.active_skills = [
                active for active in self.active_skills if active.timer_remain > 0
            ]

    def draw(self):
        if self.active_skills:
            for active in self.active_skills:
                active.draw()


def func_op700(): #ファイア
    func_effect = debuff_burn
    func_attackrange = range_type_S0
    func_drawtype = draw_type_S0
    movespeed = 2
    image_source = G_.ImageAddress.SKILL["ball"]
    palette = None
    return locals()
def func_op701(): #アイス
    func_effect = debuff_slow
    func_attackrange = range_type_S0
    func_drawtype = draw_type_S0
    movespeed = 2
    image_source = G_.ImageAddress.SKILL["ball"]
    palette = ((8,6),(9,5),(10,12))
    return locals()
def func_op702(): #ウインド
    func_effect = debuff_bind
    func_attackrange = range_type_S0
    func_drawtype = draw_type_S0
    movespeed = 2
    image_source = G_.ImageAddress.SKILL["ball"]
    palette = ((8,3),(9,16),(10,11))
    return locals()
def func_op703(): #ストーン
    func_effect = debuff_recoil
    func_attackrange = range_type_S0
    func_drawtype = draw_type_S0
    movespeed = 2
    image_source = G_.ImageAddress.SKILL["ball"]
    palette = ((8,4),(10,15))
    return locals()
def func_op704(): #フレイム
    func_effect = debuff_burn
    func_attackrange = range_type_S1
    func_drawtype = draw_type_S0
    movespeed = 1
    image_source = G_.ImageAddress.SKILL["cannon"]
    palette = None
    return locals()
def func_op705(): #フロスト
    func_effect = debuff_slow
    func_attackrange = range_type_S1
    func_drawtype = draw_type_S0
    movespeed = 1
    image_source = G_.ImageAddress.SKILL["cannon"]
    palette = ((8,6),(9,5),(10,12))
    return locals()
def func_op706(): #ストーム
    func_effect = debuff_bind
    func_attackrange = range_type_S1
    func_drawtype = draw_type_S0
    movespeed = 1
    image_source = G_.ImageAddress.SKILL["cannon"]
    palette = ((8,3),(9,16),(10,11))
    return locals()
def func_op707(): #ロック
    func_effect = debuff_recoil
    func_attackrange = range_type_S1
    func_drawtype = draw_type_S0
    movespeed = 1
    image_source = G_.ImageAddress.SKILL["cannon"]
    palette = ((8,4),(10,15))
    return locals()
def func_op708(): #バーン
    func_effect = debuff_burn
    func_attackrange = range_type_S2
    func_drawtype = draw_type_S2
    movespeed = 0
    image_source = G_.ImageAddress.SKILL["fan"]
    palette = None
    return locals()
def func_op709(): #フリーズ
    func_effect = debuff_slow
    func_attackrange = range_type_S2
    func_drawtype = draw_type_S2
    movespeed = 0
    image_source = G_.ImageAddress.SKILL["fan"]
    palette = ((8,6),(9,5),(10,12))
    return locals()
def func_op710(): #サイクロン
    func_effect = debuff_bind
    func_attackrange = range_type_S2
    func_drawtype = draw_type_S2
    movespeed = 0
    image_source = G_.ImageAddress.SKILL["fan"]
    palette = ((8,3),(9,16),(10,11))
    return locals()
def func_op711(): #ボルダー
    func_effect = debuff_recoil
    func_attackrange = range_type_S2
    func_drawtype = draw_type_S2
    movespeed = 0
    image_source = G_.ImageAddress.SKILL["fan"]
    palette =  ((8,4),(10,15))
    return locals()
def func_op712(): #ブラスト
    func_effect = debuff_burn
    func_attackrange = range_type_S3
    func_drawtype = draw_type_S3
    movespeed = 0
    image_source = G_.ImageAddress.SKILL["area"]
    palette = None
    return locals()
def func_op713(): #ブリザード
    func_effect = debuff_slow
    func_attackrange = range_type_S3
    func_drawtype = draw_type_S3
    movespeed = 0
    image_source = G_.ImageAddress.SKILL["area"]
    palette = ((8,6),(9,5),(10,12))
    return locals()
def func_op714(): #テンペスト
    func_effect = debuff_bind
    func_attackrange = range_type_S3
    func_drawtype = draw_type_S3
    movespeed = 0
    image_source = G_.ImageAddress.SKILL["area"]
    palette = ((8,3),(9,16),(10,11))
    return locals()
def func_op715(): #メテオ
    func_effect = debuff_recoil
    func_attackrange = range_type_S3
    func_drawtype = draw_type_S3
    movespeed = 0
    image_source = G_.ImageAddress.SKILL["area"]
    palette =  ((8,4),(10,15))
    return locals()
def func_op716(): #クラッシュ
    func_effect = None
    func_attackrange = range_type_S4
    func_drawtype = draw_type_S4
    movespeed = 0
    image_source = G_.ImageAddress.SKILL["front"]
    palette = None
    return locals()
def func_op717(): #ソニック
    func_effect = None
    func_attackrange = range_type_S5
    func_drawtype = draw_type_S5
    movespeed = 3
    image_source = G_.ImageAddress.SKILL["shoot"]
    palette = None
    return locals()
def func_op718(): #クレセント
    func_effect = None
    func_attackrange = range_type_S6
    func_drawtype = draw_type_S6
    movespeed = 0
    image_source = G_.ImageAddress.SKILL["slash"]
    palette = None
    return locals()
def func_op719(): #スパイラル
    func_effect = None
    func_attackrange = range_type_S7
    func_drawtype = draw_type_S7
    movespeed = 0
    image_source = G_.ImageAddress.SKILL["swing"]
    palette = None
    return locals()
def func_op720(): #リフレクト
    func_effect = None
    func_attackrange = range_type_none
    func_drawtype = draw_type_none
    movespeed = 0
    image_source = G_.ImageAddress.SKILL["shine"]
    palette = None
    return locals()
def func_op721(): #ブロウ
    func_effect = None
    func_attackrange = range_type_S8
    func_drawtype = draw_type_S8
    movespeed = 0
    image_source = G_.ImageAddress.SKILL["front"]
    palette = None
    return locals()
def func_op722(): #アサシネイト
    func_effect = None
    func_attackrange = range_type_S9
    func_drawtype = draw_type_S9
    movespeed = 0
    image_source = G_.ImageAddress.SKILL["deadly"]
    palette = None
    return locals()
def func_op723(): #インフェルノ
    func_effect = debuff_burn
    func_attackrange = range_type_S3
    func_drawtype = draw_type_S3
    movespeed = 0
    image_source = G_.ImageAddress.SKILL["area"]
    palette = None
    return locals()
def func_op724(): #コキュートス
    func_effect = debuff_slow
    func_attackrange = range_type_S3
    func_drawtype = draw_type_S3
    movespeed = 0
    image_source = G_.ImageAddress.SKILL["area"]
    palette = ((8,19),(9,28),(10,6))
    return locals()
def func_op725(): #ヴォルテクス
    func_effect = debuff_bind
    func_attackrange = range_type_S3
    func_drawtype = draw_type_S3
    movespeed = 0
    image_source = G_.ImageAddress.SKILL["area"]
    palette = ((8,27),(9,22),(10,16))
    return locals()
def func_op726(): #カタストロフ
    func_effect = debuff_recoil
    func_attackrange = range_type_S3
    func_drawtype = draw_type_S3
    movespeed = 0
    image_source = G_.ImageAddress.SKILL["area"]
    palette =  ((8,20),(10,4))
    return locals()