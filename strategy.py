"""
Strategic Plant Placement System
IMPROVED: Plants 3 sunflowers, then immediately starts defense
More aggressive zombie detection and response
WITH COOLDOWN SYSTEM AND CHERRY BOMB LOGIC
"""

import time
from config import *
from typing import List, Tuple, Set, Dict

class CooldownManager:
    """Manages cooldown timers for each plant type"""
    def __init__(self):
        self.cooldowns = {}  # {plant_name: time_when_ready}
        self.start_time = time.time()
    
    def can_use_plant(self, plant_name: str) -> bool:
        """Check if plant is off cooldown"""
        current_time = time.time()
        
        # If plant never used, check initial cooldown
        if plant_name not in self.cooldowns:
            initial_cooldown, _ = PLANT_COOLDOWNS.get(plant_name, (0, 0))
            ready_time = self.start_time + initial_cooldown
            return current_time >= ready_time
        
        # Check if recharge finished
        return current_time >= self.cooldowns[plant_name]
    
    def use_plant(self, plant_name: str):
        """Mark plant as used and start recharge cooldown"""
        current_time = time.time()
        _, recharge_cooldown = PLANT_COOLDOWNS.get(plant_name, (0, 0))
        self.cooldowns[plant_name] = current_time + recharge_cooldown
    
    def get_time_remaining(self, plant_name: str) -> float:
        """Get remaining cooldown time in seconds"""
        current_time = time.time()
        
        if plant_name not in self.cooldowns:
            initial_cooldown, _ = PLANT_COOLDOWNS.get(plant_name, (0, 0))
            ready_time = self.start_time + initial_cooldown
            remaining = ready_time - current_time
            return max(0, remaining)
        
        remaining = self.cooldowns[plant_name] - current_time
        return max(0, remaining)
    
    def reset(self):
        """Reset all cooldowns"""
        self.cooldowns.clear()
        self.start_time = time.time()


