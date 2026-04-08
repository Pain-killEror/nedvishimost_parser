import requests
import time

def format_street_name(name):
    """Форматирует название в красивый вид 'ул. Название'"""
    name_lower = name.lower()
    
    if "улица" in name_lower or "вуліца" in name_lower:
        clean = name.replace("улица", "").replace("Улица", "").replace("вуліца", "").replace("Вуліца", "").strip()
        return f"ул. {clean}"
    elif "проспект" in name_lower or "праспект" in name_lower:
        clean = name.replace("проспект", "").replace("Проспект", "").replace("праспект", "").replace("Праспект", "").strip()
        return f"пр. {clean}"
    elif "переулок" in name_lower or "завулак" in name_lower:
        clean = name.replace("переулок", "").replace("Переулок", "").replace("завулак", "").replace("Завулак", "").strip()
        return f"пер. {clean}"
    elif "тракт" in name_lower:
        clean = name.replace("тракт", "").replace("Тракт", "").strip()
        return f"тракт {clean}"
    elif "шоссе" in name_lower:
        clean = name.replace("шоссе", "").replace("Шоссе", "").strip()
        return f"{clean} шоссе"
        
    return f"ул. {name.strip()}"

def get_unique_real_addresses_ru(area_name):
    print(f"🔍 Ищу русские адреса для: {area_name}...")
    overpass_url = "https://overpass-api.de/api/interpreter"
    
    # 1. Сначала просим сервер дать нам сами улицы (highway), чтобы взять их name:ru
    # 2. Затем просим выдать здания (node/way с addr:housenumber)
    overpass_query = f"""
    [out:json][timeout:35];
    area["name:ru"="{area_name}"]->.searchArea;
    
    // Берем дороги для словаря перевода (максимум 5000)
    way["highway"]["name"]["name:ru"](area.searchArea);
    out 5000 tags;
    
    // Берем здания для адресов (максимум 15000)
    (
      node["addr:street"]["addr:housenumber"](area.searchArea);
      way["addr:street"]["addr:housenumber"](area.searchArea);
    );
    out 15000 tags;
    """
    
    session = requests.Session()
    session.trust_env = False 
    headers = {"User-Agent": "Mozilla/5.0"}
    
    try:
        response = session.post(overpass_url, data={'data': overpass_query}, headers=headers, timeout=40)
        
        if response.status_code == 200:
            data = response.json()
            
            # Словарь для перевода (белорусское название -> русское)
            street_translation_dict = {}
            buildings = []
            
            # Разбираем ответ сервера
            for element in data.get('elements', []):
                tags = element.get('tags', {})
                
                # Если это дорога, добавляем в наш словарь перевода
                if 'highway' in tags and 'name' in tags and 'name:ru' in tags:
                    street_translation_dict[tags['name']] = tags['name:ru']
                    
                # Если это здание с номером дома, откладываем в список
                if 'addr:housenumber' in tags and 'addr:street' in tags:
                    buildings.append(tags)
            
            seen_streets = set() 
            final_addresses = []
            
            # Обрабатываем здания и переводим названия
            for tags in buildings:
                house = tags.get('addr:housenumber')
                
                # Сначала ищем русский тег прямо на здании (бывает редко)
                street_ru = tags.get('addr:street:ru')
                
                # Если на здании нет русского названия, достаем его из нашего словаря!
                if not street_ru:
                    street_default = tags.get('addr:street') # Обычно тут на белорусском
                    street_ru = street_translation_dict.get(street_default)
                
                # Если перевода всё равно нет — пропускаем здание
                if not street_ru:
                    continue
                    
                # Убираем "1-я", "2-й" и т.д.
                if any(char.isdigit() for char in street_ru):
                    continue
                    
                # Форматируем
                street_formatted = format_street_name(street_ru)
                
                # Сохраняем по одному дому на улицу
                if street_formatted not in seen_streets:
                    seen_streets.add(street_formatted)
                    final_addresses.append(f"{street_formatted}, д. {house}")
                    
            return final_addresses
        else:
            print(f"❌ Ошибка API: {response.status_code}")
            return []
            
    except Exception as e:
        print(f"❌ Ошибка подключения: {e}")
        return []

def save_to_txt(filename, addresses):
    if not addresses:
        print(f"⚠️ Нет данных для сохранения в {filename}.")
        return
        
    sorted_addresses = sorted(addresses)
    with open(filename, "w", encoding="utf-8") as file:
        for address in sorted_addresses:
            file.write(address + "\n")
    print(f"📁 Успешно сохранено {len(sorted_addresses)} адресов в файл: {filename}")

if __name__ == "__main__":
    minsk_addresses = get_unique_real_addresses_ru("Минск")
    
    print("⏳ Пауза 3 секунды...")
    time.sleep(3) 
    
    region_addresses = get_unique_real_addresses_ru("Минский район")
    region_unique = list(set(region_addresses) - set(minsk_addresses))
    
    print("-" * 40)
    save_to_txt("addresses_minsk.txt", minsk_addresses)
    save_to_txt("addresses_region.txt", region_unique)
    print("🏁 Готово! База полностью на РУССКОМ языке.")