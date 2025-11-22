import requests
import xml.etree.ElementTree as ET
import json
from datetime import datetime
import urllib3

# Wyłączamy ostrzeżenia SSL
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --- KONFIGURACJA ---
NBP_XML_URL = "https://static.nbp.pl/dane/stopy/stopy_procentowe_archiwum.xml"
START_YEAR = 1998 # Zmieniam na 1998, żeby na pewno nic nie odrzucił datą
OUTPUT_FILE = "rates.json"

def pobierz_dane_nbp():
    try:
        print(f"Pobieranie XML z NBP...")
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(NBP_XML_URL, verify=False, headers=headers)
        response.raise_for_status()
        return response.content
    except Exception as e:
        print(f"BŁĄD POBIERANIA: {e}")
        return None

def parsuj_i_oblicz(xml_content):
    root = ET.fromstring(xml_content)
    rates_list = []
    
    # Szukamy wszystkich pozycji
    pozycje = list(root.iter('pozycja'))
    print(f"Znaleziono {len(pozycje)} wpisów. Analiza...")

    # --- DIAGNOSTYKA ---
    if len(pozycje) > 0:
        pierwszy = pozycje[0]
        print("\n--- [DEBUG] ANALIZA PIERWSZEGO ELEMENTU ---")
        print(f"Znaczniki (keys): {pierwszy.keys()}")
        print(f"Atrybuty (attrib): {pierwszy.attrib}")
        print(f"Tekst w środku: {pierwszy.text}")
        print("-------------------------------------------\n")
    # -------------------

    processed_count = 0
    for pozycja in pozycje:
        # Próbujemy pobrać dane z atrybutów (najczęstszy standard NBP)
        data_str = pozycja.get('obowiazuje_od')
        ref_str = pozycja.get('ref')
        lom_str = pozycja.get('lom')

        # Jeśli nie ma w atrybutach, szukamy w dzieciach (alternatywny format)
        if not data_str:
            child = pozycja.find('obowiazuje_od')
            if child is not None: data_str = child.text
        
        if not ref_str:
            child = pozycja.find('ref')
            if child is not None: ref_str = child.text

        if not lom_str:
            child = pozycja.find('lom')
            if child is not None: lom_str = child.text

        # Diagnostyka błędów dla pierwszych 5 braków
        if not data_str or not ref_str:
            if processed_count < 5:
                print(f"[POMINIĘTO] Brak danych: data='{data_str}', ref='{ref_str}'")
            continue

        try:
            data_obj = datetime.strptime(data_str, "%Y-%m-%d")
            
            # --- OBLICZENIA (Uproszczone dla testu) ---
            stopa_ref = float(ref_str.replace(',', '.'))
            
            rates_list.append({
                "id": f"TEST-{data_str}",
                "effectiveDate": f"{data_str}T00:00:00Z",
                "rate": stopa_ref,
                "type": "TESTOWY WPIS"
            })
            processed_count += 1

        except ValueError as e:
            print(f"Błąd konwersji: {e}")
            continue 

    rates_list.sort(key=lambda x: x['effectiveDate'], reverse=True)
    return rates_list

# --- START ---
xml_content = pobierz_dane_nbp()
if xml_content:
    final_json = parsuj_i_oblicz(xml_content)
    if final_json:
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            json.dump(final_json, f, indent=4)
        print(f"SUKCES: Zapisano {len(final_json)} stawek do {OUTPUT_FILE}")
    else:
        print("Nadal 0 wyników. Zrób zdjęcie powyższych logów [DEBUG]!")
else:
    print("Błąd pobierania.")


