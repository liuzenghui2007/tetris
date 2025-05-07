import pygame
import random
import json
from datetime import datetime
import numpy as np
from scipy.io import wavfile
import wave
 
# 通用参数
sample_rate = 44100  # 采样率
duration = 0.15      # 音效时长（秒）
volume = 0.3         # 音量
 
def generate_move_sound():
    """生成移动音效（短促方波）"""
    t = np.linspace(0, duration, int(sample_rate * duration))
    freq = 800
    wave = np.sign(np.sin(2 * np.pi * freq * t))
    data = (wave * volume * 32767).astype(np.int16)
    wavfile.write('move.wav', sample_rate, data)
 
def generate_rotate_sound():
    """生成旋转音效（正弦波滑音）"""
    t = np.linspace(0, duration, int(sample_rate * duration))
    freq_start = 1200
    freq_end = 800
    freq = np.linspace(freq_start, freq_end, len(t))
    wave = np.sin(2 * np.pi * np.cumsum(freq) / sample_rate)
    data = (wave * volume * 32767).astype(np.int16)
    wavfile.write('rotate.wav', sample_rate, data)
 
def generate_clear_sound():
    """生成消除音效（和弦）"""
    t = np.linspace(0, 0.4, int(sample_rate * 0.4))
    wave = (
        np.sin(2 * np.pi * 440 * t) + 
        np.sin(2 * np.pi * 880 * t) + 
        np.sin(2 * np.pi * 1320 * t)
    ) / 3
    data = (wave * volume * 32767).astype(np.int16)
    wavfile.write('clear.wav', sample_rate, data)
 
def generate_game_over_sound():
    """生成游戏结束音效（低频脉冲）"""
    t = np.linspace(0, 1.0, int(sample_rate * 1.0))
    freq = 220 * (1 - t)  # 频率逐渐降低
    wave = np.sin(2 * np.pi * np.cumsum(freq) / sample_rate)
    wave *= np.exp(-3 * t)  # 指数衰减
    data = (wave * volume * 32767).astype(np.int16)
    wavfile.write('game_over.wav', sample_rate, data)
 
# 生成所有音效
if __name__ == "__main__":
    generate_move_sound()
    generate_rotate_sound()
    generate_clear_sound()
    generate_game_over_sound()
    print("音效文件已生成：move.wav, rotate.wav, clear.wav, game_over.wav")
 
 
# 初始化配置
pygame.init()
pygame.mixer.init()
BLOCK_SIZE = 30
GRID_PADDING = 1
GAME_WIDTH = 10
GAME_HEIGHT = 20
SCREEN_WIDTH = BLOCK_SIZE * (GAME_WIDTH + 8)
SCREEN_HEIGHT = BLOCK_SIZE * GAME_HEIGHT
FPS = 60
 
COLORS = [
    (40, 40, 40),        # 背景
    (255, 0, 0),         # 红色
    (0, 150, 0),         # 绿色
    (0, 0, 255),         # 蓝色
    (255, 120, 0),       # 橙色
    (255, 255, 0),       # 黄色
    (180, 0, 255),       # 紫色
    (0, 220, 220),       # 青色
    (100, 100, 100),     # 界面分隔色
    (200, 200, 200)      # 网格线颜色
]
 
SHAPES = [
    [[1, 1, 1, 1]],       # I
    [[1, 1], [1, 1]],     # O
    [[1, 1, 1], [0, 1, 0]], # T
    [[1, 1, 1], [1, 0, 0]], # L
    [[1, 1, 1], [0, 0, 1]], # J
    [[1, 1, 0], [0, 1, 1]], # S
    [[0, 1, 1], [1, 1, 0]]  # Z
]
 
class Button:
    def __init__(self, x, y, width, height, text, color, hover_color):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.color = color
        self.hover_color = hover_color
        self.hovered = False
 
    def draw(self, screen):
        """Draw button"""
        color = self.hover_color if self.hovered else self.color
        pygame.draw.rect(screen, color, self.rect)
        
        font = pygame.font.SysFont(None, 24)
        text_surface = font.render(self.text, True, (255, 255, 255))
        text_rect = text_surface.get_rect(center=self.rect.center)
        screen.blit(text_surface, text_rect)
 
    def check_hover(self, mouse_pos):
        """Check mouse hover"""
        self.hovered = self.rect.collidepoint(mouse_pos)
 
