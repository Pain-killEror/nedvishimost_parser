import pymysql
import uuid
import random
import json
import os

# ================= НАСТРОЙКИ БД =================
DB_CONFIG = {
    "host": "127.0.0.1",
    "user": "root",
    "password": "?Gore#!OT?!YMA", # Твой пароль
    "database": "investor_db",
    "charset": "utf8mb4"
}

# ================= ЗАГРУЗКА ДАННЫХ ИЗ ФАЙЛОВ =================

def load_addresses(filename):
    if not os.path.exists(filename):
        print(f"⚠️ Файл {filename} не найден! Убедись, что парсер адресов отработал.")
        return [f"ул. Резервная, д. {i}" for i in range(1, 2000)] # Заглушка, если файла нет
    with open(filename, "r", encoding="utf-8") as f:
        addresses = [line.strip() for line in f if line.strip()]
        random.shuffle(addresses) # Перемешиваем адреса как колоду карт!
        return addresses

# Загружаем и сразу перемешиваем
MINSK_ADDRESSES = load_addresses("addresses_minsk.txt")
REGION_ADDRESSES = load_addresses("addresses_region.txt")

def load_photos(base_dir="photos"):
    loaded_photos = {}
    folder_mapping = {
        "квартиры": "КВАРТИРА", "дом": "ДОМ", "офис": "ОФИС",
        "склад": "СКЛАД", "коммерция": "КОММЕРЦИЯ", "участок": "УЧАСТОК", "гараж": "ГАРАЖ"
    }

    if not os.path.exists(base_dir):
        print(f"⚠️ Папка {base_dir} не найдена.")
        return loaded_photos

    for folder_name, cat_key in folder_mapping.items():
        folder_path = os.path.join(base_dir, folder_name)
        loaded_photos[cat_key] = {}
        
        if os.path.exists(folder_path):
            for filename in os.listdir(folder_path):
                if filename.endswith(".txt"):
                    state_name = filename[:-4] 
                    file_path = os.path.join(folder_path, filename)
                    with open(file_path, "r", encoding="utf-8") as file:
                        urls = [line.strip() for line in file if line.strip()]
                        loaded_photos[cat_key][state_name] = urls
    return loaded_photos

PHOTOS = load_photos()

# ================= ЛОГИКА АДРЕСОВ И ЦЕН =================

def get_location(cat, allowed_zones=None):
    """
    Берет строго УНИКАЛЬНЫЙ адрес.
    """
    if cat in ["ДОМ", "УЧАСТОК"]:
        # Достаем адрес и удаляем его из списка (.pop), чтобы он больше не выпал
        if REGION_ADDRESSES:
            address = REGION_ADDRESSES.pop()
        else:
            address = f"Минский район, резервный дом {random.randint(1000, 9999)}"
            
        loc_coeff = round(random.uniform(0.8, 1.2), 2)
        return "Минский район", address, loc_coeff
    else:
        if MINSK_ADDRESSES:
            address = MINSK_ADDRESSES.pop()
        else:
            address = f"г. Минск, резервный дом {random.randint(1000, 9999)}"
            
        if allowed_zones and "INDUSTRIAL" in allowed_zones and len(allowed_zones) == 1:
            loc_coeff = round(random.uniform(0.6, 0.8), 2) 
        elif allowed_zones and "CENTER" in allowed_zones:
            loc_coeff = round(random.uniform(1.1, 1.5), 2) 
        else:
            loc_coeff = round(random.uniform(0.9, 1.1), 2) 
            
        return "г. Минск", address, loc_coeff


# ================= ГЛАВНЫЙ ГЕНЕРАТОР =================

