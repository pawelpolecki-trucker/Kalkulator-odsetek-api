#!/bin/bash

# Przejdź do folderu z repozytorium (Zmień ścieżkę na swoją!)
cd /home/pi/kalkulator-api 

# 1. Uruchom generator
python3 generator.py

# 2. Sprawdź, czy są zmiany w pliku JSON
if [[ `git status --porcelain` ]]; then
  # Są zmiany - wysyłamy na GitHub
  git add rates.json
  git commit -m "Auto-aktualizacja stawek NBP: $(date)"
  git push origin main
  echo "Zaktualizowano stawki na GitHub!"
else
  # Brak zmian (NBP nie zmienił stóp)
  echo "Brak zmian w stawkach."
fi
