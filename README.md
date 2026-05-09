# 📷 Fotograf Czeladnik — System nauki do egzaminu

Aplikacja webowa do nauki przed egzaminem czeladniczym z fotografii.

## Wymagania

- Python 3.8+
- Flask (`pip install flask`)

## Uruchomienie

```bash
# 1. Zainstaluj zależności (jednorazowo)
pip install flask

# 2. Uruchom aplikację
bash start.sh
# lub:
cd backend && python3 app.py
```

Aplikacja dostępna pod adresem: **http://localhost:5000**

## Adresy

| Adres | Opis |
|-------|------|
| `http://localhost:5000` | Strona do nauki |
| `http://localhost:5000/admin` | Panel dodawania pytań |

## Jak dodać pytania?

1. Wejdź na `http://localhost:5000/admin`
2. Wybierz dział (Technologia / Maszynoznawstwo / Materiałoznawstwo)
3. Kliknij **+ Dodaj pytanie**
4. Wybierz typ:
   - **Zamknięte** — wpisz 2–4 odpowiedzi, zaznacz poprawną
   - **Otwarte** — wpisz przykładową odpowiedź modelową
5. Zapisz

## Funkcje

### Nauka
- Testy po 15 pytań (10 zamkniętych + 5 otwartych)
- System wag — pytania z błędnymi odpowiedziami losują się częściej
- Pytania zamknięte — 4 odpowiedzi, zaznacz jedną
- Pytania otwarte — wpisujesz odpowiedź, porównujesz z przykładem, sam oceniasz

### Po teście
- Wynik procentowy
- Przegląd wszystkich odpowiedzi
- Poprawne odpowiedzi dla pomylonych pytań

### Przeglądarka pytań
- Wszystkie pytania z historią odpowiedzi
- Filtrowanie po dziale i wyszukiwanie
- Procent poprawnych odpowiedzi dla każdego pytania

### Statystyki
- Skuteczność per dział
- Najtrudniejsze pytania
- Historia ostatnich testów

## Reset postępu (ukryta komenda)

Wpisz na stronie nauki: `RESETASTER2137`  
(klawiatura, bez pola input — po prostu wpisz te litery będąc na stronie)

## Struktura bazy danych

Baza SQLite zapisywana w `backend/fotograf.db`

Tabele:
- `chapters` — działy (Technologia, Maszynoznawstwo, Materiałoznawstwo)
- `questions` — pytania
- `answers` — odpowiedzi do pytań zamkniętych
- `open_answers` — przykładowe odpowiedzi do pytań otwartych
- `user_answers` — historia odpowiedzi użytkownika
- `sessions` — sesje testowe