class PlantingStrategy:
    def __init__(self, plant_manager):
        self.plant_manager = plant_manager
        self.placed_plants = set()  # Set of (col, row) tuples
        self.placed_peashooters = {}  # {(col, row): plant_name} - track peashooters
        self.last_plant_time = {}  # Track when each cell was last planted
        
        # Cooldown manager
        self.cooldown_manager = CooldownManager()
        
        # Strategy phases
        self.production_phase = True  # Start with sun production
        self.sunflowers_needed = 3  # Start with 3 sunflowers
        self.sunflowers_planted = 0
        self.defense_started = False
        
        # Zombie tracking
        self.active_zombie_rows = set()  # Rows where zombies have appeared
        self.zombie_history = {}  # {row: last_seen_time}
        self.row_defense_started = set()  # Rows where we started defense
        self.closest_zombies = {}  # {row: (col, row)} - closest zombie per row
        
        # All rows should be defended by default
        self.rows_to_defend = set(range(GRID_ROWS))  # Defend all rows
        
    def reset(self):
        """Reset strategy state for new level"""
        self.placed_plants.clear()
        self.placed_peashooters.clear()
        self.last_plant_time.clear()
        self.cooldown_manager.reset()
        self.production_phase = True
        self.sunflowers_needed = 3
        self.sunflowers_planted = 0
        self.defense_started = False
        self.active_zombie_rows.clear()
        self.zombie_history.clear()
        self.row_defense_started.clear()
        self.closest_zombies.clear()
        self.rows_to_defend = set(range(GRID_ROWS))
        print("🔄 Стратегия сброшена")
    
    def is_cell_empty(self, col: int, row: int) -> bool:
        """Check if a grid cell is empty"""
        return (col, row) not in self.placed_plants
    
    def mark_planted(self, col: int, row: int, plant_name: str = None):
        """Mark a cell as planted"""
        self.placed_plants.add((col, row))
        self.last_plant_time[(col, row)] = time.time()
        
        # Track peashooters and similar shooters
        if plant_name in ["peashooter", "snow pea", "repeater"]:
            self.placed_peashooters[(col, row)] = plant_name
        
        # Mark cooldown
        if plant_name:
            self.cooldown_manager.use_plant(plant_name)
    
    def remove_plant(self, col: int, row: int):
        """Remove plant marker (e.g., after it's eaten or explodes)"""
        if (col, row) in self.placed_plants:
            self.placed_plants.remove((col, row))
        if (col, row) in self.placed_peashooters:
            del self.placed_peashooters[(col, row)]
    
    def update_zombie_tracking(self, zombies: List[Tuple[int, int]]):
        """
        Update which rows have zombies and find closest zombie per row
        zombies: list of (col, row) tuples
        """
        current_time = time.time()
        
        # Clear closest zombies tracking
        self.closest_zombies.clear()
        
        # Update active rows and find closest zombie per row
        for col, row in zombies:
            if 0 <= row < GRID_ROWS:
                self.active_zombie_rows.add(row)
                self.zombie_history[row] = current_time
                
                # Track closest zombie in each row (lowest col = closest to plants)
                if row not in self.closest_zombies or col < self.closest_zombies[row][0]:
                    self.closest_zombies[row] = (col, row)
        
        # Remove rows where zombies haven't been seen for ZOMBIE_MEMORY_TIME
        rows_to_remove = []
        for row, last_seen in self.zombie_history.items():
            if current_time - last_seen > ZOMBIE_MEMORY_TIME:
                rows_to_remove.append(row)
        
        for row in rows_to_remove:
            if row in self.active_zombie_rows:
                self.active_zombie_rows.discard(row)
            del self.zombie_history[row]
    
    def get_next_action(self, zombies: List[Tuple[int, int]], sun_count: int) -> dict:
        """
        Determine next planting action based on game state
        
        НОВАЯ СТРАТЕГИЯ:
        1. Посадить 3 подсолнуха в колонке 0 (ряды 1, 2, 3)
        2. СРАЗУ начать защиту рядов 2, 3, 4 горохострелами (колонки 1-5)
        3. Если появляются зомби - приоритет ближайшим зомби
        4. Аварийная защита при близких зомби (вишня)
        
        Returns:
            dict with "action", "plant", "col", "row" or None if no action needed
        """
        
        # Update zombie tracking
        self.update_zombie_tracking(zombies)
        
        # Phase 0: Emergency defense (zombies too close)
        emergency = self._check_emergency(zombies, sun_count)
        if emergency:
            return emergency
        
        # Phase 1: Plant initial 3 sunflowers in column 0
        if self.production_phase and self.sunflowers_planted < self.sunflowers_needed:
            sun_prod = self._plan_initial_sunflowers(sun_count)
            if sun_prod:
                return sun_prod
            else:
                # All initial sunflowers planted - START DEFENSE IMMEDIATELY
                print("🌻 3 подсолнуха посажено! Начинаем защиту рядов 2, 3, 4!")
                self.production_phase = False
                self.defense_started = True
        
        # Phase 2: AGGRESSIVE DEFENSE - plant shooters in allowed rows
        if self.defense_started and sun_count >= MIN_SUN_FOR_OFFENSE:
            # Priority 1: Rows with zombies
            if self.active_zombie_rows:
                offensive = self._plan_targeted_offense(sun_count)
                if offensive:
                    return offensive
            
            # Priority 2: Proactive defense in allowed rows
            proactive = self._plan_proactive_defense(sun_count)
            if proactive:
                return proactive
        
        # Phase 3: If we have good economy (300+ sun), plant 2 more sunflowers
        if sun_count >= ECONOMY_THRESHOLD and self.sunflowers_needed == 3 and self.sunflowers_planted >= 3:
            print("💰 Хорошая экономика! Добавляем ещё 2 подсолнуха...")
            self.sunflowers_needed = 5
            self.production_phase = True
            return self._plan_additional_sunflowers(sun_count)
        
        # Phase 4: Defensive reinforcement (walls)
        defensive = self._plan_defense(zombies, sun_count)
        if defensive:
            return defensive
        
        return None
    
    def _check_emergency(self, zombies: List[Tuple[int, int]], sun_count: int) -> dict:
        """Check for emergency situations requiring immediate action"""
        
        # Check 1: Zombie very close to peashooter (within CHERRY_BOMB_DANGER_DISTANCE)
        if self.plant_manager.has_plant("cherry bomb") and sun_count >= 150:
            if self.cooldown_manager.can_use_plant("cherry bomb"):
                cherry_action = self._check_cherry_bomb_near_peashooter(zombies)
                if cherry_action:
                    return cherry_action
        
        # Check 2: Multiple zombies in 3x3 area
        if self.plant_manager.has_plant("cherry bomb") and sun_count >= 150:
            if self.cooldown_manager.can_use_plant("cherry bomb"):
                cherry_action = self._check_cherry_bomb_cluster(zombies)
                if cherry_action:
                    return cherry_action
        
        # Check 3: Dangerous zombies (col <= PANIC_COLUMN)
        dangerous = [(c, r) for c, r in zombies if c <= PANIC_COLUMN]
        
        if not dangerous:
            return None
        
        print(f"⚠️ ОПАСНОСТЬ! Зомби в колонке {dangerous[0][0]}")
        
        # Try to use instant-kill plants
        for c, r in dangerous:
            # Cherry Bomb
            if self.plant_manager.has_plant("cherry bomb") and sun_count >= 150:
                if self.cooldown_manager.can_use_plant("cherry bomb"):
                    return {
                        "action": "plant",
                        "plant": "cherry bomb",
                        "col": c,
                        "row": r,
                        "reason": "🚨 EMERGENCY - Cherry Bomb"
                    }
            
            # Jalapeno (clears entire row)
            if self.plant_manager.has_plant("jalapeno") and sun_count >= 125:
                if self.cooldown_manager.can_use_plant("jalapeno"):
                    return {
                        "action": "plant",
                        "plant": "jalapeno",
                        "col": c,
                        "row": r,
                        "reason": "🚨 EMERGENCY - Jalapeno"
                    }
            
            # Squash
            if self.plant_manager.has_plant("squash") and sun_count >= 50:
                if self.cooldown_manager.can_use_plant("squash"):
                    if self.is_cell_empty(max(0, c-1), r):
                        return {
                            "action": "plant",
                            "plant": "squash",
                            "col": max(0, c-1),
                            "row": r,
                            "reason": "🚨 EMERGENCY - Squash"
                        }
            
            # Wall-nut as last resort
            if self.plant_manager.has_plant("wall-nut") and sun_count >= 50:
                if self.cooldown_manager.can_use_plant("wall-nut"):
                    if self.is_cell_empty(max(0, c-1), r):
                        return {
                            "action": "plant",
                            "plant": "wall-nut",
                            "col": max(0, c-1),
                            "row": r,
                            "reason": "🚨 EMERGENCY - Wall-nut"
                        }
        
        return None
    
    def _check_cherry_bomb_near_peashooter(self, zombies: List[Tuple[int, int]]) -> dict:
        """Check if zombie is very close to a peashooter and use cherry bomb"""
        for pea_pos, pea_type in self.placed_peashooters.items():
            pea_col, pea_row = pea_pos
            
            # Find zombies in same row
            for z_col, z_row in zombies:
                if z_row == pea_row:
                    # Check distance between zombie and peashooter
                    distance = abs(z_col - pea_col)
                    
                    if distance <= CHERRY_BOMB_DANGER_DISTANCE:
                        # Place cherry bomb between zombie and peashooter
                        cherry_col = min(z_col, pea_col) + abs(z_col - pea_col) // 2
                        cherry_col = max(0, min(GRID_COLS - 1, cherry_col))
                        
                        print(f"💣 Зомби очень близко к горохострелу! ({z_col},{z_row}) → ({pea_col},{pea_row})")
                        return {
                            "action": "plant",
                            "plant": "cherry bomb",
                            "col": cherry_col,
                            "row": z_row,
                            "reason": f"💣 Защита горохострела! Дистанция: {distance}"
                        }
        
        return None
    
    def _check_cherry_bomb_cluster(self, zombies: List[Tuple[int, int]]) -> dict:
        """Check if there are multiple zombies in 3x3 area"""
        # Group zombies and find clusters
        for center_col, center_row in zombies:
            # Count zombies in 3x3 area around this zombie
            zombies_in_area = []
            
            for z_col, z_row in zombies:
                col_diff = abs(z_col - center_col)
                row_diff = abs(z_row - center_row)
                
                # Check if within 3x3 area (1 cell in each direction)
                if col_diff <= 1 and row_diff <= 1:
                    zombies_in_area.append((z_col, z_row))
            
            # If enough zombies clustered, use cherry bomb
            if len(zombies_in_area) >= CHERRY_BOMB_MIN_ZOMBIES:
                print(f"💣 Группа зомби обнаружена! {len(zombies_in_area)} зомби в области 3x3")
                return {
                    "action": "plant",
                    "plant": "cherry bomb",
                    "col": center_col,
                    "row": center_row,
                    "reason": f"💣 Группа {len(zombies_in_area)} зомби!"
                }
        
        return None
    
    def _plan_initial_sunflowers(self, sun_count: int) -> dict:
        """
        Plant first 3 sunflowers in column 0
        Priority order: rows 2, 1, 3 (middle rows first)
        """
        
        if not self.plant_manager.has_plant("sunflower"):
            return None
        
        if sun_count < 50:
            return None
        
        # Check cooldown
        if not self.cooldown_manager.can_use_plant("sunflower"):
            remaining = self.cooldown_manager.get_time_remaining("sunflower")
            if remaining > 0:
                print(f"⏳ Подсолнух перезаряжается: {remaining:.1f}с")
            return None
        
        # Plant order: middle rows first for better coverage
        priority_rows = [2, 1, 3, 0, 4]
        
        for row in priority_rows:
            if self.sunflowers_planted >= self.sunflowers_needed:
                break
            
            if self.is_cell_empty(0, row):
                self.sunflowers_planted += 1
                return {
                    "action": "plant",
                    "plant": "sunflower",
                    "col": 0,
                    "row": row,
                    "reason": f"☀️ Подсолнух {self.sunflowers_planted}/{self.sunflowers_needed}"
                }
        
        return None
    
    def _plan_additional_sunflowers(self, sun_count: int) -> dict:
        """Plant additional 2 sunflowers (rows 0 and 4)"""
        
        if not self.plant_manager.has_plant("sunflower"):
            return None
        
        if sun_count < 50:
            return None
        
        # Check cooldown
        if not self.cooldown_manager.can_use_plant("sunflower"):
            return None
        
        # Plant in rows 0 and 4 (top and bottom)
        for row in [0, 4]:
            if self.is_cell_empty(0, row):
                self.sunflowers_planted += 1
                return {
                    "action": "plant",
                    "plant": "sunflower",
                    "col": 0,
                    "row": row,
                    "reason": f"☀️ Доп. подсолнух {self.sunflowers_planted}/5"
                }
        
        return None
    
    def _plan_targeted_offense(self, sun_count: int) -> dict:
        """
        Plant offensive plants in rows where zombies have been detected
        HIGHER PRIORITY than proactive defense
        RESTRICTED to rows 2,3,4 (indices 1,2,3) and columns 1-5
        PRIORITIZES closest zombies
        """
        
        if not self.active_zombie_rows:
            return None
        
        # Try different shooters in order of preference
        shooters = [
            ("peashooter", 100),  # Start cheap
            ("snow pea", 175),
            ("repeater", 200),
        ]
        
        # Sort active rows by closest zombie (lowest column = highest priority)
        sorted_rows = sorted(
            self.active_zombie_rows,
            key=lambda r: self.closest_zombies.get(r, (999, r))[0]  # Sort by zombie column
        )
        
        for plant_name, cost in shooters:
            if not self.plant_manager.has_plant(plant_name):
                continue
            
            if sun_count < cost:
                continue
            
            # Check cooldown
            if not self.cooldown_manager.can_use_plant(plant_name):
                continue
            
            # Plant only in allowed rows for peashooters
            for row in sorted_rows:
                # Restrict peashooters to rows 2, 3, 4 (indices 1, 2, 3)
                if row not in PEASHOOTER_ROWS:
                    continue
                
                # Mark that we started defense in this row
                if row not in self.row_defense_started:
                    self.row_defense_started.add(row)
                    closest_col = self.closest_zombies.get(row, (999, row))[0]
                    print(f"🎯 Зомби обнаружены в ряду {row}, колонка {closest_col}! СРОЧНАЯ защита...")
                
                # Plant only in allowed columns (1-5)
                for col in PEASHOOTER_COLS:
                    if self.is_cell_empty(col, row):
                        closest_zombie_col = self.closest_zombies.get(row, (999, row))[0]
                        return {
                            "action": "plant",
                            "plant": plant_name,
                            "col": col,
                            "row": row,
                            "reason": f"🎯 ЗОМБИ близко! Ряд {row}, зомби в колонке {closest_zombie_col}"
                        }
        
        return None
    
    def _plan_proactive_defense(self, sun_count: int) -> dict:
        """
        НОВАЯ ФУНКЦИЯ: Проактивная защита
        Сажаем горохострелы, ОГРАНИЧЕНИЕ на ряды 2,3,4 (indices 1,2,3) и колонки 1-5
        """
        
        # Try different shooters in order of preference
        shooters = [
            ("peashooter", 100),  # Начинаем с дешёвых
            ("snow pea", 175),
            ("repeater", 200),
        ]
        
        for plant_name, cost in shooters:
            if not self.plant_manager.has_plant(plant_name):
                continue
            
            if sun_count < cost:
                continue
            
            # Check cooldown
            if not self.cooldown_manager.can_use_plant(plant_name):
                continue
            
            # Plant only in allowed rows (2, 3, 4 - indices 1, 2, 3)
            priority_rows = [2, 1, 3]  # Middle first
            
            for row in priority_rows:
                if row not in PEASHOOTER_ROWS:
                    continue
                
                if row not in self.rows_to_defend:
                    continue
                
                # Plant only in allowed columns (1-5)
                for col in PEASHOOTER_COLS:
                    if self.is_cell_empty(col, row):
                        return {
                            "action": "plant",
                            "plant": plant_name,
                            "col": col,
                            "row": row,
                            "reason": f"🛡️ Защита ряда {row} (проактивная)"
                        }
        
        return None
    
    def _plan_defense(self, zombies: List[Tuple[int, int]], sun_count: int) -> dict:
        """Plan defensive plant placement for rows with close zombies"""
        
        # Find rows with zombies approaching (col <= DEFENSE_TRIGGER_COLUMN)
        approaching = {}  # {row: closest_col}
        for c, r in zombies:
            if c <= DEFENSE_TRIGGER_COLUMN and r < GRID_ROWS:
                if r not in approaching or c < approaching[r]:
                    approaching[r] = c
        
        if not approaching:
            return None
        
        # Place defensive plants in front of approaching zombies
        for row, zombie_col in approaching.items():
            defense_col = max(0, zombie_col - 1)
            
            # Try Tall-nut first, then Wall-nut
            if self.plant_manager.has_plant("tall-nut") and sun_count >= 125:
                if self.cooldown_manager.can_use_plant("tall-nut"):
                    if self.is_cell_empty(defense_col, row):
                        return {
                            "action": "plant",
                            "plant": "tall-nut",
                            "col": defense_col,
                            "row": row,
                            "reason": f"🛡️ Барьер в ряду {row}"
                        }
            
            if self.plant_manager.has_plant("wall-nut") and sun_count >= 50:
                if self.cooldown_manager.can_use_plant("wall-nut"):
                    if self.is_cell_empty(defense_col, row):
                        return {
                            "action": "plant",
                            "plant": "wall-nut",
                            "col": defense_col,
                            "row": row,
                            "reason": f"🛡️ Барьер в ряду {row}"
                        }
        
        return None
    
    def print_grid_state(self):
        """Print visual representation of planted grid with zombie rows highlighted"""
        print("\n🗺️ Текущая карта растений:")
        print("   ", end="")
        for col in range(GRID_COLS):
            print(f" {col}", end="")
        print()
        
        for row in range(GRID_ROWS):
            # Highlight rows with zombies
            if row in self.active_zombie_rows:
                zombie_col = self.closest_zombies.get(row, (99, row))[0]
                print(f"🧟{row} ", end="")
            else:
                print(f" {row} ", end="")
            
            for col in range(GRID_COLS):
                if (col, row) in self.placed_plants:
                    if (col, row) in self.placed_peashooters:
                        print(" 🔫", end="")
                    else:
                        print(" ◉", end="")
                else:
                    print(" ·", end="")
            print()
        
        print()
        if self.active_zombie_rows:
            print(f"🧟 Активные ряды с зомби: {sorted(self.active_zombie_rows)}")
            for row in sorted(self.active_zombie_rows):
                if row in self.closest_zombies:
                    col, _ = self.closest_zombies[row]
                    print(f"   Ряд {row}: ближайший зомби в колонке {col}")
        else:
            print("✅ Зомби не обнаружены")
        print(f"🌻 Подсолнухов: {self.sunflowers_planted}/{self.sunflowers_needed}")
        print(f"🛡️ Защита начата: {'Да' if self.defense_started else 'Нет'}")
        print()
