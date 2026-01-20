from enum import Enum,IntEnum,unique

###定数ファイル 

#辞書
SNDEFX = {"identify":35,"gain":36,"shattered":37,"lock":38, "lvup":39,
          "buy":40,"menu":41,"tdr1":42,"tdr2":43,"save":44,
          "load":45,"crush":46,"defeat":47,"dead":48, "pick":49,
          "po":50,"stair":51,"open":52,"unlock":53,"item":54,"special":55, "run":56, "pi":57, "skill":58, "damage":59, 
          "miss":60, "critical":61, "attack":62, "don":63}
IMGIDX = {"CHIP":0, "CHAR":1, "MOB":2}

#リスト／タプル
BUFF_DESC= ["行動停止","認識阻害","攻撃向上","魔力向上","移動向上","無敵状態","反射状態"]
ITEM_TYPE_NAME = ("杖","剣","槍","斧","衣服","軽装","中装","重装","腕輪","小盾","中盾","大盾",
             "火術","氷術","風術","土術","秘紋石","財宝","継続","消費","消耗","霊薬",)
ITEM_TYPE_DESC= ("全てにおいて非力だが、唯一魔法攻撃⼒上昇補正を持つ武器",
                 "短い射程はネックだが他に欠点のない、バランスの取れた武器",
                 "射程の長さと引き換えに、攻撃力や速度、範囲は控えめな武器",
                 "最大の攻撃力と攻撃範囲を持つが、速度が非常に遅い武器",
                 "移動が速く、デバフ抵抗とＭＰ回復上昇の効果を持つ服",
                 "防御力は控えめな分、移動速度の影響が少ない防具",
                 "防御力が高めな代わりに移動速度が低めの防具",
                 "最高の防御力と引き換えに、移動速度が最低レベルの防具",
                 "防御力がほぼ無い代わりに魔力攻撃のダメージを減らす盾",
                 "防御力は高くないが攻撃速度への影響も小さい盾",
                 "防御力を高めた分攻撃速度への影響が大きめの盾",
                 "高い防御力と引き換えに攻撃速度が大幅に下がる盾"
)
BUTTON_DESC = [
    "Ａ：装備中の武器で攻撃／メニュー時は決定\n攻撃速度は武器や特殊効果で変化。ダメージに筋力が影響",
    "Ｂ：メニュー表示／メニュー時はキャンセル\nインベントリから装備の変更とアイテムの投棄が出来る",
    "Ｘ：ゲージを消費して回避（回避中はダメージを受けない）\nゲージは一定時間で回復する（敏捷が影響）",
    "Ｙ：鶴嘴を消費して障害物を破壊する\n外壁は破壊出来ない",
    "Ｌ：キーを押しながらＡＢＸＹキーでスキル発動\n右下のアイコンが灰色のボタンはスキル未設定"
]
ELEMENT_DESC = [
    "火術：火属性のダメージを与える魔法\n効果：一定時間毎秒現HPの2%のダメージ",
    "氷術：氷属性のダメージを与える魔法\n効果：一定時間移動速度が半減し、毎秒現HPの0.1%のダメージ",
    "風術：風属性のダメージを与える魔法\n効果：一定時間攻撃間隔が遅延",
    "土術：土属性のダメージを与える魔法\n効果：長距離のノックバック効果",
    "武術：属性魔法ではない武具スキル\n武器の攻撃力を加味したダメージを与える"
] 
MENU_ITEM = [["パラメータ"],["インベントリ"],["エスケープ"],["データロード"]]
CHARA_DIR = ((0,1),(-1,0),(1,0),(0,-1))  #キャラの向き 0:下（正面）1:左 2:右 3:上（背面）
LEVELUP_COLOR = ((5,2,10,8,12,3),("Wpn","Lv","Wnd","Swd","Spr","Axe"))
size = 21
WND_MAIN = (0,0, 16*size,16*size) #x,y, w,h
WND_SIDE = (16*size,0,120,16*size) #x,y, w,h
WND_STAT = (16*size,0, 120,120) #x,y, w,h
WND_MESG = (16*size,120, 120,WND_SIDE[3]-WND_STAT[3]) #x,y, w,h
WND_INFO = (16,WND_MAIN[3]-8-64,WND_MAIN[2]+WND_SIDE[2]-32,64)
WND_BASE = (360,0,96,192)
WND_USTA = (16,176,120,80)
WND_BOSS = (8,80,440,248)
INVENTORY_FILTER_TYPES = [None, 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 16] # インベントリ絞り込み用リスト (Noneは「全て」)

