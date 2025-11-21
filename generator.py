import requests
import xml.etree.ElementTree as ET
import json
import uuid
from datetime import datetime

# --- KONFIGURACJA ---
NBP_XML_URL = "https://static.nbp.pl/dane/stopy/stopy_procentowe_archiwum.xml"
START_YEAR = 2015  # Pobieramy stawki tylko od tego roku w górę
OUTPUT_FILE = "rates.json"

# Stałe marże (zgodnie z Kodeksem Cywilnym i Ordynacją Podatkową)
MARZA_USTAWOWE = 3.5
MARZA_OPOZNIENIE = 5.5
# Dla podatkowych: (Lombard + 2%), min 8%

def pobierz_dane_nbp():
    try:
        print(f"Pobieranie XML z NBP...")
        response = requests.get(NBP_XML_URL)
        response.raise_for_status()
        return response.content
    except Exception as e:
        print(f"BŁĄD POBIERANIA: {e}")
        return None

def parsuj_i_oblicz(xml_content):
    root = ET.fromstring(xml_content)
    
    rates_list = []
    
    # Przechodzimy przez każdą zmianę stóp w historii
    for pozycja in root.findall('pozycja'):
        data_str = pozycja.get('obowiazuje_od') # YYYY-MM-DD
        ref_str = pozycja.get('ref')            # Stopa referencyjna
        lom_str = pozycja.get('lom')            # Stopa lombardowa (dla podatkowych)
        
        if not ref_str: continue
        
        # Parsowanie daty
        data_obj = datetime.strptime(data_str, "%Y-%m-%d")
        
        # Filtrowanie lat (pomijamy bardzo stare)
        if data_obj.year < START_YEAR:
            continue
            
        # Konwersja liczb (NBP używa przecinka "5,75", Python chce kropki "5.75")
        stopa_ref = float(ref_str.replace(',', '.'))
        stopa_lom = float(lom_str.replace(',', '.')) if lom_str else 0.0
        
        # --- OBLICZENIA ---
        
        # 1. Ustawowe (Ref + 3.5%)
        rate_ust = round((stopa_ref + MARZA_USTAWOWE) / 100, 4)
        rates_list.append({
            "id": f"AUTO-UST-{data_str}", # Deterministyczne ID
            "effectiveDate": f"{data_str}T00:00:00Z",
            "rate": rate_ust,
            "type": "ODSETKI USTAWOWE"
        })
        
        # 2. Za Opóźnienie (Ref + 5.5%)
        rate_opoz = round((stopa_ref + MARZA_OPOZNIENIE) / 100, 4)
        rates_list.append({
            "id": f"AUTO-OPOZ-{data_str}",
            "effectiveDate": f"{data_str}T00:00:00Z",
            "rate": rate_opoz,
            "type": "ODSETKI ZA OPÓŹNIENIE"
        })
        
        # 3. Podatkowe (Lombard + 2%, min 8%)
        # Wzór: Lombard + 2
        podstawa_podatkowe = stopa_lom + 2.0
        final_podatkowe = max(podstawa_podatkowe, 8.0) # Nie mniej niż 8%
        
        rate_pod = round(final_podatkowe / 100, 4)
        rates_list.append({
            "id": f"AUTO-POD-{data_str}",
            "effectiveDate": f"{data_str}T00:00:00Z",
            "rate": rate_pod,
            "type": "ODSETKI PODATKOWE"
        })

    # Sortowanie od najnowszej daty
    rates_list.sort(key=lambda x: x['effectiveDate'], reverse=True)
    
    return rates_list

# --- START ---
xml_content = pobierz_dane_nbp()
if xml_content:
    final_json = parsuj_i_oblicz(xml_content)
    
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(final_json, f, indent=4)
        
    print(f"SUKCES: Zapisano {len(final_json)} stawek do {OUTPUT_FILE}")
else:
    print("Nie udało się wygenerować pliku.")
