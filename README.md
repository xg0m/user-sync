# user-sync

![Testy](https://github.com/xg0m/user-sync/actions/workflows/tests.yml/badge.svg)

Synchronizacja kont użytkowników z eksportem z systemu kadrowego. Narzędzie porównuje dane kadrowe z katalogiem kont (symulacja Active Directory w pliku JSON), pokazuje plan zmian i dopiero na życzenie go wykonuje. Projekt należy do tego samego fikcyjnego wdrożenia co [obieg-dokumentow-wdrozenie](https://github.com/xg0m/obieg-dokumentow-wdrozenie): grupy kont odpowiadają rolom z tamtej konfiguracji. Dane są fikcyjne.

## Co robi

| Sytuacja w kadrach | Stan konta | Akcja |
|---|---|---|
| Pracownik aktywny | Brak konta | UTWORZ: nowy login i grupy |
| Pracownik aktywny | Inne dane lub grupy | ZMIEN: aktualizacja atrybutów |
| Pracownik aktywny | Konto wyłączone | WLACZ: ponowne zatrudnienie |
| Pracownik zwolniony | Konto aktywne | WYLACZ: wyłączenie i usunięcie z grup |
| Brak rekordu | Konto aktywne | SPRAWDZ: decyzja człowieka, bez automatycznego wyłączenia |
| Nieznany status lub jednostka bez mapowania | dowolny | SPRAWDZ |

Konta nie są nigdy usuwane, tylko wyłączane. Konta techniczne (bez `employee_id`) są pomijane.

## Reguły

- **Login:** pierwsza litera imienia i nazwisko, bez polskich znaków, maksymalnie 20 znaków (Łukasz Żółkiewski: `lzolkiewski`). Zajęty login dostaje numer (`jkowalski2`). Loginy kont wyłączonych też są zajęte, bo nie używa się ich ponownie.
- **Grupy:** grupa bazowa, grupa jednostki z `config/mapping.json` i `GRP_Kierownicy` dla osób, które mają aktywnych podwładnych.
- **Tryb podglądu:** domyślnie narzędzie tylko zapisuje raport planu. Zmiany zapisuje dopiero z `--apply`.
- **Limit bezpieczeństwa:** jeśli plan wyłącza więcej niż 20% aktywnych kont, `--apply` się zatrzymuje. Chroni to przed niepełnym eksportem z kadr, który wyłączyłby połowę firmy. Limit zmienia `--max-disable`, a omija `--force`.

## Szybki start

```bash
git clone https://github.com/xg0m/user-sync.git
cd user-sync
python -m venv venv
# Linux i macOS: source venv/bin/activate
# Windows (PowerShell): venv/Scripts/Activate.ps1
pip install -r requirements.txt

python main.py                                   # plan, bez zmian
python main.py --apply --output output/wynik.json # zapis wyniku do nowego pliku
pytest -v
```

## Wynik na danych przykładowych

```text
UTWORZ: 2
ZMIEN: 2
WLACZ: 1
WYLACZ: 1
SPRAWDZ: 3
```

| ID | Osoba | Akcja | Powód |
|---|---|---|---|
| 3 | Maria Wiśniewska | ZMIEN | Awans na profesora, została kierownikiem (nowa grupa) |
| 5 | Katarzyna Kamińska | WYLACZ | Zwolniona |
| 6 | Tomasz Lewandowski | ZMIEN | Przeniesienie z Działu Kadr do Działu IT |
| 7 | Jan Kowalski | UTWORZ | Nowy pracownik. Login `jkowalski` należy do wyłączonego konta, więc dostaje `jkowalski2` |
| 8 | Łukasz Żółkiewski | UTWORZ | Nowy pracownik, polskie znaki w loginie |
| 9 | Ewa Zielińska | WLACZ | Ponowne zatrudnienie |
| 10 | Marek Szymański | SPRAWDZ | Jednostka bez mapowania na grupę |
| 11 | Joanna Pawlak | SPRAWDZ | Nieznany status w eksporcie |
| 91 | Adam Grabowski | SPRAWDZ | Aktywne konto bez rekordu w kadrach |

Po wykonaniu planu kolejne uruchomienie zwraca już tylko trzy przypadki do sprawdzenia. Synchronizacja jest idempotentna, co sprawdza test.

## Struktura

```text
user-sync/
  config/mapping.json        jednostki i ich grupy
  sample_data/hr_export.csv  fikcyjny eksport z systemu kadrowego
  sample_data/directory.json fikcyjny stan katalogu kont
  sync/logins.py             tworzenie loginów
  sync/plan.py               plan synchronizacji i jego wykonanie
  sync/report.py             raport Markdown
  tests/                     testy (pytest)
  main.py                    wiersz poleceń
```

## Ograniczenia

- Katalog jest plikiem JSON. Prawdziwa integracja z Active Directory użyłaby LDAP (np. biblioteki ldap3) albo Microsoft Graph dla Entra ID, a reguły planu zostałyby te same.
- Brak obsługi hasła startowego i powiadomień o nowym koncie.
- Porównanie po `employee_id`, więc rekordy bez identyfikatora w kadrach trzeba uzupełnić przed synchronizacją.

## Praca z narzędziami AI

Kod powstawał z pomocą narzędzi AI. Weryfikuję go testami i czytam przed zatwierdzeniem. Reguły pracy opisuje [AGENTS.md](AGENTS.md).

## Autor

Oliwier Sieniuc, [@xg0m](https://github.com/xg0m). Licencja MIT.
