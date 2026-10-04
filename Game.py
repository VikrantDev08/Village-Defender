import pygame
import sys
import random

# Initialize Pygame & Fonts
pygame.init()
pygame.font.init()

SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Village Defender")
clock = pygame.time.Clock()

font_small = pygame.font.SysFont(None, 22)
font_large = pygame.font.SysFont(None, 48)
font_med = pygame.font.SysFont(None, 32)

# Load World Map
try:
    world_map = pygame.image.load("Map.png").convert()
    MAP_WIDTH, MAP_HEIGHT = world_map.get_size()
except pygame.error as e:
    print(f"Error loading Map.png: {e}")
    pygame.quit()
    sys.exit()

# Load Sprite Sheets (Steve & Orcs)
try:
    walk_sheet = pygame.image.load("Soldier/Soldier_Walk.png").convert_alpha()
    atk1_sheet = pygame.image.load("Soldier/Soldier_Attack01.png").convert_alpha()
    atk2_sheet = pygame.image.load("Soldier/Soldier_Attack02.png").convert_alpha()
    atk3_sheet = pygame.image.load("Soldier/Soldier_Attack03.png").convert_alpha()
    arrow_img = pygame.image.load("Arrow(projectile)/Arrow01(32x32).png").convert_alpha()
    
    orc_walk_sheet = pygame.image.load("Orc/Orc_Walk.png").convert_alpha()
    orc_atk_sheet = pygame.image.load("Orc/Orc_Attack01.png").convert_alpha()
except pygame.error as e:
    print(f"Error loading assets: {e}")
    pygame.quit()
    sys.exit()

SCALE_FACTOR = 2
FRAME_SIZE = 100
RENDER_SIZE = FRAME_SIZE * SCALE_FACTOR

def get_scaled_sprite(sheet, col, row):
    frame = pygame.Surface((FRAME_SIZE, FRAME_SIZE), pygame.SRCALPHA)
    frame.blit(sheet, (0, 0), (col * FRAME_SIZE, row * FRAME_SIZE, FRAME_SIZE, FRAME_SIZE))
    return pygame.transform.scale(frame, (RENDER_SIZE, RENDER_SIZE))

# Game States
STATE_MENU = 1
STATE_PLAYING = 2
STATE_GAMEOVER = 3
current_state = STATE_MENU

# Global game variables (reset upon starting/restarting)
player_rect = None
player_speed = 5
player_health = 100
max_player_health = 100
facing = 'DOWN'
attack2_cooldown_max = 180
attack2_cooldown_timer = 0
tree_boundary = pygame.Rect(80, 80, MAP_WIDTH - 160, MAP_HEIGHT - 160)

is_attacking = False
attack_frame_index = 0
attack_timer = 0
attack_duration_per_frame = 5
current_attack_sheet = walk_sheet
total_attack_frames = 6
is_bow_attack = False
current_attack_type = 0

arrow_group = pygame.sprite.Group()
health_pack_group = pygame.sprite.Group()
hunter_group = pygame.sprite.Group()

# Timers for Spawning
SPAWN_HUNTER_EVENT = pygame.USEREVENT + 1
SPAWN_HEALTH_PACK_EVENT = pygame.USEREVENT + 2

