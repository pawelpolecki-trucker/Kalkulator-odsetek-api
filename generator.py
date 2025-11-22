import requests
import xml.etree.ElementTree as ET
import json
from datetime import datetime
import urllib3

# Wyłączamy ostrzeżenia SSL
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --- KONFIGURACJA ---
NBP_XML_URL = "https://static.nbp.pl/dane/stopy/stopy_procentowe_archiwum.xml"
START_YEAR = 2015
OUTPUT_FILE = "rates.json"

# Stałe marże
MARZA_USTAWOWE = 3.5
MARZA_OPOZNIENIE = 5.5

def pobierz_dane_nbp():
    try:
        print(f"Pobieranie XML z NBP...")
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko)'
        }
        response = requests.get(NBP_XML_URL, verify=False, headers=headers)
        response.raise_for_status()
        return response.content
    except Exception as e:
        print(f"BŁĄD POBIERANIA: {e}")
        return None

def parsuj_i_oblicz(xml_content):
    try:
        root = ET.fromstring(xml_content)
    except ET.ParseError as e:
        print(f"Błąd parsowania XML: {e}")
        return []

    rates_list = []
    
    # --- METODA NUKLEARNA (SCANNER) ---
    # Zamiast szukać rodziców i dzieci, skanujemy plik linia po linii.
    # Jak znajdziemy datę -> zapamiętujemy ją.
    # Jak znajdziemy stopę -> przypisujemy do ostatniej zapamiętanej daty.
    
    biezaca_data = None
    licznik_znalezionych = 0

    # iter() przechodzi przez WSZYSTKIE elementy w pliku, niezależnie od głębokości
    for element in root.iter():
        
        # 1. Czy ten element zmienia datę?
        if 'obowiazuje_od' in element.attrib:
            data_str = element.attrib['obowiazuje_od']
            try:
                data_obj = datetime.strptime(data_str, "%Y-%m-%d")
                # Sprawdzamy rok OD RAZU, żeby nie przetwarzać starych danych
                if data_obj.year >= START_YEAR:
                    biezaca_data = data_str
                else:
                    biezaca_data = None # Data za stara, ignorujemy kolejne wpisy aż do nowej daty
            except ValueError:
                pass # Ignorujemy błędne daty

        # 2. Czy ten element to stopa referencyjna?
        # Musimy mieć aktywną datę i odpowiednie ID
        if biezaca_data and element.get('id') == 'ref':
            wartosc_str = element.get('oprocentowanie')
            if wartosc_str:
                try:
                    stopa_ref = float(wartosc_str.replace(',', '.'))
                    
                    # Mamy komplet (Data + Wartość) -> Robimy wpis!
                    
                    # Obliczenia (Ustawowe)
                    rate_ust = round((stopa_ref + MARZA_USTAWOWE) / 100, 4)
                    rates_list.append({
                        "id": f"AUTO-UST-{biezaca_data}",
                        "effectiveDate": f"{biezaca_data}T00:00:00Z",
                        "rate": rate_ust,
                        "type": "ODSETKI USTAWOWE"
                    })

                    # Obliczenia (Opóźnienie)
                    rate_opoz = round((stopa_ref + MARZA_OPOZNIENIE) / 100, 4)
                    rates_list.append({
                        "id": f"AUTO-OPOZ-{biezaca_data}",
                        "effectiveDate": f"{biezaca_data}T00:00:00Z",
                        "rate": rate_opoz,
                        "type": "ODSETKI ZA OPÓŹNIENIE"
                    })
                    
                    # (Dla uproszczenia pomijam podatkowe w tym trybie skanowania, 
                    #  bo wymagają pary ref+lom w tym samym momencie, a skaner idzie po kolei.
                    #  Te dwa powyżej są najważniejsze dla kalkulatora).
                    
                    licznik_znalezionych += 1
                    
                except ValueError:
                    continue

    # Sortowanie
    rates_list.sort(key=lambda x: x['effectiveDate'], reverse=True)
    return rates_list

# --- START ---
xml_content = pobierz_dane_nbp()
if xml_content:
    final_json = parsuj_i_oblicz(xml_content)
    
    if final_json:
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            json.dump(final_json, f, indent=4)
        print(f"SUKCES! Zapisano {len(final_json)} stawek do {OUTPUT_FILE}")
    else:
        print("Nadal 0 wyników. Coś jest bardzo dziwnego z tym plikiem.")
else:
    print("Nie udało się pobrać pliku.")


