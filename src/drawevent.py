import pyxel as px
import const as G_


def gameover(user, counter, window):
    if px.play_pos(0) is not None:
        px.stop()

    if px.play_pos(3) is None and px.frame_count < counter + 1:
        px.play(3, G_.SNDEFX["dead"], loop=False)

    if px.frame_count < counter + 180:
        px.blt(user.address[0]-8, user.address[1]-8, G_.IMGIDX["CHAR"],
               32*(px.frame_count%16//4),user.image_source[1],user.image_source[2],user.image_source[3],
               colkey=3)
    elif px.frame_count == counter + 180:
        if px.rndi(0,99) >= 90:
            window.message_text = ["ワーン　シンジャッタノー！",
                                "キタイシテタノニ！！","ワリトヤクタタズネ・・・"]
        else:
            window.message_text = ["守護神の声が聞こえる…",
                               "　大丈夫、まだやり直せます","　　さあ、地上へ戻りましょう"]
    else:
        return True
    return False


def anger_boss(counter):
    if counter%32 in (0,3):
        px.rect(0,0,G_.WND_MAIN[2]+G_.WND_SIDE[2],G_.WND_MAIN[3]+G_.WND_SIDE[3], 10)

    match counter:
        case 0:
            px.stop()
            px.play(1, [G_.SNDEFX["tdr2"]], loop=False)
            return False
        case 60:
            while px.play_pos(1) is not None:
                pass
            px.play(1, [G_.SNDEFX["tdr1"]], loop=False)
            return False
        case _:
            if counter > 120:
                while px.play_pos(1) is not None:
                    pass
                return True
            else:
                return False


def defeat_boss(boss, counter):
    if counter < 16:
        px.blt(px.rndi(boss.address[0]-44,boss.address[0]-28),
               px.rndi(boss.address[1]-44,boss.address[1]-28),
               G_.IMGIDX["CHIP"], *G_.ImageAddress.SKILL["cannon"],
               colkey=0, scale=0.75, rotate=px.rndi(90,180))
        px.blt(px.rndi(boss.address[0]-44,boss.address[0]-28),
               px.rndi(boss.address[1],boss.address[1]+20),
               G_.IMGIDX["CHIP"], *G_.ImageAddress.SKILL["cannon"],
               colkey=0, scale=0.75, rotate=px.rndi(180,360))
        px.blt(px.rndi(boss.address[0],boss.address[0]+20),
               px.rndi(boss.address[1]-44,boss.address[1]-28),
               G_.IMGIDX["CHIP"], *G_.ImageAddress.SKILL["cannon"],
               colkey=0, scale=0.75, rotate=px.rndi(0,360))
        px.blt(px.rndi(boss.address[0],boss.address[0]+20),
               px.rndi(boss.address[1],boss.address[1]+20),
               G_.IMGIDX["CHIP"], *G_.ImageAddress.SKILL["cannon"],
               colkey=0, scale=0.75, rotate=px.rndi(0,180))
        px.blt(px.rndi(boss.address[0]-28,boss.address[0]+4),
               px.rndi(boss.address[1]-28,boss.address[1]+4),
               G_.IMGIDX["CHIP"], *G_.ImageAddress.SKILL["cannon"],
               colkey=0, scale=0.75, rotate=px.rndi(180,270))
        px.play(3, G_.SNDEFX["crush"])
        while px.play_pos(3) is not None:
            pass
        return False
    else:
        px.stop()
        px.play(3,G_.SNDEFX["defeat"], loop=False)
        return True


def scroll_map(stage):
    match stage.scroll_direction:
        case 0:
            px.bltm(0,-stage.scroll_counter, 1, 0,0, G_.WND_MAIN[2],G_.WND_MAIN[3])
            px.bltm(0,G_.WND_MAIN[3]-stage.scroll_counter, 0, 0,0, G_.WND_MAIN[2],stage.scroll_counter)
        case 1:
            px.bltm(stage.scroll_counter,0, 1, 0,0, G_.WND_MAIN[2]-stage.scroll_counter,G_.WND_MAIN[3])
            px.bltm(0,0, 0, G_.WND_MAIN[3]-stage.scroll_counter,0, stage.scroll_counter,G_.WND_MAIN[3])
        case 2:
            px.bltm(-stage.scroll_counter,0, 1, 0,0, G_.WND_MAIN[2],G_.WND_MAIN[3])
            px.bltm(G_.WND_MAIN[2]-stage.scroll_counter,0, 0, 0,0, stage.scroll_counter,G_.WND_MAIN[3])
        case 3:
            px.bltm(0,stage.scroll_counter, 1, 0,0, G_.WND_MAIN[2],G_.WND_MAIN[3]-stage.scroll_counter)
            px.bltm(0,0, 0, 0,G_.WND_MAIN[3]-stage.scroll_counter,G_.WND_MAIN[2],stage.scroll_counter)

    stage.scroll_counter += 16
    if stage.scroll_counter >= G_.WND_MAIN[2]:
        stage.scroll_counter = 0
        return True
    return False


def opening(window, step):
    match step:
        case 0:
            window.message_text = ["迷宮都市",
                                   "",
                                   "深い森の中に姿をひそめていた迷宮が見つかったのは",
                                   "今からおよそ１０年前",
                                   ""]
        case 1:
            window.message_text = ["世紀の発見は瞬く間に世の知るところとなり、",
                                   "凄まじい人数が集まる事となった",
                                   "",
                                   "それまで何もない深い森だった場所は、",
                                   "切り拓かれ、また切り拓かれていき"]
        case 2:
            window.message_text = ["いつの間にか巨大な城塞へとその姿を変える",
                                   "",
                                   "誰が呼んだか、今では皆がここをそう呼ぶ",
                                   "",
                                   "「迷宮都市」と"]
        case 3:
            window.message_text = ["探求心と功名心、そして欲望に駆られた者達は",
                                   "次々と迷宮へ吸い込まれていき・・・",
                                   "",
                                   "そしてその多くは帰ってこなかった",
                                   ""]
        case 4:
            window.message_text = ["戻ってきた一握りの者達から噂は広まる",
                                   "　迷宮には珍しい武具が眠っている",
                                   "　迷宮には恐ろしい魔物たちが潜んでいる",
                                   "　迷宮は入る度にその姿を変える",
                                   "噂に釣られ、居なくなるより多くの人が流れ込む"]
        case 5:
            window.message_text = ["あなたもそんな大勢の中の一人だ",
                                   "まだ扱いの覚束ない真新しい武具を纏い",
                                   "しかし自分だけはと青い無謀さを勇気と履き違えたまま",
                                   "",
                                   "今まさに迷宮の入口へと足を踏み入れた"]
        case 6:
            return True
    return False


def interlude(window, step):
    match step:
        case 0:
            window.message_text = ["",
                                   "とどめの一撃を叩きこむ！",
                                   "",
                                   "無限のような闘いに、ようやく終止符を打つ事ができた",
                                   "",
                                   "またしても亡骸は光を放ち　そして消える",
                                   "",
                                   "・・・なんだろう　力が湧いてくるような気がする",
                                   "",
                                   "以前は気付かなかったが、強敵との闘いのあとは",
                                   "ひときわ強大なマナを手に入れているかも知れない",
                                   ""]
        case 1:
            window.message_text = ["",
                                   "転移の魔法陣が目の前にある",
                                   "",
                                   "荷物を失いたくなければ引き返すべきだろう",
                                   "大したものが無ければそのまま進んでもいい",
                                   "",
                                   "翼の長靴があれば、かなり安全に帰還できると聞く",
                                   "そちらに期待するのもいいだろう",
                                   "",
                                   "あなたのよろしいように",
                                   "",
                                   ""]
        case 2:
            window.message_text = ["",
                                   "転移の魔法陣が目の前にある",
                                   "",
                                   "荷物を失いたくなければ引き返すべきだろう",
                                   "大したものが無ければそのまま進んでもいい",
                                   "",
                                   "翼の長靴があれば、かなり安全に帰還できると聞く",
                                   "そちらに期待するのもいいだろう",
                                   "",
                                   "あなたのよろしいように",
                                   "",
                                   "魔法陣を踏む：Ｌ　次のＬＥＶＥＬへ：Ｒ"]
            return True
    return False


def interlude_first(window, step):
    match step:
        case 0:
            window.message_text = ["",
                                   "長い戦いに決着の時が訪れた",
                                   "",
                                   "待て　何か様子がおかしい",
                                   "戦いが終わるや否や、周囲の景色が歪み始めた",
                                   "",
                                   "周囲の景色が滲んだ水彩画のようにぼやけていき",
                                   "",
                                   "苔むした石の遺構が浮かび上がる",
                                   "",
                                   "一体どういう事なのだろうか",
                                   ""]
        case 1:
            window.message_text = ["",
                                   "幻の如く揺らめいた広間の中に",
                                   "揺らめく紋様が浮かび上がっていた",
                                   "",
                                   "ダンジョンのどこかに転移の魔法陣があると聞く",
                                   "目の前の紋様がそれなのだろうか",
                                   "",
                                   "転移魔法陣を使えば、荷物を失う事なく",
                                   "地上に戻る事ができるという",
                                   "",
                                   "今後の為にも、一度試しておくべきだろう",
                                   "",
                                   ""]
        case 2:
            window.message_text = ["",
                                   "",
                                   "",
                                   "",
                                   "",
                                   "意を決して魔法陣へと足を踏み入れた"]
        case 3:
            return True
    return False


def interlude_silence(window, step):
    match step:
        case 0:
            window.message_text = ["",
                                   "巨大な敵が居た部屋に辿り着いた",
                                   "",
                                   "まるで何事もなかったかのように",
                                   "ひっそりと静まりかえっている",
                                   "",
                                   "",
                                   "ただ魔法陣だけが音もなくそこに在る",
                                   "",
                                   "ここで一度拠点へ戻るのもいいだろう",
                                   "",
                                   ""]
        case 1:
            window.message_text = ["",
                                   "巨大な敵が居た部屋に辿り着いた",
                                   "",
                                   "まるで何事もなかったかのように",
                                   "ひっそりと静まりかえっている",
                                   "",
                                   "",
                                   "ただ魔法陣だけが音もなくそこに在る",
                                   "",
                                   "ここで一度拠点へ戻るのもいいだろう",
                                   "",
                                   "魔法陣を踏む：Ｌ　次のＬＥＶＥＬへ：Ｒ"]
            return True
    return False


def interlude_end(window, step):
    match step:
        case 0:
            window.message_text = ["",
                                   "強大な敵との戦いが終わりを告げる",
                                   "",
                                   "",
                                   "いつもと何か様子が違うようだ",
                                   "",
                                   "先へと進む道が見当たらない",
                                   "ここが終着点という事だろうか？",
                                   "",
                                   "それにしてはあまりに呆気ない",
                                   "何か財宝が見つかった訳でもない",
                                   ""]
        case 1:
            window.message_text = ["",
                                   "それにしても暑い",
                                   "地の底とは熱を秘めたものなのか",
                                   "",
                                   "",
                                   "転移魔法陣はいつも通り現れている",
                                   "これ以上ここに居ても仕方ないだろう",
                                   "",
                                   "",
                                   "後ろ髪を引かれるようにも思いつつ",
                                   "魔法陣へと足を踏み入れた",
                                   ""]
        case 2:
            window.message_text = ["",
                                   "ここまで遊んで下さってありがとうございます",
                                   "",
                                   "このゲームのステージはここが最後でした",
                                   "",
                                   "通常のプレイでは到底辿り着けない想定なので",
                                   "",
                                   "このメッセージをご覧になった方は",
                                   "",
                                   "この画面のスクショを開発者までお送り下さい",
                                   "",
                                   "何かの景品を用意しておこうと思います"]
        case 3:
            return True
    return False


def ending(window, step):
    match step:
        case 0:
            window.message_text = ["これまでになく強大な敵だった",
                                   "",
                                   "打ち勝つ事が出来たのは奇跡と言えるだろう",
                                   "",
                                   "何度か命を失う覚悟をする瞬間はあった",
                                   "",
                                   "しかし、その空隙を突いた攻撃は受けなかった",
                                   "",
                                   "手加減？情け？魔物から？考えてみれば確かに、",
                                   "",
                                   "人の姿に似てはいたが、知性を持っていた・・・？",
                                   ""]
        case 1:
            window.message_text = ["どこからともなく守護神の声が響いてくる",
                                   "",
                                   "よくここまで辿り着きました",
                                   "永遠とも思える時を隔てて、ようやく星の核を、",
                                   "その力を手にする事が出来そうです",
                                   "",
                                   "あなたの役目はもう終わりました",
                                   "どこへなりと行くがよいでしょう",
                                   "",
                                   "あなたの纏う武具は人の身には過ぎた品ですが",
                                   "ここまでの働きの褒美として差し上げます",
                                   ""]
        case 2:
            return True
    return False


class ShootingStar:
    def __init__(self):
        dx = px.rndf(-1, 1)
        dy = px.rndf(-1, 1)
        while dx == 0 and dy == 0:
            dx = px.rndf(-1, 1)
            dy = px.rndf(-1, 1)
        length = (dx * dx + dy * dy) ** 0.5
        dx /= length
        dy /= length
        speed = px.rndf(2, 4)
        self.vx = dx * speed
        self.vy = dy * speed
        self.x = px.width//2
        self.y = px.height//2
        self.life = 200
        self.colors = [7,7,7,7,7,7,7,7,7,15,15,15,15,15,15,15,6,6,6,6,6,6,14,14,14,14,14,13,13,13,13,10,10,10,9,9,2]
        self.color = self.colors[px.rndi(0,len(self.colors)-1)]
        self.size = px.rndf(0.1,1)

        # 尾の履歴（最大10個）
        self.trail = []

    def update(self):
        # 履歴を追加
        self.trail.append((self.x, self.y))
        if len(self.trail) > 3:  # 尾の長さ
            self.trail.pop(0)

        self.x += self.vx
        self.y += self.vy
        self.life -= 1
        return (
            self.life <= 0
            or self.x < -10 or self.x > G_.WND_MAIN[2] + G_.WND_SIDE[2] + 10
            or self.y < -10 or self.y > G_.WND_MAIN[3] + 10
        )

    def draw(self):
        # 尾を古い順に描画（色をだんだん暗く）
        for i, (tx, ty) in enumerate(self.trail):
            col = 7 - i // 2  # 段階的に色を暗く
            if col < 1:
                col = 1
            px.circ(tx, ty, 0.001, col)

        px.circ(self.x, self.y, self.size, self.color)