#パラメータ（指定値）
IS_DEBUG = False
CHIP_PIXEL = 8 #マップチップサイズ（Pixel）
GAME_FPS = 60
ASSET_FILE = "assets/assets.pyxres"
FONTFILE = "assets/umplus_j12r.bdf"
SMALLFONT = "assets/umplus_j10r.bdf"
JP_FONT = ""
ENCRYPT_KEY = b"Ab2sp5xlOf01"
DATA_HEADER = b"\x7F\x70\x79\x78"
APP_NAME = "AbyssOfPyxel"
APP_VERSION = "1.5.1"
REPOP_SECONDS = 8 #モンスター再出現間隔　単位秒
SKIPSTAIR_APPEAR = 20 # 複数階飛び階段の出現LEVEL
BUFFTIME = 30*GAME_FPS #タイマーバフアイテムの効果時間（秒*ゲームFPS)
SHOP_SCORE = 10000 #商店開店条件スコア値
ELITE_RATE = 5000 #エリート出現確率の分母

#パラメータ（算出）
TILEMAP_WIDTH = WND_MAIN[2]//8
TILEMAP_HEIGHT = WND_MAIN[3]//8

#新方式
class CharaType:
    POWER = 0
    SKILL = 1
    SPEED = 2
    NAME = [
        "パワー型",
        "スキル型",
        "スピード型"
    ]

class Direction:
    FRONT = 0
    BACK = 3
    LEFT = 1
    RIGHT = 2

class FlagNotice:
    KILL_MONSTER = 0
    LOCK_DOOR = 1
    POP_ELITE = 2
    REVIVE_SPAWNER = 3
    EVASION = 4
    TO_BOSS = 5
    LEVELUP = 6
    ESCAPE = 7
    MASTERY = 8
    BLUECHEST = 9
    STORAGE = 10
    ALCHEMY = 11
    RITUAL = 12
    SHOP = 13
    BACKDOOR = 14
    GETSKILL = 15

class JsonMonster:
    ID = 0
    TIER = 1
    NAME = 2
    IMAGESOURCE = 3
    DATA = 4
    MAXHP = 0
    ATTACK = 1
    DEFEND = 2
    ARCANE = 3
    ACTION_WAITTIME = 4
    MOVESPEED = 5
    REDUCE_FIRE = 6
    REDUCE_ICE = 7
    REDUCE_WIND = 8
    REDUCE_EARTH = 9
    MANA = 10
    MOVETYPE = 11
    SKILL = 12

class BonusType(IntEnum):
    ATTACK = 0
    ATTACKSPEED = 1
    EVADELENGTH = 2
    ARCANE = 3
    DEFEND = 4
    REDUCEALL = 5
    MAXHP = 6
    REGISTFIRE = 7
    REGISICE = 8
    REGISTWIND = 9
    REGISTEARTH = 10

class BuffType(IntEnum):
    TIMESTOP = 0
    HIDDEN = 1
    POWERUP = 2
    ARCANEUP = 3
    SPEEDUP = 4
    DIFLECT = 5
    REFLECT = 6

class MoveType(IntEnum):
    USER = 0
    RANDOM = 1
    TRACE = 2
    AWAY = 3
    STOP = 4
    WARP = 5

class JsonSkill(IntEnum):
    TYPE_ID = 0
    NAME = 1
    RANK = 2
    VALUE = 3
    ELEMENT = 4
    COST = 5
    FUNC_EFX = 6
    DESC = 7

class ElementType(IntEnum):
    FIRE = 0
    ICE = 1
    WIND = 2
    EARTH = 3
    NONE = 4

class JsonRune(IntEnum):
    TYPE_ID = 0
    NAME = 1
    RANK = 2
    TYPE = 3
    CATEGORY = 4
    VALUE = 5
    FUNC_EFX = 6
    DESC = 7

class RuneType(IntEnum):
    PERK = 0b100
    ABILITY = 0b010
    RUNE = 0b001

class RuneApply(IntEnum):
    WEAPON = 0b100
    ARMOR = 0b010
    SHIELD = 0b001

