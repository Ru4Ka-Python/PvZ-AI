"""
Strategic Plant Placement System
IMPROVED with:
- 3 sunflowers before zombies appear
- 2 more sunflowers when 2 peashooters per row in [1,2,3]
- Plant eaten detection (zombie within 2 cells)
- First zombie detection per row
- Cherry bomb on 3x3 zombie clusters
- Cherry bomb on close zombie-plant proximity
- Cooldown system
- Peashooters only in columns 1-5, rows 1-3
"""

import time
from config import *
from typing import List, Tuple, Set, Dict

class PlantingStrategy:
    def __init__(self, plant_manager):
        self.plant_manager = plant_manager
        self.placed_plants = {}  # {(col, row): {"plant": name, "time": timestamp}}
        
        # Plant cooldown tracking
        self.plant_cooldowns = {}  # {plant_name: last_used_time}
        self.game_start_time = time.time()
        
        # Strategy phases
        self.production_phase = True
        self.sunflowers_needed = 3
        self.sunflowers_planted = 0
        self.defense_started = False
        
        # Zombie tracking
        self.active_zombie_rows = set()
        self.zombie_history = {}  # {row: last_seen_time}
        self.zombie_positions = {}  # {row: [(col, first_seen_time)]}
        self.first_zombie_per_row = {}  # {row: col}
        
        # Plant eaten tracking
        self.plants_being_eaten = set()  # Set of (col, row)
        
        # Peashooter counting for sunflower expansion
        self.peashooter_count = {1: 0, 2: 0, 3: 0}  # Count per row
        
    def reset(self):
        """Reset strategy state for new level"""
        self.placed_plants.clear()
        self.plant_cooldowns.clear()
        self.game_start_time = time.time()
        
        self.production_phase = True
        self.sunflowers_needed = 3
        self.sunflowers_planted = 0
        self.defense_started = False
        
        self.active_zombie_rows.clear()
        self.zombie_history.clear()
        self.zombie_positions.clear()
        self.first_zombie_per_row.clear()
        self.plants_being_eaten.clear()
        
        self.peashooter_count = {0: 0, 1: 0, 2: 0, 3: 0, 4: 0}
        
        print("🔄 Стратегия сброшена")
    
    def is_cell_empty(self, col: int, row: int) -> bool:
        """Check if a grid cell is empty"""
        return (col, row) not in self.placed_plants
    
    def mark_planted(self, col: int, row: int, plant_name: str):
        """Mark a cell as planted and update cooldown"""
        self.placed_plants[(col, row)] = {
            "plant": plant_name,
            "time": time.time()
        }
        
        # Update cooldown
        self.plant_cooldowns[plant_name] = time.time()
        
        # Count peashooters for sunflower expansion
        if plant_name in ["peashooter", "snow pea", "repeater"] and row in [1, 2, 3]:
            self.peashooter_count[row] += 1
            self._check_sunflower_expansion()
    
    def remove_plant(self, col: int, row: int):
        """Remove plant marker"""
        if (col, row) in self.placed_plants:
            plant_data = self.placed_plants[(col, row)]
            plant_name = plant_data["plant"]
            
            # Update peashooter count
            if plant_name in ["peashooter", "snow pea", "repeater"]:
                row_num = row
                if row_num in self.peashooter_count:
                    self.peashooter_count[row_num] = max(0, self.peashooter_count[row_num] - 1)
            
            del self.placed_plants[(col, row)]
    
    def _check_sunflower_expansion(self):
        """Check if we should add 2 more sunflowers"""
        if self.sunflowers_needed > 3:
            return  # Already expanded
        
        # Check if each row [1,2,3] has at least 2 peashooters
        for row in [1, 2, 3]:
            if self.peashooter_count[row] < SUNFLOWER_EXPANSION_THRESHOLD:
                return
        
        # All rows have 2+ peashooters - expand!
        print(f"🌻 Каждый ряд [1,2,3] имеет {SUNFLOWER_EXPANSION_THRESHOLD}+ горохострелов! Добавляем еще 2 подсолнуха...")
        self.sunflowers_needed = 5
        self.production_phase = True
    
    def can_plant(self, plant_name: str) -> bool:
        """Check if plant is off cooldown"""
        current_time = time.time()
        elapsed_since_game_start = current_time - self.game_start_time
        
        # Check initial cooldown
        initial_cd = PLANT_INITIAL_COOLDOWNS.get(plant_name, 0)
        if elapsed_since_game_start < initial_cd:
            return False
        
        # Check recharge cooldown
        if plant_name in self.plant_cooldowns:
            last_used = self.plant_cooldowns[plant_name]
            recharge_cd = PLANT_RECHARGE_COOLDOWNS.get(plant_name, 0)
            if current_time - last_used < recharge_cd:
                return False
        
        return True
    
    def update_zombie_tracking(self, zombies: List[Tuple[int, int]]):
        """Update zombie positions and detect first zombie per row"""
        current_time = time.time()
        
        # Clear old positions
        self.zombie_positions.clear()
        
        # Track all zombies
        for col, row in zombies:
            if 0 <= row < GRID_ROWS:
                self.active_zombie_rows.add(row)
                self.zombie_history[row] = current_time
                
                if row not in self.zombie_positions:
                    self.zombie_positions[row] = []
                self.zombie_positions[row].append((col, current_time))
        
        # Determine first zombie (rightmost) per row
        self.first_zombie_per_row.clear()
        for row, positions in self.zombie_positions.items():
            if positions:
                # Get rightmost zombie (highest col value)
                rightmost = max(positions, key=lambda x: x[0])
                self.first_zombie_per_row[row] = rightmost[0]
        
        # Check for plants being eaten
        self._check_plants_being_eaten(zombies)
        
        # Remove stale zombie memory
        rows_to_remove = []
        for row, last_seen in self.zombie_history.items():
            if current_time - last_seen > ZOMBIE_MEMORY_TIME:
                rows_to_remove.append(row)
        
        for row in rows_to_remove:
            self.active_zombie_rows.discard(row)
            del self.zombie_history[row]
    
    def _check_plants_being_eaten(self, zombies: List[Tuple[int, int]]):
        """Check if any plants are being eaten (zombie within 2 cells)"""
        plants_to_remove = []
        
        for (plant_col, plant_row), plant_data in self.placed_plants.items():
            # Skip instant-kill plants
            if plant_data["plant"] in ["cherry bomb", "jalapeno", "squash", "potato mine"]:
                continue
            
            # Check if any zombie is within 2 cells
            for zombie_col, zombie_row in zombies:
                if zombie_row == plant_row:
                    distance = plant_col - zombie_col
                    if 0 <= distance <= PLANT_EATEN_DISTANCE:
                        # Plant is being eaten!
                        if (plant_col, plant_row) not in self.plants_being_eaten:
                            print(f"🍽️ Растение ({plant_col},{plant_row}) съедается зомби!")
                            self.plants_being_eaten.add((plant_col, plant_row))
                        plants_to_remove.append((plant_col, plant_row))
                        break
        
        # Remove eaten plants
        for pos in plants_to_remove:
            self.remove_plant(pos[0], pos[1])
    
    def _check_cherry_bomb_3x3(self, zombies: List[Tuple[int, int]]) -> dict:
        """Check if we should use cherry bomb on 3x3 cluster"""
        if not self.plant_manager.has_plant("cherry bomb"):
            return None
        
        if not self.can_plant("cherry bomb"):
            return None
        
        # Check all possible 3x3 centers
        for center_col in range(1, GRID_COLS - 1):
            for center_row in range(1, GRID_ROWS - 1):
                # Count zombies in 3x3 area
                zombie_count = 0
                for z_col, z_row in zombies:
                    if (abs(z_col - center_col) <= 1 and 
                        abs(z_row - center_row) <= 1):
                        zombie_count += 1
                
                # If 3+ zombies, use cherry bomb!
                if zombie_count >= CHERRY_BOMB_ZOMBIE_THRESHOLD:
                    if self.is_cell_empty(center_col, center_row):
                        print(f"💣 Обнаружено {zombie_count} зомби в области 3x3!")
                        return {
                            "action": "plant",
                            "plant": "cherry bomb",
                            "col": center_col,
                            "row": center_row,
                            "reason": f"💣 3x3 кластер ({zombie_count} зомби)"
                        }
        
        return None
    
    def _check_cherry_bomb_proximity(self, zombies: List[Tuple[int, int]]) -> dict:
        """Check if zombie is too close to plant (within 2 cells)"""
        if not self.plant_manager.has_plant("cherry bomb"):
            return None
        
        if not self.can_plant("cherry bomb"):
            return None
        
        # Check each plant
        for (plant_col, plant_row), plant_data in self.placed_plants.items():
            plant_name = plant_data["plant"]
            
            # Skip non-shooter plants
            if plant_name not in ["peashooter", "snow pea", "repeater"]:
                continue
            
            # Check if zombie is close
            for zombie_col, zombie_row in zombies:
                if zombie_row == plant_row:
                    distance = plant_col - zombie_col
                    if 0 <= distance <= CHERRY_BOMB_PROXIMITY:
                        # Too close! Use cherry bomb
                        bomb_col = max(0, min(GRID_COLS - 1, zombie_col))
                        bomb_row = zombie_row
                        
                        if self.is_cell_empty(bomb_col, bomb_row):
                            print(f"💣 Зомби слишком близко к растению ({plant_col},{plant_row})!")
                            return {
                                "action": "plant",
                                "plant": "cherry bomb",
                                "col": bomb_col,
                                "row": bomb_row,
                                "reason": f"💣 Близко к растению (дист: {distance})"
                            }
        
        return None
    
    def get_next_action(self, zombies: List[Tuple[int, int]], sun_count: int) -> dict:
        """Determine next planting action"""
        
        # Update zombie tracking
        self.update_zombie_tracking(zombies)
        
        # Priority 0: Cherry bomb on 3x3 clusters
        cherry_3x3 = self._check_cherry_bomb_3x3(zombies)
        if cherry_3x3 and sun_count >= 150:
            return cherry_3x3
        
        # Priority 1: Cherry bomb on close proximity
        cherry_prox = self._check_cherry_bomb_proximity(zombies)
        if cherry_prox and sun_count >= 150:
            return cherry_prox
        
        # Priority 2: Emergency defense
        emergency = self._check_emergency(zombies, sun_count)
        if emergency:
            return emergency
        
        # Priority 3: Plant initial 3 sunflowers (BEFORE zombies appear)
        if self.production_phase and self.sunflowers_planted < 3:
            sun_prod = self._plan_initial_sunflowers(sun_count)
            if sun_prod:
                return sun_prod
            else:
                # Initial sunflowers complete - start defense
                if not zombies:  # No zombies yet
                    print("🌻 3 подсолнуха посажено, ждем зомби...")
                else:
                    print("🌻 3 подсолнуха посажено! Начинаем защиту!")
                    self.production_phase = False
                    self.defense_started = True
        
        # Priority 4: Additional sunflowers (when conditions met)
        if self.sunflowers_needed == 5 and self.sunflowers_planted < 5:
            add_sun = self._plan_additional_sunflowers(sun_count)
            if add_sun:
                return add_sun
            else:
                self.production_phase = False
        
        # Priority 5: Targeted offense (rows with zombies)
        if zombies and sun_count >= MIN_SUN_FOR_OFFENSE:
            offensive = self._plan_targeted_offense(sun_count)
            if offensive:
                return offensive
        
        # Priority 6: Defense walls
        defensive = self._plan_defense(zombies, sun_count)
        if defensive:
            return defensive
        
        return None
    
    def _check_emergency(self, zombies: List[Tuple[int, int]], sun_count: int) -> dict:
        """Emergency response for close zombies"""
        dangerous = [(c, r) for c, r in zombies if c <= PANIC_COLUMN]
        
        if not dangerous:
            return None
        
        print(f"⚠️ ОПАСНОСТЬ! Зомби в колонке {dangerous[0][0]}")
        
        for c, r in dangerous:
            # Try jalapeno (clears row)
            if self.plant_manager.has_plant("jalapeno") and sun_count >= 125 and self.can_plant("jalapeno"):
                return {
                    "action": "plant",
                    "plant": "jalapeno",
                    "col": c,
                    "row": r,
                    "reason": "🚨 EMERGENCY - Jalapeno"
                }
            
            # Try squash
            if self.plant_manager.has_plant("squash") and sun_count >= 50 and self.can_plant("squash"):
                if self.is_cell_empty(max(0, c-1), r):
                    return {
                        "action": "plant",
                        "plant": "squash",
                        "col": max(0, c-1),
                        "row": r,
                        "reason": "🚨 EMERGENCY - Squash"
                    }
            
            # Try wall-nut
            if self.plant_manager.has_plant("wall-nut") and sun_count >= 50 and self.can_plant("wall-nut"):
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
        """Plant first 3 sunflowers in column 0, rows [1,2,3]"""
        if not self.plant_manager.has_plant("sunflower"):
            return None
        
        if sun_count < 50:
            return None
        
        if not self.can_plant("sunflower"):
            return None
        
        # Plant in middle rows first
        priority_rows = [2, 1, 3]
        
        for row in priority_rows:
            if self.sunflowers_planted >= 3:
                break
            
            if self.is_cell_empty(0, row):
                self.sunflowers_planted += 1
                return {
                    "action": "plant",
                    "plant": "sunflower",
                    "col": 0,
                    "row": row,
                    "reason": f"☀️ Подсолнух {self.sunflowers_planted}/3"
                }
        
        return None
    
    def _plan_additional_sunflowers(self, sun_count: int) -> dict:
        """Plant additional 2 sunflowers (rows 0 and 4)"""
        if not self.plant_manager.has_plant("sunflower"):
            return None
        
        if sun_count < 50:
            return None
        
        if not self.can_plant("sunflower"):
            return None
        
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
        """Plant shooters in rows with zombies (ONLY columns 1-5, rows 1-3)"""
        if not self.active_zombie_rows:
            return None
        
        shooters = [
            ("peashooter", 100),
            ("snow pea", 175),
            ("repeater", 200),
        ]
        
        # Filter to only allowed rows
        allowed_rows = [r for r in self.active_zombie_rows if r in OFFENSE_ROWS]
        
        if not allowed_rows:
            return None
        
        # Sort by first zombie position (prioritize rows with closer zombies)
        sorted_rows = sorted(
            allowed_rows,
            key=lambda r: self.first_zombie_per_row.get(r, 999)
        )
        
        for plant_name, cost in shooters:
            if not self.plant_manager.has_plant(plant_name):
                continue
            
            if sun_count < cost:
                continue
            
            if not self.can_plant(plant_name):
                continue
            
            # Plant in columns 1-5 only
            for row in sorted_rows:
                for col in range(OFFENSE_START_COLUMN, OFFENSE_END_COLUMN + 1):
                    if self.is_cell_empty(col, row):
                        return {
                            "action": "plant",
                            "plant": plant_name,
                            "col": col,
                            "row": row,
                            "reason": f"🎯 ЗОМБИ в ряду {row} (кол: {self.first_zombie_per_row.get(row, '?')})"
                        }
        
        return None
    
    def _plan_defense(self, zombies: List[Tuple[int, int]], sun_count: int) -> dict:
        """Plan defensive walls"""
        approaching = {}
        for c, r in zombies:
            if c <= DEFENSE_TRIGGER_COLUMN and r < GRID_ROWS:
                if r not in approaching or c < approaching[r]:
                    approaching[r] = c
        
        if not approaching:
            return None
        
        for row, zombie_col in approaching.items():
            defense_col = max(0, zombie_col - 1)
            
            if self.plant_manager.has_plant("wall-nut") and sun_count >= 50 and self.can_plant("wall-nut"):
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
        """Print visual grid"""
        print("\n🗺️ Текущая карта растений:")
        print("   ", end="")
        for col in range(GRID_COLS):
            print(f" {col}", end="")
        print()
        
        for row in range(GRID_ROWS):
            marker = "🧟" if row in self.active_zombie_rows else " "
            print(f"{marker}{row} ", end="")
            
            for col in range(GRID_COLS):
                if (col, row) in self.placed_plants:
                    print(" ◉", end="")
                else:
                    print(" ·", end="")
            print()
        
        print()
        if self.first_zombie_per_row:
            for row, col in sorted(self.first_zombie_per_row.items()):
                print(f"🧟 Ряд {row}: первый зомби в колонке {col}")
        print(f"🌻 Подсолнухов: {self.sunflowers_planted}/{self.sunflowers_needed}")
        print(f"🔫 Горохострелов по рядам: {self.peashooter_count}")
        print()
