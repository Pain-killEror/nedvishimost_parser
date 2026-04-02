import pymysql
import uuid
import random
import json

# ================= НАСТРОЙКИ БД =================
DB_CONFIG = {
    "host": "127.0.0.1",
    "user": "root",
    "password": "?Gore#!OT?!YMA", # Твой пароль
    "database": "investor_db",
    "charset": "utf8mb4"
}

# ================= СПРАВОЧНИКИ (УМНАЯ ЛОГИКА) =================

# 1. Зоны и улицы (Коэффициент цены, Список улиц)
ZONES = {
    "CENTER": (1.4, ["Карла Маркса", "Независимости", "Победителей", "Ленина", "Комсомольская", "Немига", "Интернациональная"]),
    "RESIDENTIAL": (1.0, ["Притыцкого", "Дзержинского", "Лобанка", "Есенина", "Маяковского", "Якуба Коласа", "Плеханова"]),
    "INDUSTRIAL": (0.7, ["Шабаны", "Селицкого", "Бабушкина", "Колядичи", "Инженерная", "Промышленная", "Машиностроителей"])
}

# 2. Наборы фотографий под каждое состояние объекта
PHOTOS = {
    "КВАРТИРА": {
        "Черновая отделка": ["https://images.unsplash.com/photo-1503387762-592deb58ef4e", "https://images.unsplash.com/photo-1590381105924-c72589b9ef3f"],
        "Предчистовая": ["https://images.unsplash.com/photo-1588854337236-6889d631faa8", "https://images.unsplash.com/photo-1513694203232-719a280e022f"],
        "Плохой ремонт": ["https://images.unsplash.com/photo-1558036117-15d82a90b9b1", "https://images.unsplash.com/photo-1497366754035-f200968a6e72"],
        "Средний ремонт": ["https://images.unsplash.com/photo-1522708323590-d24dbb6b0267", "https://images.unsplash.com/photo-1502672260266-1c1ef2d93688"],
        "Хороший ремонт": ["https://images.unsplash.com/photo-1560448204-e02f11c3d0e2", "https://images.unsplash.com/photo-1484154218962-a197022b5858"],
        "Элитный ремонт": ["https://images.unsplash.com/photo-1600596542815-ffad4c1539a9", "https://images.unsplash.com/photo-1600607687920-4e2a09cf159d"]
    },
    "ДОМ": {
        "Коттедж": ["https://images.unsplash.com/photo-1518780664697-55e3ad937233", "https://images.unsplash.com/photo-1600585154340-be6161a56a0c"],
        "Старый дом": ["https://images.unsplash.com/photo-1564013799919-ab600027ffc6", "https://images.unsplash.com/photo-1510627498534-cf7e9002facc"],
        "Таунхаус": ["https://images.unsplash.com/photo-1572120360610-d971b9d7767c", "https://images.unsplash.com/photo-1580587771525-78b9dba3b914"]
    },
    "ОФИС": {
        "A": ["https://images.unsplash.com/photo-1497366216548-37526070297c", "https://images.unsplash.com/photo-1497215728101-856f4ea42174"],
        "B": ["https://images.unsplash.com/photo-1504384308090-c894fdcc538d", "https://images.unsplash.com/photo-1527192491265-7e15c55b1ed2"],
        "C": ["https://images.unsplash.com/photo-1524861118128-4ce68fdfb6e8", "https://images.unsplash.com/photo-1536629930730-86317bc222ea"]
    },
    "СКЛАД": {
        "Отапливаемый": ["https://images.unsplash.com/photo-1586528116311-ad8dd3c8310d", "https://images.unsplash.com/photo-1553413077-190dd305871c"],
        "Холодный": ["https://images.unsplash.com/photo-1601584115197-04ecc0da31d7", "https://images.unsplash.com/photo-1505731422754-0498b31a31b2"]
    },
    "КОММЕРЦИЯ": {
        "Стрит-ритейл": ["https://images.unsplash.com/photo-1555529669-e69e7aa0ba9a", "https://images.unsplash.com/photo-1534438327276-14e5300c3a48"],
        "ТЦ": ["https://images.unsplash.com/photo-1519567281799-974249a888c3", "https://images.unsplash.com/photo-1567449303078-57ad995bd3d6"]
    },
    "УЧАСТОК": {
        "Стандарт": ["https://images.unsplash.com/photo-1500382017468-9049fed747ef", "https://images.unsplash.com/photo-1473496169904-658ba7c44d8a"]
    },
    "ГАРАЖ": {
        "Кирпичный": ["https://images.unsplash.com/photo-1595079676339-1534801ad6cf", "https://images.unsplash.com/photo-1532323544230-7191fd51bc1b"],
        "Паркинг": ["https://images.unsplash.com/photo-1506521781263-d8422e82f27a", "https://images.unsplash.com/photo-1573348722427-f1d6819fdf98"]
    }
}

