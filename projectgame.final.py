"""
==============================================
  GAME 2: DUNGEON EXPLORER - Maze Adventure
==============================================

"""

import pygame
import sys
import random
import math

pygame.init()

TILE = 40

class Player:
    """Base class untuk pemain dungeon"""
    
    def __init__(self, name, hp, attack, speed, color, x, y):
        self.name = name
        self.hp = hp
        self.max_hp = hp
        self.attack = attack
        self.speed = speed
        self.color = color
        self.col = x
        self.row = y
        self.alive = True
        self.score = 0
        self.keys_collected = 0
        self.move_cooldown = 0
        self.ability_cooldown = 0
        self.special_active = 0
        self.last_move = (0, 0)
    
    def move(self, direction, dungeon_map):
        """Bergerak sesuai arah"""
        if self.move_cooldown > 0:
            return False
        dc, dr = direction
        nc, nr = self.col + dc, self.row + dr
        if dungeon_map.is_walkable(nc, nr):
            self.col, self.row = nc, nr
            self.move_cooldown = self.speed
            self.last_move = direction
            return True
        return False
    
    def use_ability(self):
        """Method abstrak - di-override oleh subclass"""
        pass
    
    def get_hp_percent(self):
        return self.hp / self.max_hp
    
    def draw(self, screen, offset_x, offset_y):
        """Gambar pemain"""
        px = offset_x + self.col * TILE + TILE // 2
        py = offset_y + self.row * TILE + TILE // 2
        
        if self.special_active > 0:
            pygame.draw.circle(screen, (255, 255, 100), (px, py), TILE // 2 + 5)
            self.special_active -= 1
        
        pygame.draw.circle(screen, self.color, (px, py), TILE // 2 - 4)
        dx, dy = self.last_move
        pygame.draw.circle(screen, (255, 255, 255), (px + dx * 6, py + dy * 6), 5)
        pygame.draw.circle(screen, (0, 0, 0), (px + dx * 6, py + dy * 6), 2)
        
        bw = TILE - 4
        pygame.draw.rect(screen, (150, 0, 0), (px - bw//2, py - 26, bw, 5))
        pygame.draw.rect(screen, (0, 200, 0), (px - bw//2, py - 26, int(bw * self.get_hp_percent()), 5))


class Warrior(Player):
    """Warrior: HP tinggi, serangan kuat"""
    
    def __init__(self, x, y):
        super().__init__("Warrior", 120, 25, 10, (100, 160, 255), x, y)
        self.shield = 0 
    
    def use_ability(self):
        """Shield Bash - stun musuh di sekitar"""
        if self.ability_cooldown <= 0:
            self.special_active = 20
            self.ability_cooldown = 180
            self.shield = 5  
            return "shield", 3  
        return None, 0


class Rogue(Player):
    """Rogue: Cepat, bisa menghilang"""
    
    def __init__(self, x, y):
        super().__init__("Rogue", 70, 15, 6, (255, 160, 80), x, y)
        self.invisible = 0
    
    def use_ability(self):
        """Shadowstep - bergerak 3 langkah sekaligus"""
        if self.ability_cooldown <= 0:
            self.invisible = 60  
            self.special_active = 30
            self.ability_cooldown = 120
            return "invisible", 0
        return None, 0
    
    def draw(self, screen, offset_x, offset_y):
        """Override draw - efek transparent saat invisible"""
        if self.invisible > 0 and (self.invisible // 5) % 2 == 0:
            self.invisible -= 1
            return
        if self.invisible > 0:
            self.invisible -= 1
        super().draw(screen, offset_x, offset_y)


class Mage(Player):
    """Mage: Serangan sihir, bisa teleport"""
    
    def __init__(self, x, y):
        super().__init__("Mage", 60, 35, 12, (180, 80, 255), x, y)
        self.mana = 40
    
    def use_ability(self):
        """Teleport ke posisi random yang aman"""
        if self.ability_cooldown <= 0 and self.mana >= 20:
            self.mana -= 20
            self.special_active = 25
            self.ability_cooldown = 150
            return "teleport", 0
        return None, 0


class DungeonMap:
    """Peta dungeon dengan maze generation"""
    
    WALL = 0
    FLOOR = 1
    DOOR = 2
    EXIT = 3
    
    def __init__(self, cols, rows):
        self.cols = cols
        self.rows = rows
        self.grid = [[self.WALL] * cols for _ in range(rows)]
        self.generate()
    
    def generate(self):
        """Buat dungeon dengan Recursive Backtracking"""
        stack = [(1, 1)]
        visited = {(1, 1)}
        self.grid[1][1] = self.FLOOR
        
        while stack:
            c, r = stack[-1]
            dirs = [(0, 2), (0, -2), (2, 0), (-2, 0)]
            random.shuffle(dirs)
            moved = False
            for dc, dr in dirs:
                nc, nr = c + dc, r + dr
                if 0 < nc < self.cols - 1 and 0 < nr < self.rows - 1 and (nc, nr) not in visited:
                    self.grid[nr][nc] = self.FLOOR
                    self.grid[r + dr // 2][c + dc // 2] = self.FLOOR
                    visited.add((nc, nr))
                    stack.append((nc, nr))
                    moved = True
                    break
            if not moved:
                stack.pop()
        
        self.grid[self.rows - 2][self.cols - 2] = self.EXIT
    
    def is_walkable(self, c, r):
        if 0 <= c < self.cols and 0 <= r < self.rows:
            return self.grid[r][c] in [self.FLOOR, self.EXIT]
        return False
    
    def is_exit(self, c, r):
        return self.grid[r][c] == self.EXIT


class Treasure:
    """Harta karun di dungeon"""
    
    TYPES = ["gold", "potion", "key"]
    
    def __init__(self, col, row):
        self.col = col
        self.row = row
        self.type = random.choice(self.TYPES)
        self.collected = False
        self.bob_offset = 0
        self.bob_dir = 1
    
    def update(self):
        self.bob_offset += 0.1 * self.bob_dir
        if abs(self.bob_offset) > 3:
            self.bob_dir *= -1
    
    def draw(self, screen, offset_x, offset_y):
        if self.collected:
            return
        px = offset_x + self.col * TILE + TILE // 2
        py = offset_y + self.row * TILE + TILE // 2 + self.bob_offset
        
        colors = {"gold": (255, 215, 0), "potion": (255, 50, 150), "key": (200, 200, 50)}
        symbols = {"gold": "G", "potion": "P", "key": "K"}
        
        pygame.draw.circle(screen, colors[self.type], (int(px), int(py)), 10)
        font = pygame.font.Font(None, 18)
        txt = font.render(symbols[self.type], True, (0, 0, 0))
        screen.blit(txt, (int(px) - 4, int(py) - 6))


class DungeonMonster:
    """Monster di dungeon yang berpatroli"""
    
    def __init__(self, col, row, dungeon_map):
        self.col = col
        self.row = row
        self.dungeon = dungeon_map
        self.hp = random.randint(20, 50)
        self.max_hp = self.hp
        self.damage = random.randint(10, 20)
        self.move_timer = 0
        self.move_interval = random.randint(30, 60)
        self.color = (random.randint(150, 255), random.randint(50, 100), random.randint(50, 100))
        self.alive = True
        self.patrol_dir = random.choice([(0,1),(0,-1),(1,0),(-1,0)])
    
    def update(self):
        if not self.alive:
            return
        self.move_timer += 1
        if self.move_timer >= self.move_interval:
            self.move_timer = 0
            dc, dr = self.patrol_dir
            nc, nr = self.col + dc, self.row + dr
            if self.dungeon.is_walkable(nc, nr):
                self.col, self.row = nc, nr
            else:
                self.patrol_dir = random.choice([(0,1),(0,-1),(1,0),(-1,0)])
    
    def draw(self, screen, offset_x, offset_y):
        if not self.alive:
            return
        px = offset_x + self.col * TILE + TILE // 2
        py = offset_y + self.row * TILE + TILE // 2
        pygame.draw.rect(screen, self.color, (px - 12, py - 12, 24, 24))
        # Mata
        pygame.draw.circle(screen, (255, 0, 0), (px - 4, py - 4), 3)
        pygame.draw.circle(screen, (255, 0, 0), (px + 4, py - 4), 3)


class DungeonGame:
    
    def __init__(self):
        self.W, self.H = 900, 650
        self.screen = pygame.display.set_mode((self.W, self.H))
        pygame.display.set_caption("Dungeon Explorer - OOP Adventure")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 24)
        self.font_big = pygame.font.Font(None, 44)
        self.font_small = pygame.font.Font(None, 18)
        self.state = "select"  
        self.selected_class = 0
        self.classes = ["Warrior", "Rogue", "Mage"]
        self.class_desc = [
            "HP: 120 | ATK: 25 | Ability: Shield Bash",
            "HP: 70  | ATK: 15 | Ability: Shadowstep (invisible)",
            "HP: 60  | ATK: 35 | Ability: Teleport"
        ]
        self.floor = 1
        self.reset_floor()
    
    def reset_floor(self):
        COLS, ROWS = 19, 15
        self.dungeon = DungeonMap(COLS, ROWS)
        
        class_map = {"Warrior": Warrior, "Rogue": Rogue, "Mage": Mage}
        PlayerClass = class_map[self.classes[self.selected_class]]
        
        if not hasattr(self, 'player') or self.state == "select":
            self.player = PlayerClass(1, 1)
        else:
            old = self.player
            self.player = PlayerClass(1, 1)
            self.player.score = old.score
            self.player.hp = old.hp
            self.player.max_hp = old.max_hp

        floors = [(c, r) for r in range(1, ROWS - 1) for c in range(1, COLS - 1)
                  if self.dungeon.grid[r][c] == DungeonMap.FLOOR and (c, r) != (1, 1)]
        random.shuffle(floors)
        self.treasures = [Treasure(c, r) for c, r in floors[:8 + self.floor * 2]]
        
        self.monsters = []
        random.shuffle(floors)
        for c, r in floors[8:8 + 4 + self.floor * 2]:
            if abs(c - 1) + abs(r - 1) > 4:  
                self.monsters.append(DungeonMonster(c, r, self.dungeon))
        
        self.COLS, self.ROWS = COLS, ROWS
        self.messages = []
        self.state = "playing"
        self.fog = [[True] * COLS for _ in range(ROWS)]
        self.update_fog()
    
    def update_fog(self):
        """Fog of War"""
        c, r = self.player.col, self.player.row
        for dr in range(-3, 4):
            for dc in range(-3, 4):
                if abs(dc) + abs(dr) <= 4:
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < self.ROWS and 0 <= nc < self.COLS:
                        self.fog[nr][nc] = False
    
    def add_msg(self, text, color=(255, 255, 100)):
        self.messages.append([text, 120, color])
    
    def handle_ability(self):
        """Handle penggunaan ability"""
        result_type, result_val = self.player.use_ability()
        if result_type == "shield":
            killed = 0
            for m in self.monsters:
                if m.alive:
                    dc = abs(m.col - self.player.col)
                    dr = abs(m.row - self.player.row)
                    if dc + dr <= result_val:
                        m.alive = False
                        self.player.score += 50
                        killed += 1
            if killed > 0:
                self.add_msg(f"Shield Bash! {killed} monster terkena!", (100, 150, 255))
            else:
                self.add_msg("Shield raised!", (100, 150, 255))
        
        elif result_type == "invisible":
            self.add_msg("Shadowstep! Tak terlihat!", (255, 180, 50))
        
        elif result_type == "teleport":
            floors = [(c, r) for r in range(1, self.ROWS - 1) for c in range(1, self.COLS - 1)
                      if self.dungeon.grid[r][c] == DungeonMap.FLOOR]
            if floors:
                c, r = random.choice(floors)
                self.player.col, self.player.row = c, r
                self.add_msg("Teleport!", (200, 100, 255))
        elif result_type is None and self.player.ability_cooldown > 0:
            self.add_msg(f"Ability cooldown: {self.player.ability_cooldown // 60 + 1}s", (200, 100, 100))
    
    def update(self):
        if self.state != "playing":
            return
        
        keys = pygame.key.get_pressed()
        dirs = {pygame.K_w: (0,-1), pygame.K_UP: (0,-1),
                pygame.K_s: (0,1), pygame.K_DOWN: (0,1),
                pygame.K_a: (-1,0), pygame.K_LEFT: (-1,0),
                pygame.K_d: (1,0), pygame.K_RIGHT: (1,0)}
        
        for key, direction in dirs.items():
            if keys[key]:
                if self.player.move(direction, self.dungeon):
                    self.update_fog()
                break
        
        if self.player.move_cooldown > 0:
            self.player.move_cooldown -= 1
        if self.player.ability_cooldown > 0:
            self.player.ability_cooldown -= 1
        
        for t in self.treasures:
            if not t.collected and t.col == self.player.col and t.row == self.player.row:
                t.collected = True
                if t.type == "gold":
                    self.player.score += 50
                    self.add_msg("+50 Gold!", (255, 215, 0))
                elif t.type == "potion":
                    heal = 30
                    self.player.hp = min(self.player.max_hp, self.player.hp + heal)
                    self.add_msg(f"+{heal} HP!", (0, 255, 150))
                elif t.type == "key":
                    self.player.keys_collected += 1
                    self.player.score += 30
                    self.add_msg("+1 Key!", (200, 200, 50))
        
        for m in self.monsters:
            m.update()
            if m.alive and m.col == self.player.col and m.row == self.player.row:
                if isinstance(self.player, Rogue) and self.player.invisible > 0:
                    pass  
                else:
                    self.player.hp -= m.damage // 10  
                    if self.player.hp <= 0:
                        self.player.hp = 0
                        self.state = "lose"
        
        for t in self.treasures:
            t.update()
        
        if self.dungeon.is_exit(self.player.col, self.player.row):
            if self.floor < 3:
                self.floor += 1
                self.add_msg(f"Masuk lantai {self.floor}!", (255, 255, 0))
                self.reset_floor()
            else:
                self.state = "win"
        
        for msg in self.messages[:]:
            msg[1] -= 1
            if msg[1] <= 0:
                self.messages.remove(msg)
    
    def draw_dungeon(self):
        COLS, ROWS = self.COLS, self.ROWS
        map_w = COLS * TILE
        map_h = ROWS * TILE
        offset_x = (self.W - map_w) // 2
        offset_y = 30
        
        colors = {
            DungeonMap.WALL: (40, 30, 60),
            DungeonMap.FLOOR: (100, 90, 80),
            DungeonMap.EXIT: (50, 220, 50),
        }
        
        for r in range(ROWS):
            for c in range(COLS):
                tile = self.dungeon.grid[r][c]
                px = offset_x + c * TILE
                py = offset_y + r * TILE
                
                if self.fog[r][c]:
                    pygame.draw.rect(self.screen, (5, 5, 20), (px, py, TILE, TILE))
                else:
                    col = colors.get(tile, (60, 60, 60))
                    pygame.draw.rect(self.screen, col, (px, py, TILE, TILE))
                    if tile == DungeonMap.WALL:
                        pygame.draw.rect(self.screen, (60, 50, 90), (px, py, TILE, TILE), 1)
                    elif tile == DungeonMap.FLOOR:
                        pygame.draw.rect(self.screen, (80, 70, 60), (px, py, TILE, TILE), 1)
                    elif tile == DungeonMap.EXIT:
                        # Tanda keluar
                        font = pygame.font.Font(None, 20)
                        txt = font.render("EXIT", True, (0, 0, 0))
                        self.screen.blit(txt, (px + 3, py + 12))
        
        for t in self.treasures:
            if not self.fog[t.row][t.col]:
                t.draw(self.screen, offset_x, offset_y)
        
        for m in self.monsters:
            if m.alive and not self.fog[m.row][m.col]:
                m.draw(self.screen, offset_x, offset_y)
        
        self.player.draw(self.screen, offset_x, offset_y)
        
        return offset_x, offset_y
    
    def draw_ui(self):
        panel = pygame.Surface((200, 160))
        panel.fill((20, 15, 40))
        panel.set_alpha(220)
        self.screen.blit(panel, (5, 5))
        
        hp_r = self.player.get_hp_percent()
        pygame.draw.rect(self.screen, (100, 0, 0), (10, 10, 180, 15))
        pygame.draw.rect(self.screen, (0, 200, 80), (10, 10, int(180 * hp_r), 15))
        self.screen.blit(self.font_small.render(f"HP: {self.player.hp}/{self.player.max_hp}", True, (255,255,255)), (12, 12))
        
        info = [
            f"Class: {self.player.name}",
            f"Lantai: {self.floor}/3",
            f"Score: {self.player.score}",
            f"Keys: {self.player.keys_collected}",
            f"Ability CD: {max(0, self.player.ability_cooldown // 60 + (1 if self.player.ability_cooldown % 60 else 0))}s",
        ]
        for i, t in enumerate(info):
            self.screen.blit(self.font_small.render(t, True, (200, 200, 150)), (10, 30 + i * 20))
        
        hints = ["[WASD] Move", "[Q] Ability", "[ESC] Menu"]
        for i, h in enumerate(hints):
            self.screen.blit(self.font_small.render(h, True, (150, 180, 200)), (5, self.H - 20 - (len(hints) - 1 - i) * 18))
        
        for i, msg in enumerate(self.messages[-4:]):
            t = self.font_small.render(msg[0], True, msg[2])
            self.screen.blit(t, (self.W - t.get_width() - 10, 10 + i * 20))
    
    def draw_select(self):
        self.screen.fill((15, 10, 30))
        title = self.font_big.render("DUNGEON EXPLORER", True, (255, 200, 50))
        self.screen.blit(title, (self.W // 2 - title.get_width() // 2, 60))
        sub = self.font.render("Pilih kelas karakter:", True, (200, 180, 255))
        self.screen.blit(sub, (self.W // 2 - sub.get_width() // 2, 120))
        
        class_colors = [(100, 160, 255), (255, 160, 80), (180, 80, 255)]
        for i, cls in enumerate(self.classes):
            x = 150 + i * 220
            y = 220
            col = class_colors[i]
            border = (255, 255, 100) if i == self.selected_class else (80, 80, 120)
            pygame.draw.rect(self.screen, (30, 25, 60), (x - 90, y - 10, 180, 230), border_radius=12)
            pygame.draw.rect(self.screen, border, (x - 90, y - 10, 180, 230), 3, border_radius=12)
            
            pygame.draw.circle(self.screen, col, (x, y + 50), 35)
            t = self.font_big.render(cls[0], True, (255,255,255))
            self.screen.blit(t, (x - t.get_width()//2, y + 33))
            
            name = self.font.render(cls, True, (255, 255, 255))
            self.screen.blit(name, (x - name.get_width()//2, y + 95))
            
            words = self.class_desc[i].split("|")
            for j, w in enumerate(words):
                d = self.font_small.render(w.strip(), True, (180, 180, 220))
                self.screen.blit(d, (x - d.get_width()//2, y + 120 + j * 22))
        
        hint = self.font.render("[←/→] Pilih   [Enter] Mulai", True, (200, 200, 150))
        self.screen.blit(hint, (self.W//2 - hint.get_width()//2, self.H - 60))
    
    def draw_result(self):
        overlay = pygame.Surface((self.W, self.H), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 170))
        self.screen.blit(overlay, (0, 0))
        
        if self.state == "win":
            msg = self.font_big.render("DUNGEON CLEARED!", True, (255, 215, 0))
            sub = self.font.render("Anda melewati semua lantai dungeon!", True, (200, 255, 200))
        else:
            msg = self.font_big.render("GAME OVER", True, (255, 50, 50))
            sub = self.font.render("Anda jatuh di dalam dungeon...", True, (255, 150, 150))
        
        self.screen.blit(msg, (self.W//2 - msg.get_width()//2, self.H//2 - 80))
        self.screen.blit(sub, (self.W//2 - sub.get_width()//2, self.H//2 - 30))
        score_txt = self.font_big.render(f"Score: {self.player.score}", True, (255, 220, 100))
        self.screen.blit(score_txt, (self.W//2 - score_txt.get_width()//2, self.H//2 + 20))
        
        restart = self.font.render("[R] Main Lagi   [ESC] Pilih Kelas", True, (180, 255, 180))
        self.screen.blit(restart, (self.W//2 - restart.get_width()//2, self.H//2 + 100))
    
    def run(self):
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                if event.type == pygame.KEYDOWN:
                    if self.state == "select":
                        if event.key in [pygame.K_LEFT, pygame.K_a]:
                            self.selected_class = (self.selected_class - 1) % 3
                        elif event.key in [pygame.K_RIGHT, pygame.K_d]:
                            self.selected_class = (self.selected_class + 1) % 3
                        elif event.key == pygame.K_RETURN:
                            self.floor = 1
                            self.reset_floor()
                    elif self.state == "playing":
                        if event.key == pygame.K_ESCAPE:
                            self.state = "select"
                        elif event.key == pygame.K_q:
                            self.handle_ability()
                    elif self.state in ["win", "lose"]:
                        if event.key == pygame.K_r:
                            self.floor = 1
                            self.reset_floor()
                        elif event.key == pygame.K_ESCAPE:
                            self.state = "select"
            
            if self.state == "select":
                self.draw_select()
            else:
                self.update()
                self.screen.fill((10, 8, 20))
                self.draw_dungeon()
                self.draw_ui()
                if self.state in ["win", "lose"]:
                    self.draw_result()
            
            pygame.display.flip()
            self.clock.tick(60)
        
        pygame.quit()


if __name__ == "__main__":
    game = DungeonGame()
    game.run()