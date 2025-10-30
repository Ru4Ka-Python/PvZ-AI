"""
Strategic Plant Placement System
IMPROVED: Plants 3 sunflowers, then immediately starts defense
More aggressive zombie detection and response
"""

import time
from config import *
from typing import List, Tuple, Set

class PlantingStrategy:
    def __init__(self, plant_manager):
        self.plant_manager = plant_manager
        self.placed_plants = set()  # Set of (col, row) tuples
        self.last_plant_time = {}  # Track when each cell was last planted
        
        # Strategy phases
        self.production_phase = True  # Start with sun production
        self.sunflowers_needed = 3  # Start with 3 sunflowers
        self.sunflowers_planted = 0
        self.defense_started = False
        
        # Zombie tracking
        self.active_zombie_rows = set()  # Rows where zombies have appeared
        self.zombie_history = {}  # {row: last_seen_time}
        self.row_defense_started = set()  # Rows where we started defense
        
        # All rows should be defended by default
        self.rows_to_defend = set(range(GRID_ROWS))  # Defend all rows
        
    def reset(self):
        """Reset strategy state for new level"""
        self.placed_plants.clear()
        self.last_plant_time.clear()
        self.production_phase = True
        self.sunflowers_needed = 3
        self.sunflowers_planted = 0
        self.defense_started = False
        self.active_zombie_rows.clear()
        self.zombie_history.clear()
        self.row_defense_started.clear()
        self.rows_to_defend = set(range(GRID_ROWS))
        print("🔄 Стратегия сброшена")
    
    def is_cell_empty(self, col: int, row: int) -> bool:
        """Check if a grid cell is empty"""
        return (col, row) not in self.placed_plants
    
    def mark_planted(self, col: int, row: int):
        """Mark a cell as planted"""
        self.placed_plants.add((col, row))
        self.last_plant_time[(col, row)] = time.time()
    
    def remove_plant(self, col: int, row: int):
        """Remove plant marker (e.g., after it's eaten or explodes)"""
        if (col, row) in self.placed_plants:
            self.placed_plants.remove((col, row))
    
    def update_zombie_tracking(self, zombies: List[Tuple[int, int]]):
        """
        Update which rows have zombies
        zombies: list of (col, row) tuples
        """
        current_time = time.time()
        
        # Update active rows
        for col, row in zombies:
            if 0 <= row < GRID_ROWS:
                self.active_zombie_rows.add(row)
                self.zombie_history[row] = current_time
        
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
        2. СРАЗУ начать защиту всех рядов горохострелами
        3. Если появляются зомби - приоритет рядам с зомби
        4. Аварийная защита при близких зомби
        
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
                print("🌻 3 подсолнуха посажено! Начинаем защиту ВСЕХ рядов!")
                self.production_phase = False
                self.defense_started = True
        
        # Phase 2: AGGRESSIVE DEFENSE - plant shooters in all rows
        if self.defense_started and sun_count >= MIN_SUN_FOR_OFFENSE:
            # Priority 1: Rows with zombies
            if self.active_zombie_rows:
                offensive = self._plan_targeted_offense(sun_count)
                if offensive:
                    return offensive
            
            # Priority 2: All other rows (proactive defense)
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
        
        # Find dangerous zombies (col <= PANIC_COLUMN)
        dangerous = [(c, r) for c, r in zombies if c <= PANIC_COLUMN]
        
        if not dangerous:
            return None
        
        print(f"⚠️ ОПАСНОСТЬ! Зомби в колонке {dangerous[0][0]}")
        
        # Try to use instant-kill plants
        for c, r in dangerous:
            # Cherry Bomb
            if self.plant_manager.has_plant("cherry bomb") and sun_count >= 150:
                return {
                    "action": "plant",
                    "plant": "cherry bomb",
                    "col": c,
                    "row": r,
                    "reason": "🚨 EMERGENCY - Cherry Bomb"
                }
            
            # Jalapeno (clears entire row)
            if self.plant_manager.has_plant("jalapeno") and sun_count >= 125:
                return {
                    "action": "plant",
                    "plant": "jalapeno",
                    "col": c,
                    "row": r,
                    "reason": "🚨 EMERGENCY - Jalapeno"
                }
            
            # Squash
            if self.plant_manager.has_plant("squash") and sun_count >= 50:
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
                if self.is_cell_empty(max(0, c-1), r):
                    return {
                        "action": "plant",
                        "plant": "wall-nut",
                        "col": max(0, c-1),
                        "row": r,
                        "reason": "🚨 EMERGENCY - Wall-nut"
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
        """
        
        if not self.active_zombie_rows:
            return None
        
        # Try different shooters in order of preference
        shooters = [
            ("repeater", 200),
            ("snow pea", 175),
            ("peashooter", 100),
        ]
        
        # Sort active rows by priority (rows with recent zombies first)
        sorted_rows = sorted(
            self.active_zombie_rows,
            key=lambda r: self.zombie_history.get(r, 0),
            reverse=True
        )
        
        for plant_name, cost in shooters:
            if not self.plant_manager.has_plant(plant_name):
                continue
            
            if sun_count < cost:
                continue
            
            # Plant from column 1 to OFFENSE_END_COLUMN in active zombie rows
            for row in sorted_rows:
                # Mark that we started defense in this row
                if row not in self.row_defense_started:
                    self.row_defense_started.add(row)
                    print(f"🎯 Зомби обнаружены в ряду {row}! СРОЧНАЯ защита...")
                
                for col in range(OFFENSE_START_COLUMN, OFFENSE_END_COLUMN + 1):
                    if self.is_cell_empty(col, row):
                        return {
                            "action": "plant",
                            "plant": plant_name,
                            "col": col,
                            "row": row,
                            "reason": f"🎯 ЗОМБИ в ряду {row}!"
                        }
        
        return None
    
    def _plan_proactive_defense(self, sun_count: int) -> dict:
        """
        НОВАЯ ФУНКЦИЯ: Проактивная защита всех рядов
        Сажаем горохострелы во всех рядах, даже если зомби ещё не видели
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
            
            # Plant in all rows, prioritizing middle rows
            priority_rows = [2, 1, 3, 0, 4]
            
            for row in priority_rows:
                if row not in self.rows_to_defend:
                    continue
                
                # Plant from column 1 to OFFENSE_END_COLUMN
                for col in range(OFFENSE_START_COLUMN, OFFENSE_END_COLUMN + 1):
                    if self.is_cell_empty(col, row):
                        return {
                            "action": "plant",
                            "plant": plant_name,
                            "col": col,
                            "row": row,
                            "reason": f"🛡️ Защита ряда {row}"
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
                if self.is_cell_empty(defense_col, row):
                    return {
                        "action": "plant",
                        "plant": "tall-nut",
                        "col": defense_col,
                        "row": row,
                        "reason": f"🛡️ Барьер в ряду {row}"
                    }
            
            if self.plant_manager.has_plant("wall-nut") and sun_count >= 50:
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
                print(f"🧟{row} ", end="")
            else:
                print(f" {row} ", end="")
            
            for col in range(GRID_COLS):
                if (col, row) in self.placed_plants:
                    print(" ◉", end="")
                else:
                    print(" ·", end="")
            print()
        
        print()
        if self.active_zombie_rows:
            print(f"🧟 Активные ряды с зомби: {sorted(self.active_zombie_rows)}")
        else:
            print("✅ Зомби не обнаружены")
        print(f"🌻 Подсолнухов: {self.sunflowers_planted}/{self.sunflowers_needed}")
        print(f"🛡️ Защита начата: {'Да' if self.defense_started else 'Нет'}")
        print()