def get_location(allowed_zones):
    """Выбирает улицу из разрешенных зон. ВОЗВРАЩАЕТ ТОЛЬКО УЛИЦУ И ДОМ."""
    zone_name = random.choice(allowed_zones)
    loc_coeff, streets = ZONES[zone_name]
    street = random.choice(streets)
    address = f"ул. {street}, д. {random.randint(1, 150)}"
    return address, loc_coeff

def run_smart_generator(count=300):
    conn = pymysql.connect(**DB_CONFIG)
    cursor = conn.cursor()
    print(f"🚀 Запуск генератора: {count} объектов...")
    success_count = 0

    categories = list(PHOTOS.keys())

    for i in range(count):
        cat = random.choice(categories)
        
        # ДЕФОЛТНЫЕ ПАРАМЕТРЫ (чтобы в БД не было NULL и ошибок)
        area_total = 0.0
        area_living = 0.0 
        floor = 0
        floors_total = 0
        wall_material = "Кирпичный"
        year_built = random.randint(1960, 2024)
        price_total, base_price_m2, loc_coeff, state_coeff = 0, 0, 1.0, 1.0
        desc, title = "", ""
        
        # СЛОВАРЬ ДЛЯ JSON КОЛОНКИ (СЮДА ИДЕТ РЕМОНТ И ПРОЧЕЕ)
        extra_attributes = {}

        # ================= ЛОГИКА ПО КАТЕГОРИЯМ =================
        if cat == "КВАРТИРА":
            base_price_m2 = 1350
            address, loc_coeff = get_location(["CENTER", "RESIDENTIAL"])
            
            # Состояния ремонта и их влияние на цену
            renovation_types = {
                "Черновая отделка": 0.8, "Предчистовая": 0.9, "Плохой ремонт": 0.7, 
                "Средний ремонт": 1.0, "Хороший ремонт": 1.2, "Элитный ремонт": 1.6
            }
            renovation = random.choice(list(renovation_types.keys()))
            state_coeff = renovation_types[renovation]
            
            rooms = random.randint(1, 4)
            area_total = round(random.uniform(28 * rooms, 35 * rooms), 1) 
            area_living = round(area_total * random.uniform(0.5, 0.7), 1)
            floors_total = random.choice([5, 9, 12, 19, 25])
            floor = random.randint(1, floors_total)
            wall_material = random.choice(["Панельный", "Кирпичный", "Монолитный"])
            
            # ЗАПОЛНЯЕМ JSON АТРИБУТЫ
            extra_attributes["rooms_count"] = rooms
            extra_attributes["renovation_state"] = renovation
            extra_attributes["has_balcony"] = random.choice([True, False])
            
            photo_set = PHOTOS[cat][renovation]
            title = f"{rooms}-комн. квартира, {area_total} м²"
            desc = f"Продается {rooms}-комнатная квартира. Состояние ремонта: {renovation}. Материал стен: {wall_material}."

        elif cat == "ДОМ":
            base_price_m2 = 1000
            address, loc_coeff = get_location(["RESIDENTIAL", "INDUSTRIAL"])
            
            house_types = {"Коттедж": 1.5, "Таунхаус": 1.2, "Старый дом": 0.6}
            h_type = random.choice(list(house_types.keys()))
            state_coeff = house_types[h_type]
            
            area_total = round(random.uniform(60, 300), 1)
            # ТЕПЕРЬ ЖИЛАЯ ПЛОЩАДЬ СЧИТАЕТСЯ КОРРЕКТНО
            area_living = round(area_total * random.uniform(0.6, 0.8), 1)
            plot_area = round(random.uniform(4, 15), 1)
            floors_total = random.randint(1, 3)
            floor = 1
            
            extra_attributes["house_type"] = h_type
            extra_attributes["plot_area_acres"] = plot_area
            extra_attributes["heating_type"] = random.choice(["Газ", "Твердотопливный", "Электрическое"])
            
            photo_set = PHOTOS[cat][h_type]
            title = f"{h_type}, {area_total} м²"
            desc = f"В продаже {h_type.lower()} на участке {plot_area} соток. Отопление: {extra_attributes['heating_type']}."

        elif cat == "ОФИС":
            base_price_m2 = 1800
            address, loc_coeff = get_location(["CENTER", "RESIDENTIAL"])
            
            office_classes = {"A": 1.4, "B": 1.0, "C": 0.7}
            o_class = random.choice(list(office_classes.keys()))
            state_coeff = office_classes[o_class]
            
            area_total = round(random.uniform(30, 500), 1)
            floors_total = random.randint(3, 20)
            floor = random.randint(1, floors_total)
            
            extra_attributes["business_center_class"] = o_class
            extra_attributes["access_24_7"] = random.choice([True, False])
            
            photo_set = PHOTOS[cat][o_class]
            title = f"Офис {area_total} м² (Класс {o_class})"
            desc = f"Офисное помещение класса {o_class}. Доступ 24/7: {'Да' if extra_attributes['access_24_7'] else 'Нет'}."

        elif cat == "СКЛАД":
            base_price_m2 = 500
            address, loc_coeff = get_location(["INDUSTRIAL"])
            
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
            
            photo_set = PHOTOS[cat][w_type]
            title = f"Склад ({w_type.lower()}), {area_total} м²"
            desc = f"Отличный склад. Потолки {ceiling_h}м. Рампа: {'Есть' if extra_attributes['has_ramp'] else 'Нет'}."

        elif cat == "КОММЕРЦИЯ":
            base_price_m2 = 2200
            address, loc_coeff = get_location(["CENTER", "RESIDENTIAL"])
            
            com_types = {"Стрит-ритейл": 1.3, "ТЦ": 1.0}
            c_type = random.choice(list(com_types.keys()))
            state_coeff = com_types[c_type]
            
            area_total = round(random.uniform(40, 300), 1)
            floor = 1 if c_type == "Стрит-ритейл" else random.randint(1, 3)
            floors_total = floor + random.randint(0, 2)
            
            extra_attributes["retail_type"] = c_type
            extra_attributes["power_kw"] = random.choice([15, 30, 50, 100])
            
            photo_set = PHOTOS[cat][c_type]
            title = f"Коммерческое помещение, {area_total} м²"
            desc = f"Формат: {c_type}. Выделенная мощность: {extra_attributes['power_kw']} кВт. Высокий пешеходный трафик."

        elif cat == "УЧАСТОК":
            base_price_m2 = 5000 # Цена за сотку
            address, loc_coeff = get_location(["RESIDENTIAL", "INDUSTRIAL"])
            area_total = round(random.uniform(5, 50), 1) # Храним сотки в area_total
            
            extra_attributes["land_purpose"] = random.choice(["ИЖС", "Промназначение", "Коммерция"])
            
            photo_set = PHOTOS[cat]["Стандарт"]
            title = f"Участок {area_total} сот."
            desc = f"Продается земельный участок. Назначение: {extra_attributes['land_purpose']}."

        elif cat == "ГАРАЖ":
            address, loc_coeff = get_location(["RESIDENTIAL", "INDUSTRIAL"])
            garage_prices = {"Кирпичный": 6000, "Паркинг": 12000}
            g_type = random.choice(list(garage_prices.keys()))
            
            area_total = round(random.uniform(14, 25), 1)
            price_total = int(garage_prices[g_type] * loc_coeff) 
            
            extra_attributes["garage_type"] = g_type
            extra_attributes["has_security"] = True
            
            photo_set = PHOTOS[cat][g_type]
            title = f"Гараж/Место ({g_type}), {area_total} м²"
            desc = f"Тип: {g_type}. Круглосуточная охрана и видеонаблюдение."

        # ================= МАТЕМАТИКА ЦЕНЫ =================
        if cat != "ГАРАЖ":
            price_total = int(area_total * base_price_m2 * loc_coeff * state_coeff)
        
        price_per_m2 = round(price_total / area_total, 2) if area_total > 0 else 0

        # ================= ЗАПИСЬ В БАЗУ ДАННЫХ =================
        obj_uuid = uuid.uuid4().bytes
        
        # ОБРАТИ ВНИМАНИЕ: latitude и longitude убраны, добавлен attributes
        query = """INSERT INTO real_estate_objects 
                   (id, external_id, type, category, title, description, city, address, 
                    area_total, area_living, floor, floors_total, 
                    wall_material, year_built, price_total, price_per_m2, currency, 
                    images_urls, source_url, created_at, updated_at, attributes) 
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW(), %s)"""
        
        try:
            cursor.execute(query, (
                obj_uuid, 
                f"SEED-{cat[:3]}-{random.randint(10000,99999)}",
                "REALTY", # Всегда REALTY, как мы обсуждали
                cat, 
                title, 
                desc, 
                "Минск", # Город отдельно
                address, # Адрес отдельно (ул. ..., д. ...)
                area_total, 
                area_living, 
                floor, 
                floors_total, 
                wall_material, 
                year_built, 
                price_total, 
                price_per_m2, 
                "USD", 
                json.dumps(photo_set), 
                f"https://example.com/realty/{i}",
                
                # ВОТ ЗДЕСЬ ВСЕ НАШИ ДОП. ДАННЫЕ (РЕМОНТ, РАМПА И Т.Д.) ПРЕВРАЩАЮТСЯ В JSON:
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
    run_smart_generator(300)