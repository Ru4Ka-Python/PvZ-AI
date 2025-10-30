"""
Plant Manager - Handles plant inventory and availability
Improved version with dynamic slot count
"""

import json
import os
from config import SEED_SLOTS, PLANT_COSTS

class PlantManager:
    def __init__(self):
        self.plants = {}  # {plant_name: {"slot": slot_num, "coord": (x,y)}}
        self.config_file = "plant_config.json"
        self.slot_count = 6  # Default slot count
    
    def setup_interactive(self):
        """Interactive setup for plant configuration"""
        print("\n" + "="*60)
        print("🌱 НАСТРОЙКА РАСТЕНИЙ")
        print("="*60)
        
        # Ask for number of slots
        while True:
            try:
                slot_input = input(f"\nСколько у вас слотов для растений? (1-10, по умолчанию 6): ").strip()
                if slot_input == "":
                    self.slot_count = 6
                    break
                slot_count = int(slot_input)
                if 1 <= slot_count <= 10:
                    self.slot_count = slot_count
                    break
                else:
                    print("  ❌ Введите число от 1 до 10")
            except ValueError:
                print("  ❌ Введите корректное число")
        
        print(f"\n✅ Настроено слотов: {self.slot_count}")
        
        print("\nДоступные растения:")
        print("  1. Sunflower      (50 sun)")
        print("  2. Peashooter     (100 sun)")
        print("  3. Snow Pea       (175 sun)")
        print("  4. Repeater       (200 sun)")
        print("  5. Cherry Bomb    (150 sun)")
        print("  6. Wall-nut       (50 sun)")
        print("  7. Tall-nut       (125 sun)")
        print("  8. Potato Mine    (25 sun)")
        print("  9. Squash         (50 sun)")
        print(" 10. Chomper        (150 sun)")
        print(" 11. Spikeweed      (100 sun)")
        print(" 12. Jalapeno       (125 sun)")
        print(" 13. Torchwood      (175 sun)")
        print("  0. Пропустить слот (оставить пустым)")
        print()
        
        plant_names = {
            1: "sunflower",
            2: "peashooter",
            3: "snow pea",
            4: "repeater",
            5: "cherry bomb",
            6: "wall-nut",
            7: "tall-nut",
            8: "potato mine",
            9: "squash",
            10: "chomper",
            11: "spikeweed",
            12: "jalapeno",
            13: "torchwood",
        }
        
        for slot_num in range(1, self.slot_count + 1):
            if slot_num not in SEED_SLOTS:
                print(f"⚠️ Слот {slot_num} не настроен в config.py, пропускаем")
                break
                
            while True:
                try:
                    coord = SEED_SLOTS[slot_num]
                    user_input = input(f"Слот {slot_num} ({coord}): ").strip()
                    
                    if user_input == "0" or user_input == "":
                        print(f"  ⊘ Слот {slot_num} пропущен\n")
                        break
                    
                    choice = int(user_input)
                    
                    if choice in plant_names:
                        plant_name = plant_names[choice]
                        
                        # Check if plant already assigned
                        if plant_name in self.plants:
                            print(f"  ⚠️ {plant_name} уже назначен на слот {self.plants[plant_name]['slot']}")
                            continue
                        
                        self.plants[plant_name] = {
                            "slot": slot_num,
                            "coord": coord
                        }
                        
                        print(f"  ✅ {plant_name} в слоте {slot_num}\n")
                        break
                    else:
                        print("  ❌ Неверный номер, попробуй снова")
                
                except ValueError:
                    print("  ❌ Введи число")
                except Exception as e:
                    print(f"  ❌ Ошибка: {e}")
        
        self.save_config()
        self.print_summary()
    
    def save_config(self):
        """Save plant configuration to file"""
        try:
            config_data = {
                "slot_count": self.slot_count,
                "plants": self.plants
            }
            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(config_data, f, indent=2, ensure_ascii=False)
            print(f"\n💾 Конфигурация сохранена в {self.config_file}")
        except Exception as e:
            print(f"⚠️ Не удалось сохранить: {e}")
    
    def load_config(self):
        """Load plant configuration from file"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, "r", encoding="utf-8") as f:
                    config_data = json.load(f)
                
                # Handle old format (direct plants dict)
                if "plants" in config_data:
                    self.slot_count = config_data.get("slot_count", 6)
                    self.plants = config_data["plants"]
                else:
                    # Old format compatibility
                    self.plants = config_data
                    self.slot_count = len(self.plants)
                
                print(f"✅ Конфигурация загружена из {self.config_file}")
                self.print_summary()
                return True
        except Exception as e:
            print(f"⚠️ Не удалось загрузить: {e}")
        return False
    
    def print_summary(self):
        """Print current plant configuration"""
        print("\n" + "="*60)
        print("📋 ТЕКУЩАЯ КОНФИГУРАЦИЯ")
        print("="*60)
        print(f"Слотов доступно: {self.slot_count}")
        
        if not self.plants:
            print("⚠️ Нет настроенных растений")
            return
        
        print("\n🟢 Доступные растения:")
        for name, data in sorted(self.plants.items(), key=lambda x: x[1]["slot"]):
            slot = data["slot"]
            coord = data["coord"]
            cost = PLANT_COSTS.get(name, "?")
            print(f"  ✅ Слот {slot}: {name:15} | {coord} | {cost} sun")
        
        print("="*60 + "\n")
    
    def get_plant(self, plant_name):
        """Get plant data if it exists"""
        if plant_name in self.plants:
            return self.plants[plant_name]
        return None
    
    def get_all_available(self):
        """Get list of all available plants"""
        return list(self.plants.keys())
    
    def has_plant(self, plant_name):
        """Check if plant is available"""
        return plant_name in self.plants


if __name__ == "__main__":
    manager = PlantManager()
    
    print("Выбери действие:")
    print("1. Новая настройка")
    print("2. Загрузить сохраненную")
    
    choice = input("\nВыбор (1/2): ").strip()
    
    if choice == "2" and manager.load_config():
        print("\n✅ Конфигурация загружена")
    else:
        manager.setup_interactive()