def reset_game():
    global player_rect, player_health, attack2_cooldown_timer, is_attacking, arrow_group, health_pack_group, hunter_group
    player_rect = pygame.Rect(MAP_WIDTH // 2, MAP_HEIGHT // 2, 40, 40)
    player_health = 100
    attack2_cooldown_timer = 0
    is_attacking = False
    
    arrow_group.empty()
    health_pack_group.empty()
    hunter_group.empty()
    
    # Spawn initial hunter
    rx = random.randint(tree_boundary.left + 50, tree_boundary.right - 50)
    ry = random.randint(tree_boundary.top + 50, tree_boundary.bottom - 50)
    hunter_group.add(Hunter(rx, ry))
    
    pygame.time.set_timer(SPAWN_HUNTER_EVENT, 10000)
    pygame.time.set_timer(SPAWN_HEALTH_PACK_EVENT, 25000)

# Arrow Class
class Arrow(pygame.sprite.Sprite):
    def __init__(self, x, y, direction):
        super().__init__()
        self.speed = 12
        self.direction = direction
        self.damage = 25
        
        if direction == 'LEFT':
            self.image = pygame.transform.rotate(arrow_img, 180)
            self.vx, self.vy = -self.speed, 0
        elif direction == 'RIGHT':
            self.image = arrow_img
            self.vx, self.vy = self.speed, 0
        elif direction == 'UP':
            self.image = pygame.transform.rotate(arrow_img, 90)
            self.vx, self.vy = 0, -self.speed
        elif direction == 'DOWN':
            self.image = pygame.transform.rotate(arrow_img, 270)
            self.vx, self.vy = 0, self.speed

        self.rect = self.image.get_rect(center=(x, y))

    def update(self):
        self.rect.x += self.vx
        self.rect.y += self.vy

# Health Pack Class
class HealthPack(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface((30, 30), pygame.SRCALPHA)
        pygame.draw.rect(self.image, (0, 200, 0), (0, 0, 30, 30), border_radius=5)
        pygame.draw.rect(self.image, (255, 255, 255), (11, 5, 8, 20))
        pygame.draw.rect(self.image, (255, 255, 255), (5, 11, 20, 8))
        self.rect = self.image.get_rect(center=(x, y))

# Hunter (Orc) Class
class Hunter(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.rect = pygame.Rect(x, y, 40, 40)
        self.speed = 2
        self.health = 100
        self.max_health = 100
        self.frame_index = 0
        self.anim_timer = 0
        self.is_attacking = False
        self.attack_cooldown = 0

    def update(self, target_rect):
        dx, dy = 0, 0
        if self.rect.x < target_rect.x:
            dx = self.speed
        elif self.rect.x > target_rect.x:
            dx = -self.speed

        if self.rect.y < target_rect.y:
            dy = self.speed
        elif self.rect.y > target_rect.y:
            dy = -self.speed

        self.rect.x += dx
        self.rect.y += dy

        global player_health
        if self.rect.colliderect(target_rect.inflate(30, 30)):
            self.is_attacking = True
            if self.attack_cooldown <= 0:
                dmg = random.choice([10, 20])
                player_health = max(0, player_health - dmg)
                self.attack_cooldown = 60
        else:
            self.is_attacking = False

        if self.attack_cooldown > 0:
            self.attack_cooldown -= 1

        self.anim_timer += 1
        if self.anim_timer >= 8:
            self.anim_timer = 0
            self.frame_index = (self.frame_index + 1) % 6

def spawn_hunter():
    rx = random.randint(tree_boundary.left + 50, tree_boundary.right - 50)
    ry = random.randint(tree_boundary.top + 50, tree_boundary.bottom - 50)
    hunter_group.add(Hunter(rx, ry))

def spawn_health_pack():
    rx = random.randint(tree_boundary.left + 50, tree_boundary.right - 50)
    ry = random.randint(tree_boundary.top + 50, tree_boundary.bottom - 50)
    health_pack_group.add(HealthPack(rx, ry))

# Camera Class
class Camera:
    def __init__(self, width, height):
        self.camera = pygame.Rect(0, 0, width, height)
        self.width = width
        self.height = height

    def apply(self, entity_rect):
        return entity_rect.move(self.camera.topleft)

    def update(self, target_rect):
        x = -target_rect.centerx + SCREEN_WIDTH // 2
        y = -target_rect.centery + SCREEN_HEIGHT // 2
        x = min(0, x)
        y = min(0, y)
        x = max(-(self.width - SCREEN_WIDTH), x)
        y = max(-(self.height - SCREEN_HEIGHT), y)
        self.camera = pygame.Rect(x, y, self.width, self.height)

camera = Camera(MAP_WIDTH, MAP_HEIGHT)

# Main Game Loop
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if current_state == STATE_PLAYING:
            if event.type == SPAWN_HUNTER_EVENT:
                spawn_hunter()
            if event.type == SPAWN_HEALTH_PACK_EVENT:
                spawn_health_pack()

            if event.type == pygame.KEYDOWN and not is_attacking:
                if event.key == pygame.K_SPACE:
                    is_attacking = True
                    is_bow_attack = False
                    current_attack_type = 1
                    attack_frame_index, attack_timer = 0, 0
                    current_attack_sheet = atk1_sheet
                elif event.key == pygame.K_z:
                    if attack2_cooldown_timer <= 0:
                        is_attacking = True
                        is_bow_attack = False
                        current_attack_type = 2
                        attack_frame_index, attack_timer = 0, 0
                        current_attack_sheet = atk2_sheet
                        attack2_cooldown_timer = attack2_cooldown_max
                elif event.key == pygame.K_x:
                    is_attacking = True
                    is_bow_attack = True
                    current_attack_type = 3
                    attack_frame_index, attack_timer = 0, 0
                    current_attack_sheet = atk3_sheet

        elif current_state == STATE_MENU:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
                reset_game()
                current_state = STATE_PLAYING
            elif event.type == pygame.MOUSEBUTTONDOWN:
                # Click check for Start button box
                mouse_pos = event.pos
                if start_button_rect.collidepoint(mouse_pos):
                    reset_game()
                    current_state = STATE_PLAYING

        elif current_state == STATE_GAMEOVER:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_r:
                reset_game()
                current_state = STATE_PLAYING
            elif event.type == pygame.MOUSEBUTTONDOWN:
                mouse_pos = event.pos
                if restart_button_rect.collidepoint(mouse_pos):
                    reset_game()
                    current_state = STATE_PLAYING

    if current_state == STATE_MENU:
        screen.fill((20, 20, 40))
        title_surf = font_large.render("VILLAGE DEFENDER", True, (255, 215, 0))
        screen.blit(title_surf, (SCREEN_WIDTH // 2 - title_surf.get_width() // 2, 160))

        start_button_rect = pygame.Rect(SCREEN_WIDTH // 2 - 100, 280, 200, 50)
        pygame.draw.rect(screen, (0, 150, 0), start_button_rect, border_radius=8)
        pygame.draw.rect(screen, (255, 255, 255), start_button_rect, 2, border_radius=8)
        
        btn_text = font_med.render("Start Game", True, (255, 255, 255))
        screen.blit(btn_text, (start_button_rect.centerx - btn_text.get_width() // 2, start_button_rect.centery - btn_text.get_height() // 2))

        inst_text = font_small.render("Press Enter or Click to Play", True, (180, 180, 180))
        screen.blit(inst_text, (SCREEN_WIDTH // 2 - inst_text.get_width() // 2, 360))

    elif current_state == STATE_PLAYING:
        # Tick down Attack 2 cooldown
        if attack2_cooldown_timer > 0:
            attack2_cooldown_timer -= 1

        # Movement Input
        dx, dy = 0, 0
        if not is_attacking:
            keys = pygame.key.get_pressed()
            if keys[pygame.K_LEFT] or keys[pygame.K_a]:
                dx = -player_speed
                facing = 'LEFT'
            elif keys[pygame.K_RIGHT] or keys[pygame.K_d]:
                dx = player_speed
                facing = 'RIGHT'
            elif keys[pygame.K_UP] or keys[pygame.K_w]:
                dy = -player_speed
                facing = 'UP'
            elif keys[pygame.K_DOWN] or keys[pygame.K_s]:
                dy = player_speed
                facing = 'DOWN'

            player_rect.x += dx
            if not tree_boundary.contains(player_rect):
                player_rect.x -= dx

            player_rect.y += dy
            if not tree_boundary.contains(player_rect):
                player_rect.y -= dy
        else:
            attack_timer += 1
            if attack_timer >= attack_duration_per_frame:
                attack_timer = 0
                
                if not is_bow_attack and attack_frame_index == 2:
                    damage_to_deal = 20 if current_attack_type == 1 else 50
                    hit_rect = player_rect.inflate(60, 60)
                    for hunter in hunter_group:
                        if hit_rect.colliderect(hunter.rect):
                            hunter.health -= damage_to_deal
                            if hunter.health <= 0:
                                hunter.kill()

                if is_bow_attack and attack_frame_index == 2:
                    new_arrow = Arrow(player_rect.centerx, player_rect.centery, facing)
                    arrow_group.add(new_arrow)

                attack_frame_index += 1
                if attack_frame_index >= total_attack_frames:
                    is_attacking = False
                    is_bow_attack = False

        # Update Arrows
        arrow_group.update()
        for arrow in arrow_group:
            hit_hunters = pygame.sprite.spritecollide(arrow, hunter_group, False)
            if hit_hunters or not tree_boundary.contains(arrow.rect):
                if hit_hunters:
                    for h in hit_hunters:
                        h.health -= arrow.damage
                        if h.health <= 0:
                            h.kill()
                arrow.kill()

        # Check Health Pack Pickups
        for pack in list(health_pack_group):
            if player_rect.colliderect(pack.rect):
                player_health = min(max_player_health, player_health + 50)
                pack.kill()

        # Check Death Condition
        if player_health <= 0:
            current_state = STATE_GAMEOVER
            pygame.time.set_timer(SPAWN_HUNTER_EVENT, 0)
            pygame.time.set_timer(SPAWN_HEALTH_PACK_EVENT, 0)

        # Update Hunters & Camera
        hunter_group.update(player_rect)
        camera.update(player_rect)

        # Drawing / Rendering
        screen.fill((0, 0, 0))
        screen.blit(world_map, camera.camera.topleft)

        for pack in health_pack_group:
            screen.blit(pack.image, camera.apply(pack.rect))

        for arrow in arrow_group:
            screen.blit(arrow.image, camera.apply(arrow.rect))

        for hunter in hunter_group:
            sheet = orc_atk_sheet if hunter.is_attacking else orc_walk_sheet
            hunter_image = get_scaled_sprite(sheet, hunter.frame_index, 0)
            draw_pos = camera.apply(hunter.rect)
            screen.blit(hunter_image, (draw_pos.x - (RENDER_SIZE // 2) + 20, draw_pos.y - (RENDER_SIZE // 2) + 20))
            
            bar_width = 40
            bar_height = 5
            fill = max(0, (hunter.health / hunter.max_health) * bar_width)
            pygame.draw.rect(screen, (200, 0, 0), (draw_pos.x - 10, draw_pos.y - 25, bar_width, bar_height))
            pygame.draw.rect(screen, (0, 200, 0), (draw_pos.x - 10, draw_pos.y - 25, fill, bar_height))

        if is_attacking:
            steve_image = get_scaled_sprite(current_attack_sheet, attack_frame_index, 0)
        else:
            steve_image = get_scaled_sprite(walk_sheet, 0, 0)

        draw_pos = camera.apply(player_rect)
        screen.blit(steve_image, (draw_pos.x - (RENDER_SIZE // 2) + 20, draw_pos.y - (RENDER_SIZE // 2) + 20))

        # --- UI / Status Bar (Top Right) ---
        ui_x = SCREEN_WIDTH - 230
        ui_y = 15

        hp_label = font_small.render("Steve HP", True, (255, 255, 255))
        screen.blit(hp_label, (ui_x, ui_y))
        
        bar_w = 140
        bar_h = 14
        hp_fill = max(0, (player_health / max_player_health) * bar_w)
        hp_color = (int(255 * (1 - player_health/100)), int(255 * (player_health/100)), 0)
        
        pygame.draw.rect(screen, (50, 50, 50), (ui_x + 70, ui_y + 2, bar_w, bar_h))
        pygame.draw.rect(screen, hp_color, (ui_x + 70, ui_y + 2, hp_fill, bar_h))
        pygame.draw.rect(screen, (255, 255, 255), (ui_x + 70, ui_y + 2, bar_w, bar_h), 1)

        cd_label = font_small.render("Skill Z CD", True, (255, 255, 255))
        screen.blit(cd_label, (ui_x, ui_y + 24))

        cd_fill = (attack2_cooldown_timer / attack2_cooldown_max) * bar_w
        pygame.draw.rect(screen, (50, 50, 50), (ui_x + 70, ui_y + 26, bar_w, bar_h))
        pygame.draw.rect(screen, (0, 150, 255), (ui_x + 70, ui_y + 26, bar_w - cd_fill, bar_h))
        pygame.draw.rect(screen, (255, 255, 255), (ui_x + 70, ui_y + 26, bar_w, bar_h), 1)

    elif current_state == STATE_GAMEOVER:
        screen.fill((30, 10, 10))
        over_text = font_large.render("GAME OVER", True, (255, 50, 50))
        screen.blit(over_text, (SCREEN_WIDTH // 2 - over_text.get_width() // 2, 160))

        sub_text = font_med.render("Try Again", True, (255, 255, 255))
        screen.blit(sub_text, (SCREEN_WIDTH // 2 - sub_text.get_width() // 2, 230))

        restart_button_rect = pygame.Rect(SCREEN_WIDTH // 2 - 100, 290, 200, 50)
        pygame.draw.rect(screen, (180, 0, 0), restart_button_rect, border_radius=8)
        pygame.draw.rect(screen, (255, 255, 255), restart_button_rect, 2, border_radius=8)
        
        btn_text = font_med.render("Play Again", True, (255, 255, 255))
        screen.blit(btn_text, (restart_button_rect.centerx - btn_text.get_width() // 2, restart_button_rect.centery - btn_text.get_height() // 2))

        inst_text = font_small.render("Press 'R' or Click to Restart", True, (180, 180, 180))
        screen.blit(inst_text, (SCREEN_WIDTH // 2 - inst_text.get_width() // 2, 370))

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
sys.exit()
