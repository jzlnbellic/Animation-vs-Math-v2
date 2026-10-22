"""
Mathverse: Neon Void - Cinematic & Audio Edition
------------------------------------------------------
Fully updated with:
  - 1600x900 resolution & immersive dark theme
  - NEW: Dynamic "Flinch" damage animation & color strobe on impact
  - Perfected IK Running: 95% scale, upright posture, wide arm pendulum swing
  - Global Screen Shake effect when taking damage
  - Start Screen -> Rules Screen -> Game loop
  - Pause functionality (ESC to pause/resume, Q to quit to main menu)
"""

import pygame
import random
import sys
import math
import os

# ----------------------------------------------------------------------
# Config / constants
# ----------------------------------------------------------------------
SCREEN_WIDTH, SCREEN_HEIGHT = 1600, 900
GROUND_Y = 720  

FPS = 60

BLACK = (10, 10, 12)
WHITE = (240, 240, 240)
ORANGE = (255, 120, 30)
DARK_GRAY = (40, 40, 45)
RED = (230, 60, 60)
GREEN = (60, 200, 100)
CYAN = (50, 220, 255)  
DIM_WHITE = (150, 150, 150)

QUESTION_TIME_LIMIT = 10000
STARTING_HP = 3

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
AUDIO_PATH = os.path.join(BASE_DIR, "Sounds") + os.sep

RUN_CYCLE_SPEED = 0.15

# ----------------------------------------------------------------------
# Math Helpers for Smooth Animation Blending
# ----------------------------------------------------------------------
def lerp(a, b, t):
    return a + (b - a) * t

def lerp2d(p1, p2, t):
    return (lerp(p1[0], p2[0], t), lerp(p1[1], p2[1], t))

# ----------------------------------------------------------------------
# Particles & Projectiles
# ----------------------------------------------------------------------
class Particle:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        angle = random.uniform(0, 2 * math.pi)
        speed = random.uniform(2, 7)
        self.vx = math.cos(angle) * speed
        self.vy = math.sin(angle) * speed
        self.life = random.randint(20, 40)
        self.char = random.choice(["0", "1", "+", "-", "=", "*", "/"])

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.vy += 0.2
        self.life -= 1

    def draw(self, surf, font):
        if self.life > 0:
            txt = font.render(self.char, True, WHITE)
            surf.blit(txt, (int(self.x), int(self.y)))

