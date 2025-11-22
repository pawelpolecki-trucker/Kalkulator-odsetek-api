import requests
import xml.etree.ElementTree as ET
import urllib3

# Wyłączamy błędy SSL
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

url = "https://static.nbp.pl/dane/stopy/stopy_procentowe_archiwum.xml"

print("Pobieram plik...")
headers = {'User-Agent': 'Mozilla/5.0'}
try:
    r = requests.get(url, verify=False, headers=headers)
    root = ET.fromstring(r.content)
    
    # Bierzemy pierwszy element z brzegu
    pierwszy_wpis = list(root.iter('pozycja'))[0]
    
    print("\n--- OTO CO WIDZI PYTHON (Zrób screena tego!) ---")
    print(f"ATRYBUTY (To tu szukamy nazw): {pierwszy_wpis.attrib}")
    print("--------------------------------------------------\n")
    
except Exception as e:
    print(f"Błąd: {e}")

