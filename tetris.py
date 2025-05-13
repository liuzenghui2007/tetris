import pygame
import sys
import random
import os

# 游戏窗口参数
WINDOW_WIDTH = 400
WINDOW_HEIGHT = 500
GRID_SIZE = 25
COLUMNS = 10
ROWS = 20

# 优化后的配色方案
BG_COLOR = (30, 36, 40)         # 深灰蓝，护眼
GRID_COLOR = (60, 70, 80)       # 柔和深灰蓝
SCORE_COLOR = (255, 220, 120)   # 柔和暖黄
NEXT_BG = (40, 48, 56)          # 深灰蓝，和背景区分
PAUSE_COLOR = (120, 200, 180)   # 柔和青绿色
GAMEOVER_COLOR = (255, 140, 120) # 柔和橙红

# 颜色定义
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GRAY = (128, 128, 128)
COLORS = [
    (120, 210, 255),   # I型：天蓝
    (120, 160, 255),   # J型：柔和蓝
    (255, 180, 120),   # L型：橙黄
    (255, 220, 120),   # O型：暖黄
    (120, 255, 180),   # S型：青绿
    (200, 120, 255),   # T型：紫色
    (255, 120, 180)    # Z型：粉红
]

# 七种方块的形状
SHAPES = [
    [[1, 1, 1, 1]],  # I
    [[1, 0, 0], [1, 1, 1]],  # J
    [[0, 0, 1], [1, 1, 1]],  # L
    [[1, 1], [1, 1]],        # O
    [[0, 1, 1], [1, 1, 0]],  # S
    [[0, 1, 0], [1, 1, 1]],  # T
    [[1, 1, 0], [0, 1, 1]]   # Z
]

# 行消除与得分
SCORES = [0, 100, 300, 600, 1000]  # 消除0~4行的得分

# 音效文件路径
SOUND_FILES = {
    'rotate': 'sounds/rotate.mp3',
    'move': 'sounds/move.mp3',
    'clear': 'sounds/clear.mp3',
    'game_over': 'sounds/game_over.mp3',
    'land': 'sounds/land.mp3'
}

# 音效对象
sounds = {}

# 加载自定义字体
FONT_PATH = os.path.join(os.path.dirname(__file__), 'fonts', 'STHeiti Medium.ttc')

def load_sounds():
    """加载所有音效"""
    try:
        pygame.mixer.init()
        # 加载背景音乐
        pygame.mixer.music.load('sounds/tetris_theme.mp3')
        pygame.mixer.music.set_volume(0.3)
        pygame.mixer.music.play(-1)  # -1表示循环播放
        print('背景音乐加载成功')
        
        # 加载音效
        for name, file in SOUND_FILES.items():
            try:
                sounds[name] = pygame.mixer.Sound(file)
                sounds[name].set_volume(0.5)  # 设置音效音量
                print(f'音效 {name} 加载成功')
            except pygame.error as e:
                print(f'音效 {name} 加载失败:', e)
    except Exception as e:
        print('音效加载失败:', e)

def play_sound(name):
    """播放指定音效"""
    if name in sounds:
        sounds[name].play()

# 方块类
class Tetromino:
    def __init__(self, shape, color):
        self.shape = shape
        self.color = color
        self.x = COLUMNS // 2 - len(shape[0]) // 2
        self.y = 0

    def rotate(self):
        # 顺时针旋转
        self.shape = [list(row) for row in zip(*self.shape[::-1])]

# 创建空网格
def create_grid():
    return [[None for _ in range(COLUMNS)] for _ in range(ROWS)]

# 检查方块是否可以移动
def valid_move(grid, tetromino, dx, dy, rotated_shape=None):
    shape = rotated_shape if rotated_shape else tetromino.shape
    for y, row in enumerate(shape):
        for x, cell in enumerate(row):
            if cell:
                nx = tetromino.x + x + dx
                ny = tetromino.y + y + dy
                if nx < 0 or nx >= COLUMNS or ny < 0 or ny >= ROWS:
                    return False
                if grid[ny][nx]:
                    return False
    return True

# 将方块固定到网格上
def lock_tetromino(grid, tetromino):
    for y, row in enumerate(tetromino.shape):
        for x, cell in enumerate(row):
            if cell:
                grid[tetromino.y + y][tetromino.x + x] = tetromino.color

# 随机生成一个方块
def get_new_tetromino():
    idx = random.randint(0, 6)
    return Tetromino(SHAPES[idx], COLORS[idx])

# 绘制网格和方块
def draw_grid(screen, grid):
    for y in range(ROWS):
        for x in range(COLUMNS):
            rect = pygame.Rect(x * GRID_SIZE, y * GRID_SIZE, GRID_SIZE, GRID_SIZE)
            pygame.draw.rect(screen, GRID_COLOR, rect, 1)
            if grid[y][x]:
                pygame.draw.rect(screen, grid[y][x], rect)

def draw_tetromino(screen, tetromino):
    for y, row in enumerate(tetromino.shape):
        for x, cell in enumerate(row):
            if cell:
                rect = pygame.Rect((tetromino.x + x) * GRID_SIZE, (tetromino.y + y) * GRID_SIZE, GRID_SIZE, GRID_SIZE)
                pygame.draw.rect(screen, tetromino.color, rect)