class Tetris:
    def __init__(self):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Tetris")
        self.clock = pygame.time.Clock()
        
        # Load sounds
        self.move_sound = pygame.mixer.Sound('move.wav')
        self.rotate_sound = pygame.mixer.Sound('rotate.wav')
        self.clear_sound = pygame.mixer.Sound('clear.wav')
        self.game_over_sound = pygame.mixer.Sound('game_over.wav')
        
        # Initialize game state
        self.high_score = 0
        self.score = 0
        self.load_high_score()
        
        # Create control buttons
        panel_x = GAME_WIDTH * BLOCK_SIZE
        button_width = 100
        button_height = 40
        self.buttons = [
            Button(panel_x + 20, 200, button_width, button_height, "Left", COLORS[7], COLORS[8]),
            Button(panel_x + 20, 260, button_width, button_height, "Right", COLORS[7], COLORS[8]),
            Button(panel_x + 20, 320, button_width, button_height, "Rotate", COLORS[7], COLORS[8]),
            Button(panel_x + 20, 380, button_width, button_height, "Drop", COLORS[7], COLORS[8])
        ]
        
        # Key states tracking
        self.key_states = {
            pygame.K_LEFT: {'pressed': False, 'last_time': 0},
            pygame.K_RIGHT: {'pressed': False, 'last_time': 0},
            pygame.K_DOWN: {'pressed': False, 'last_time': 0}
        }
        self.repeat_delay = 200  # Initial delay
        self.repeat_interval = 50  # Repeat interval
        
        self.reset_game()
 
    def load_high_score(self):
        """Load high score from file"""
        try:
            with open("highscore.json", "r") as f:
                data = json.load(f)
                self.high_score = data.get("high_score", 0)
        except (FileNotFoundError, json.JSONDecodeError):
            self.high_score = 0
 
    def save_high_score(self):
        """Save high score to file"""
        if self.score > self.high_score:
            try:
                with open("highscore.json", "w") as f:
                    json.dump({"high_score": self.score}, f)
                self.high_score = self.score
            except Exception as e:
                print(f"Error saving high score: {e}")
 
    def reset_game(self):
        """Reset game state"""
        self.game_field = [[0] * GAME_WIDTH for _ in range(GAME_HEIGHT)]
        self.score = 0
        self.level = 1
        self.current_piece = None
        self.next_piece = None
        self.paused = False
        self.game_over_flag = False
        self.start_time = datetime.now()
        self.new_piece()
 
    def create_new_piece(self):
        """Create new tetromino"""
        shape = random.choice(SHAPES)
        x = GAME_WIDTH // 2 - len(shape[0]) // 2
        return {
            'shape': shape,
            'color': random.randint(1, len(COLORS)-2),
            'x': x,
            'y': 0
        }
 
    def new_piece(self):
        """Generate new piece"""
        self.current_piece = self.next_piece if self.next_piece else self.create_new_piece()
        self.next_piece = self.create_new_piece()
        
        if self.check_collision(self.current_piece):
            self.game_over_sound.play()
            self.game_over_flag = True
            self.save_high_score()
 
    def check_collision(self, piece, dx=0, dy=0):
        """Collision detection"""
        shape = piece['shape']
        for y, row in enumerate(shape):
            for x, cell in enumerate(row):
                if cell:
                    new_x = piece['x'] + x + dx
                    new_y = piece['y'] + y + dy
                    if new_x < 0 or new_x >= GAME_WIDTH:
                        return True
                    if new_y >= GAME_HEIGHT:
                        return True
                    if new_y >= 0 and self.game_field[new_y][new_x]:
                        return True
        return False
 
    def rotate_piece(self):
        """Rotate piece with wall kicks"""
        if self.game_over_flag or self.paused:
            return
        
        original_piece = {
            'shape': [row[:] for row in self.current_piece['shape']],
            'x': self.current_piece['x'],
            'y': self.current_piece['y'],
            'color': self.current_piece['color']
        }
        
        new_shape = [list(row) for row in zip(*original_piece['shape'][::-1])]
        self.current_piece['shape'] = new_shape
        
        wall_kicks = [(0, 0), (-1, 0), (1, 0), (0, -1), (-2, 0), (2, 0)]
        for dx, dy in wall_kicks:
            if not self.check_collision(self.current_piece, dx, dy):
                self.current_piece['x'] += dx
                self.current_piece['y'] += dy
                self.rotate_sound.play()
                return
        
        self.current_piece['shape'] = original_piece['shape']
 
    def move(self, dx):
        """Move piece horizontally"""
        if self.game_over_flag or self.paused:
            return
        if not self.check_collision(self.current_piece, dx, 0):
            self.current_piece['x'] += dx
            self.move_sound.play()
 
    def drop(self):
        """Soft drop"""
        if self.game_over_flag or self.paused:
            return False
        if not self.check_collision(self.current_piece, 0, 1):
            self.current_piece['y'] += 1
            return True
        
        self.merge_piece()
        lines = self.clear_lines()
        if lines > 0:
            self.score += lines * 100
            self.level = 1 + self.score // 500
            self.clear_sound.play()
        self.new_piece()
        return False
 
    def hard_drop(self):
        """Hard drop"""
        if self.game_over_flag or self.paused:
            return
        while not self.check_collision(self.current_piece, 0, 1):
            self.current_piece['y'] += 1
        self.merge_piece()
        self.clear_lines()
        self.new_piece()
 
    def merge_piece(self):
        """Merge piece to game field"""
        shape = self.current_piece['shape']
        color = self.current_piece['color']
        for y, row in enumerate(shape):
            for x, cell in enumerate(row):
                if cell:
                    gy = y + self.current_piece['y']
                    gx = x + self.current_piece['x']
                    if 0 <= gy < GAME_HEIGHT and 0 <= gx < GAME_WIDTH:
                        self.game_field[gy][gx] = color
 
    def clear_lines(self):
        """Clear completed lines"""
        lines_cleared = 0
        new_field = []
        for row in self.game_field:
            if 0 not in row:
                lines_cleared += 1
            else:
                new_field.append(row)
        self.game_field = [[0]*GAME_WIDTH for _ in range(lines_cleared)] + new_field
        return lines_cleared
 
    def get_ghost_piece(self):
        """Get ghost piece position"""
        ghost = {
            'shape': [row[:] for row in self.current_piece['shape']],
            'x': self.current_piece['x'],
            'y': self.current_piece['y'],
            'color': self.current_piece['color']
        }
        while not self.check_collision(ghost, 0, 1):
            ghost['y'] += 1
        return ghost
 
    def draw_block(self, x, y, color, alpha=255, is_preview=False):
        """Draw single block"""
        if color == 0:
            return
        rect_size = BLOCK_SIZE - GRID_PADDING * 2
        pos_x = x * BLOCK_SIZE + GRID_PADDING
        pos_y = y * BLOCK_SIZE + GRID_PADDING
        pygame.draw.rect(self.screen, COLORS[9], (x*BLOCK_SIZE, y*BLOCK_SIZE, BLOCK_SIZE, BLOCK_SIZE), 1)
        surface = pygame.Surface((rect_size, rect_size))
        surface.set_alpha(alpha)
        base_color = list(COLORS[color])
        if is_preview:
            base_color = [min(c+50, 255) for c in base_color]
        surface.fill(base_color)
        self.screen.blit(surface, (pos_x, pos_y))
 
    def draw_piece(self, piece, alpha=255, is_preview=False):
        """Draw current piece"""
        for y, row in enumerate(piece['shape']):
            for x, cell in enumerate(row):
                if cell:
                    self.draw_block(
                        x + piece['x'],
                        y + piece['y'],
                        piece['color'],
                        alpha,
                        is_preview=is_preview
                    )
 
    def draw_sidebar(self):
        """Draw right panel"""
        panel_x = GAME_WIDTH * BLOCK_SIZE
        pygame.draw.rect(self.screen, COLORS[8], (panel_x, 0, SCREEN_WIDTH-panel_x, SCREEN_HEIGHT))
        
        font = pygame.font.SysFont(None, 24)
        
        # Score info
        high_score_text = font.render(f"High Score: {self.high_score}", True, COLORS[7])
        current_score_text = font.render(f"Score: {self.score}", True, COLORS[7])
        level_text = font.render(f"Level: {self.level}", True, COLORS[7])
        
        self.screen.blit(high_score_text, (panel_x + 10, 20))
        self.screen.blit(current_score_text, (panel_x + 10, 60))
        self.screen.blit(level_text, (panel_x + 10, 100))
        
        # Draw buttons
        for button in self.buttons:
            button.draw(self.screen)
        
        # Next piece preview
        preview_x = GAME_WIDTH + 2
        preview_y = 5
        for y, row in enumerate(self.next_piece['shape']):
            for x, cell in enumerate(row):
                if cell:
                    self.draw_block(
                        preview_x + x,
                        preview_y + y,
                        self.next_piece['color'],
                        is_preview=True
                    )
 
    def draw_game_over(self):
        """Game over screen"""
        font = pygame.font.SysFont(None, 48, bold=True)
        text = font.render("Game Over", True, (255, 0, 0))
        self.screen.blit(text, (BLOCK_SIZE*3, SCREEN_HEIGHT//2 - 48))
        
        font_small = pygame.font.SysFont(None, 24)
        text_score = font_small.render(f"Final Score: {self.score}", True, (255, 255, 255))
        self.screen.blit(text_score, (BLOCK_SIZE*3, SCREEN_HEIGHT//2))
        
        text_restart = font_small.render("Press R to restart", True, (200, 200, 200))
        self.screen.blit(text_restart, (BLOCK_SIZE*3, SCREEN_HEIGHT//2 + 40))
 
    def handle_input(self):
        """Handle input events"""
        current_time = pygame.time.get_ticks()
        mouse_pos = pygame.mouse.get_pos()
        
        # Update button states
        for button in self.buttons:
            button.check_hover(mouse_pos)
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
                
            # Mouse clicks
            if event.type == pygame.MOUSEBUTTONDOWN:
                if self.buttons[0].hovered:  # Left
                    self.move(-1)
                elif self.buttons[1].hovered:  # Right
                    self.move(1)
                elif self.buttons[2].hovered:  # Rotate
                    self.rotate_piece()
                elif self.buttons[3].hovered:  # Drop
                    self.hard_drop()
            
            # Keyboard events
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_p:
                    self.paused = not self.paused
                elif event.key == pygame.K_UP:
                    self.rotate_piece()
                elif event.key == pygame.K_SPACE:
                    self.hard_drop()
                elif event.key == pygame.K_r and self.game_over_flag:
                    self.reset_game()
                elif event.key in self.key_states:
                    self.key_states[event.key]['pressed'] = True
                    self.key_states[event.key]['last_time'] = current_time
                    # Immediate response
                    if event.key == pygame.K_LEFT:
                        self.move(-1)
                    elif event.key == pygame.K_RIGHT:
                        self.move(1)
                    elif event.key == pygame.K_DOWN:
                        self.drop()
            elif event.type == pygame.KEYUP:
                if event.key in self.key_states:
                    self.key_states[event.key]['pressed'] = False
 
        # Continuous movement
        for key in [pygame.K_LEFT, pygame.K_RIGHT, pygame.K_DOWN]:
            if self.key_states[key]['pressed']:
                time_diff = current_time - self.key_states[key]['last_time']
                if time_diff > self.repeat_delay:
                    interval = self.repeat_interval if time_diff > self.repeat_delay + self.repeat_interval else self.repeat_delay
                    if (time_diff - self.repeat_delay) % interval < 15:  # ~60fps check
                        if key == pygame.K_LEFT:
                            self.move(-1)
                        elif key == pygame.K_RIGHT:
                            self.move(1)
                        elif key == pygame.K_DOWN:
                            self.drop()
        return True
 
    def run(self):
        """Main game loop"""
        fall_time = 0
        running = True
        
        while running:
            delta_time = self.clock.tick(FPS)
            self.screen.fill(COLORS[0])
            
            # Handle input
            running = self.handle_input()
            
            if not self.paused and not self.game_over_flag:
                # Auto-drop logic
                fall_speed = max(50, 500 - self.score//10)
                fall_time += delta_time
                if fall_time >= fall_speed:
                    fall_time = 0
                    self.drop()
 
            # Draw game elements
            for y in range(GAME_HEIGHT):
                for x in range(GAME_WIDTH):
                    self.draw_block(x, y, self.game_field[y][x])
            
            if self.current_piece and not self.game_over_flag:
                ghost = self.get_ghost_piece()
                self.draw_piece(ghost, alpha=100)
                self.draw_piece(self.current_piece)
            
            self.draw_sidebar()
            
            if self.game_over_flag:
                self.draw_game_over()
            
            pygame.display.flip()
        
        pygame.quit()
 
if __name__ == "__main__":
    game = Tetris()
    game.run()
 