class RuneList(Enum):
    DUMMY="0" #ダミー処理用
    ATTACK="900" # 剛力
    ARCANE="901" # 叡智
    HASTE="902" # 神速
    MASTER="903" # 絶技
    CRITICAL="904" # 致命
    FATAL="905" # 必殺
    DRAIN="906" # 吸血
    WAND="907" # 熟杖
    SWORD="908" # 熟剣
    SPEAR="909" # 熟槍
    AXE="910" # 熟斧
    FIRE="911" # 爆炎
    ICE="912" # 氷嵐
    WIND="913" # 暴風
    EARTH="914" # 轟震
    MORTAL="915" # 骨断
    FULLPOW="916" # 渾身
    BURN="917" # 炎上
    SLOW="918" # 鈍足
    BIND="919" # 束縛
    RECOIL="920" # 反衝
    ELITEATTACK="921" # 破邪
    OVERRANGE="922" # 掃滅
    COOLDOWN="923" # 敏腕
    ECONOM="924" # 省力
    VITAL="925" # 体力
    DEFEND="926" # 鉄壁
    SOLID="927" # 剛体
    LONGDASH="928" # 縮地
    STAMINA="929" # 持久
    RDCEVADE="930" # 連跳
    HIGAIN="931" # 健脚
    REDUCTION="932" # 速癒
    RDCFIRE="933" # 耐火
    RDCICE="934" # 耐氷
    RDCWIND="935" # 耐風
    RDCEARTH="936" # 耐地
    REVENGE="937" # 報復
    REFLECT="938" # 反射
    REGENERATE="939" # 治癒
    POTION="940" # 薬効
    GIANT="941" # 巨体
    ANTIBURN="942" # 抗炎
    ANTISLOW="943" # 抗氷
    ANTIBIND="944" # 抗風
    ANTIKNOCK="945" # 抗地
    EXTING="946" # 消火
    WARMTH="947" # 懐炉
    BREEZE="948" # 柳風
    ROBE="949" # 熟服
    LEATHER="950" # 熟軽
    CHAIN="951" # 熟鎖
    PLATE="952" # 熟鎧
    BUNGLE="953" # 熟輪
    ROUND="954" # 熟小
    KITE="955" # 熟中
    TOWER="956" # 熟大
    CLEANSE="957" # 滅邪
    DASH="958" # 縮地
    MANAUP="959" # 吸魔
    GEMUP="960" # 強欲
    BOUNTY="961" # 大漁
    LUCKY="962" # 幸運
    DISCOUNT="963" # 値引
    BONUS="964" # 割増
    CARGO="965" # 積載
    UNLOCK="966" # 開錠
    TOUGH="967" # 頑丈
    HOLD="968" # 保持
    DIVINE="969" # 天授
    RELEASE="970" # 開放
    RDCFOOD="971" # 小食
    FUELEFF="972" # 燃費
    STR="973" # 筋力
    INT="974" # 知力
    DEX="975" # 器用
    AGL="976" # 敏捷
    CON="977" # 耐久
    LUK="978" # 幸運
    SUSTAIN="979" # 持続
    BLESS="980" # 天恵
    BACK="981" # 衝撃

class LanguageType(IntEnum):
    JAPANESE = 0
    ENGLISH = 1

class ConfigManager:
    VOLUME = 100
    LANGUAGE = LanguageType.JAPANESE

class HitboxSize:
    SAME = (16,16)
    MIDDLE = (12,12)
    SMALL = (8,8)

class MenuType(IntEnum):
    MAIN = 0
    CHARASELECT = 1
    SHOP = 2
    TITLE = 3
    NAMEENTRY = 4
    SELECTITEM = 5
    SAVE = 6
    LOAD = 7
    INVENTORY = 8
    INVENTORYSUB = 9
    BASEMAIN = 10
    BASESTORAGE = 20
    STORESTORAGE = 21
    GETSTORAGE = 22
    BASEALCHEMY = 30
    IDENTIFY = 31
    BASERITUAL = 40
    GETPERK = 41
    MANADRAINRATE = 42
    EQUIPSKILL = 43
    BASESHOP = 50
    SHOPBUY = 51
    SHOPSELL = 52
    SHOPSELLALL = 53
    BASEBACKDOOR = 60
    BASEDISCOVER = 70
    BASEUPGRADE = 80

class ItemData(IntEnum):
    TYPE = 0
    BASENAME = 1
    PRICE = 2
    VALUE = 3
    RANK = 4

class JsonItem(IntEnum):
    TYPE_ID = 0
    BASENAME = 1
    PRICE = 2
    VALUE = 3
    RANK = 4
    DESC = 5

