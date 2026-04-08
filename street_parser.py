import requests
import time

def format_street_name(name):
    """Форматирует название в красивый вид 'ул. Название'"""
    name_lower = name.lower()
    
    if "улица" in name_lower or "вуліца" in name_lower:
        clean_name = name.replace("улица", "").replace("Улица", "").replace("вуліца", "").replace("Вуліца", "").strip()
        return f"ул. {clean_name}"
    elif "проспект" in name_lower or "праспект" in name_lower:
        clean_name = name.replace("проспект", "").replace("Проспект", "").replace("праспект", "").replace("Праспект", "").strip()
        return f"пр. {clean_name}"
    elif "переулок" in name_lower or "завулак" in name_lower:
        clean_name = name.replace("переулок", "").replace("Переулок", "").replace("завулак", "").replace("Завулак", "").strip()
        return f"пер. {clean_name}"
    elif "тракт" in name_lower:
        clean_name = name.replace("тракт", "").replace("Тракт", "").strip()
        return f"тракт {clean_name}"
    elif "шоссе" in name_lower:
        clean_name = name.replace("шоссе", "").replace("Шоссе", "").strip()
        return f"{clean_name} шоссе"
        
    return f"ул. {name.strip()}"

def get_unique_real_addresses(area_name, limit=15000):
    print(f"🔍 Ищу адреса для: {area_name} (лимит {limit} зданий)...")
    overpass_url = "https://overpass-api.de/api/interpreter"
    
    # Ограничиваем выдачу, чтобы сервер не падал с 504 ошибкой
    overpass_query = f"""
    [out:json][timeout:25];
    area["name:ru"="{area_name}"]->.searchArea;
    (
      node["addr:street"]["addr:housenumber"](area.searchArea);
      way["addr:street"]["addr:housenumber"](area.searchArea);
    );
    out {limit} tags;
    """
    
    # Отключаем использование системных прокси/VPN, чтобы избежать ProxyError
    session = requests.Session()
    session.trust_env = False 
    
    # Притворяемся обычным браузером
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    try:
        response = session.post(overpass_url, data={'data': overpass_query}, headers=headers, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            seen_streets = set() 
            final_addresses = []
            
            for element in data.get('elements', []):
                tags = element.get('tags', {})
                
                street_raw = tags.get('addr:street:ru', tags.get('addr:street'))
                house = tags.get('addr:housenumber')
                
                if not street_raw or not house:
                    continue
                if any(char.isdigit() for char in street_raw):
                    continue
                    
                street_formatted = format_street_name(street_raw)
                
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
    # Парсим Минск
    minsk_addresses = get_unique_real_addresses("Минск", limit=15000)
    
    print("⏳ Пауза 3 секунды...")
    time.sleep(3) 
    
    # Парсим Минский район
    region_addresses = get_unique_real_addresses("Минский район", limit=15000)
    
    region_unique = list(set(region_addresses) - set(minsk_addresses))
    
    print("-" * 40)
    save_to_txt("addresses_minsk.txt", minsk_addresses)
    save_to_txt("addresses_region.txt", region_unique)
    print("🏁 Готово! База чистая и отформатированная.")