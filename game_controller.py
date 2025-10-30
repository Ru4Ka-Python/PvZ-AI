"""
Game Controller - Handles all interactions with the game
Updated to work with improved zombie detection
"""

import pyautogui
import time
import cv2
import numpy as np
from config import *

class GameController:
    def __init__(self):
        self.last_click_time = 0
        pyautogui.PAUSE = 0.05  # Reduce default pause
        pyautogui.FAILSAFE = True  # Move mouse to corner to stop
    
    def click_seed(self, coord: tuple) -> bool:
        """Click on a seed slot"""
        try:
            x, y = coord
            pyautogui.click(x, y)
            time.sleep(CLICK_DELAY)
            self.last_click_time = time.time()
            return True
        except Exception as e:
            print(f"❌ Ошибка клика по семени {coord}: {e}")
            return False
    
    def click_grid(self, col: int, row: int) -> bool:
        """Click on a grid cell"""
        try:
            if not (0 <= row < GRID_ROWS and 0 <= col < GRID_COLS):
                print(f"❌ Неверные координаты: col={col}, row={row}")
                return False
            
            x, y = GRID[row][col]
            pyautogui.click(x, y)
            time.sleep(CLICK_DELAY)
            self.last_click_time = time.time()
            return True
        except Exception as e:
            print(f"❌ Ошибка клика по ячейке ({col},{row}): {e}")
            return False
    
    def plant(self, plant_coord: tuple, grid_col: int, grid_row: int) -> bool:
        """Plant a plant at specified grid location"""
        try:
            # Click seed
            if not self.click_seed(plant_coord):
                return False
            
            # Click grid location
            if not self.click_grid(grid_col, grid_row):
                return False
            
            return True
        except Exception as e:
            print(f"❌ Ошибка посадки: {e}")
            return False
    
    def check_seed_ready(self, coord: tuple) -> bool:
        """
        Check if seed is ready (not recharging)
        Uses visual detection of seed brightness
        """
        try:
            x, y = coord
            
            # Capture seed icon area
            size = 45
            region = (x - size//2, y - size//2, size, size)
            screenshot = pyautogui.screenshot(region=region)
            img = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
            
            # Convert to HSV
            hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
            
            # Check average brightness (V channel)
            avg_brightness = np.mean(hsv[:, :, 2])
            
            # If brightness > threshold, seed is ready
            is_ready = avg_brightness > 80
            
            return is_ready
        except Exception as e:
            print(f"⚠️ Ошибка проверки семени: {e}")
            return True  # Assume ready on error
    
    def collect_collectibles(self, yolo_model, sun_tracker=None):
        """
        Collect suns and coins using YOLO detection
        If sun_tracker is provided, update sun count
        Returns number of items collected
        """
        if yolo_model is None:
            return 0
        
        try:
            screenshot = pyautogui.screenshot()
            frame = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
            
            results = yolo_model.predict(source=frame, conf=YOLO_CONFIDENCE, verbose=False)[0]
            
            collected = 0
            sun_collected = 0
            
            for box in results.boxes:
                cls_id = int(box.cls[0])
                label = yolo_model.names[cls_id]
                
                if label in ["sun", "coin"]:
                    x, y, w, h = box.xywh[0].cpu().numpy()
                    pyautogui.click(int(x), int(y))
                    collected += 1
                    
                    # Track sun collection
                    if label == "sun" and sun_tracker is not None:
                        sun_tracker.add_sun(25)  # Default sun value
                        sun_collected += 1
                    
                    time.sleep(0.05)
            
            if sun_collected > 0 and sun_tracker is not None:
                print(f"☀️ Собрано солнц: {sun_collected} (+{sun_collected * 25}) | Всего: {sun_tracker.sun_count}")
            
            return collected
        
        except Exception as e:
            print(f"⚠️ Ошибка сбора: {e}")
            return 0
    
    def detect_zombies(self, yolo_model) -> list:
        """
        Detect zombie positions using YOLO with improved hitbox detection
        """
        try:
            screenshot = pyautogui.screenshot()
            frame = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
            
            results = yolo_model.predict(source=frame, conf=YOLO_CONFIDENCE, verbose=False)[0]
            
            zombies = []
            for box in results.boxes:
                label = yolo_model.names[int(box.cls[0])]
                
                if label == "zombie":
                    x, y, w, h = box.xywh[0].cpu().numpy()
                    
                    # Применяем смещение для более точного определения ряда
                    # Используем нижнюю часть хитбокса зомби
                    adjusted_y = y + (h / 2) + ZOMBIE_ROW_OFFSET
                    
                    col, row = self._pixel_to_grid(x, adjusted_y)
                    
                    if 0 <= col < GRID_COLS and 0 <= row < GRID_ROWS:
                        zombies.append((col, row))
            
            return zombies
        
        except Exception as e:
            print(f"⚠️ Ошибка детекции зомби: {e}")
            return []
    
    def _pixel_to_grid(self, x: float, y: float) -> tuple:
        """
        Convert pixel coordinates to grid cell
        Улучшенная версия с более точным определением ряда
        """
        col = int((x - GRID_START_X) // CELL_WIDTH)
        row = int((y - GRID_START_Y) // CELL_HEIGHT)
        
        # Ограничиваем значения
        col = max(0, min(GRID_COLS - 1, col))
        row = max(0, min(GRID_ROWS - 1, row))
        
        return col, row
    
    def emergency_stop(self):
        """Emergency stop - move mouse to corner"""
        print("\n🛑 АВАРИЙНАЯ ОСТАНОВКА")
        pyautogui.moveTo(0, 0)