class ItemRank:
    UNIDENTIFIED = -1 #未鑑定
    COMMON = 0 # 量産
    UNCOMMON = 1 # 特注
    RARE =	2 # 名品
    SUPERRARE = 3 # 秘宝
    EXTREME = 4 # 究極
    LEGEND = 5 # 伝説
    ANCIENT = 6 # 神代
    NAME = {
        COMMON:"COMMON",
        UNCOMMON:"UNCOMMON",
        RARE:"RARE",
        SUPERRARE:"SUPERRARE",
        EXTREME:"EXTREME",
        LEGEND:"LEGEND",
        ANCIENT:"ANCIENT"
    }
    SHORTEN = {
        COMMON:"C",
        UNCOMMON:"UC",
        RARE:"R",
        SUPERRARE:"SR",
        EXTREME:"EX",
        LEGEND:"LG",
        ANCIENT:"AN"
    }
    COLOR = {
        COMMON:23,
        UNCOMMON:22,
        RARE:26,
        SUPERRARE:25,
        EXTREME:32,
        LEGEND:18,
        ANCIENT:24
    }

@unique
class ItemStatus(IntEnum):
    DROP = 0 #	床置き
    CHEST = 1 #	宝箱入り
    SHOP = 2 #	店売り
    BUGGAGE = 3 #キャラクタ所有
    EQUIP = 4 #	装備中
    STORAGE =	5 #	倉庫格納
    RUNESLOT = 6 #ルーンスロットに設定
    ABILITY = 7 #オプション効果（確定した値
    DEATH = 8 #死亡時の装備
    GARBAGE = 9 #削除待ち状態

class ItemType:
    WAND = 0
    SWORD = 1
    SPEAR = 2
    AXE = 3
    ROBE = 4
    LEATHER = 5
    CHAIN = 6
    PLATE = 7
    BUNGLE = 8
    ROUND = 9
    KITE = 10
    TOWER = 11
    SKILL = 15
    RUNE = 16
    INSTANT = 17
    TIMER = 18
    STOCK = 19
    INCREASE = 20
    EX = 21

    CATEGORY_CONSUME = 0
    CATEGORY_WEAPON = 1
    CATEGORY_ARMOR = 2
    CATEGORY_SHIELD = 3
    CATEGORY_RUNE = 4
    CATEGORY_SKILL = 5

    NAME = {
        0:"wand",
        1:"sword",
        2:"spear",
        3:"axe"
    }

    _TYPE_TO_CATEGORY_MAP = {
        # WEAPON
        WAND: CATEGORY_WEAPON,
        SWORD: CATEGORY_WEAPON,
        SPEAR: CATEGORY_WEAPON,
        AXE: CATEGORY_WEAPON,
        # ARMOR
        ROBE: CATEGORY_ARMOR,
        LEATHER: CATEGORY_ARMOR,
        CHAIN: CATEGORY_ARMOR,
        PLATE: CATEGORY_ARMOR,
        # SHIELD
        BUNGLE: CATEGORY_SHIELD,
        ROUND: CATEGORY_SHIELD,
        KITE: CATEGORY_SHIELD,
        TOWER: CATEGORY_SHIELD,
        # SKILL
        SKILL: CATEGORY_SKILL,
        # RUNE
        RUNE: CATEGORY_RUNE,
        # CONSUME
        INSTANT: CATEGORY_CONSUME,
        TIMER: CATEGORY_CONSUME,
        STOCK: CATEGORY_CONSUME,
        INCREASE: CATEGORY_CONSUME,
        EX: CATEGORY_CONSUME,
    }

    @classmethod
    def get_category(cls, item_type_id):
        """アイテム種別IDからカテゴリIDを取得する（辞書参照）"""
        return cls._TYPE_TO_CATEGORY_MAP.get(item_type_id)

    @classmethod
    def get_items_in_category(cls, category_id):
        """カテゴリIDに属するアイテム種別IDのリストを取得する"""
        return [
            item_type_id for item_type_id, cat_id in cls._TYPE_TO_CATEGORY_MAP.items()
            if cat_id == category_id
        ]

class BaseFunc:
    STORAGE = 0
    ALCHEMY = 1
    RITUAL = 2
    SHOP = 3
    BACKDOOR = 4
    DISCOVER = 5
    UPGRADE = 6

@unique
class DungeonType(IntEnum):
    ROOM = 0
    CAVE = 1
    MAZE = 2

