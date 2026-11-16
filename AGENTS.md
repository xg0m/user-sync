# Reguły pracy z narzędziami AI w tym repozytorium

Plik dla narzędzi AI w wierszu poleceń (Claude Code, Gemini CLI, Codex CLI) i dla osób współpracujących.

## Kontekst

Narzędzie w Pythonie 3.12 (tylko biblioteka standardowa) do synchronizacji kont z eksportem kadrowym. Logika planu jest w sync/plan.py.

## Reguły

- Kont nigdy nie usuwamy, tylko wyłączamy.
- Konto bez rekordu w kadrach trafia do sprawdzenia, nie jest wyłączane automatycznie.
- Tryb podglądu zostaje domyślny. Zapis zmian tylko z --apply.
- Nie usuwaj ani nie osłabiaj limitu wyłączeń bez uzasadnienia w opisie zmiany.
- Każda zmiana reguł wymaga testu i aktualizacji tabeli w README.
- W sample_data używaj wyłącznie danych fikcyjnych.

## Sposób pracy

1. Przeczytaj README i sync/plan.py.
2. Najpierw napisz test, potem kod.
3. Uruchom pytest -v oraz python main.py.
4. Sprawdź zmiany ręcznie przed zatwierdzeniem. Odpowiedzi AI traktuj jako szkic.
