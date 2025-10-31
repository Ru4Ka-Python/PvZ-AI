"""
Strategic Plant Placement System
UPDATED VERSION:
- Improved zombie tracking with memory
- Sunflowers in row 1, columns 1-5
- Peashooters prioritize row 2, then expand
- Detects when plants are eaten
"""

import time
from config import *
from typing import List, Tuple, Set, Dict, Optional

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


class ZombieTracker:
    """Enhanced zombie tracking system with memory"""
    def __init__(self):
        self.zombie_history = {}  # {zombie_id: [(col, row, timestamp), ...]}
        self.current_zombies = []  # Current frame zombies: [(col, row)]
        self.closest_zombies_per_row = {}  # {row: (col, row)}
        self.active_rows = set()  # Rows with zombies
        self.next_zombie_id = 0
        
    def update(self, detected_zombies: List[Tuple[int, int]]):
        """
        Update zombie tracking with new detections
        Tracks zombie movement to detect if they ate plants
        """
        current_time = time.time()
        self.current_zombies = detected_zombies
        
        # Update closest zombie per row
        self.closest_zombies_per_row.clear()
        self.active_rows.clear()
        
        for col, row in detected_zombies:
            self.active_rows.add(row)
            if row not in self.closest_zombies_per_row or col < self.closest_zombies_per_row[row][0]:
                self.closest_zombies_per_row[row] = (col, row)
        
        # Simple tracking: store positions by row
        # We track the closest zombie in each row
        for row in self.active_rows:
            col, _ = self.closest_zombies_per_row[row]
            key = f"row_{row}"
            if key not in self.zombie_history:
                self.zombie_history[key] = []
            
            self.zombie_history[key].append((col, row, current_time))
            
            # Keep only last 10 positions per row
            if len(self.zombie_history[key]) > 10:
                self.zombie_history[key] = self.zombie_history[key][-10:]
    
    def get_zombie_movement(self, row: int) -> Optional[int]:
        """
        Get how many cells a zombie moved in a row
        Returns negative number if moved towards plants (left)
        """
        key = f"row_{row}"
        if key not in self.zombie_history or len(self.zombie_history[key]) < 2:
            return None
        
        # Compare current position with position 2 frames ago
        if len(self.zombie_history[key]) >= 3:
            old_col = self.zombie_history[key][-3][0]
            current_col = self.zombie_history[key][-1][0]
            movement = old_col - current_col  # Positive = moved towards plants
            return movement
        
        return None
    
    def get_closest_zombie_per_row(self) -> Dict[int, Tuple[int, int]]:
        """Get closest zombie position for each row"""
        return self.closest_zombies_per_row.copy()
    
    def get_active_rows(self) -> Set[int]:
        """Get rows that have zombies"""
        return self.active_rows.copy()
    
    def get_sorted_rows_by_danger(self) -> List[int]:
        """
        Get rows sorted by danger level (closest zombie = most dangerous)
        """
        rows_with_distance = []
        for row, (col, _) in self.closest_zombies_per_row.items():
            rows_with_distance.append((row, col))
        
        # Sort by column (lower column = closer to plants = more dangerous)
        rows_with_distance.sort(key=lambda x: x[1])
        
        return [row for row, col in rows_with_distance]
    
    def reset(self):
        """Reset all tracking"""
        self.zombie_history.clear()
        self.current_zombies.clear()
        self.closest_zombies_per_row.clear()
        self.active_rows.clear()
        self.next_zombie_id = 0


class PlantMemory:
    """Memory system for tracking planted plants"""
    def __init__(self):
        self.plants = {}  # {(col, row): {"type": plant_name, "planted_at": timestamp}}
        self.peashooters = {}  # {(col, row): plant_name}
        
    def add_plant(self, col: int, row: int, plant_name: str):
        """Add a plant to memory"""
        self.plants[(col, row)] = {
            "type": plant_name,
            "planted_at": time.time()
        }
        
        # Track peashooters separately
        if plant_name in ["peashooter", "snow pea", "repeater"]:
            self.peashooters[(col, row)] = plant_name
    
    def remove_plant(self, col: int, row: int):
        """Remove a plant from memory"""
        pos = (col, row)
        if pos in self.plants:
            del self.plants[pos]
        if pos in self.peashooters:
            del self.peashooters[pos]
    
    def has_plant_at(self, col: int, row: int) -> bool:
        """Check if there's a plant at position"""
        return (col, row) in self.plants
    
    def get_plant_at(self, col: int, row: int) -> Optional[Dict]:
        """Get plant info at position"""
        return self.plants.get((col, row))
    
    def get_all_plants(self) -> Set[Tuple[int, int]]:
        """Get all plant positions"""
        return set(self.plants.keys())
    
    def get_peashooters(self) -> Dict[Tuple[int, int], str]:
        """Get all peashooter positions"""
        return self.peashooters.copy()
    
    def reset(self):
        """Reset memory"""
        self.plants.clear()
        self.peashooters.clear()