class TileBlock:
    FLOOR = {"room":(0,0),"cave":(0,2),"maze":(0,4)}
    WALL = {"room":(2,0),"cave":(2,2),"maze":(2,4)}
    BLOCK = {"room":(4,0),"cave":(4,2),"maze":(4,4)}
    FENCE = {"room":(9,30),"cave":(9,30),"maze":(9,30)}
    FREE = (31,31)

@unique
class TilemapIndex(IntEnum):
    OBSTACLE=0 #障害物　当たり判定はこのマップ
    FLOOR=1 #床

class ImageAddress:
    DOOR=(72,240,16,16)
    STAIR=(88,240,16,16)
    BLUECHEST=(64,208,16,16)
    REDCHEST=(80,208,16,16)
    SPAWNER=(104,240,16,16)
    CURSOR=(32,248,8,8)
    BIGARROW=(200,240,16,16)
    LEVEL=(32,160,16,16)
    LEVELNUM=(96,160,16,16)
    EVASION=(0,160,16,16)
    MINIHEART=(0,232,8,8)
    MINIFOOD=(8,232,8,8)
    MINIEXP=(16,232,8,8)
    MINIGOLD=(24,232,8,8)
    MINISCORE=(32,232,8,8)
    MINILEVEL=(88,232,8,8)
    MINIKEY=(40,232,8,8)
    MINIMATTOCK=(48,232,8,8)
    MPBAR=(153,192,103,18)
    MANAPOT=(218,141,38,19)
    DIAGRAM=(96,224,32,8)
    SKILL={
        "ball":(0,88,8,8),
        "cannon":(8,88,24,24),
        "fan":(32,88,64,64),
        "area":(96,88,16,16),
        "front":(96,104,32,32),
        "shoot":(0,144,16,8),
        "slash":(128,80,64,32),
        "swing":(128,112,48,48),
        "shine":(48,240,8,8),
        "deadly":(0,96,8,16)
    }
    BUTTON={
        "a":(0,208,16,16),
        "b":(16,208,16,16),
        "x":(32,208,16,16),
        "y":(48,208,16,16),
        "ang":(184,18,16,12),
        "bng":(200,18,16,12),
        "xng":(184,34,16,12),
        "yng":(200,34,16,12),
        "L":(168,16,16,8),
        "R":(168,24,16,8)
    }
    BASE_FUNC=[
        (165,178,64,48,32,32),
        (305,94,96,48,32,32),
        (374,194,128,48,32,32),
        (249,178,160,48,32,32),
        (290,21,192,48,32,32),
        (113,26,224,48,32,32),
        (231,116,224,80,32,32),
        (231,116,224,80,32,32),
    ]
    ITEM=[
        (0,112,8,8),
        (8,112,8,16),
        (16,112,8,16),
        (24,112,8,16),

        (64,16,16,16),
        (80,16,16,16),
        (96,16,16,16),
        (112,16,16,16),

        (64,32,16,16),
        (80,32,16,16),
        (96,32,16,16),
        (112,32,16,16),

        (112,192,16,16),

        (0,176,16,16),
        (16,176,16,16),
        (32,176,16,16),
        (48,176,16,16),
        (64,176,16,16),
        (80,176,16,16),
        (96,176,16,16),
        (112,176,16,16),
        (128,176,16,16),
        (144,176,16,16),
        (160,176,16,16),
        (176,176,16,16),
        (192,176,16,16),
        (208,176,16,16),
        (224,176,16,16),
        (240,176,16,16),

        (0,192,16,16),
        (16,192,16,16),
        (32,192,16,16),
        (48,192,16,16),
        (64,192,16,16),
        (80,192,16,16),
        (96,192,16,16),

        (136,240,16,16),
        (152,240,16,16),
        (168,240,16,16),
        (184,240,16,16),
    ]

@unique
class GameState(IntEnum):
    TITLE=0
    SELECTCHARA=10; NAMEENTRY=15; OPENING=18
    SELECT_TUTRIAL=20; PREPARE_GAME=25; PREPARE_NEXTFLOOR=27; STARTFLOOR=29
    BASE=30; STORAGE=31; ALCHEMY=32; RITUAL=33; SHOP=34; BACKDOOR=35; UPGRADE=36; ENTRY=37; PREPARE_BASE=39
    DUNGEON=40; DUNGEON_CAVE=41; DUNGEON_MAZE=42
    MENU=60; MOBLIST=66
    BOSSBATTLE=70; LASTBOSS=75
    STAGECLEAR=80
    ENDING=90; GAMEOVER=99
