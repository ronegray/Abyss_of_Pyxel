import pyxel as px
import const as G_


def func_op900(): #剛力
    return None
def func_op901(base, val): #叡智
    return None
def func_op902(di, item_obj, val): #神速
    pass
def func_op903(di, item_obj, val): #絶技
    pass
def func_op904(di, item_obj, val): #致命
    pass
def func_op905(di, item_obj, val): #必殺
    pass
def func_op906(di, item_obj, val): #吸血
    pass
def func_op907(di, item_obj, val): #熟杖
    if item_obj.type_id != G_.ItemType.WAND:
        return 1
    weapon_val = (di.user.weapon.value * (1+val/100))
    return weapon_val
def func_op908(di, item_obj, val): #熟剣
    if item_obj.type_id != G_.ItemType.SWORD:
        return 1
    weapon_val = (di.user.weapon.value * (1+val/100))
    return weapon_val
def func_op909(di, item_obj, val): #熟槍
    if item_obj.type_id != G_.ItemType.SPEAR:
        return 1
    weapon_val = (di.user.weapon.value * (1+val/100))
    return weapon_val
def func_op910(di, item_obj, val): #熟斧
    if item_obj.type_id != G_.ItemType.AXE:
        return 1
    weapon_val = (di.user.weapon.value * (1+val/100))
    return weapon_val
def func_op911(di, item_obj, val): #爆炎
    pass
def func_op912(di, item_obj, val): #氷嵐
    pass
def func_op913(di, item_obj, val): #暴風
    pass
def func_op914(di, item_obj, val): #轟震
    pass
# def func_op915(di, item_obj, val): #骨断
#     pass
def func_op916(di, item_obj, val): #渾身
    pass
# def func_op917(di, item_obj, val): #炎上
#     pass
# def func_op918(di, item_obj, val): #鈍足
#     pass
# def func_op919(di, item_obj, val): #束縛
#     pass
# def func_op920(di, item_obj, val): #反衝
#     pass
def func_op921(di, item_obj, val): #破邪
    pass
def func_op922(di, item_obj, val): #掃滅
    pass
def func_op923(di, item_obj, val): #敏腕
    pass
def func_op924(di, item_obj, val): #省力
    pass
def func_op925(di, item_obj, val): #体力
    pass
def func_op926(di, item_obj, val): #鉄壁
    pass
def func_op927(di, item_obj, val): #剛体
    pass
def func_op928(di, item_obj, val): #縮地
    pass
def func_op929(di, item_obj, val): #持久
    pass
def func_op930(di, item_obj, val): #連跳
    pass
def func_op931(di, item_obj, val): #健脚
    pass
def func_op932(di, item_obj, val): #速癒
    pass
def func_op933(di, item_obj, val): #耐火
    pass
def func_op934(di, item_obj, val): #耐氷
    pass
def func_op935(di, item_obj, val): #耐風
    pass
def func_op936(di, item_obj, val): #耐地
    pass
# def func_op937(di, item_obj, val): #報復
#     pass
def func_op938(di, item_obj, val): #反射
    pass
# def func_op939(di, item_obj, val): #治癒
#     pass
# def func_op940(di, item_obj, val): #薬効
#     pass
def func_op941(di, item_obj, val): #巨体
    pass
def func_op942(di, item_obj, val): #抗炎
    pass
def func_op943(di, item_obj, val): #抗氷
    pass
def func_op944(di, item_obj, val): #抗風
    pass
def func_op945(di, item_obj, val): #抗地
    pass
def func_op946(di, item_obj, val): #消火
    pass
def func_op947(di, item_obj, val): #懐炉
    pass
def func_op948(di, item_obj, val): #柳風
    pass
def func_op949(di, item_obj, val): #熟服
    if item_obj.type_id != G_.ItemType.ROBE:
        return 1
    armor_val = (di.user.armor.value * (1+val/100))
    return armor_val
def func_op950(di, item_obj, val): #熟軽
    if item_obj.type_id != G_.ItemType.LEATHER:
        return 1
    armor_val = (di.user.armor.value * (1+val/100))
    return armor_val
def func_op951(di, item_obj, val): #熟鎖
    if item_obj.type_id != G_.ItemType.CHAIN:
        return 1
    armor_val = (di.user.armor.value * (1+val/100))
    return armor_val
def func_op952(di, item_obj, val): #熟鎧
    if item_obj.type_id != G_.ItemType.PLATE:
        return 1
    armor_val = (di.user.armor.value * (1+val/100))
    return armor_val
def func_op953(di, item_obj, val): #熟輪
    if item_obj.type_id != G_.ItemType.BUNGLE:
        return 1
    shield_val = (di.user.shield.value * (1+val/100))
    return shield_val
def func_op954(di, item_obj, val): #熟小
    if item_obj.type_id != G_.ItemType.ROUND:
        return 1
    shield_val = (di.user.shield.value * (1+val/100))
    return shield_val
def func_op955(di, item_obj, val): #熟中
    if item_obj.type_id != G_.ItemType.KITE:
        return 1
    shield_val = (di.user.shield.value * (1+val/100))
    return shield_val
def func_op956(di, item_obj, val): #熟大
    if item_obj.type_id != G_.ItemType.TOWER:
        return 1
    shield_val = (di.user.shield.value * (1+val/100))
    return shield_val
def func_op957(di, item_obj, val): #滅邪
    pass
def func_op958(di, item_obj, val): #縮地
    pass
def func_op959(di, item_obj, val): #吸魔
    pass
def func_op960(di, item_obj, val): #強欲
    pass
# def func_op961(di, item_obj, val): #大漁
#     pass
def func_op962(di, item_obj, val): #幸運
    pass
def func_op963(di, item_obj, val): #値引
    pass
def func_op964(di, item_obj, val): #割増
    pass
def func_op965(di, item_obj, val): #積載
    pass
def func_op966(di, item_obj, val): #開錠
    pass
def func_op967(di, item_obj, val): #頑丈
    pass
def func_op968(di, item_obj, val): #保持
    pass
def func_op969(di, item_obj, val): #天授
    pass
def func_op970(di, item_obj, val): #開放
    pass
def func_op971(di, item_obj, val): #小食
    pass
def func_op972(di, item_obj, val): #燃費
    pass
def func_op973(di, item_obj, val): #筋力
    pass
def func_op974(di, item_obj, val): #知力
    pass
def func_op975(di, item_obj, val): #器用
    pass
def func_op976(di, item_obj, val): #敏捷
    pass
def func_op977(di, item_obj, val): #耐久
    pass
def func_op978(di, item_obj, val): #幸運
    pass
def func_op979(di, item_obj, val): #持続
    pass
# def func_op980(di, item_obj, val): #天恵
#     pass
def func_op981(di, item_obj, val): #衝撃
    pass