# 行消除与得分
def clear_lines(grid):
    cleared = 0
    new_grid = []
    for row in grid:
        if all(row):
            cleared += 1
        else:
            new_grid.append(row)
    for _ in range(cleared):
        new_grid.insert(0, [None for _ in range(COLUMNS)])
    return new_grid, cleared

# 在界面上显示分数
def draw_score(screen, score):
    font = pygame.font.Font(FONT_PATH, 24)
    text = font.render(f'分数: {score}', True, SCORE_COLOR)
    screen.blit(text, (WINDOW_WIDTH - 150, 20))

# 绘制下一块方块预览
def draw_next(screen, next_tetromino):
    font = pygame.font.Font(FONT_PATH, 20)
    text = font.render('下一块:', True, SCORE_COLOR)
    screen.blit(text, (WINDOW_WIDTH - 150, 70))
    preview_rect = pygame.Rect(WINDOW_WIDTH - 130, 95, 4 * GRID_SIZE, 4 * GRID_SIZE)
    pygame.draw.rect(screen, NEXT_BG, preview_rect, border_radius=8)
    for y, row in enumerate(next_tetromino.shape):
        for x, cell in enumerate(row):
            if cell:
                rect = pygame.Rect(WINDOW_WIDTH - 120 + x * GRID_SIZE, 100 + y * GRID_SIZE, GRID_SIZE, GRID_SIZE)
                pygame.draw.rect(screen, next_tetromino.color, rect)

# 游戏结束界面
def draw_game_over(screen, score):
    font1 = pygame.font.Font(FONT_PATH, 36)
    font2 = pygame.font.Font(FONT_PATH, 24)
    text1 = font1.render('游戏结束', True, GAMEOVER_COLOR)
    text2 = font2.render(f'最终得分: {score}', True, SCORE_COLOR)
    text3 = font2.render('按回车键重新开始', True, SCORE_COLOR)
    screen.blit(text1, (WINDOW_WIDTH // 2 - 80, WINDOW_HEIGHT // 2 - 60))
    screen.blit(text2, (WINDOW_WIDTH // 2 - 80, WINDOW_HEIGHT // 2 - 20))
    screen.blit(text3, (WINDOW_WIDTH // 2 - 110, WINDOW_HEIGHT // 2 + 20))

def main():
    pygame.init()
    screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    pygame.display.set_caption('俄罗斯方块')
    clock = pygame.time.Clock()
    
    # 加载音效
    load_sounds()
    
    def reset():
        grid = create_grid()
        current = get_new_tetromino()
        next_tetromino = get_new_tetromino()
        score = 0
        return grid, current, next_tetromino, score

    grid, current, next_tetromino, score = reset()
    fall_time = 0
    fall_speed = 0.5
    paused = False
    game_over = False

    running = True
    while running:
        dt = clock.tick(60) / 1000
        if not paused and not game_over:
            fall_time += dt
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    if not game_over:
                        paused = not paused
                if not paused and not game_over:
                    if event.key == pygame.K_LEFT:
                        if valid_move(grid, current, -1, 0):
                            current.x -= 1
                            play_sound('move')
                    elif event.key == pygame.K_RIGHT:
                        if valid_move(grid, current, 1, 0):
                            current.x += 1
                            play_sound('move')
                    elif event.key == pygame.K_DOWN:
                        # 快速下落到底部
                        while valid_move(grid, current, 0, 1):
                            current.y += 1
                        play_sound('land')  # 播放落地音效
                        lock_tetromino(grid, current)
                        grid, cleared = clear_lines(grid)
                        if cleared > 0:
                            play_sound('clear')
                        score += SCORES[cleared]
                        current = next_tetromino
                        next_tetromino = get_new_tetromino()
                        if not valid_move(grid, current, 0, 0):
                            game_over = True
                            play_sound('game_over')
                        fall_time = 0  # 重置下落时间
                    elif event.key == pygame.K_UP:
                        rotated = [list(row) for row in zip(*current.shape[::-1])]
                        if valid_move(grid, current, 0, 0, rotated):
                            current.shape = rotated
                            play_sound('rotate')
                if game_over and event.key == pygame.K_RETURN:
                    grid, current, next_tetromino, score = reset()
                    fall_time = 0
                    paused = False
                    game_over = False

        if not paused and not game_over:
            if fall_time > fall_speed:
                if valid_move(grid, current, 0, 1):
                    current.y += 1
                else:
                    lock_tetromino(grid, current)
                    play_sound('land')
                    grid, cleared = clear_lines(grid)
                    if cleared > 0:
                        play_sound('clear')
                    score += SCORES[cleared]
                    current = next_tetromino
                    next_tetromino = get_new_tetromino()
                    if not valid_move(grid, current, 0, 0):
                        game_over = True
                        play_sound('game_over')
                fall_time = 0

        screen.fill(BG_COLOR)
        draw_grid(screen, grid)
        if not game_over:
            draw_tetromino(screen, current)
        draw_score(screen, score)
        draw_next(screen, next_tetromino)
        if paused and not game_over:
            font = pygame.font.Font(FONT_PATH, 36)
            text = font.render('暂停', True, PAUSE_COLOR)
            screen.blit(text, (WINDOW_WIDTH // 2 - 50, WINDOW_HEIGHT // 2 - 20))
        if game_over:
            draw_game_over(screen, score)
        pygame.display.flip()

    pygame.quit()
    sys.exit()

if __name__ == '__main__':
    main()
