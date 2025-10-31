"""
PvZ AI - Main Controller
With improved strategy and cooldown tracking
"""

import time
import keyboard
import os
import sys
from plant_manager import PlantManager
from strategy import PlantingStrategy
from game_controller import GameController
from config import *

# Optional: YOLO model
try:
    from ultralytics import YOLO
    yolo_available = os.path.exists(YOLO_MODEL_PATH)
    if yolo_available:
        yolo_model = YOLO(YOLO_MODEL_PATH)
        print("✅ YOLO модель загружена")
    else:
        yolo_model = None
        print("⚠️ YOLO модель не найдена, работа без детекции зомби")
except ImportError:
    yolo_model = None
    yolo_available = False
    print("⚠️ Ultralytics не установлен, работа без детекции зомби")


class SunTracker:
    """Отслеживание количества солнц"""
    def __init__(self, initial_sun=50):
        self.sun_count = initial_sun
        self.total_collected = 0
        self.total_spent = 0
    
    def add_sun(self, amount=25):
        """Добавить солнца (при сборе)"""
        self.sun_count += amount
        self.total_collected += amount
    
    def spend_sun(self, amount):
        """Потратить солнца (при посадке)"""
        if self.sun_count >= amount:
            self.sun_count -= amount
            self.total_spent += amount
            return True
        return False
    
    def can_afford(self, cost):
        """Проверить, хватает ли солнц"""
        return self.sun_count >= cost
    
    def reset(self, initial_sun=50):
        """Сбросить счётчик"""
        self.sun_count = initial_sun
        self.total_collected = 0
        self.total_spent = 0
    
    def get_stats(self):
        """Получить статистику"""
        return {
            "current": self.sun_count,
            "collected": self.total_collected,
            "spent": self.total_spent
        }