class Shockwave:
    def __init__(self, x, y):
        self.x, self.y = x, y
        self.radius = 6
        self.max_radius = 90
        self.life = 18
        self.max_life = self.life

    def update(self):
        self.radius += (self.max_radius - self.radius) * 0.35
        self.life -= 1

    def draw(self, surf):
        if self.life <= 0:
            return
        alpha = max(0, int(255 * (self.life / self.max_life)))
        d = int(self.radius * 2) + 6
        ring = pygame.Surface((d, d), pygame.SRCALPHA)
        pygame.draw.circle(ring, (255, 255, 255, alpha), (d // 2, d // 2), int(self.radius), 3)
        surf.blit(ring, (int(self.x - d / 2), int(self.y - d / 2)))

class DotProjectile:
    def __init__(self, x, y, difficulty):
        self.x = x
        self.y = y
        speed_boost = max(0, (difficulty - 5) * 2.5)
        self.speed = 15 + speed_boost
        self.active = True

    def update(self):
        self.x += self.speed
        if self.x > SCREEN_WIDTH + 50:
            self.active = False

    def draw(self, surf, font):
        dot_surf = font.render("*", True, WHITE)
        surf.blit(dot_surf, (int(self.x), int(self.y - 20)))

    def get_rect(self):
        return pygame.Rect(int(self.x), int(self.y - 10), 20, 20)

# ----------------------------------------------------------------------
# Hazards & Obstacles
# ----------------------------------------------------------------------
class AlGebraHazard:
    def __init__(self, difficulty):
        self.x = SCREEN_WIDTH + 60
        self.y = GROUND_Y - 25
        self.width = 44
        self.height = 44
        
        speed_boost = max(0, (difficulty - 5) * 1.5)
        self.speed = random.uniform(7.5, 10.0) + speed_boost
        self.symbol = random.choice(["∑", "∏", "Ω", "∫", "X", "∞", "∅"])
        self.active = True
        self.angle = 0
        
        base_spin = random.uniform(6, 12) + speed_boost
        self.spin_speed = base_spin * random.choice([1, -1])

    def update(self):
        self.x -= self.speed
        self.angle = (self.angle + self.spin_speed) % 360
        if self.x < -80:
            self.active = False

    def draw(self, surf, font):
        sym_surf = font.render(self.symbol, True, WHITE)
        rotated_surf = pygame.transform.rotate(sym_surf, self.angle)
        rot_rect = rotated_surf.get_rect(center=(int(self.x), int(self.y - self.height // 2)))
        surf.blit(rotated_surf, rot_rect)

    def get_rect(self):
        return pygame.Rect(int(self.x - self.width / 2), int(self.y - self.height), self.width, self.height)

class EquationBarrier:
    def __init__(self, difficulty):
        self.generate(difficulty)
        self.x = SCREEN_WIDTH + 100
        self.target_x = SCREEN_WIDTH - 300 
        self.user_input = ""
        self.time_left = QUESTION_TIME_LIMIT
        self.visible = True

    def generate(self, difficulty):
        ops = ["+", "-"]
        if difficulty >= 2: ops.append("*")
        if difficulty >= 3: ops.append("/")

        self.op = random.choice(ops) 
        
        if self.op == "+":
            a, b = random.randint(2, 8 + difficulty * 4), random.randint(2, 8 + difficulty * 4)
            self.answer = a + b
        elif self.op == "-":
            a, b = random.randint(2, 10 + difficulty * 4), random.randint(2, 10 + difficulty * 4)
            if b > a: a, b = b, a
            self.answer = a - b
        elif self.op == "*":
            a, b = random.randint(2, 5 + difficulty), random.randint(2, 5 + difficulty)
            self.answer = a * b
        else:
            b = random.randint(2, 4 + difficulty)
            self.answer = random.randint(2, 8 + difficulty)
            a = b * self.answer

        self.question_str = f"{a} {self.op} {b} = ?"

    def update(self, dt):
        if self.x > self.target_x:
            self.x -= 6
        else:
            self.time_left -= dt

    def draw(self, surf, font, small_font):
        box_w, box_h = 240, 110
        box_rect = pygame.Rect(int(self.x - box_w // 2), GROUND_Y - 140, box_w, box_h)
        pygame.draw.rect(surf, BLACK, box_rect, border_radius=10)
        pygame.draw.rect(surf, WHITE, box_rect, 2, border_radius=10)

        q_surf = font.render(self.question_str, True, WHITE)
        surf.blit(q_surf, (box_rect.centerx - q_surf.get_width() // 2, box_rect.y + 12))

        input_rect = pygame.Rect(box_rect.centerx - 70, box_rect.y + 55, 140, 32)
        pygame.draw.rect(surf, DARK_GRAY, input_rect, border_radius=6)
        pygame.draw.rect(surf, WHITE, input_rect, 1, border_radius=6)
        
        ans_surf = font.render(self.user_input or "_", True, WHITE)
        surf.blit(ans_surf, (input_rect.centerx - ans_surf.get_width() // 2, input_rect.y + 3))

        bar_w = 200
        pct = max(0, self.time_left / QUESTION_TIME_LIMIT)
        bar_bg = pygame.Rect(box_rect.centerx - bar_w // 2, box_rect.bottom + 6, bar_w, 4)
        pygame.draw.rect(surf, DARK_GRAY, bar_bg)
        bar_fg = pygame.Rect(bar_bg.x, bar_bg.y, int(bar_w * pct), 4)
        color = GREEN if pct > 0.3 else RED
        pygame.draw.rect(surf, color, bar_fg)

# ----------------------------------------------------------------------
# Floating Background Math Symbols & Player
# ----------------------------------------------------------------------
class FloatingSymbol:
    SYMBOLS = ["+", "-", "x", "÷", "=", "π", "√", "∫", "∑", "∞"]

    def __init__(self):
        self.reset(random.randint(0, SCREEN_WIDTH))

    def reset(self, x=None):
        self.x = x if x is not None else random.randint(SCREEN_WIDTH, SCREEN_WIDTH + 200)
        self.y = random.randint(20, GROUND_Y - 40)
        self.symbol = random.choice(self.SYMBOLS)
        self.speed = random.uniform(0.3, 1.0)
        self.size = random.randint(16, 28)

    def update(self):
        self.x -= self.speed
        if self.x < -30:
            self.reset()

    def draw(self, surf, font_cache):
        font = font_cache.setdefault(self.size, pygame.font.SysFont("arial", self.size))
        s = font.render(self.symbol, True, (35, 35, 45))
        surf.blit(s, (self.x, self.y))

class Player:
    def __init__(self):
        self.x = 250 
        self.y = GROUND_Y
        self.width = 24
        self.height = 60
        self.vel_y = 0
        self.jump_force = -13
        self.gravity = 0.7
        self.on_ground = True
        self.walk_cycle = 0
        self.move_blend = 0.0  
        self.ammo = 0  
        self.infinity_ammo = 0  

    def jump(self):
        if self.on_ground:
            self.vel_y = self.jump_force
            self.on_ground = False

    def update(self, is_moving):
        if is_moving:
            self.move_blend = min(1.0, self.move_blend + 0.08)
        else:
            self.move_blend = max(0.0, self.move_blend - 0.08)

        if self.move_blend > 0:
            self.walk_cycle += 1 * self.move_blend
        else:
            self.walk_cycle = 0

        self.vel_y += self.gravity
        self.y += self.vel_y
        if self.y > GROUND_Y:
            self.y = GROUND_Y
            self.vel_y = 0
            self.on_ground = True

    def draw(self, surf, is_moving, font_gun, damage_timer=0):
        # 1. Base Variables & Color Flicker
        stick_color = ORANGE
        if damage_timer > 0:
            # Strobe flashes Red and White when damaged!
            stick_color = RED if (damage_timer // 3) % 2 == 0 else WHITE
            
        hip_x, hip_y = int(self.x), int(self.y - 38)
        head_r = 12 
        
        # 2. Torso & Head Math
        lean = 12 * self.move_blend if self.on_ground else 0
        neck_x, neck_y = hip_x + lean, hip_y - 26
        head_center = (neck_x + (lean // 4), neck_y - 14)

        if self.on_ground and self.move_blend > 0:
            phase = self.walk_cycle * RUN_CYCLE_SPEED
            bob = abs(math.sin(phase * 2)) * 5 * self.move_blend
            hip_y -= bob
            neck_y -= bob
            head_center = (head_center[0], head_center[1] - bob)
        else:
            phase = 0

        # 3. Dynamic Limb Calculations
        if not self.on_ground:
            # JUMPING POSE
            knees = [(hip_x + 12, hip_y + 12), (hip_x - 4, hip_y + 20)]
            feet = [(hip_x + 5, hip_y + 35), (hip_x - 4, hip_y + 40)]
            elbows = [(neck_x + 16, neck_y - 8), (neck_x - 16, neck_y - 8)]
            hands = [(neck_x + 30, neck_y - 20), (neck_x - 30, neck_y - 20)]
            
        else:
            # IDLE POSE DATA
            idle_knees = [(hip_x + 4, hip_y + 18), (hip_x - 4, hip_y + 18)]
            idle_feet = [(hip_x + 6, hip_y + 40), (hip_x - 6, hip_y + 40)]
            idle_elbows = [(neck_x + 8, neck_y + 14), (neck_x - 8, neck_y + 14)]
            idle_hands = [(neck_x + 12, neck_y + 28), (neck_x - 12, neck_y + 28)]

            # RUNNING POSE DATA
            thigh_len, calf_len = 21, 21
            bicep_len, forearm_len = 15, 17
            
            thigh_angle_r = math.sin(phase) * 1.0
            knee_bend_r = max(0, math.cos(phase)) * 1.8 
            calf_angle_r = thigh_angle_r - knee_bend_r
            run_k1_x = hip_x + math.sin(thigh_angle_r) * thigh_len
            run_k1_y = hip_y + math.cos(thigh_angle_r) * thigh_len
            run_f1_x = run_k1_x + math.sin(calf_angle_r) * calf_len
            run_f1_y = run_k1_y + math.cos(calf_angle_r) * calf_len
            
            thigh_angle_l = math.sin(phase + math.pi) * 1.0
            knee_bend_l = max(0, math.cos(phase + math.pi)) * 1.8 
            calf_angle_l = thigh_angle_l - knee_bend_l
            run_k2_x = hip_x + math.sin(thigh_angle_l) * thigh_len
            run_k2_y = hip_y + math.cos(thigh_angle_l) * thigh_len
            run_f2_x = run_k2_x + math.sin(calf_angle_l) * calf_len
            run_f2_y = run_k2_y + math.cos(calf_angle_l) * calf_len
            
            arm_phase_r = phase + math.pi
            bicep_angle_r = math.sin(arm_phase_r) * 1.2
            elbow_bend_r = 1.1 + math.sin(arm_phase_r) * 0.3
            forearm_angle_r = bicep_angle_r + elbow_bend_r
            run_e1_x = neck_x + math.sin(bicep_angle_r) * bicep_len
            run_e1_y = neck_y + math.cos(bicep_angle_r) * bicep_len
            run_h1_x = run_e1_x + math.sin(forearm_angle_r) * forearm_len
            run_h1_y = run_e1_y + math.cos(forearm_angle_r) * forearm_len
            
            arm_phase_l = phase
            bicep_angle_l = math.sin(arm_phase_l) * 1.2
            elbow_bend_l = 1.1 + math.sin(arm_phase_l) * 0.3
            forearm_angle_l = bicep_angle_l + elbow_bend_l
            run_e2_x = neck_x + math.sin(bicep_angle_l) * bicep_len
            run_e2_y = neck_y + math.cos(bicep_angle_l) * bicep_len
            run_h2_x = run_e2_x + math.sin(forearm_angle_l) * forearm_len
            run_h2_y = run_e2_y + math.cos(forearm_angle_l) * forearm_len
            
            run_knees = [(run_k1_x, run_k1_y), (run_k2_x, run_k2_y)]
            run_feet = [(run_f1_x, run_f1_y), (run_f2_x, run_f2_y)]
            run_elbows = [(run_e1_x, run_e1_y), (run_e2_x, run_e2_y)]
            run_hands = [(run_h1_x, run_h1_y), (run_h2_x, run_h2_y)]

            # SMOOTH BLENDING BETWEEN IDLE AND RUN
            knees = [lerp2d(i, r, self.move_blend) for i, r in zip(idle_knees, run_knees)]
            feet = [lerp2d(i, r, self.move_blend) for i, r in zip(idle_feet, run_feet)]
            elbows = [lerp2d(i, r, self.move_blend) for i, r in zip(idle_elbows, run_elbows)]
            hands = [lerp2d(i, r, self.move_blend) for i, r in zip(idle_hands, run_hands)]

        # --- 4. OVERRIDE: FLINCH ANIMATION ON DAMAGE ---
        # If we just took damage (first 15 frames of the timer), completely throw the stickman into a flinch!
        if damage_timer > 15:
            lean = -15  # Thrown backward
            neck_x, neck_y = hip_x + lean, hip_y - 20
            head_center = (neck_x - 5, neck_y - 12)
            
            knees = [(hip_x + 10, hip_y + 15), (hip_x - 12, hip_y + 10)]
            feet = [(hip_x + 15, hip_y + 38), (hip_x - 18, hip_y + 35)]
            elbows = [(neck_x + 10, neck_y + 10), (neck_x - 15, neck_y + 5)]
            # Hands thrown up defensively
            hands = [(neck_x + 20, neck_y - 15), (neck_x - 25, neck_y - 20)]

        # --- 5. RENDER BONES ---
        pygame.draw.circle(surf, stick_color, head_center, head_r, 4)
        pygame.draw.line(surf, stick_color, (hip_x, hip_y), (neck_x, neck_y), 4)

        # Draw Back Arm & Leg
        pygame.draw.line(surf, stick_color, (hip_x, hip_y), knees[1], 4)
        pygame.draw.line(surf, stick_color, knees[1], feet[1], 4)
        pygame.draw.line(surf, stick_color, (neck_x, neck_y), elbows[1], 4)
        pygame.draw.line(surf, stick_color, elbows[1], hands[1], 4)

        # Draw Front Arm & Leg
        pygame.draw.line(surf, stick_color, (hip_x, hip_y), knees[0], 4)
        pygame.draw.line(surf, stick_color, knees[0], feet[0], 4)
        pygame.draw.line(surf, stick_color, (neck_x, neck_y), elbows[0], 4)
        pygame.draw.line(surf, stick_color, elbows[0], hands[0], 4)

        # Gun rendering dynamically follows the front right hand
        if self.infinity_ammo > 0:
            gun_surf = font_gun.render("f(∞)=", True, WHITE)
            surf.blit(gun_surf, (hands[0][0], hands[0][1] - 15))
        elif self.ammo > 0:
            gun_surf = font_gun.render("f(.)=", True, WHITE)
            surf.blit(gun_surf, (hands[0][0], hands[0][1] - 15))

    def get_rect(self):
        return pygame.Rect(int(self.x - self.width / 2), int(self.y - self.height), self.width, self.height)


# ----------------------------------------------------------------------
# Main Game Engine
# ----------------------------------------------------------------------
class Game:
    def __init__(self):
        pygame.init()
        pygame.mixer.init()
        
        self.window = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        self.screen = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Mathverse: Neon Void - Cinematic Edition")
        
        self.clock = pygame.time.Clock()

        self.font_med = pygame.font.SysFont("arial", 26, bold=True)
        self.font_big = pygame.font.SysFont("arial", 42, bold=True)
        self.font_small = pygame.font.SysFont("arial", 18, bold=True)
        self.font_giant = pygame.font.SysFont("arial", 60, bold=True)
        self.font_gun = pygame.font.SysFont("arial", 28, bold=True)
        self.font_projectile = pygame.font.SysFont("arial", 50, bold=True) 

        self.symbol_font_cache = {}
        self.symbols = [FloatingSymbol() for _ in range(35)]
        
        self.opening_radius = 1 
        
        try:
            pygame.mixer.music.load(AUDIO_PATH + "atmosphere.mp3")
            self.sfx_jump = pygame.mixer.Sound(AUDIO_PATH + "jump.mp3")
            self.sfx_algebra = pygame.mixer.Sound(AUDIO_PATH + "Al-gebra.wav")
            self.sfx_explosion = pygame.mixer.Sound(AUDIO_PATH + "explosion.mp3")
            self.sfx_damage = pygame.mixer.Sound(AUDIO_PATH + "damage.mp3")
            self.sfx_gameover = pygame.mixer.Sound(AUDIO_PATH + "game-over.mp3")
            self.sfx_timer = pygame.mixer.Sound(AUDIO_PATH + "timer.wav")
            self.sfx_blackhole = pygame.mixer.Sound(AUDIO_PATH + "blackhole.mp3")
        except FileNotFoundError as e:
            print(f"Audio file missing: {e}. Running without sound.")
            self.sfx_jump = self.sfx_algebra = self.sfx_explosion = self.sfx_damage = self.sfx_gameover = self.sfx_timer = self.sfx_blackhole = None

        self.reset()
        self.state = "start_screen"

    def reset(self):
        pygame.mixer.stop() 

        self.player = Player()
        self.score = 0
        self.health = STARTING_HP
        self.difficulty = 1
        self.state = "playing"
        self.game_over_reason = "Mathematical Damage"

        self.al_gebra_kills = 0  
        self.start_transition = False  

        self.world_offset = 0
        self.current_barrier = EquationBarrier(self.difficulty)
        self.is_passing_barrier = False
        self.passing_timer = 0
        self.timer_is_playing = False 

        self.particles = []
        self.shockwaves = []
        self.algebra_hazards = []
        self.projectiles = []
        self.active_mini_black_hole = None  
        self.algebra_spawn_timer = random.randint(300, 600)

        self.damage_flash_timer = 0
        self.black_hole_radius = 0
        
        if pygame.mixer.music.get_busy() == False:
            try:
                pygame.mixer.music.play(-1)
            except:
                pass

    def trigger_game_over(self, reason):
        self.game_over_reason = reason
        self.state = "game_over"
        self.black_hole_radius = 10
        
        # FIX: Reset the damage timer so the screen stops shaking and flashing!
        self.damage_flash_timer = 0 
        
        pygame.mixer.music.stop()
        pygame.mixer.stop() 
        self.timer_is_playing = False
        
        if self.sfx_damage:
            self.sfx_damage.play()
        if self.sfx_gameover:
            self.sfx_gameover.play()
            
    def run(self):
        while True:
            dt = self.clock.tick(FPS)
            self.handle_events()
            
            if self.state == "start_screen":
                for s in self.symbols:
                    s.update()
                    
            elif self.state == "rules_screen":
                for s in self.symbols:
                    s.update()
                
                if self.start_transition and self.active_mini_black_hole:
                    self.active_mini_black_hole['radius'] += 45
                    if self.active_mini_black_hole['phase'] == 'expanding_black' and self.active_mini_black_hole['radius'] > 2000:
                        self.active_mini_black_hole['phase'] = 'expanding_clear'
                        self.active_mini_black_hole['radius'] = 1
                        self.state = "playing"
                        
            elif self.state == "playing":
                self.update(dt)
                
            elif self.state == "game_over":
                if self.black_hole_radius < 2000:
                    self.black_hole_radius += 30
                    
            self.draw()
            
            shake_x, shake_y = 0, 0
            if self.damage_flash_timer > 0:
                intensity = min(10, self.damage_flash_timer // 2)
                if intensity > 0:
                    shake_x = random.randint(-intensity, intensity)
                    shake_y = random.randint(-intensity, intensity)
            
            self.window.fill(BLACK)
            self.window.blit(self.screen, (shake_x, shake_y))
            pygame.display.flip()

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if self.state == "start_screen":
                if event.type in (pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN):
                    if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                        pygame.quit()
                        sys.exit()
                    else:
                        self.state = "rules_screen"
                continue

            if self.state == "rules_screen":
                if event.type in (pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN):
                    if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                        pygame.quit()
                        sys.exit()
                    
                    if not self.start_transition:
                        self.start_transition = True
                        if self.sfx_blackhole:
                            self.sfx_blackhole.play()
                        
                        self.active_mini_black_hole = {
                            'x': SCREEN_WIDTH // 2, 
                            'y': SCREEN_HEIGHT // 2, 
                            'radius': 1, 
                            'phase': 'expanding_black'
                        }
                continue

            if event.type == pygame.KEYDOWN:
                
                if event.key == pygame.K_ESCAPE:
                    if self.state == "playing":
                        self.state = "paused"
                        pygame.mixer.music.pause()
                        pygame.mixer.pause()
                    elif self.state == "paused":
                        self.state = "playing"
                        pygame.mixer.music.unpause()
                        pygame.mixer.unpause()
                    continue 

                if self.state == "paused":
                    if event.key == pygame.K_q:
                        self.reset()
                        self.state = "start_screen"
                    continue

                if self.state == "playing":
                    if event.key in (pygame.K_SPACE, pygame.K_UP, pygame.K_w):
                        self.player.jump()
                        if self.sfx_jump: self.sfx_jump.play()
                    
                    elif event.key in (pygame.K_LSHIFT, pygame.K_RSHIFT):
                        if self.player.ammo > 0:
                            self.player.ammo -= 1
                            self.projectiles.append(DotProjectile(self.player.x + 20, self.player.y - 30, self.difficulty))
                            if self.sfx_jump: self.sfx_jump.play() 

                    elif event.key in (pygame.K_LCTRL, pygame.K_RCTRL):
                        if self.player.infinity_ammo > 0 and self.current_barrier and self.current_barrier.visible:
                            self.trigger_infinity_skip()

                    elif self.current_barrier and self.current_barrier.x <= self.current_barrier.target_x and not self.is_passing_barrier:
                        if event.key == pygame.K_RETURN:
                            self.submit_answer()
                        elif event.key == pygame.K_BACKSPACE:
                            self.current_barrier.user_input = self.current_barrier.user_input[:-1]
                        elif event.unicode.isdigit() or (event.unicode == "-" and self.current_barrier.user_input == ""):
                            if len(self.current_barrier.user_input) < 5:
                                self.current_barrier.user_input += event.unicode

                elif self.state == "game_over":
                    if event.key == pygame.K_r:
                        self.reset()

    def trigger_infinity_skip(self):
        self.player.infinity_ammo -= 1
        bx, by = self.current_barrier.x, GROUND_Y - 90
        self.current_barrier.visible = False

        if self.timer_is_playing and self.sfx_timer:
            self.sfx_timer.stop()
            self.timer_is_playing = False
        
        if self.sfx_blackhole:
            self.sfx_blackhole.play()

        self.active_mini_black_hole = {
            'x': bx, 
            'y': by, 
            'radius': 1, 
            'phase': 'expanding_black'
        }

        self.score += 1
        self.difficulty = 1 + self.score // 4
        self.is_passing_barrier = True
        self.passing_timer = 130

    def submit_answer(self):
        if not self.current_barrier or self.current_barrier.user_input == "":
            return

        try:
            guess = int(self.current_barrier.user_input)
        except ValueError:
            self.current_barrier.user_input = ""
            return

        if guess == self.current_barrier.answer:
            self.current_barrier.user_input = ""
            
            bx, by = self.current_barrier.x, GROUND_Y - 90
            self.current_barrier.visible = False
            
            if self.current_barrier.op in ["*", "/"]:
                self.player.ammo += 1

            if self.timer_is_playing and self.sfx_timer:
                self.sfx_timer.stop()
                self.timer_is_playing = False
            if self.sfx_explosion: self.sfx_explosion.play()

            for _ in range(25):
                self.particles.append(Particle(bx, by))
            self.shockwaves.append(Shockwave(bx, by))

            self.score += 1
            self.difficulty = 1 + self.score // 4
            self.is_passing_barrier = True
            self.passing_timer = 130
        else:
            self.health -= 1
            self.damage_flash_timer = 30
            self.current_barrier.user_input = ""
            
            if self.health <= 0:
                self.trigger_game_over("Mathematical Damage")
            else:
                if self.sfx_damage: self.sfx_damage.play()

    def update(self, dt):
        if self.damage_flash_timer > 0:
            self.damage_flash_timer -= 1

        for p in self.particles[:]:
            p.update()
            if p.life <= 0:
                self.particles.remove(p)

        for sw in self.shockwaves[:]:
            sw.update()
            if sw.life <= 0:
                self.shockwaves.remove(sw)

        if self.active_mini_black_hole:
            self.active_mini_black_hole['radius'] += 45
            
            if self.active_mini_black_hole['phase'] == 'expanding_black':
                if self.active_mini_black_hole['radius'] > 2000:
                    self.active_mini_black_hole['phase'] = 'expanding_clear'
                    self.active_mini_black_hole['radius'] = 1
                    
            elif self.active_mini_black_hole['phase'] == 'expanding_clear':
                if self.active_mini_black_hole['radius'] > 2000:
                    self.active_mini_black_hole = None

        for proj in self.projectiles[:]:
            proj.update()
            if not proj.active:
                self.projectiles.remove(proj)
                continue
            
            for ah in self.algebra_hazards[:]:
                if proj.get_rect().colliderect(ah.get_rect()):
                    proj.active = False
                    self.algebra_hazards.remove(ah)
                    
                    if self.sfx_explosion: self.sfx_explosion.play()
                    for _ in range(15):
                        self.particles.append(Particle(ah.x, ah.y))
                    
                    self.al_gebra_kills += 1
                    if self.al_gebra_kills >= 3:
                        self.al_gebra_kills = 0
                        self.player.infinity_ammo += 1
                    
                    break

        self.algebra_spawn_timer -= 1
        if self.algebra_spawn_timer <= 0:
            self.algebra_hazards.append(AlGebraHazard(self.difficulty))
            self.algebra_spawn_timer = random.randint(200, 450)
            if self.sfx_algebra: self.sfx_algebra.play()

        for ah in self.algebra_hazards[:]:
            ah.update()
            if not ah.active:
                self.algebra_hazards.remove(ah)
            elif self.player.get_rect().colliderect(ah.get_rect()):
                self.health -= 1
                self.damage_flash_timer = 30
                self.algebra_hazards.remove(ah)
                
                if self.health <= 0:
                    self.trigger_game_over("Al-Gebra Damage")
                else:
                    if self.sfx_damage: self.sfx_damage.play()

        is_moving = True
        barrier_active = (self.current_barrier and self.current_barrier.x <= self.current_barrier.target_x and not self.is_passing_barrier)
        
        if barrier_active and self.state == "playing":
            is_moving = False
            if not self.timer_is_playing and self.sfx_timer:
                self.sfx_timer.play(-1)
                self.timer_is_playing = True

        if self.is_passing_barrier:
            is_moving = True
            self.world_offset += 4
            self.passing_timer -= 1
            self.current_barrier.x -= 8

            if self.passing_timer <= 0:
                self.is_passing_barrier = False
                self.current_barrier = EquationBarrier(self.difficulty)

        elif self.current_barrier and self.current_barrier.x <= self.current_barrier.target_x:
            self.current_barrier.update(dt)

            if self.current_barrier.time_left <= 0:
                self.health -= 1
                self.damage_flash_timer = 30
                
                if self.timer_is_playing and self.sfx_timer:
                    self.sfx_timer.stop()
                    self.timer_is_playing = False

                if self.health <= 0:
                    self.trigger_game_over("Mathematical Damage")
                else:
                    if self.sfx_damage: self.sfx_damage.play()
                    self.current_barrier = EquationBarrier(self.difficulty)
        else:
            if self.current_barrier:
                self.current_barrier.x -= 6

        for s in self.symbols:
            s.update()

        self.player.update(is_moving)

    def draw(self):
        self.screen.fill(BLACK)
        
        for s in self.symbols:
            s.draw(self.screen, self.symbol_font_cache)

        if self.state == "start_screen":
            self.draw_start_screen()
            return
            
        if self.state == "rules_screen":
            self.draw_rules_screen()
            if self.start_transition and self.active_mini_black_hole and self.active_mini_black_hole['phase'] == 'expanding_black':
                r = self.active_mini_black_hole['radius']
                bh_center = (int(self.active_mini_black_hole['x']), int(self.active_mini_black_hole['y']))
                pygame.draw.circle(self.screen, BLACK, bh_center, int(r))
                pygame.draw.circle(self.screen, WHITE, bh_center, int(r), 4) 
            return

        pygame.draw.line(self.screen, WHITE, (0, GROUND_Y + 2), (SCREEN_WIDTH, GROUND_Y + 2), 2)
        grid_start = -(self.world_offset % 40)
        for x in range(grid_start, SCREEN_WIDTH, 40):
            pygame.draw.line(self.screen, (20, 20, 25), (x, GROUND_Y + 3), (x - 20, GROUND_Y + 40), 1)

        if self.current_barrier and self.current_barrier.visible:
            self.current_barrier.draw(self.screen, self.font_med, self.font_small)

        for ah in self.algebra_hazards:
            ah.draw(self.screen, self.font_giant)

        for proj in self.projectiles:
            proj.draw(self.screen, self.font_projectile)

        for sw in self.shockwaves:
            sw.draw(self.screen)

        for p in self.particles:
            p.draw(self.screen, self.font_small)

        is_moving_state = not (self.current_barrier and self.current_barrier.x <= self.current_barrier.target_x and not self.is_passing_barrier)
        
        # NOTE: Passing the current damage_flash_timer into the player's draw method!
        self.player.draw(self.screen, is_moving=is_moving_state, font_gun=self.font_gun, damage_timer=self.damage_flash_timer)
        
        if self.active_mini_black_hole:
            r = self.active_mini_black_hole['radius']
            bh_center = (int(self.active_mini_black_hole['x']), int(self.active_mini_black_hole['y']))
            
            if self.active_mini_black_hole['phase'] == 'expanding_black':
                pygame.draw.circle(self.screen, BLACK, bh_center, int(r))
                pygame.draw.circle(self.screen, WHITE, bh_center, int(r), 4) 
                
            elif self.active_mini_black_hole['phase'] == 'expanding_clear':
                overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
                overlay.fill(BLACK)
                overlay.set_colorkey((255, 0, 255))
                pygame.draw.circle(overlay, (255, 0, 255), bh_center, int(r))
                pygame.draw.circle(overlay, WHITE, bh_center, int(r), 4)
                self.screen.blit(overlay, (0, 0))

        self.draw_hud()

        if self.damage_flash_timer > 0:
            progress = self.damage_flash_timer / 30.0
            current_alpha = int(75 * math.sin(math.pi * progress))
            current_alpha = max(0, min(255, current_alpha))

            flash_surf = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            flash_surf.fill((220, 40, 40, current_alpha))
            self.screen.blit(flash_surf, (0, 0))

        if self.state == "paused":
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 180)) 
            self.screen.blit(overlay, (0, 0))

            title = self.font_giant.render("PAUSED", True, WHITE)
            self.screen.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, SCREEN_HEIGHT // 2 - 40))

            hint = self.font_small.render("Press ESC to resume or Q for Main Menu", True, DIM_WHITE)
            self.screen.blit(hint, (SCREEN_WIDTH // 2 - hint.get_width() // 2, SCREEN_HEIGHT // 2 + 50))

        if self.state == "game_over":
            self.draw_game_over()

    def draw_start_screen(self):
        title_anim = self.font_giant.render("Animation", True, ORANGE)
        title_math = self.font_giant.render(" vs Math", True, WHITE)

        total_width = title_anim.get_width() + title_math.get_width()
        start_x = SCREEN_WIDTH // 2 - total_width // 2
        y = SCREEN_HEIGHT // 2 - 50

        self.screen.blit(title_anim, (start_x, y))
        self.screen.blit(title_math, (start_x + title_anim.get_width(), y))

        if (pygame.time.get_ticks() // 600) % 2 == 0:
            hint = self.font_med.render("Press any key to continue", True, DIM_WHITE)
            self.screen.blit(hint, (SCREEN_WIDTH // 2 - hint.get_width() // 2, y + 80))

        max_radius = 2000 
        if self.opening_radius < max_radius:
            self.opening_radius += 30 
            
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
            overlay.fill(BLACK)
            overlay.set_colorkey((255, 0, 255))
            
            center = (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)
            pygame.draw.circle(overlay, (255, 0, 255), center, int(self.opening_radius))
            
            self.screen.blit(overlay, (0, 0))

    def draw_rules_screen(self):
        title = self.font_big.render("SYSTEM PROTOCOLS", True, ORANGE)
        self.screen.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 120))

        texts = [
            ("CONTROLS", CYAN),
            ("  • Jump: SPACE / W / UP Arrow", WHITE),
            ("  • Solve Equations: Type numbers, press ENTER", WHITE),
            ("  • Pause: ESC", WHITE),
            ("", WHITE),
            ("HAZARDS", CYAN),
            ("  • Equation Barriers: Solve them before the timer runs out!", WHITE),
            ("  • Al-Gebra Hazards: Spinning symbols that damage you. Jump or shoot!", WHITE),
            ("", WHITE),
            ("SPECIAL WEAPONS", CYAN),
            ("  • Dot Function f(.)= [L-SHIFT]: Shoots Al-Gebra hazards.", WHITE),
            ("      (Earn ammo by solving * and / equations)", DIM_WHITE),
            ("  • Infinity Gun f(∞)= [L-CTRL]: Instantly obliterates a math barrier!", WHITE),
            ("      (Earned by destroying 3 Al-Gebra hazards)", DIM_WHITE)
        ]

        start_y = 220
        for text, color in texts:
            if text == "":
                start_y += 15
                continue
            
            font_to_use = self.font_med if color == CYAN else self.font_small
            surf = font_to_use.render(text, True, color)
            self.screen.blit(surf, (SCREEN_WIDTH // 2 - 380, start_y))
            start_y += 35

        if (pygame.time.get_ticks() // 600) % 2 == 0:
            hint = self.font_med.render("Press ANY KEY to initiate sequence...", True, ORANGE)
            self.screen.blit(hint, (SCREEN_WIDTH // 2 - hint.get_width() // 2, start_y + 40))

    def draw_hud(self):
        HUD_X = 80

        score_surf = self.font_med.render(f"SCORE: {self.score}", True, WHITE)
        self.screen.blit(score_surf, (HUD_X, 20))
        
        for i in range(self.health):
            pygame.draw.circle(self.screen, ORANGE, (HUD_X + 5 + i * 24, 62), 7)
        
        diff_surf = self.font_small.render(f"STAGE: {self.difficulty}", True, DIM_WHITE)
        self.screen.blit(diff_surf, (HUD_X, 80))

        if self.player.ammo > 0:
            ammo_surf = self.font_small.render(f"AMMO: {self.player.ammo}", True, DIM_WHITE)
            self.screen.blit(ammo_surf, (HUD_X, 110))

        if self.player.infinity_ammo > 0:
            inf_surf = self.font_small.render(f"INFINITY BLACKHOLE GUN: {self.player.infinity_ammo}", True, WHITE)
            self.screen.blit(inf_surf, (HUD_X, 140))
        else:
            prog_surf = self.font_small.render(f"DOT FUNCTION KILLS: {self.al_gebra_kills}/3", True, WHITE)
            self.screen.blit(prog_surf, (HUD_X, 140))

    def draw_game_over(self):
        bh_center = (int(self.player.x), int(self.player.y - 30))
        pygame.draw.circle(self.screen, BLACK, bh_center, int(self.black_hole_radius))
        pygame.draw.circle(self.screen, WHITE, bh_center, int(self.black_hole_radius), 3)

        if self.black_hole_radius > 1000:
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 220))
            self.screen.blit(overlay, (0, 0))

            title = self.font_big.render(self.game_over_reason, True, RED)
            self.screen.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, SCREEN_HEIGHT // 2 - 80))

            score_txt = self.font_med.render(f"Final Score: {self.score}", True, WHITE)
            self.screen.blit(score_txt, (SCREEN_WIDTH // 2 - score_txt.get_width() // 2, SCREEN_HEIGHT // 2))

            hint = self.font_small.render("Press R to reboot or ESC to exit", True, DIM_WHITE)
            self.screen.blit(hint, (SCREEN_WIDTH // 2 - hint.get_width() // 2, SCREEN_HEIGHT // 2 + 50))

# ----------------------------------------------------------------------
if __name__ == "__main__":
    Game().run()