def run_smart_generator(count=1000): # <--- ТЕПЕРЬ ТУТ 1000 ПО УМОЛЧАНИЮ
    if not PHOTOS:
        print("❌ Ошибка: Фотографии не загружены.")
        return

    conn = pymysql.connect(**DB_CONFIG)
    cursor = conn.cursor()
    print(f"🚀 Запуск генератора: {count} объектов...")
    success_count = 0

    categories = list(PHOTOS.keys())

    for i in range(count):
        cat = random.choice(categories)
        
        # ДЕФОЛТНЫЕ ПАРАМЕТРЫ
        area_total, area_living, floor, floors_total = 0.0, 0.0, 0, 0
        wall_material = "Кирпичный"
        year_built = random.randint(1960, 2024)
        price_total, base_price_m2, loc_coeff, state_coeff = 0, 0, 1.0, 1.0
        desc, title = "", ""
        extra_attributes = {}

        # ================= ЛОГИКА ПО КАТЕГОРИЯМ =================
        if cat == "КВАРТИРА":
            base_price_m2 = 1350
            city, address, loc_coeff = get_location(cat, ["CENTER", "RESIDENTIAL"])
            renovation_types = {"Черновая отделка": 0.8, "Предчистовая": 0.9, "Плохой ремонт": 0.7, "Средний ремонт": 1.0, "Хороший ремонт": 1.2, "Элитный ремонт": 1.6}
            renovation = random.choice(list(renovation_types.keys()))
            state_coeff = renovation_types[renovation]
            rooms = random.randint(1, 4)
            area_total = round(random.uniform(28 * rooms, 35 * rooms), 1) 
            area_living = round(area_total * random.uniform(0.5, 0.7), 1)
            floors_total = random.choice([5, 9, 12, 19, 25])
            floor = random.randint(1, floors_total)
            wall_material = random.choice(["Панельный", "Кирпичный", "Монолитный"])
            extra_attributes["rooms_count"] = rooms
            extra_attributes["renovation_state"] = renovation
            extra_attributes["has_balcony"] = random.choice([True, False])
            photo_set = PHOTOS.get(cat, {}).get(renovation, [])
            title = f"{rooms}-комн. квартира, {area_total} м²"
            desc = f"Продается {rooms}-комнатная квартира. Состояние ремонта: {renovation}. Материал стен: {wall_material}."

        elif cat == "ДОМ":
            base_price_m2 = 1000
            city, address, loc_coeff = get_location(cat) 
            house_types = {"Коттедж": 1.5, "Таунхаус": 1.2, "Старый дом": 0.6}
            h_type = random.choice(list(house_types.keys()))
            state_coeff = house_types[h_type]
            area_total = round(random.uniform(60, 300), 1)
            area_living = round(area_total * random.uniform(0.6, 0.8), 1)
            plot_area = round(random.uniform(4, 15), 1)
            floors_total = random.randint(1, 3)
            floor = 0
            extra_attributes["house_type"] = h_type
            extra_attributes["plot_area_acres"] = plot_area
            extra_attributes["heating_type"] = random.choice(["Газ", "Твердотопливный", "Электрическое"])
            photo_set = PHOTOS.get(cat, {}).get(h_type, [])
            title = f"{h_type}, {area_total} м²"
            desc = f"В продаже {h_type.lower()} на участке {plot_area} соток. Отопление: {extra_attributes['heating_type']}."

        elif cat == "ОФИС":
            base_price_m2 = 1800
            city, address, loc_coeff = get_location(cat, ["CENTER", "RESIDENTIAL"])
            office_classes = {"A": 1.4, "B": 1.0, "C": 0.7}
            o_class = random.choice(list(office_classes.keys()))
            state_coeff = office_classes[o_class]
            area_total = round(random.uniform(30, 500), 1)
            floors_total = random.randint(3, 20)
            floor = random.randint(1, floors_total)
            extra_attributes["business_center_class"] = o_class
            extra_attributes["access_24_7"] = random.choice([True, False])
            photo_set = PHOTOS.get(cat, {}).get(o_class, [])
            title = f"Офис {area_total} м² (Класс {o_class})"
            desc = f"Офисное помещение класса {o_class}. Доступ 24/7: {'Да' if extra_attributes['access_24_7'] else 'Нет'}."

        elif cat == "СКЛАД":
            base_price_m2 = 500
            city, address, loc_coeff = get_location(cat, ["INDUSTRIAL"])
            warehouse_types = {"Отапливаемый": 1.2, "Холодный": 0.8}
            w_type = random.choice(list(warehouse_types.keys()))
            state_coeff = warehouse_types[w_type]
            area_total = round(random.uniform(150, 2000), 1)
            ceiling_h = random.randint(4, 12)
            floor = 1
            floors_total = 1
            extra_attributes["warehouse_type"] = w_type
            extra_attributes["ceiling_height_m"] = ceiling_h
            extra_attributes["has_ramp"] = random.choice([True, False])
            photo_set = PHOTOS.get(cat, {}).get(w_type, [])
            title = f"Склад ({w_type.lower()}), {area_total} м²"
            desc = f"Отличный склад. Потолки {ceiling_h}м. Рампа: {'Есть' if extra_attributes['has_ramp'] else 'Нет'}."

        elif cat == "КОММЕРЦИЯ":
            base_price_m2 = 2200
            city, address, loc_coeff = get_location(cat, ["CENTER", "RESIDENTIAL"])
            com_types = {"Стрит-ритейл": 1.3, "ТЦ": 1.0}
            c_type = random.choice(list(com_types.keys()))
            state_coeff = com_types[c_type]
            area_total = round(random.uniform(40, 300), 1)
            floor = 1 if c_type == "Стрит-ритейл" else random.randint(1, 3)
            floors_total = floor + random.randint(0, 2)
            extra_attributes["retail_type"] = c_type
            extra_attributes["power_kw"] = random.choice([15, 30, 50, 100])
            photo_set = PHOTOS.get(cat, {}).get(c_type, [])
            title = f"Коммерческое помещение, {area_total} м²"
            desc = f"Формат: {c_type}. Выделенная мощность: {extra_attributes['power_kw']} кВт. Высокий пешеходный трафик."

        elif cat == "УЧАСТОК":
            base_price_m2 = 5000
            city, address, loc_coeff = get_location(cat) 
            area_total = round(random.uniform(5, 50), 1)
            extra_attributes["land_purpose"] = random.choice(["ИЖС", "Промназначение", "Коммерция"])
            extra_attributes["has_electricity"] = random.choice([True, False])
            extra_attributes["has_gas"] = random.choice([True, False])
            photo_set = PHOTOS.get(cat, {}).get("Стандарт", [])
            title = f"Участок {area_total} сот."
            electricity_str = "Есть" if extra_attributes["has_electricity"] else "Нет"
            gas_str = "Есть" if extra_attributes["has_gas"] else "Нет"
            desc = f"Продается земельный участок. Назначение: {extra_attributes['land_purpose']}. Электричество: {electricity_str}, Газ: {gas_str}."

        elif cat == "ГАРАЖ":
            city, address, loc_coeff = get_location(cat, ["RESIDENTIAL", "INDUSTRIAL"])
            material = random.choice(["Кирпичный", "Металлический"])
            wall_material = material
            base_price = 6000 if material == "Кирпичный" else 2500
            area_total = round(random.uniform(14, 25), 1)
            price_total = int(base_price * loc_coeff) 
            extra_attributes["is_covered"] = random.choice([True, False])
            extra_attributes["material"] = material
            extra_attributes["has_pit"] = random.choice([True, False])
            photo_set = PHOTOS.get(cat, {}).get(material, [])
            title = f"Гараж ({material.lower()}), {area_total} м²"
            covered_str = "Да" if extra_attributes["is_covered"] else "Нет"
            pit_str = "Есть" if extra_attributes["has_pit"] else "Нет"
            desc = f"Продается {material.lower()} гараж. Крытый: {covered_str}. Смотровая яма: {pit_str}."

        # ================= МАТЕМАТИКА ЦЕНЫ =================
        if cat != "ГАРАЖ":
            price_total = int(area_total * base_price_m2 * loc_coeff * state_coeff)
        
        price_per_m2 = round(price_total / area_total, 2) if area_total > 0 else 0

        # ================= ЗАПИСЬ В БАЗУ ДАННЫХ =================
        obj_uuid = uuid.uuid4().bytes
        query = """INSERT INTO real_estate_objects 
                   (id, external_id, type, category, title, description, city, address, 
                    area_total, area_living, floor, floors_total, 
                    wall_material, year_built, price_total, price_per_m2, currency, 
                    images_urls, source_url, created_at, updated_at, attributes) 
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW(), %s)"""
        
        try:
            cursor.execute(query, (
                obj_uuid, 
                f"SEED-{cat[:3]}-{uuid.uuid4().hex[:8].upper()}",
                "REALTY",
                cat, title, desc, city, address, area_total, area_living, 
                floor, floors_total, wall_material, year_built, price_total, 
                price_per_m2, "USD", json.dumps(photo_set),
                f"https://example.com/realty/{i}",
                json.dumps(extra_attributes, ensure_ascii=False) 
            ))
            success_count += 1
        except Exception as e:
            print(f"⚠️ Ошибка при добавлении объекта (индекс {i}): {e}")
            conn.rollback()

    conn.commit()
    cursor.close()
    conn.close()
    print(f"🏁 ГОТОВО! Успешно создано: {success_count} из {count} объектов.")

if __name__ == "__main__":
    run_smart_generator(1000) # Генерируем 1000 объектов