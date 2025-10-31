"""
PvZ AI Configuration File
Adjust these values to match your game window and screen resolution
"""

# ===== GAME WINDOW COORDINATES =====
# Top-left corner of the game window
GAME_WINDOW_X = 0
GAME_WINDOW_Y = 0

# ===== SEED SLOT POSITIONS =====
# Format: (x, y) - coordinates of center of each seed slot
# Slots are numbered 1-10 from left to right
SEED_SLOTS = {
    1: (120, 40),   # Slot 1
    2: (180, 40),   # Slot 2
    3: (240, 40),   # Slot 3
    4: (300, 40),   # Slot 4
    5: (355, 40),   # Slot 5
    6: (415, 40),   # Slot 6
    7: (475, 40),   # Slot 7 (if exists)
    8: (535, 40),   # Slot 8 (if exists)
    9: (595, 40),   # Slot 9 (if exists)
    10: (655, 40),  # Slot 10 (if exists)
}

# ===== SUN COUNTER =====
# Region where sun counter is displayed (x, y, width, height)
SUN_COUNTER_REGION = (21, 60, 56, 24)

# ===== GAME GRID =====
# 5 rows × 9 columns grid coordinates
# Each cell contains (x, y) coordinate of its center
GRID = [
    # Row 0 (top)
    [(75, 130), (155, 130), (230, 130), (310, 130), (395, 130), 
     (475, 130), (555, 130), (635, 130), (715, 130)],
    # Row 1
    [(75, 225), (155, 225), (230, 225), (310, 225), (395, 225),
     (475, 225), (555, 225), (635, 225), (715, 225)],
    # Row 2
    [(75, 325), (155, 325), (230, 325), (310, 325), (395, 325),
     (475, 325), (555, 325), (635, 325), (715, 325)],
    # Row 3
    [(75, 425), (155, 425), (230, 425), (310, 425), (395, 425),
     (475, 425), (555, 425), (635, 425), (715, 425)],
    # Row 4 (bottom)
    [(75, 520), (155, 520), (230, 520), (310, 520), (395, 520),
     (475, 520), (555, 520), (635, 520), (715, 520)],
]

# Grid dimensions
GRID_ROWS = 5
GRID_COLS = 9

# ===== PLANT COSTS =====
PLANT_COSTS = {
    "sunflower": 50,
    "peashooter": 100,
    "snow pea": 175,
    "repeater": 200,
    "cherry bomb": 150,
    "wall-nut": 50,
    "tall-nut": 125,
    "potato mine": 25,
    "squash": 50,
    "chomper": 150,
    "spikeweed": 100,
    "jalapeno": 125,
    "torchwood": 175,
}

# ===== PLANT COOLDOWNS (in seconds) =====
PLANT_COOLDOWNS = {
    "sunflower": 7.5,
    "peashooter": 8.5,
    "snow pea": 30.0,
    "repeater": 30.0,
    "cherry bomb": 50.5,
    "wall-nut": 33.5,
    "tall-nut": 33.5,
    "potato mine": 30.0,
    "squash": 30.0,
    "chomper": 30.0,
    "spikeweed": 7.5,
    "jalapeno": 50.5,
    "torchwood": 30.0,
}

# Initial cooldowns (time before first use)
PLANT_INITIAL_COOLDOWNS = {
    "sunflower": 0.0,
    "peashooter": 0.0,
    "snow pea": 0.0,
    "repeater": 0.0,
    "cherry bomb": 37.5,
    "wall-nut": 20.5,
    "tall-nut": 20.5,
    "potato mine": 0.0,
    "squash": 0.0,
    "chomper": 0.0,
    "spikeweed": 0.0,
    "jalapeno": 37.5,
    "torchwood": 0.0,
}

# ===== ZOMBIE DETECTION =====
# Cell width and height for zombie grid mapping
CELL_WIDTH = 80
CELL_HEIGHT = 95
GRID_START_X = 75
GRID_START_Y = 85  # Понижено с 130 до 85 (хитбоксы зомби ниже)

# Offset для более точного определения ряда зомби
ZOMBIE_ROW_OFFSET = -5  # Добавляем смещение вниз для детекции

# ===== YOLO MODEL =====
YOLO_MODEL_PATH = "assets/yolov8_pvz.pt"
YOLO_CONFIDENCE = 0.4  # Понижено для лучшей детекции
YOLO_CHECK_INTERVAL = 0.5  # Reduced from 2.0 to 0.5 for faster detection

# ===== TIMING =====
LOOP_DELAY = 0.5  # Main loop delay in seconds
CLICK_DELAY = 0.15  # Delay between clicks
STATUS_CHECK_COOLDOWN = 2.0  # Seconds between status checks for same seed

# ===== STRATEGY SETTINGS =====
# Sunflower strategy
INITIAL_SUNFLOWERS = 3  # Plant 3 sunflowers first (rows 1,2,3)
ADDITIONAL_SUNFLOWERS = 2  # Plant 2 more when economy is good (rows 0,4)
ECONOMY_THRESHOLD = 300  # Sun amount to trigger additional sunflowers

# Sunflower column (always column 0)
SUNFLOWER_COLUMN = 0

# Peashooter columns (where to plant offensive plants)
OFFENSE_START_COLUMN = 1  # Start from column 1
OFFENSE_END_COLUMN = 7    # End at column 7 (увеличено для большего покрытия)

# Zombie tracking
ZOMBIE_MEMORY_TIME = 20  # Remember zombie rows for 20 seconds (уменьшено)

# Panic mode threshold (zombie column)
PANIC_COLUMN = 3  # If zombie reaches this column, use emergency plants

# Defensive plant placement
DEFENSE_TRIGGER_COLUMN = 4  # Plant walls when zombies reach this column

# Aggressive mode - start planting shooters even without seeing zombies
AGGRESSIVE_MODE = True  # После 3 подсолнухов сразу начинаем защиту
MIN_SUN_FOR_OFFENSE = 150  # Минимум солнц для начала атаки

# ===== PEASHOOTER PLACEMENT RESTRICTIONS =====
# Restrict peashooters to specific rows and columns
PEASHOOTER_ALLOWED_ROWS = [1, 2, 3]  # Rows 2, 3, 4 (0-indexed: 1, 2, 3)
PEASHOOTER_ALLOWED_COLS = [1, 2, 3, 4, 5]  # Columns 1-5

# ===== PLANT EATEN DETECTION =====
# Distance threshold for considering a plant eaten
PLANT_EATEN_THRESHOLD = 1  # If zombie is 1 cell away, consider plant eaten

# ===== CHERRY BOMB SETTINGS =====
# Minimum zombies in 3x3 area to use cherry bomb
CHERRY_BOMB_3X3_THRESHOLD = 3
# Distance threshold for placing cherry bomb near peashooter
CHERRY_BOMB_CLOSE_DISTANCE = 2  # If zombie is 2 cells from peashooter

# ===== CURSOR MOVEMENT =====
# Smooth cursor movement settings
SMOOTH_CURSOR_ENABLED = False  # Toggle smooth cursor movement
SMOOTH_CURSOR_FPS = 60  # Target FPS for smooth movement
SMOOTH_CURSOR_DURATION = 0.3  # Duration of movement in seconds