class PvZAI:
    def __init__(self):
        self.plant_manager = PlantManager()
        self.sun_tracker = SunTracker(initial_sun=50)
        self.strategy = PlantingStrategy(self.plant_manager)
        self.controller = GameController()
        
        self.running = False
        self.setup_complete = False
        self.loop_count = 0
        self.plants_placed = 0
        self.last_sun_check = 0
        
    def setup(self):
        """Initial setup"""
        print("\n" + "="*60)
        print("🌻 PvZ AI - Улучшенная версия")
        print("="*60)
        
        # Load or create plant configuration
        if self.plant_manager.load_config():
            response = input("\nИспользовать эту конфигурацию? (y/n): ").strip().lower()
            if response != 'y':
                self.plant_manager.setup_interactive()
        else:
            print("\n⚠️ Конфигурация не найдена")
            self.plant_manager.setup_interactive()
        
        if not self.plant_manager.plants:
            print("❌ Нет растений для работы!")
            return False
        
        self.setup_complete = True
        return True
    
    def run(self):
        """Main game loop"""
        if not self.setup_complete:
            if not self.setup():
                return
        
        print("\n" + "="*60)
        print("🎮 УПРАВЛЕНИЕ")
        print("="*60)
        print("  [Z] - Старт/Пауза")
        print("  [R] - Сброс стратегии (новый уровень)")
        print("  [P] - Показать карту растений")
        print("  [S] - Показать статистику")
        print("  [D] - Показать перезарядки")
        print("  [C] - Собрать солнца вручную")
        print("  [X] - Выход")
        print("="*60)
        print(f"\n☀️ Начальное солнце: {self.sun_tracker.sun_count}")
        print("\n⏸️  Нажми [Z] для старта...")
        
        try:
            while True:
                # Handle keyboard input
                if keyboard.is_pressed("z"):
                    self.running = not self.running
                    status = "🟢 АКТИВЕН" if self.running else "🔴 ПАУЗА"
                    print(f"\n{status} | ☀️ Солнце: {self.sun_tracker.sun_count}")
                    time.sleep(0.5)
                
                if keyboard.is_pressed("r"):
                    self.strategy.reset()
                    self.sun_tracker.reset()
                    self.loop_count = 0
                    self.plants_placed = 0
                    print(f"🔄 Сброшено | ☀️ Солнце: {self.sun_tracker.sun_count}")
                    time.sleep(0.5)
                
                if keyboard.is_pressed("p"):
                    self.strategy.print_grid_state()
                    time.sleep(0.5)
                
                if keyboard.is_pressed("s"):
                    self.print_stats()
                    time.sleep(0.5)
                
                if keyboard.is_pressed("d"):
                    self.print_cooldowns()
                    time.sleep(0.5)
                
                if keyboard.is_pressed("c"):
                    if yolo_model:
                        collected = self.controller.collect_collectibles(yolo_model, self.sun_tracker)
                        if collected > 0:
                            print(f"☀️ Собрано вручную: {collected} | Всего: {self.sun_tracker.sun_count}")
                    else:
                        print("⚠️ YOLO модель недоступна")
                    time.sleep(0.5)
                
                if keyboard.is_pressed("x"):
                    print("\n👋 Выход...")
                    break
                
                # Main AI loop
                if self.running:
                    self.ai_loop()
                
                time.sleep(0.1)
        
        except KeyboardInterrupt:
            print("\n⚠️ Прервано пользователем")
        except Exception as e:
            print(f"\n❌ Критическая ошибка: {e}")
            import traceback
            traceback.print_exc()
        finally:
            self.controller.emergency_stop()
    
    def ai_loop(self):
        """Single iteration of AI logic"""
        try:
            self.loop_count += 1
            
            # Collect suns and coins
            if yolo_model and time.time() - self.last_sun_check > 2.0:
                self.controller.collect_collectibles(yolo_model, self.sun_tracker)
                self.last_sun_check = time.time()
            
            # Detect zombies
            zombies = []
            if yolo_model:
                zombies = self.controller.detect_zombies(yolo_model)
            
            # Get next action from strategy
            action = self.strategy.get_next_action(zombies, self.sun_tracker.sun_count)
            
            if action:
                self.execute_action(action)
            
            # Status update every 10 loops
            if self.loop_count % 10 == 0:
                zombie_rows = sorted(set(r for c, r in zombies))
                zombie_info = f"Ряды: {zombie_rows}" if zombie_rows else "Нет"
                print(f"🔄 Loop {self.loop_count} | ☀️ {self.sun_tracker.sun_count} | 🧟 {len(zombies)} ({zombie_info}) | 🌱 {self.plants_placed}")
            
            time.sleep(LOOP_DELAY)
        
        except Exception as e:
            print(f"⚠️ Ошибка в цикле: {e}")
    
    def execute_action(self, action: dict):
        """Execute a planting action"""
        try:
            plant_name = action["plant"]
            col = action["col"]
            row = action["row"]
            reason = action.get("reason", "")
            
            # Get plant data
            plant_data = self.plant_manager.get_plant(plant_name)
            if not plant_data:
                print(f"❌ Растение {plant_name} недоступно")
                return
            
            # Get plant cost
            plant_cost = PLANT_COSTS.get(plant_name, 0)
            
            # Check if we can afford it
            if not self.sun_tracker.can_afford(plant_cost):
                return
            
            # Check cooldown
            if not self.strategy.can_plant(plant_name):
                return
            
            # Check if seed is ready
            if not self.controller.check_seed_ready(plant_data["coord"]):
                return
            
            # Plant it
            success = self.controller.plant(
                plant_data["coord"],
                col,
                row
            )
            
            if success:
                # Spend sun
                self.sun_tracker.spend_sun(plant_cost)
                
                # Mark planted with name
                self.strategy.mark_planted(col, row, plant_name)
                self.plants_placed += 1
                
                emoji = self._get_plant_emoji(plant_name)
                print(f"{emoji} {plant_name} → ({col},{row}) | {reason} | ☀️ -{plant_cost} (осталось: {self.sun_tracker.sun_count})")
                
                # Remove plant marker for instant-kill plants
                if plant_name in ["cherry bomb", "jalapeno", "squash", "potato mine"]:
                    time.sleep(3)
                    self.strategy.remove_plant(col, row)
        
        except Exception as e:
            print(f"❌ Ошибка выполнения действия: {e}")
    
    def _get_plant_emoji(self, plant_name: str) -> str:
        """Get emoji for plant"""
        emojis = {
            "sunflower": "🌻",
            "peashooter": "🔫",
            "snow pea": "❄️",
            "repeater": "🔫🔫",
            "cherry bomb": "💣",
            "wall-nut": "🛡️",
            "tall-nut": "🛡️",
            "potato mine": "💥",
            "squash": "🎯",
            "chomper": "🦖",
            "spikeweed": "🌵",
            "jalapeno": "🌶️",
            "torchwood": "🔥",
        }
        return emojis.get(plant_name, "🌱")
    
    def print_cooldowns(self):
        """Print current cooldown status"""
        current_time = time.time()
        elapsed_since_start = current_time - self.strategy.game_start_time
        
        print("\n" + "="*60)
        print("⏱️ ПЕРЕЗАРЯДКИ РАСТЕНИЙ")
        print("="*60)
        
        for plant_name in self.plant_manager.get_all_available():
            initial_cd = PLANT_INITIAL_COOLDOWNS.get(plant_name, 0)
            recharge_cd = PLANT_RECHARGE_COOLDOWNS.get(plant_name, 0)
            
            # Check initial cooldown
            if elapsed_since_start < initial_cd:
                remaining = initial_cd - elapsed_since_start
                print(f"  🔴 {plant_name:15} | Начальная: {remaining:.1f}s")
                continue
            
            # Check recharge cooldown
            if plant_name in self.strategy.plant_cooldowns:
                last_used = self.strategy.plant_cooldowns[plant_name]
                time_since_use = current_time - last_used
                
                if time_since_use < recharge_cd:
                    remaining = recharge_cd - time_since_use
                    print(f"  🟡 {plant_name:15} | Перезарядка: {remaining:.1f}s")
                else:
                    print(f"  🟢 {plant_name:15} | ГОТОВ")
            else:
                print(f"  🟢 {plant_name:15} | ГОТОВ")
        
        print("="*60 + "\n")
    
    def print_stats(self):
        """Print current statistics"""
        sun_stats = self.sun_tracker.get_stats()
        
        print("\n" + "="*60)
        print("📊 СТАТИСТИКА")
        print("="*60)
        print(f"  Циклов выполнено: {self.loop_count}")
        print(f"  Растений посажено: {self.plants_placed}")
        print(f"  Занятых клеток: {len(self.strategy.placed_plants)}")
        print(f"  Фаза: {'Производство солнца' if self.strategy.production_phase else 'Защита'}")
        print()
        print("☀️ СОЛНЦЕ:")
        print(f"  Текущее: {sun_stats['current']}")
        print(f"  Собрано: {sun_stats['collected']}")
        print(f"  Потрачено: {sun_stats['spent']}")
        print()
        print("🔫 ГОРОХОСТРЕЛЫ ПО РЯДАМ:")
        for row, count in sorted(self.strategy.peashooter_count.items()):
            print(f"  Ряд {row}: {count} шт.")
        print("="*60 + "\n")


def main():
    """Entry point"""
    ai = PvZAI()
    ai.run()


if __name__ == "__main__":
    main()