class PlantingStrategy:
    def __init__(self, plant_manager):
        self.plant_manager = plant_manager
        
        # New memory systems
        self.plant_memory = PlantMemory()
        self.zombie_tracker = ZombieTracker()
        
        # Legacy compatibility
        self.placed_plants = set()
        self.placed_peashooters = {}
        self.last_plant_time = {}
        
        # Cooldown manager
        self.cooldown_manager = CooldownManager()
        
        # Strategy phases
        self.production_phase = True
        self.sunflowers_needed = 3
        self.sunflowers_planted = 0
        self.defense_started = False
        
        # Row 2 (primary peashooter row) tracking
        self.row2_filled = False
        
    def reset(self):
        """Reset strategy state for new level"""
        self.plant_memory.reset()
        self.zombie_tracker.reset()
        self.placed_plants.clear()
        self.placed_peashooters.clear()
        self.last_plant_time.clear()
        self.cooldown_manager.reset()
        self.production_phase = True
        self.sunflowers_needed = 3
        self.sunflowers_planted = 0
        self.defense_started = False
        self.row2_filled = False
        print("🔄 Стратегия сброшена")
    
    def is_cell_empty(self, col: int, row: int) -> bool:
        """Check if a grid cell is empty"""
        return not self.plant_memory.has_plant_at(col, row)
    
    def mark_planted(self, col: int, row: int, plant_name: str = None):
        """Mark a cell as planted"""
        self.placed_plants.add((col, row))
        self.last_plant_time[(col, row)] = time.time()
        
        if plant_name:
            self.plant_memory.add_plant(col, row, plant_name)
            self.cooldown_manager.use_plant(plant_name)
            
            # Track peashooters for legacy code
            if plant_name in ["peashooter", "snow pea", "repeater"]:
                self.placed_peashooters[(col, row)] = plant_name
    
    def remove_plant(self, col: int, row: int):
        """Remove plant marker (e.g., after it's eaten or explodes)"""
        if (col, row) in self.placed_plants:
            self.placed_plants.remove((col, row))
        if (col, row) in self.placed_peashooters:
            del self.placed_peashooters[(col, row)]
        self.plant_memory.remove_plant(col, row)
    
    def check_plants_eaten(self):
        """
        Check if any plants were eaten by zombies
        If zombie moved 2+ cells past a plant position, mark plant as eaten
        """
        for row in self.zombie_tracker.get_active_rows():
            movement = self.zombie_tracker.get_zombie_movement(row)
            if movement and movement >= ZOMBIE_MOVEMENT_THRESHOLD:
                # Zombie moved forward significantly
                closest_zombie = self.zombie_tracker.closest_zombies_per_row.get(row)
                if closest_zombie:
                    zombie_col, _ = closest_zombie
                    
                    # Check plants behind the zombie
                    for col in range(zombie_col - movement, zombie_col):
                        if self.plant_memory.has_plant_at(col, row):
                            plant_info = self.plant_memory.get_plant_at(col, row)
                            print(f"🍽️ Зомби съел растение {plant_info['type']} на ({col},{row})")
                            self.remove_plant(col, row)
    
    def update_zombie_tracking(self, zombies: List[Tuple[int, int]]):
        """Update zombie tracking system"""
        self.zombie_tracker.update(zombies)
        self.check_plants_eaten()
    
    def get_next_action(self, zombies: List[Tuple[int, int]], sun_count: int) -> dict:
        """
        Determine next planting action based on game state
        
        NEW STRATEGY:
        1. Plant 3 sunflowers in row 1, columns 1-5
        2. Fill row 2 with peashooters (columns 1-5)
        3. After row 2 is filled, plant 2 more sunflowers
        4. Expand peashooters to rows 3 and 4
        5. Emergency defense when needed
        
        Returns:
            dict with "action", "plant", "col", "row" or None if no action needed
        """
        
        # Update zombie tracking
        self.update_zombie_tracking(zombies)
        
        # Phase 0: Emergency defense (zombies too close)
        emergency = self._check_emergency(zombies, sun_count)
        if emergency:
            return emergency
        
        # Phase 1: Plant initial 3 sunflowers in row 1
        if self.production_phase and self.sunflowers_planted < self.sunflowers_needed:
            sun_prod = self._plan_initial_sunflowers(sun_count)
            if sun_prod:
                return sun_prod
            else:
                # Initial sunflowers planted - start defense
                print(f"🌻 {self.sunflowers_planted} подсолнухов посажено! Начинаем защиту ряда 2!")
                self.production_phase = False
                self.defense_started = True
        
        # Phase 2: Fill row 2 with peashooters (priority)
        if self.defense_started and not self.row2_filled and sun_count >= MIN_SUN_FOR_OFFENSE:
            row2_action = self._plan_row2_peashooters(sun_count)
            if row2_action:
                return row2_action
            else:
                # Row 2 is filled, plant 2 more sunflowers
                if self.sunflowers_needed == 3:
                    print("🎯 Ряд 2 заполнен горохострелами! Сажаем 2 дополнительных подсолнуха...")
                    self.sunflowers_needed = 5
                    self.production_phase = True
                    self.row2_filled = True
        
        # Phase 3: Plant additional sunflowers (after row 2 filled)
        if self.production_phase and self.row2_filled and self.sunflowers_planted < self.sunflowers_needed:
            additional = self._plan_additional_sunflowers(sun_count)
            if additional:
                return additional
            else:
                print("🌻 Все подсолнухи посажены! Продолжаем защиту...")
                self.production_phase = False
        
        # Phase 4: Aggressive defense - expand to other rows
        if self.defense_started and sun_count >= MIN_SUN_FOR_OFFENSE:
            # Priority to rows with zombies
            if self.zombie_tracker.get_active_rows():
                targeted = self._plan_targeted_offense(sun_count)
                if targeted:
                    return targeted
            
            # Proactive defense in remaining rows
            proactive = self._plan_proactive_defense(sun_count)
            if proactive:
                return proactive
        
        # Phase 5: Defensive reinforcement (walls)
        defensive = self._plan_defense(zombies, sun_count)
        if defensive:
            return defensive
        
        return None
    
    def _check_emergency(self, zombies: List[Tuple[int, int]], sun_count: int) -> dict:
        """Check for emergency situations requiring immediate action"""
        
        # Check 1: Zombie very close to peashooter
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
            
            # Jalapeno
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
        peashooters = self.plant_memory.get_peashooters()
        
        for pea_pos, pea_type in peashooters.items():
            pea_col, pea_row = pea_pos
            
            # Find zombies in same row
            for z_col, z_row in zombies:
                if z_row == pea_row:
                    distance = abs(z_col - pea_col)
                    
                    if distance <= CHERRY_BOMB_DANGER_DISTANCE:
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
        for center_col, center_row in zombies:
            zombies_in_area = []
            
            for z_col, z_row in zombies:
                col_diff = abs(z_col - center_col)
                row_diff = abs(z_row - center_row)
                
                if col_diff <= 1 and row_diff <= 1:
                    zombies_in_area.append((z_col, z_row))
            
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
        Plant first 3 sunflowers in row 1 (index 0), columns 1-5
        """
        if not self.plant_manager.has_plant("sunflower"):
            return None
        
        if sun_count < 50:
            return None
        
        if not self.cooldown_manager.can_use_plant("sunflower"):
            remaining = self.cooldown_manager.get_time_remaining("sunflower")
            if remaining > 0:
                print(f"⏳ Подсолнух перезаряжается: {remaining:.1f}с")
            return None
        
        # Plant in row 1 (SUNFLOWER_ROW = 0), columns 1-5
        for col in SUNFLOWER_COLUMNS:
            if self.sunflowers_planted >= self.sunflowers_needed:
                break
            
            if self.is_cell_empty(col, SUNFLOWER_ROW):
                self.sunflowers_planted += 1
                print(f"☀️ Сажаю подсолнух {self.sunflowers_planted}/{self.sunflowers_needed} в ряду 1, колонка {col}")
                return {
                    "action": "plant",
                    "plant": "sunflower",
                    "col": col,
                    "row": SUNFLOWER_ROW,
                    "reason": f"☀️ Подсолнух {self.sunflowers_planted}/{self.sunflowers_needed}"
                }
        
        return None
    
    def _plan_additional_sunflowers(self, sun_count: int) -> dict:
        """Plant additional 2 sunflowers in row 1"""
        if not self.plant_manager.has_plant("sunflower"):
            return None
        
        if sun_count < 50:
            return None
        
        if not self.cooldown_manager.can_use_plant("sunflower"):
            return None
        
        # Continue planting in row 1, columns 1-5
        for col in SUNFLOWER_COLUMNS:
            if self.is_cell_empty(col, SUNFLOWER_ROW):
                self.sunflowers_planted += 1
                return {
                    "action": "plant",
                    "plant": "sunflower",
                    "col": col,
                    "row": SUNFLOWER_ROW,
                    "reason": f"☀️ Доп. подсолнух {self.sunflowers_planted}/5"
                }
        
        return None
    
    def _plan_row2_peashooters(self, sun_count: int) -> dict:
        """
        Fill row 2 (PEASHOOTER_PRIMARY_ROW) with peashooters first
        Priority order: columns 1, 2, 3, 4, 5
        """
        shooters = [
            ("peashooter", 100),
            ("snow pea", 175),
            ("repeater", 200),
        ]
        
        for plant_name, cost in shooters:
            if not self.plant_manager.has_plant(plant_name):
                continue
            
            if sun_count < cost:
                continue
            
            if not self.cooldown_manager.can_use_plant(plant_name):
                continue
            
            # Plant in row 2, columns 1-5
            for col in PEASHOOTER_COLS:
                if self.is_cell_empty(col, PEASHOOTER_PRIMARY_ROW):
                    print(f"🔫 Заполняю ряд 2: сажаю {plant_name} в колонке {col}")
                    return {
                        "action": "plant",
                        "plant": plant_name,
                        "col": col,
                        "row": PEASHOOTER_PRIMARY_ROW,
                        "reason": f"🎯 Приоритет ряд 2, колонка {col}"
                    }
        
        return None
    
    def _plan_targeted_offense(self, sun_count: int) -> dict:
        """
        Plant offensive plants in rows where zombies detected
        Higher priority for rows with closer zombies
        """
        active_rows = self.zombie_tracker.get_active_rows()
        if not active_rows:
            return None
        
        shooters = [
            ("peashooter", 100),
            ("snow pea", 175),
            ("repeater", 200),
        ]
        
        # Get rows sorted by danger (closest zombie first)
        sorted_rows = self.zombie_tracker.get_sorted_rows_by_danger()
        
        for plant_name, cost in shooters:
            if not self.plant_manager.has_plant(plant_name):
                continue
            
            if sun_count < cost:
                continue
            
            if not self.cooldown_manager.can_use_plant(plant_name):
                continue
            
            for row in sorted_rows:
                # Only plant in allowed peashooter rows
                if row not in PEASHOOTER_ROWS:
                    continue
                
                # Get available columns (expand dynamically)
                available_cols = self._get_available_columns()
                
                for col in available_cols:
                    if self.is_cell_empty(col, row):
                        zombie_info = self.zombie_tracker.closest_zombies_per_row.get(row)
                        zombie_col = zombie_info[0] if zombie_info else "?"
                        print(f"🎯 Зомби в ряду {row+1}, колонка {zombie_col}! Сажаю {plant_name} → ({col},{row+1})")
                        return {
                            "action": "plant",
                            "plant": plant_name,
                            "col": col,
                            "row": row,
                            "reason": f"🎯 Зомби в ряду {row+1}, колонка {zombie_col}"
                        }
        
        return None
    
    def _plan_proactive_defense(self, sun_count: int) -> dict:
        """
        Proactive defense: expand peashooters to remaining rows
        Priority: rows 3, 4 (after row 2 is filled)
        """
        shooters = [
            ("peashooter", 100),
            ("snow pea", 175),
            ("repeater", 200),
        ]
        
        for plant_name, cost in shooters:
            if not self.plant_manager.has_plant(plant_name):
                continue
            
            if sun_count < cost:
                continue
            
            if not self.cooldown_manager.can_use_plant(plant_name):
                continue
            
            # Plant in secondary rows (3, 4)
            for row in PEASHOOTER_SECONDARY_ROWS:
                available_cols = self._get_available_columns()
                
                for col in available_cols:
                    if self.is_cell_empty(col, row):
                        print(f"🛡️ Проактивная защита: сажаю {plant_name} в ряду {row+1}, колонка {col}")
                        return {
                            "action": "plant",
                            "plant": plant_name,
                            "col": col,
                            "row": row,
                            "reason": f"🛡️ Защита ряда {row+1}"
                        }
        
        return None
    
    def _get_available_columns(self) -> List[int]:
        """
        Get available columns for peashooters (expands dynamically)
        Start with 1-5, expand to 6-7, then 8
        """
        # Start with primary columns
        current_cols = PEASHOOTER_COLS
        
        # Check if primary columns are filled in primary rows
        all_primary_filled = True
        for col in current_cols:
            for row in PEASHOOTER_ROWS:
                if self.is_cell_empty(col, row):
                    all_primary_filled = False
                    break
            if not all_primary_filled:
                break
        
        if not all_primary_filled:
            return current_cols
        
        # Expand to 6-7
        extended_cols = current_cols + PEASHOOTER_COLS_EXTENDED
        
        all_extended_filled = True
        for col in PEASHOOTER_COLS_EXTENDED:
            for row in PEASHOOTER_ROWS:
                if self.is_cell_empty(col, row):
                    all_extended_filled = False
                    break
            if not all_extended_filled:
                break
        
        if not all_extended_filled:
            return extended_cols
        
        # Expand to column 8
        return extended_cols + PEASHOOTER_COLS_FINAL
    
    def _plan_defense(self, zombies: List[Tuple[int, int]], sun_count: int) -> dict:
        """Plan defensive plant placement for rows with close zombies"""
        approaching = {}
        for c, r in zombies:
            if c <= DEFENSE_TRIGGER_COLUMN and r < GRID_ROWS:
                if r not in approaching or c < approaching[r]:
                    approaching[r] = c
        
        if not approaching:
            return None
        
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
                            "reason": f"🛡️ Барьер в ряду {row+1}"
                        }
            
            if self.plant_manager.has_plant("wall-nut") and sun_count >= 50:
                if self.cooldown_manager.can_use_plant("wall-nut"):
                    if self.is_cell_empty(defense_col, row):
                        return {
                            "action": "plant",
                            "plant": "wall-nut",
                            "col": defense_col,
                            "row": row,
                            "reason": f"🛡️ Барьер в ряду {row+1}"
                        }
        
        return None
    
    def print_grid_state(self):
        """Print visual representation of planted grid with zombie info"""
        print("\n🗺️ Текущая карта растений:")
        print("   ", end="")
        for col in range(GRID_COLS):
            print(f" {col}", end="")
        print()
        
        active_rows = self.zombie_tracker.get_active_rows()
        closest_zombies = self.zombie_tracker.get_closest_zombie_per_row()
        
        for row in range(GRID_ROWS):
            # Highlight rows with zombies
            if row in active_rows:
                zombie_col = closest_zombies.get(row, (99, row))[0]
                print(f"🧟{row+1}", end="")
            else:
                print(f" {row+1}", end="")
            
            for col in range(GRID_COLS):
                if self.plant_memory.has_plant_at(col, row):
                    plant_info = self.plant_memory.get_plant_at(col, row)
                    if plant_info["type"] in ["peashooter", "snow pea", "repeater"]:
                        print(" 🔫", end="")
                    elif plant_info["type"] == "sunflower":
                        print(" 🌻", end="")
                    else:
                        print(" ◉", end="")
                else:
                    print(" ·", end="")
            print()
        
        print()
        if active_rows:
            print(f"🧟 Активные ряды с зомби: {sorted([r+1 for r in active_rows])}")
            for row in sorted(active_rows):
                if row in closest_zombies:
                    col, _ = closest_zombies[row]
                    print(f"   Ряд {row+1}: ближайший зомби в колонке {col}")
        else:
            print("✅ Зомби не обнаружены")
        
        print(f"🌻 Подсолнухов: {self.sunflowers_planted}/{self.sunflowers_needed}")
        print(f"🎯 Ряд 2 заполнен: {'Да' if self.row2_filled else 'Нет'}")
        print(f"🛡️ Защита начата: {'Да' if self.defense_started else 'Нет'}")
        
        available_cols = self._get_available_columns()
        print(f"🔫 Доступные колонки для горохострелов: {available_cols}")
        print()
