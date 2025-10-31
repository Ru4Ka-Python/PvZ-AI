# Changelog

## v2.0 - Comprehensive AI Improvements

### Added Features

#### 1. Plant Cooldown System
- **CooldownManager class** in `strategy.py`
  - Tracks initial cooldowns and recharge times for each plant
  - Prevents spamming plant placement
  - Initial cooldowns:
    - Sunflower: 0s → 7.5s recharge
    - Peashooter: 0s → 8.5s recharge
    - Wall-nut: 20.5s initial → 33.5s recharge
    - Cherry Bomb: 37.5s initial → 50.5s recharge
  - Methods: `can_use_plant()`, `use_plant()`, `get_time_remaining()`, `reset()`

#### 2. Peashooter Zone Restrictions
- Limited to specific rows and columns for better strategy
- **PEASHOOTER_ROWS**: [1, 2, 3] (game rows 2, 3, 4)
- **PEASHOOTER_COLS**: [1, 2, 3, 4, 5]
- Implemented in `_plan_targeted_offense()` and `_plan_proactive_defense()`

#### 3. Priority Sunflower System
- AI now plants **exactly 3 sunflowers first** before any defense
- Planted in column 0, rows 1, 2, 3 (middle rows prioritized)
- Defense only starts after all 3 sunflowers are placed
- Method: `_plan_initial_sunflowers()`

#### 4. Enhanced Cherry Bomb Logic

##### 4.1 Peashooter Protection
- Monitors distance between zombies and peashooters
- Triggers cherry bomb when zombie within **2 cells** of peashooter
- Places bomb between zombie and peashooter for optimal damage
- Method: `_check_cherry_bomb_near_peashooter()`

##### 4.2 Cluster Detection
- Scans for zombie clusters in **3x3 areas**
- Triggers when **3+ zombies** grouped together
- Places bomb in center of cluster
- Method: `_check_cherry_bomb_cluster()`

#### 5. Zombie Priority System
- Tracks **closest zombie per row**
- Dictionary `closest_zombies` stores {row: (col, row)}
- Updated in `update_zombie_tracking()`
- Defense prioritizes rows with closest zombies
- Sorts rows by zombie proximity for targeted offense

### Modified Files

#### `config.py`
- Added `PLANT_COOLDOWNS` dictionary with (initial, recharge) tuples
- Added `PEASHOOTER_ROWS` and `PEASHOOTER_COLS` constants
- Added `CHERRY_BOMB_DANGER_DISTANCE`, `CHERRY_BOMB_AREA_SIZE`, `CHERRY_BOMB_MIN_ZOMBIES`

#### `strategy.py`
- Added `CooldownManager` class (54 lines)
- Modified `PlantingStrategy.__init__()`:
  - Added `cooldown_manager` instance
  - Added `placed_peashooters` dictionary for tracking shooters
  - Added `closest_zombies` dictionary for priority tracking
- Modified `PlantingStrategy.reset()`: Resets cooldown manager and new tracking dicts
- Modified `PlantingStrategy.mark_planted()`: Accepts plant_name, updates cooldown, tracks peashooters
- Modified `PlantingStrategy.update_zombie_tracking()`: Tracks closest zombie per row
- Completely rewrote `PlantingStrategy._check_emergency()`: Added cherry bomb logic
- Added `_check_cherry_bomb_near_peashooter()` method
- Added `_check_cherry_bomb_cluster()` method
- Modified all planting methods to check `cooldown_manager.can_use_plant()`
- Modified `_plan_targeted_offense()`: Zone restrictions + zombie priority
- Modified `_plan_proactive_defense()`: Zone restrictions
- Enhanced `print_grid_state()`: Shows peashooters and closest zombies

#### `main.py`
- Modified `execute_action()`: Passes `plant_name` to `strategy.mark_planted()`

#### `README.md`
- Complete rewrite documenting all v2.0 features
- Added usage instructions, configuration examples
- Added technical details and algorithm descriptions

### New Files
- `.gitignore`: Standard Python gitignore with project-specific additions

### Configuration Changes
All new configurations in `config.py` are documented and can be adjusted:

```python
# Cooldown timings (seconds)
PLANT_COOLDOWNS = {
    "sunflower": (0.0, 7.5),
    "peashooter": (0.0, 8.5),
    "wall-nut": (20.5, 33.5),
    "cherry bomb": (37.5, 50.5),
    # ...
}

# Peashooter placement restrictions
PEASHOOTER_ROWS = [1, 2, 3]  # Middle rows only
PEASHOOTER_COLS = [1, 2, 3, 4, 5]  # Left-middle columns

# Cherry bomb triggers
CHERRY_BOMB_DANGER_DISTANCE = 2  # Cells between zombie and peashooter
CHERRY_BOMB_MIN_ZOMBIES = 3  # Minimum zombies in 3x3 cluster
```

### Testing
All features tested with custom test suite:
- CooldownManager functionality
- Zone restrictions enforcement
- Cherry bomb trigger conditions
- Zombie proximity tracking
- Initial sunflower priority

### Backwards Compatibility
- Existing plant_config.json files remain compatible
- No breaking changes to game_controller.py or plant_manager.py
- Enhanced, not replaced, existing strategy logic

---

**Implemented**: All requested features from task
**Status**: Complete and tested
**Version**: 2.0
