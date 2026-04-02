import pymysql
import uuid
import random
import json
from datetime import datetime

DB_CONFIG = {
    "host": "127.0.0.1",
    "user": "root",
    "password": "?Gore#!OT?!YMA",
    "database": "investor_db",
    "charset": "utf8mb4"
}

PHOTOS = {
    "КВАРТИРА": ["https://images.unsplash.com/photo-1522708323590-d24dbb6b0267", "https://images.unsplash.com/photo-1502672260266-1c1ef2d93688"],
    "ДОМ": ["https://images.unsplash.com/photo-1518780664697-55e3ad937233", "https://images.unsplash.com/photo-1600585154340-be6161a56a0c"],
    "ОФИС": ["https://images.unsplash.com/photo-1497366216548-37526070297c", "https://images.unsplash.com/photo-1497215728101-856f4ea42174"],
    "СКЛАД": ["https://images.unsplash.com/photo-1586528116311-ad8dd3c8310d", "https://images.unsplash.com/photo-1553413077-190dd305871c"],
    "КОММЕРЦИЯ": ["https://images.unsplash.com/photo-1555529669-e69e7aa0ba9a", "https://images.unsplash.com/photo-1534438327276-14e5300c3a48"],
    "УЧАСТОК": ["https://images.unsplash.com/photo-1500382017468-9049fed747ef", "https://images.unsplash.com/photo-1473496169904-658ba7c44d8a"],
    "ГАРАЖ": ["https://images.unsplash.com/photo-1595079676339-1534801ad6cf", "https://images.unsplash.com/photo-1532323544230-7191fd51bc1b"]
}

STREETS = ["Победителей", "Независимости", "Притыцкого", "Дзержинского", "Маяковского", "Ленина", "Коласа", "Беломорская", "Карла Маркса", "Романовская Слобода"]
WALL_MATERIALS = ["Кирпичный", "Панельный", "Монолитный", "Блочный", "Деревянный", "Сип-панели"]

def run_generator(count=300):
    try:
        conn = pymysql.connect(**DB_CONFIG)
        cursor = conn.cursor()
    except Exception as e:
        print(f"❌ Ошибка подключения к БД: {e}")
        return

    print(f"🚀 Начинаю генерацию {count} детализированных объектов...")
    
    categories = list(PHOTOS.keys())
    success_count = 0

    for i in range(count):
        cat = random.choice(categories)
        
        # Общие параметры
        area_total = 0.0
        area_living = None
        floor = None
        floors_total = None
        wall_material = random.choice(WALL_MATERIALS)
        year_built = random.randint(1960, 2024)
        price_total = 0
        desc = ""
        
        # Логика по категориям
        if cat == "КВАРТИРА":
            area_total = round(random.uniform(30, 120), 1)
            area_living = round(area_total * random.uniform(0.5, 0.7), 1)
            floors_total = random.choice([5, 9, 12, 16, 20, 25])
            floor = random.randint(1, floors_total)
            price_total = int(area_total * random.randint(1100, 2200))
            wall_material = random.choice(["Кирпичный", "Панельный", "Монолитный"])
            desc = f"Прекрасная квартира. Этаж {floor}/{floors_total}. Материал стен: {wall_material}."

        elif cat == "ДОМ":
            area_total = round(random.uniform(60, 350), 1)
            area_living = round(area_total * random.uniform(0.6, 0.8), 1)
            floors_total = random.randint(1, 3)
            floor = 1
            price_total = int(area_total * random.randint(700, 1500))
            wall_material = random.choice(["Деревянный", "Блочный", "Кирпичный"])
            desc = f"Уютный дом, {year_built} года постройки. Участок включен."

        elif cat == "ОФИС" or cat == "КОММЕРЦИЯ":
            area_total = round(random.uniform(20, 500), 1)
            floors_total = random.randint(1, 20)
            floor = random.randint(1, floors_total)
            price_total = int(area_total * random.randint(1500, 3500))
            wall_material = random.choice(["Монолитный", "Кирпичный"])
            desc = f"Объект под бизнес. Высокий трафик. Класс {random.choice(['A', 'B', 'C'])}."

        elif cat == "СКЛАД":
            area_total = round(random.uniform(150, 2000), 1)
            floors_total = random.randint(1, 2)
            floor = 1
            price_total = int(area_total * random.randint(400, 900))
            wall_material = "Металлоконструкции/Блоки"
            desc = f"Складское помещение. Удобный подъезд. Потолки {random.randint(4, 12)}м."

        elif cat == "УЧАСТОК":
            area_total = round(random.uniform(5, 50), 1) # в сотках
            price_total = int(area_total * random.randint(500, 5000))
            wall_material = None
            year_built = None
            desc = "Участок под застройку. Ровный рельеф, коммуникации рядом."

        elif cat == "ГАРАЖ":
            area_total = round(random.uniform(18, 30), 1)
            floor = 1
            floors_total = 1
            price_total = random.randint(3000, 15000)
            wall_material = "Блочный/Кирпичный"
            desc = "Сухой гараж в охраняемом ГСК."

        # Расчет цены за м2
        price_per_m2 = round(price_total / area_total, 2) if area_total > 0 else 0

        title = f"{cat.capitalize()} {area_total} " + ("сот." if cat == "УЧАСТОК" else "м²")
        address = f"Минск, ул. {random.choice(STREETS)}, {random.randint(1, 150)}"
        lat = 53.9 + random.uniform(-0.07, 0.07)
        lon = 27.5 + random.uniform(-0.07, 0.07)

        # SQL
        obj_uuid = uuid.uuid4().bytes
        query = """INSERT INTO real_estate_objects 
                   (id, external_id, type, category, title, description, city, address, 
                    latitude, longitude, area_total, area_living, floor, floors_total, 
                    wall_material, year_built, price_total, price_per_m2, currency, 
                    images_urls, source_url, created_at, updated_at) 
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW())"""
        
        try:
            cursor.execute(query, (
                obj_uuid, 
                f"SEED-{i}-{random.randint(1000,9999)}", # external_id
                "REALTY",      # type
                cat,           # category
                title, 
                desc, 
                "Минск",       # city
                address,
                lat, lon, 
                area_total, 
                area_living, 
                floor, 
                floors_total, 
                wall_material, 
                year_built, 
                price_total, 
                price_per_m2, 
                "USD",         # currency
                json.dumps(PHOTOS[cat]),
                f"https://domovita.by/fake-id-{i}" # source_url
            ))
            success_count += 1
        except Exception as e:
            print(f"⚠️ Ошибка на объекте {i}: {e}")
            conn.rollback()
            continue

    conn.commit()
    cursor.close()
    conn.close()
    print(f"🏁 ГОТОВО! Успешно создано и заполнено объектов: {success_count} из {count}")

if __name__ == "__main__":
    run_generator(300)