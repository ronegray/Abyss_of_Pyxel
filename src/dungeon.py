import pyxel as px
import const as G_
from random import choice as random_choice, choices as random_choices
import common_func as comf
import item


class Floor:
    def __init__(self, di, depth_level:int):
        item.ItemManager.garbage_correct()
        self.di = di 
        self.di.dungeon = self
        self.ref_user = di.user #ユーザインスタンス
        self.is_nextlevel = False
        self.depth_level = depth_level

        self.floor_tier = self.determine_difficulty_tier_polynomial()

        if self.di.flg.is_first:
            match self.depth_level:
                case 1:
                    num_rooms = 1
                case 2|3:
                    num_rooms = 2
                case 4|5:
                    num_rooms = 3
                case 6|7:
                    num_rooms = 4
                case 8:
                    num_rooms = 5
                case _:
                    num_rooms = 6
        else:
            num_rooms = 1+self.depth_level//2 if self.depth_level <= 5 else (
                            self.depth_level//2 if self.depth_level <= 20 else (
                                10+self.depth_level//20 if self.depth_level <= 100 else (
                                    15+self.depth_level//200) ) )
        num_entrance = 1 if self.depth_level <= G_.SKIPSTAIR_APPEAR else 2 #スキップ用階段の有無
        self.stairs = [] #Stairオブジェクト（ダンジョン内で通常１、スキップ１）

        self.rooms = [] #Roomオブジェクト一覧
        self.now_room_pos = (0,0) #現在の部屋位置
        self.now_room = None #roomsから現在選択されるオブジェクトへの参照
        self.floortype = list(G_.TileBlock.FLOOR.keys())[px.rndi(0,len(G_.TileBlock.FLOOR.keys())-1)] #マップチップタイプ

        #床用タイルマップ生成
        self.generate_tilemap_floor()

        #ダンジョン構造生成
        self.rooms_structure = self.generate_dungeon(num_rooms, num_entrance)
        #隣室の有無が確定してからRoomオブジェクト生成
        for room in self.rooms_structure:
            self.rooms.append(Room(self.di, room))
            #事前生成した階段をroomオブジェクトに定義
            for stair in self.stairs:
                if stair.pos_room == room:
                    self.rooms[-1].set_stair(stair)
            # 配置順序: 階段(上記) -> 宝箱 -> 床置き -> 障害物
            self.rooms[-1].generate_chest()
            self.rooms[-1].generate_dropitem()
            self.rooms[-1].generate_blocks(min(120,
                int((G_.TILEMAP_WIDTH+self.di.app.depth_level)*0.5)+10))
            
            # プレイヤーの初期位置設定（スタート地点）
            if room == (0,0):
                # プレイヤーもオブジェクトと重ならない安全な場所に配置
                address = self.rooms[-1].get_random_free_pixel_address()
                self.di.user.address = [address["x"],address["y"]]

        if depth_level%5 == 0:
            # foodroom = random_choice(self.rooms_structure)
            if self.di.flg.is_first:
                foodroom = self.rooms_structure[-1]
            else:
                foodroom = random_choice(self.rooms_structure)
            [room.generate_food() for room in self.rooms
            if room.pos_room == foodroom]
        if self.di.flg.is_first:
            if depth_level == 4:
                 self.rooms[0].generate_mattock()
            if depth_level == 5:
                self.rooms[0].generate_key()
            if depth_level == 6:
                self.rooms[0].generate_chest(True)

        self.now_room = self.rooms[self.rooms_structure.index(self.now_room_pos)]
        self.now_room.set_tilemap(G_.TilemapIndex.OBSTACLE)
        self.dungeon_id = 0
        self.monsters = None

    def determine_difficulty_tier_polynomial(self):
        # 難易度決定のパラメータ
        # 階層の区切り（例: 0-9階は0, 10-19階は1, ...）
        depth_base = self.depth_level // 10
        # 適正難易度の中央値 (μ)
        base_tier = depth_base
        if self.di.flg.is_first:
            maxtier = 0
        else:
            maxtier = min(base_tier + (1 if px.rndi(0,100)<self.depth_level else 0), 9)
        min_available_tier = min(self.depth_level//25,8)
        candidates = list(range(min_available_tier, maxtier+1))

        # 1. 重みの計算（多項式による急激な減少）
        # 中央値 (base_tier) から1離れるごとに重みが減少するベースレート
        # この値が小さいほど、中央値への集中度が高まります。（例: 0.3）
        WEIGHT_DECAY_RATE = 0.85
        # 距離のべき乗 (指数)
        # この値が大きいほど、中央値から離れる重みの減少が急激になります。（例: 3）
        DISTANCE_POWER = 1.5# - self.depth_level // 15
        
        weights = []
        for tier in candidates:
            tier *= 1.5 if tier > base_tier else 1
            distance = abs(tier - base_tier)
            # 中央値との距離(distance)に応じて重みを計算
            # 重み W = 1.0 - (減衰率 * 距離^べき乗)
            # ただし、重みが0未満にならないように max(0.01, ...) でクリップします。
            # 中央値 (distance=0) の時: weight = 1.0
            # それ以外: weight は distance に応じて急激に減少
            # 減衰率を調整し、1.0から引くことで、tier=base_tierで1.0を保ちます
            decay_factor = WEIGHT_DECAY_RATE * (distance ** DISTANCE_POWER)
            
            weight = max(0.01, 1.0 - decay_factor)
            weights.append(weight)

        # 2. 重み付きランダム選択
        if not candidates:
            return 0
            
        return random_choice(random_choices(candidates, weights=weights, k=1))

    #床タイルマップの生成（床を全部埋める）
    def generate_tilemap_floor(self):
        px.tilemaps[G_.TilemapIndex.FLOOR].cls((31,31))
        for dy in range(0, G_.TILEMAP_WIDTH, 2):
            for dx in range(0, G_.TILEMAP_HEIGHT, 2):
                refer = G_.TileBlock.FLOOR[self.floortype]
                tile_id = (refer,(refer[0],refer[1]+1),(refer[0]+1,refer[1]),(refer[0]+1,refer[1]+1))
                px.tilemaps[G_.TilemapIndex.FLOOR].pset(dx, dy, tile_id[0])
                px.tilemaps[G_.TilemapIndex.FLOOR].pset(dx, dy+1, tile_id[1])
                px.tilemaps[G_.TilemapIndex.FLOOR].pset(dx+1, dy, tile_id[2])
                px.tilemaps[G_.TilemapIndex.FLOOR].pset(dx+1, dy+1, tile_id[3])

    #ダンジョン構造（部屋の繋がり）を生成
    def generate_dungeon(self, num_rooms:int, num_entrance:int):
        dungeon_rooms = [(0, 0)]
        new_block = (0, 0)
        #num_roomに応じて部屋(new_block)の追加
        while len(dungeon_rooms) < num_rooms:
            base_x, base_y = random_choice(dungeon_rooms)
            dx, dy = random_choice(G_.CHARA_DIR)
            new_block = (base_x + dx, base_y + dy)
            if new_block not in dungeon_rooms:
                dungeon_rooms.append(new_block)
        #階段は事後生成のRoomに割り付ける為、ここでは対象の部屋アドレスのみを定義
        self.stairs = [Stair(new_block)] #最後に追加した部屋が次のフロアへの階段
        if self.depth_level > G_.SKIPSTAIR_APPEAR\
            and px.rndi(0,1024) < self.depth_level: #指定以上のレベルではスキップ用階段を設置
            candidate_rooms = [r for r in dungeon_rooms if r != new_block]
            if candidate_rooms:
                self.stairs.append(Stair(random_choice(candidate_rooms), True))

        return dungeon_rooms
    
    def move_room(self, direction:int):
        destination_room_pos = (self.now_room_pos[0] + G_.CHARA_DIR[direction][0],
                               self.now_room_pos[1] + G_.CHARA_DIR[direction][1])
        if destination_room_pos in self.rooms_structure:
            self.now_room_pos = destination_room_pos
            self.now_room = self.rooms[self.rooms_structure.index(self.now_room_pos)]
            if self.now_room.is_unlocked is False:
                px.play(2, G_.SNDEFX["lock"], resume=True)
            for skill in self.di.user.skillbook.values():
                if skill is not None:
                    skill.clear_activeskill()
            self.now_room.set_tilemap(G_.TilemapIndex.OBSTACLE)
            self.monsters.set_mobgroup_index(self.now_room_pos)
            #極稀にスポナーは復活する　深いLEVEL程頻度は高い
            if self.monsters.get_spawner_state():
                if px.rndi(1,1000) <= self.depth_level:
                    self.monsters.revive_spawner()
                    self.monsters.spawn_monster(self.depth_level)
            self.is_ondoor = True
        else:
            px.play(3,G_.SNDEFX["don"], resume=True)
            return False

    def update(self, scene=40):
        #アイテムマネージャからの通知確認（床置きアイテムの発生）
        relay = item.ItemManager.notice_relay()
        if len(relay):
            self.now_room.drop_items += relay

        #全滅時のルーム封鎖解除
        if self.now_room.is_unlocked is False and self.now_room.is_defeat:
            self.now_room.open_fence()
            self.now_room.is_unlocked = True

        #ルーム更新（オブジェクト当たり判定等）
        self.now_room.update()
        if self.is_nextlevel:
            return

        #モンスター行動
        self.monsters.update()
        #モンスタースポーン
        novice = 2 if self.di.flg.is_first else 1
        if px.frame_count%(G_.GAME_FPS * G_.REPOP_SECONDS * novice) == 0:
            self.monsters.spawn_monster(self.depth_level)


    def draw(self, scene=40):
        #マップ描画
        self.now_room.draw()
        #砂時計の効果エフェクト
        if scene == 40:
            item.func_effect_item11(self.monsters.ref_user)
        #モンスター描画
        self.monsters.draw(scene)

    #ボスステージ描画（メニュー表示時背景用の共通化目的で関数化）
    @staticmethod
    def draw_boss_stage(scene=None):
        px.bltm(0,0, 1, 0,0, G_.WND_MAIN[2]+G_.WND_SIDE[2],G_.WND_MAIN[3],colkey=0)


class Stair:
    def __init__(self, pos_room:tuple[int,int], flag_skip:bool=False):
        self.pos_room = pos_room
        self.address = {}
        self.is_skip = flag_skip
        self.next_level = px.rndi(2,12) if self.is_skip else 1

    def draw(self):
        px.blt(self.address["x"]-8, self.address["y"]-8, G_.IMGIDX["CHIP"],
               *G_.ImageAddress.STAIR, colkey=0)
        if self.is_skip:
            offset = px.frame_count%16
            px.rectb(self.address["x"]-8+offset/2,self.address["y"]-8+offset/2,
                    16-offset, 16-offset, 22)


class BlueChest:
    def __init__(self, address:dict, item_uuid, item_num):
        self.address = address
        self.is_opened = False
        self.item_uuid = item_uuid
        self.item_num = item_num   

    def draw(self):
        if self.is_opened is False:
            px.blt(self.address["x"]-8,self.address["y"]-8, G_.IMGIDX["CHIP"],
                   *G_.ImageAddress.BLUECHEST, colkey=0)


class Room:
    def __init__(self, di, pos_room:tuple[int,int]):
        self.di = di
        self.pos_room = pos_room
        self.virtual_map = [] #仮想タイルマップ配列
        self.obstacles = [] #障害物オブジェクト
        self.chest = [] #宝箱オブジェクト 部屋に一つ
        self.drop_items = [] #床置きアイテムオブジェクト
        self.occupied_address = [] #オブジェクト配置により占有済のアドレス
        self.occupied_tiles = set() #オブジェクト配置により占有済のタイル
        self.stair = None #Stairオブジェクト（階段）
        self.is_defeat = False #室内一掃フラグ
        self.is_unlocked = False #封鎖解放済フラグ
        #パーク：初期封鎖確率解除
        rune_effect = self.di.user.get_rune_effect(G_.RuneList.RELEASE)
        if rune_effect is not None:
            if px.rndi(0,99) < (rune_effect[1]+min(50,self.di.user.luck//100)):
                self.is_defeat = True

        self.is_on_drop = False #床置き接触フラグ
        self.is_on_chest = False #宝箱接触フラグ
        
        # 1. まず外周ブロックとフェンスの配置を行う
        self.generate_virtual_tilemap_base()
        
        # ルールA: 扉ブロックの周囲を占有領域として登録する
        self.protect_fence_area()


    def is_position_valid(self, address: dict) -> bool:
        '''指定されたピクセル座標が配置可能エリア内かつ、既存オブジェクトと重ならないか判定'''
        # 1. 外周（壁）チェック
        # get_random_pixel_address で使用している計算式と同じ範囲制限を適用
        block_size = 16
        object_size = G_.CHIP_PIXEL * 2
        min_pix = block_size + (object_size // 2)
        max_pix = G_.WND_MAIN[2] - (block_size + (object_size // 2))

        if not (min_pix <= address["x"] <= max_pix and min_pix <= address["y"] <= max_pix):
            return False

        # 2. 占有タイル重複チェック (ルールA, B適用)
        if self.is_overlap_with_occupied(address):
            return False

        return True

    def get_random_pixel_address(self):
        '''外周ブロックに接触しない範囲のピクセルアドレスを{"x":x,"y":y}の形で返却'''
        block_size = 16
        object_size = G_.CHIP_PIXEL*2
        min_pix = block_size+(object_size//2)
        max_pix = G_.WND_MAIN[2]-(block_size+(object_size//2))

        rand_x = px.rndi(min_pix, max_pix)
        rand_y = px.rndi(min_pix, max_pix)
        return {"x": rand_x, "y": rand_y}

    def get_occupied_tile(self, address):
        '''指定アドレス(中心座標)へのオブジェクト配置で占有されるタイルマップアドレスの取得'''
        tiles = set()
        # アドレスはオブジェクトの中心。16x16の範囲を計算
        half_size = G_.CHIP_PIXEL # 8
        
        # 左上と右下のピクセル座標（境界値を含む）
        left_px = address["x"] - half_size
        top_px = address["y"] - half_size
        right_px = address["x"] + half_size - 1
        bottom_px = address["y"] + half_size - 1

        # 該当するタイル座標範囲を計算
        tile_left = left_px // G_.CHIP_PIXEL
        tile_right = right_px // G_.CHIP_PIXEL
        tile_top = top_px // G_.CHIP_PIXEL
        tile_bottom = bottom_px // G_.CHIP_PIXEL
        
        # 範囲内の全タイルをセットに追加
        for ty in range(tile_top, tile_bottom + 1):
            for tx in range(tile_left, tile_right + 1):
                tiles.add((tx, ty))
        return tiles
    
    def set_occupied_info(self, address_dict):
        '''指定のアドレス辞書を使って占有アドレスと占有タイルアドレスを更新'''
        for address in self.get_occupied_tile(address_dict):
            self.occupied_tiles.add(address)
        self.occupied_address.append(address_dict)

    def is_overlap_with_occupied(self, address_dict):
        '''指定のアドレスが既存の占有タイルと重なるかチェック (ルールB)'''
        candidate_tiles = self.get_occupied_tile(address_dict)
        # 積集合があれば重複しているとみなす
        if not candidate_tiles.isdisjoint(self.occupied_tiles):
            return True
        return False

    def get_random_free_pixel_address(self, align_to_tile=False):
        '''既存オブジェクトとの衝突判定(タイルベース)を行いながらピクセルアドレスを取得'''
        retry_max = 1000
        for _ in range(retry_max):
            candidate = self.get_random_pixel_address()
            
            # タイルグリッドにスナップする場合（障害物など）
            if align_to_tile:
                # 16pxグリッドの偶数タイル中心などに合わせる場合
                # ここでは単純に8px単位のタイル境界に合わせる
                # 中心座標をタイルの中心(8n+4)にするか、2x2ブロックの中心(16n+8)にするか
                # Obstacleの仕様に合わせて調整（Obstacleは中心座標を受け取り、pos_tileを計算）
                # ここでは直前のピクセル取得結果を、最も近い16pxブロックの中心に補正する例
                candidate["x"] = (candidate["x"] // 16) * 16 + 8
                candidate["y"] = (candidate["y"] // 16) * 16 + 8

            # ルールB: タイル単位で重なりチェック
            if not self.is_overlap_with_occupied(candidate):
                self.set_occupied_info(candidate)
                return candidate

        # 配置できない場合は、例外ではなく安全な場所（画面外など）を返すか、エラーとする
        # ここではエラー送出を維持
        raise RuntimeError("No free pixel address found")

    def protect_fence_area(self):
        '''ルールA: 仮想マップ上のフェンス(扉)を探し、その周囲を占有済みとする'''
        # generate_virtual_tilemap_base で生成されたマップを参照
        tm = px.tilemaps[G_.TilemapIndex.OBSTACLE]
        refer_fence = G_.TileBlock.FENCE[self.di.dungeon.floortype]
        # フェンスを構成する4つのタイルIDセット
        fence_ids = {
            refer_fence, 
            (refer_fence[0], refer_fence[1]+1), 
            (refer_fence[0]+1, refer_fence[1]), 
            (refer_fence[0]+1, refer_fence[1]+1)
        }

        # 保護範囲（タイル数）: フェンス自身の位置 ± 2タイル (16px)
        margin = 2 

        for y in range(G_.TILEMAP_HEIGHT):
            for x in range(G_.TILEMAP_WIDTH):
                tile_id = tm.pget(x, y)
                if tile_id in fence_ids:
                    # フェンス発見。周囲を占有登録
                    for dy in range(-margin, margin + 1):
                        for dx in range(-margin, margin + 1):
                            # 画面外チェックはsetへの追加なので不要（あっても無視されるだけだが、範囲内のみ追加）
                            tx, ty = x + dx, y + dy
                            if 0 <= tx < G_.TILEMAP_WIDTH and 0 <= ty < G_.TILEMAP_HEIGHT:
                                self.occupied_tiles.add((tx, ty))

    def set_stair(self, stair:Stair):
        '''Dungeon単位に生成するStairオブジェクトを部屋に配置'''
        if self.stair is None:
            self.stair = stair
            # 新しい共通メソッドを使用（衝突判定込み）
            try:
                self.stair.address = self.get_random_free_pixel_address(align_to_tile=True)
            except RuntimeError:
                 # 万が一配置できない場合は中央へ（フェイルセーフ）
                self.stair.address = {"x": G_.WND_MAIN[2]//2, "y": G_.WND_MAIN[3]//2}
        else:
            raise Exception

    def generate_chest(self,force:bool=False):
        '''チェスト設定対象のアイテムタイプを元に、アイテムをランダム生成'''
        if px.rndi(1,250) < self.di.app.depth_level/5+(self.di.user.luck)/50 or force:
            item_type_list = [G_.ItemType.RUNE,G_.ItemType.INSTANT,G_.ItemType.INCREASE,
                              G_.ItemType.EX]
            self.chest.append(BlueChest(*self.generate_item(item_type_list,G_.ItemStatus.CHEST)))
        elif px.rndi(1,250) < self.di.app.depth_level/10+(self.di.user.luck)/16:
            item_type_list = [G_.ItemType.RUNE]
            self.chest.append(BlueChest(*self.generate_item(item_type_list,G_.ItemStatus.CHEST)))

    def generate_dropitem(self):
        '''床置き設定対象のアイテムタイプを元に、アイテムをランダム生成'''
        rune_effect = self.di.user.get_rune_effect(G_.RuneList.LUCKY)
        bonus = 0 if rune_effect is None else rune_effect[1]
        if px.rndi(1,250) < self.di.app.depth_level+(self.di.user.luck)/50+bonus:
            item_type_list = [G_.ItemType.TIMER,G_.ItemType.STOCK]
            address, item_uuid, item_num = self.generate_item(item_type_list,G_.ItemStatus.DROP)
            item.ItemManager.get_item(item_uuid).address = address
            self.drop_items.append([item_uuid,item_num])

    def generate_item(self, item_type_list:list, status):
        '''指定されたアイテムタイプのリストを元にアイテムを生成し、アドレス他の情報を戻す'''
        item_type_id = random_choice(item_type_list)
        item_num = 1
        if item_type_id == G_.ItemType.RUNE:
            item_uuid = item.ItemManager.create_randomitem(self.di.app.depth_level,
                                                            G_.ItemType.CATEGORY_RUNE,
                                                            status)
        else:
            item_uuid = item.ItemManager.create_randomitem(self.di.app.depth_level,
                                                            item_type_id, status)
            if item.ItemManager.get_item(item_uuid).type_id == G_.ItemType.INCREASE:
                item_num = int((self.di.app.depth_level*px.rndf(1.5,3.0))**2)
        
        # 新しい共通メソッドを使用（衝突判定込み）
        try:
            address = self.get_random_free_pixel_address(align_to_tile=True)
        except RuntimeError:
            address = {"x": G_.WND_MAIN[2]//2, "y": G_.WND_MAIN[3]//2}
            
        return [address, item_uuid, item_num]
    
    def generate_food(self):
        item_uuid = item.ItemManager.create_item("18")
        try:
            address = self.get_random_free_pixel_address(align_to_tile=True)
        except RuntimeError:
            address = {"x": G_.WND_MAIN[2]//2, "y": G_.WND_MAIN[3]//2}
        item.ItemManager.get_item(item_uuid).address = address
        self.drop_items.append([item_uuid,(self.di.app.depth_level*3)**2*2])

    def generate_mattock(self):
        item_uuid = item.ItemManager.create_item("15")
        try:
            address = self.get_random_free_pixel_address(align_to_tile=True)
        except RuntimeError:
            address = {"x": G_.WND_MAIN[2]//2, "y": G_.WND_MAIN[3]//2}
        item.ItemManager.get_item(item_uuid).address = address
        self.drop_items.append([item_uuid,1])

    def generate_key(self):
        item_uuid = item.ItemManager.create_item("19")
        try:
            address = self.get_random_free_pixel_address(align_to_tile=True)
        except RuntimeError:
            address = {"x": G_.WND_MAIN[2]//2, "y": G_.WND_MAIN[3]//2}
        item.ItemManager.get_item(item_uuid).address = address
        self.drop_items.append([item_uuid,1])

    def generate_blocks(self, num_blocks:int):
        '''障害物を「壁」のように連続性を持たせて配置する'''
        placed_count = 0
        retry_limit = num_blocks * 10 # 全体の試行回数上限
        total_tries = 0
        
        while placed_count < num_blocks and total_tries < retry_limit:
            total_tries += 1

            # 1. 新しい壁の「種」となる開始位置を探す
            try:
                # この関数内で「占有済み」として登録されるため、他との重複はない
                start_address = self.get_random_free_pixel_address(align_to_tile=True)
            except RuntimeError:
                break # 配置場所がない場合は終了

            # ★修正点: 取得した開始位置は「予約済み」なので、チェックせず即座に配置する
            self.obstacles.append(Obstacle(self, start_address))
            placed_count += 1
            
            if placed_count >= num_blocks:
                break

            # 2. 壁を伸ばす設定
            chain_length = px.rndi(2, 6) 
            direction = random_choice([(16,0), (-16,0), (0,16), (0,-16)])
            
            current_addr = start_address.copy()

            # 3. チェーン配置ループ (開始位置の"隣"からスタート)
            for _ in range(chain_length):
                if placed_count >= num_blocks:
                    break

                # 先に座標を移動させる
                current_addr = {
                    "x": current_addr["x"] + direction[0],
                    "y": current_addr["y"] + direction[1]
                }

                # 移動先が配置可能かチェック
                if self.is_position_valid(current_addr):
                    # 配置して占有情報を更新
                    self.obstacles.append(Obstacle(self, current_addr))
                    self.set_occupied_info(current_addr) 
                    placed_count += 1
                else:
                    # 障害物や壁、他のオブジェクトにぶつかったらこのチェーンは終了
                    break

        # 障害物オブジェクトの生成が終わってから仮想タイルマップ配列を更新
        self.virtual_map = self.generate_virtual_tilemap(G_.TilemapIndex.OBSTACLE)

    #タイルマップオブジェクトからタイルマップ配列を生成
    def generate_virtual_tilemap(self, tilemap_id):
        tm = px.tilemaps[tilemap_id]
        virtual_map = [[tm.pget(x, y) for x in range(G_.TILEMAP_WIDTH)]
                       for y in range(G_.TILEMAP_HEIGHT)]
        return virtual_map

    #仮想マップ配列から現在表示位置を元に必要データを抽出してタイルマップを生成
    def set_tilemap(self, tilemap_id:int=0):
        try:
            for y in range(G_.TILEMAP_HEIGHT):
                for x in range(G_.TILEMAP_WIDTH):
                    px.tilemaps[tilemap_id].pset(x, y, self.virtual_map[y][x])
        except Exception as e:
            comf.error_message([f"予期しないエラーが発生しました: {e}"])

    #ルーム封鎖解除
    def open_fence(self):
        if self.di.app.depth_level == 1:
            return
        refer_fence = G_.TileBlock.FENCE[self.di.dungeon.floortype]
        tile_id_fence = {refer_fence, (refer_fence[0],refer_fence[1]+1), (refer_fence[0]+1,refer_fence[1]), (refer_fence[0]+1,refer_fence[1]+1)}
        new_virtual_map = [[(31,31) if tile in tile_id_fence else tile 
                            for tile in row] for row in self.virtual_map]
        self.virtual_map = new_virtual_map
        self.set_tilemap(G_.TilemapIndex.OBSTACLE)
        px.play(2,[G_.SNDEFX["open"]], resume=True)

    #部屋別タイルマップ生成（外壁（隣室有なら扉設定））
    def generate_virtual_tilemap_base(self):
        px.tilemaps[G_.TilemapIndex.OBSTACLE].cls((31,31))
        #外壁
        x,y = self.pos_room
        refer = G_.TileBlock.WALL[self.di.dungeon.floortype]
        tile_id = (refer, (refer[0],refer[1]+1), (refer[0]+1,refer[1]), (refer[0]+1,refer[1]+1))
        refer_fence = G_.TileBlock.FENCE[self.di.dungeon.floortype]
        tile_id_fence = (refer_fence, (refer_fence[0],refer_fence[1]+1), (refer_fence[0]+1,refer_fence[1]), (refer_fence[0]+1,refer_fence[1]+1))

        dx, dy = 0, 0
        for dx in range(0, G_.TILEMAP_WIDTH, 2):
            if (x, y - 1) in self.di.dungeon.rooms_structure and dx in (G_.TILEMAP_WIDTH//2-3,G_.TILEMAP_WIDTH//2-1,G_.TILEMAP_WIDTH//2+1):
                #初期化時は扉設置
                px.tilemaps[G_.TilemapIndex.OBSTACLE].pset(dx, 0, tile_id_fence[0])
                px.tilemaps[G_.TilemapIndex.OBSTACLE].pset(dx, 1, tile_id_fence[1])
                px.tilemaps[G_.TilemapIndex.OBSTACLE].pset(dx+1, 0, tile_id_fence[2])
                px.tilemaps[G_.TilemapIndex.OBSTACLE].pset(dx+1, 1, tile_id_fence[3])
            else:
                px.tilemaps[G_.TilemapIndex.OBSTACLE].pset(dx, 0, tile_id[0])
                px.tilemaps[G_.TilemapIndex.OBSTACLE].pset(dx, 1, tile_id[1])
                px.tilemaps[G_.TilemapIndex.OBSTACLE].pset(dx+1, 0, tile_id[2])
                px.tilemaps[G_.TilemapIndex.OBSTACLE].pset(dx+1, 1, tile_id[3])
            if (x, y + 1) in self.di.dungeon.rooms_structure and dx in (G_.TILEMAP_WIDTH//2-3,G_.TILEMAP_WIDTH//2-1,G_.TILEMAP_WIDTH//2+1):
                px.tilemaps[G_.TilemapIndex.OBSTACLE].pset(dx, G_.TILEMAP_HEIGHT-2, tile_id_fence[0])
                px.tilemaps[G_.TilemapIndex.OBSTACLE].pset(dx, G_.TILEMAP_HEIGHT-1, tile_id_fence[1])
                px.tilemaps[G_.TilemapIndex.OBSTACLE].pset(dx+1, G_.TILEMAP_HEIGHT-2, tile_id_fence[2])
                px.tilemaps[G_.TilemapIndex.OBSTACLE].pset(dx+1, G_.TILEMAP_HEIGHT-1, tile_id_fence[3])
            else:
                px.tilemaps[G_.TilemapIndex.OBSTACLE].pset(dx, G_.TILEMAP_HEIGHT-2, tile_id[0])
                px.tilemaps[G_.TilemapIndex.OBSTACLE].pset(dx, G_.TILEMAP_HEIGHT-1, tile_id[1])
                px.tilemaps[G_.TilemapIndex.OBSTACLE].pset(dx+1, G_.TILEMAP_HEIGHT-2, tile_id[2])
                px.tilemaps[G_.TilemapIndex.OBSTACLE].pset(dx+1, G_.TILEMAP_HEIGHT-1, tile_id[3])
        for dy in range(0, G_.TILEMAP_HEIGHT, 2):
            if (x - 1, y) in self.di.dungeon.rooms_structure and dy in (G_.TILEMAP_HEIGHT//2-3,G_.TILEMAP_HEIGHT//2-1,G_.TILEMAP_HEIGHT//2+1):
                px.tilemaps[G_.TilemapIndex.OBSTACLE].pset(0, dy, tile_id_fence[0])
                px.tilemaps[G_.TilemapIndex.OBSTACLE].pset(0, dy+1, tile_id_fence[1])
                px.tilemaps[G_.TilemapIndex.OBSTACLE].pset(1, dy, tile_id_fence[2])
                px.tilemaps[G_.TilemapIndex.OBSTACLE].pset(1, dy+1, tile_id_fence[3])
            else:
                px.tilemaps[G_.TilemapIndex.OBSTACLE].pset(0, dy, tile_id[0])
                px.tilemaps[G_.TilemapIndex.OBSTACLE].pset(0, dy+1, tile_id[1])
                px.tilemaps[G_.TilemapIndex.OBSTACLE].pset(1, dy, tile_id[2])
                px.tilemaps[G_.TilemapIndex.OBSTACLE].pset(1, dy+1, tile_id[3])
            if (x + 1, y) in self.di.dungeon.rooms_structure and dy in (G_.TILEMAP_HEIGHT//2-3,G_.TILEMAP_HEIGHT//2-1,G_.TILEMAP_HEIGHT//2+1):
                px.tilemaps[G_.TilemapIndex.OBSTACLE].pset(G_.TILEMAP_WIDTH-2, dy, tile_id_fence[0])
                px.tilemaps[G_.TilemapIndex.OBSTACLE].pset(G_.TILEMAP_WIDTH-2, dy+1, tile_id_fence[1])
                px.tilemaps[G_.TilemapIndex.OBSTACLE].pset(G_.TILEMAP_WIDTH-1, dy, tile_id_fence[2])
                px.tilemaps[G_.TilemapIndex.OBSTACLE].pset(G_.TILEMAP_WIDTH-1, dy+1, tile_id_fence[3])
            else:
                px.tilemaps[G_.TilemapIndex.OBSTACLE].pset(G_.TILEMAP_WIDTH-2, dy, tile_id[0])
                px.tilemaps[G_.TilemapIndex.OBSTACLE].pset(G_.TILEMAP_WIDTH-2, dy+1, tile_id[1])
                px.tilemaps[G_.TilemapIndex.OBSTACLE].pset(G_.TILEMAP_WIDTH-1, dy, tile_id[2])
                px.tilemaps[G_.TilemapIndex.OBSTACLE].pset(G_.TILEMAP_WIDTH-1, dy+1, tile_id[3])
        return

    def update(self):
        if self.di.flg.is_before_boss is False and self.di.app.depth_level == 9 and self.stair is not None:
            self.di.app.notice_window.message_text = self.di.flg.notice_rule(G_.FlagNotice.TO_BOSS)

        #階段接触
        if self.stair is not None and \
                comf.check_collision_hitbox(*self.stair.address.values(),*G_.HitboxSize.SAME,
                                            *self.di.user.address,
                                            *G_.HitboxSize.MIDDLE):
            px.stop()
            px.play(3,G_.SNDEFX["stair"])
            while px.play_pos(3) is not None:
                pass
            # px.flip()
            self.di.dungeon.is_nextlevel = True
            return

        #チェスト接触
        if len(self.chest):
            is_pick_chest = False
            tmp_is_on_chest = False
            for chest in self.chest:
                if chest.is_opened:
                    continue
                treasure = item.ItemManager.get_item(chest.item_uuid)
                if comf.check_collision_hitbox(*chest.address.values(),*G_.HitboxSize.SAME,
                                               self.di.user.address[0],self.di.user.address[1]+2,
                                               *G_.HitboxSize.MIDDLE):
                    tmp_is_on_chest = True
                    if self.di.flg.is_bluechest is False:
                        self.di.app.notice_window.message_text = self.di.flg.notice_rule(G_.FlagNotice.BLUECHEST)
                        return
                    if self.di.user.key:
                        if len(self.di.user.inventory) \
                                >= self.di.user.inventory_max:
                            if self.is_on_chest is False:
                                self.di.message_manager.add_message(f"これ以上　持てない！")
                            break
                        rune_effect = self.di.user.get_rune_effect(G_.RuneList.UNLOCK)
                        bonus = 0 if rune_effect is None else (rune_effect[1]+self.di.user.luck//50)
                        if px.rndi(0,99) >= bonus:
                            self.di.user.key -= 1
                        self.di.app.notice_window.message_text = item.notice_item(item.ItemManager.get_item(chest.item_uuid), self.di.flg)
                        numtext = chest.item_num if chest.item_num>1 else ""
                        self.di.message_manager.add_message(f"{treasure.name} {numtext}獲得")
                        item.pick_item(chest.item_uuid, chest.item_num, self.di.user)
                        is_pick_chest = True
                    else:
                        sidx = ["x","y"]
                        match self.di.user.direction:
                            case G_.Direction.FRONT:
                                idx = 1
                                vec = -1
                            case G_.Direction.BACK:
                                idx = 1
                                vec = 1
                            case G_.Direction.LEFT:
                                idx = 0
                                vec = 1
                            case G_.Direction.RIGHT:
                                idx = 0
                                vec = -1
                        self.di.user.address[idx] = chest.address[sidx[idx]] + (vec*15) - (
                                2 if self.di.user.direction in (
                                    G_.Direction.FRONT,G_.Direction.BACK) else 0)
                        # 現在の移動ベクトルを取得 (dx, dy)
                        dx = G_.CHARA_DIR[self.di.user.direction][0]
                        dy = G_.CHARA_DIR[self.di.user.direction][1]
                        # 接触限界距離（2つの矩形の中心間距離の最小値）
                        limit_x = (G_.HitboxSize.MIDDLE[0] + G_.HitboxSize.SAME[0]) / 2 + 0.01
                        limit_y = (G_.HitboxSize.MIDDLE[1] + G_.HitboxSize.SAME[1]) / 2 + 0.01
                        # 進行方向に応じて、めり込みを解消する位置へ座標を補正（スナップ）
                        if dx > 0: # 右へ移動中に衝突（＝自分は箱の左側にいる）
                            # 箱のX座標 - 限界距離
                            self.di.user.address[0] = chest.address["x"] - limit_x
                        elif dx < 0: # 左へ移動中に衝突（＝自分は箱の右側にいる）
                            # 箱のX座標 + 限界距離
                            self.di.user.address[0] = chest.address["x"] + limit_x
                        
                        if dy > 0: # 下へ移動中に衝突（＝自分は箱の上側にいる）
                            # 箱のY座標 - 限界距離 - オフセット補正
                            self.di.user.address[1] = chest.address["y"] - limit_y - 2
                        elif dy < 0: # 上へ移動中に衝突（＝自分は箱の下側にいる）
                            # 箱のY座標 + 限界距離 - オフセット補正
                            self.di.user.address[1] = chest.address["y"] + limit_y - 2
                        self.di.message_manager.add_message(f"鍵を　持っていない")
                    break
            if is_pick_chest:
                chest.is_opened = True
                tmp_is_on_chest = False
            self.is_on_chest = tmp_is_on_chest

        #床置きアイテム接触
        if len(self.drop_items):
            is_pick_item = False
            tmp_is_on_obj = False
            for drop_info in self.drop_items:
                drop_item = item.ItemManager.get_item(drop_info[0])
                if comf.check_collision_hitbox(
                        *drop_item.address.values(),
                        *G_.HitboxSize.MIDDLE,
                        *self.di.user.address, *G_.HitboxSize.MIDDLE):
                    tmp_is_on_obj = True
                    if G_.ItemType.get_category(drop_item.type_id) != G_.ItemType.CATEGORY_CONSUME\
                            and len(self.di.user.inventory) >= self.di.user.inventory_max:
                        if self.is_on_drop is False:
                            self.di.message_manager.add_message(f"これ以上　持てない！")
                        break
                    self.di.app.notice_window.message_text = item.notice_item(drop_item, self.di.flg)
                    numtext = drop_info[1] if drop_info[1]>1 else ""
                    self.di.message_manager.add_message(f"{drop_item.name} {numtext}獲得")
                    item.pick_item(*drop_info,self.di.user)
                    is_pick_item = True
                    break
            if is_pick_item:
                self.drop_items.remove([*drop_info])
                tmp_is_on_obj = False
            self.is_on_drop = tmp_is_on_obj
                    
        return

    def draw(self):
        dx = dy = 0
        if self.di.app.game_state == G_.GameState.DUNGEON:
            if self.di.user.timer_damaged > G_.GAME_FPS*0.75 or\
                self.di.user.timer_magicdamaged > G_.GAME_FPS*0.75:
                dx = px.rndi(-1,1)
                dy = px.rndi(-1,1)
        px.bltm(dx,dy,G_.TilemapIndex.FLOOR, 0,0,px.width,px.height, colkey=0)
        px.bltm(dx,dy,G_.TilemapIndex.OBSTACLE, 0,0,px.width,px.height, colkey=0)
        if len(self.chest):
            self.chest[0].draw()
        if isinstance(self.stair,Stair):
            self.stair.draw()
        if len(self.drop_items):
            for drop_info in self.drop_items:
                item_ = item.ItemManager.get_item(drop_info[0])
                if item_.type_id == 16:
                    px.blt(item_.address["x"]-8,item_.address["y"]-8,G_.IMGIDX["CHIP"],
                        *G_.ImageAddress.ITEM[int(item_.type_id)-4], colkey=px.COLOR_BLACK)
                elif item_.type_id >= 17:
                    px.blt(item_.address["x"]-8,item_.address["y"]-8,G_.IMGIDX["CHIP"],
                        *G_.ImageAddress.ITEM[int(item_.id)+13], colkey=px.COLOR_BLACK)
                else:
                    px.blt(item_.address["x"]-8,item_.address["y"]-8,G_.IMGIDX["CHIP"],
                        *G_.ImageAddress.ITEM[item_.type_id], colkey=px.COLOR_PEACH)

class Obstacle:
    def __init__(self, parent:Room, address):
        self.ref_room = parent
        self.address = address
        self.pos_tile = (address["x"]//8,address["y"]//8)
        self.is_placed = True
        self.update_virtual_tilemap()
    
    def update_virtual_tilemap(self):
        refer = G_.TileBlock.BLOCK[self.ref_room.di.dungeon.floortype]
        tile_id = (refer, (refer[0],refer[1]+1), (refer[0]+1,refer[1]), (refer[0]+1,refer[1]+1))
        if self.is_placed:
            px.tilemaps[G_.TilemapIndex.OBSTACLE].pset(self.pos_tile[0]-1,
                                                       self.pos_tile[1]-1, tile_id[0])
            px.tilemaps[G_.TilemapIndex.OBSTACLE].pset(self.pos_tile[0],
                                                       self.pos_tile[1]-1, tile_id[1])
            px.tilemaps[G_.TilemapIndex.OBSTACLE].pset(self.pos_tile[0]-1,
                                                       self.pos_tile[1], tile_id[2])
            px.tilemaps[G_.TilemapIndex.OBSTACLE].pset(self.pos_tile[0],
                                                       self.pos_tile[1], tile_id[3])
        else:
            px.tilemaps[G_.TilemapIndex.OBSTACLE].pset(self.pos_tile[0]-1,
                                                       self.pos_tile[1]-1, (31,31))
            px.tilemaps[G_.TilemapIndex.OBSTACLE].pset(self.pos_tile[0],
                                                       self.pos_tile[1]-1, (31,31))
            px.tilemaps[G_.TilemapIndex.OBSTACLE].pset(self.pos_tile[0]-1,
                                                       self.pos_tile[1], (31,31))
            px.tilemaps[G_.TilemapIndex.OBSTACLE].pset(self.pos_tile[0],
                                                       self.pos_tile[1], (31,31))
        self.ref_room.virtual_map = self.ref_room.generate_virtual_tilemap(G_.TilemapIndex.OBSTACLE)
