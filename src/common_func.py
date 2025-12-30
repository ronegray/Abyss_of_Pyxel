import pyxel as px
from random import seed, sample, shuffle
import json
import pickle
import gzip
import re
import const as G_
import menu


def array_to_csv(array):
    '''デバッグ用：リストをCSV化'''
    import csv
    with open("data.csv", "w", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerows(array)

# 保存対象外にする属性のパターン
# 1. "di": 依存性の注入コンテナ
# 2. "^image_": Pyxelの画像オブジェクト (image_baseなど)
# 3. ".*(_window|_menu)$": 末尾が_window, _menuのUIインスタンス
SAVE_EXCLUDE_PATTERN = re.compile(r"^(di|image_.*)|.*\.di\..*|.*(_window|_menu|base_mainmenu)$")

def get_clean_state(instance):
    """pickle保存用に、インスタンスから除外対象の属性を削除した辞書を返す"""
    state = instance.__dict__.copy()
    keys_to_delete = [k for k in state.keys() if SAVE_EXCLUDE_PATTERN.search(k)]
    for key in keys_to_delete:
        del state[key]
    return state


def generate_random_iterater(start:int, end:int, num:int):
    '''0～numの範囲の整数をランダムに並べ替えた数列イテレータを返却'''
    seed()
    return iter(sample(range(start,end),k=num))


def convert_random_iterater(numlist:list[int,]):
    '''整数のリストをランダムに並べ替えたイテレータを返却'''
    shuffle(numlist)
    return iter(numlist)


def check_collision_hitbox(x1,y1,w1,h1, x2,y2,w2,h2):
    '''矩形二つの接触判定(AABB)'''
    return abs(x1 - x2) <= (w1 + w2) / 2 and abs(y1 - y2) <= (h1 + h2) / 2


def get_tileinfo(x:float, y:float, layer:int):
    '''画面内の指定アドレスのタイルマップチップの情報取得
    type 0:xy指定値(タイル座標) 1:画面座標から変換 2:マップ全体座標から変換'''
    x //= 8
    y //= 8
    return px.tilemaps[layer].pget(x, y)


def check_hit_tile(target, tilemap_id, check:list, checktype:bool=None):
    '''移動不可タイルとの接触チェック'''
    destination_address = [int(target.address[0] + G_.CHARA_DIR[target.direction][0]),
                           int(target.address[1] + G_.CHARA_DIR[target.direction][1])]
    #当たり判定は16ドットキャラの中心ではなく足元寄りの8x8ドット(狭い範囲の通行の為)
    corners = [(destination_address[0]-3,destination_address[1]-2), #左上
               (destination_address[0]+3,destination_address[1]-2), #右上
               (destination_address[0]-3,destination_address[1]+5), #左下
               (destination_address[0]+3,destination_address[1]+5), #右下
    ]
    result = False
    for i,[x,y] in enumerate(corners):
        if target.direction == 0 and i in (0,1):
            continue
        elif target.direction == 1 and i in (1,3):
            continue
        elif target.direction == 2 and i in (0,2):
            continue
        elif target.direction == 3 and i in (2,3):
            continue
        tile_x = x // 8
        tile_y = y // 8
        if checktype: #True X軸のみ
            result = result or (px.tilemaps[tilemap_id].pget(tile_x, tile_y)[0] in check)
        elif checktype is False: #False Y軸のみ
            result = result or (px.tilemaps[tilemap_id].pget(tile_x, tile_y)[1] in check)
        else: #None　デフォルト　XY座標
            result = result or (px.tilemaps[tilemap_id].pget(tile_x, tile_y) in check)
    return result


def get_button_state():
    '''入力キー情報を取得（複数同時押し可能）'''
    repeat = [int(G_.GAME_FPS//4), int(G_.GAME_FPS//4)]
    btn = {
        "u": px.btn(px.KEY_W) or px.btn(px.GAMEPAD1_BUTTON_DPAD_UP) or px.btn(px.KEY_UP),
        "l": px.btn(px.KEY_A) or px.btn(px.GAMEPAD1_BUTTON_DPAD_LEFT) or px.btn(px.KEY_LEFT),
        "r": px.btn(px.KEY_D) or px.btn(px.GAMEPAD1_BUTTON_DPAD_RIGHT) or px.btn(px.KEY_RIGHT),
        "d": px.btn(px.KEY_S) or px.btn(px.GAMEPAD1_BUTTON_DPAD_DOWN) or px.btn(px.KEY_DOWN),
        "a": px.btnp(px.KEY_RETURN, *repeat) or px.btnp(px.GAMEPAD1_BUTTON_A, *repeat) or px.btnp(px.KEY_Z, *repeat),
        "b": px.btnp(px.KEY_ESCAPE, *repeat) or px.btnp(px.GAMEPAD1_BUTTON_B, *repeat),
        "x": px.btnp(px.KEY_RIGHTBRACKET, *repeat) or px.btnp(px.GAMEPAD1_BUTTON_X, *repeat) or px.btnp(px.KEY_X, *repeat),
        "y": px.btnp(px.KEY_SPACE, *repeat) or px.btnp(px.GAMEPAD1_BUTTON_Y, *repeat) or px.btnp(px.KEY_C, *repeat),
        "L": px.btn(px.KEY_LSHIFT) or px.btn(px.GAMEPAD1_BUTTON_LEFTSHOULDER),
        "R": px.btn(px.KEY_RSHIFT) or px.btn(px.GAMEPAD1_BUTTON_RIGHTSHOULDER),
        "E": px.btn(px.KEY_BACKSPACE) or px.btn(px.GAMEPAD1_BUTTON_BACK),
        "S": px.btn(px.KEY_F1) or px.btn(px.GAMEPAD1_BUTTON_START),
    }
    return btn


def fill_tilemap(layer:int, tile:tuple, tile_right:int=256, tile_under:int=256,
                 width_start:int=0, height_start:int=0):
    '''指定のタイルIDで(width_start,height_start ～ tile_right,tile_under)の範囲でタイルマップを埋める'''
    tilemap = px.tilemaps[layer].data_ptr()
    u, v = tile  # Pyxel Editor上でのタイルID
    for y in range(height_start, tile_under):
        for x in range(width_start, tile_right):
            i = (y * 256 + x) * 2
            tilemap[i] = u      # u座標
            tilemap[i + 1] = v  # v座標


def read_json(filename:str):
    '''jsonファイルの読み込み（非デバッグ時は要encrypt済ファイル）'''
    if G_.IS_DEBUG:
        with open(filename, "r", encoding = "UTF-8") as f:
            data = json.load(f)
        return data
    else:
        return decrypt_json(f"{filename}.bin")


def decrypt_json(filename:str):
    '''暗号圧縮jsonファイルの読み込み'''
    try:
        with open(filename, "rb") as f:
            data = f.read()

        if not data.startswith(G_.DATA_HEADER):
            error_message(["Invalid json data"])

        encrypted = data[len(G_.DATA_HEADER):]
        compressed = bytes(b ^ G_.ENCRYPT_KEY[i % len(G_.ENCRYPT_KEY)] for i, b in enumerate(encrypted))
        raw = gzip.decompress(compressed)
        json = pickle.loads(raw)
    except Exception:
        error_message(["Invalid json data"])

    return json


def error_message(message:Exception):
    '''エラー落ち抑止用メッセージ表示'''
    errmsg_window = menu.Window(16,16,px.width-32,px.height-32)
    errmsg_window.message_text = message
    errmsg_window.message_text.append("決定/キャンセルボタンでタイトルに戻ります")
    px.flip()
    while errmsg_window.update():
        px.flip()
        errmsg_window.draw()
        errmsg_window.draw_message()
