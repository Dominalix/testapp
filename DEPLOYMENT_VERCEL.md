# 🚀 Prywatny Deployment na Vercel

## 📋 Wymagania
- Konto GitHub (prywatne repozytorium)
- Konto Vercel (darmowe)
- Kod aplikacji

---

## 🔧 Krok po kroku

### 1. Przygotowanie repozytorium
1. Upewnij się że wszystkie pliki są w Twoim prywatnym repozytorium GitHub
2. Sprawdź czy pliki konfiguracyjne istnieją:
   - `vercel.json`
   - `api/index.py`
   - `package.json`

### 2. Połączenie Vercel z GitHub
1. Zaloguj się na [vercel.com](https://vercel.com)
2. Kliknij `Add New...` → `Project`
3. Wybierz `Import Git Repository`
4. Połącz swoje konto GitHub z Vercel
5. Wybierz prywatne repozytorium `fotograf-app`

### 3. Konfiguracja projektu
Vercel automatycznie wykryje konfigurację z `vercel.json`:
- Python 3.9 jako runtime
- Pliki statyczne z `frontend/public`
- API z `api/index.py`

### 4. Deployment
1. Kliknij `Deploy`
2. Poczekaj na zakończenie budowania
3. Gotowe! Aplikacja dostępna pod adresem Vercel

---

## 🔐 Bezpieczeństwo i dostęp

### Ochrona hasłem
Aplikacja jest chroniona hasłem:
1. Dostęp do strony: `https://twoja-domena.vercel.app`
2. Pojawi się ekran logowania
3. Wpisz hasło: `wasze-haslo` (zmień w `api/index.py`)
4. Hasło jest ważne przez 24 godziny (cookie)

### Zarządzanie dostępem
**Zmiana hasła:**
```python
# W api/index.py linii ~15
const correctPassword = 'nowe-haslo'
```

**Dodawanie uprawnień IP:**
```python
# W api/index.py linii ~10
ALLOWED_IPS = ['192.168.1.1', 'twoje-ip']  # Dodaj swoje IP
```

**Bloowanie IP:**
```python
# W api/index.py linii ~11
BLOCKED_IPS = ['192.168.1.100']  # Dodaj IP do zablokowania
```

---

## 🛡️ Funkcje bezpieczeństwa

### 1. Ograniczanie rate limitu
- Maksymalnie 30 requestów na minutę na IP
- Automatyczne blokowanie przy przekroczeniu

### 2. Biał lista IP (whitelist)
- Możesz dodać zaufane adresy IP
- Tylko te IP mają dostęp niezależnie od hasła

### 3. Czarna lista IP (blacklist)
- Możesz zablokować konkretne adresy IP
- Natychmiastowe blokowanie bez możliwości dostępu

### 4. Logowanie prób dostępu
- Każda próba jest logowana (możesz dodać logi do bazy)

---

## 📱 Dostęp mobilny i komputerowy

Aplikacja działa na:
- ✅ Komputerach (PC, Mac, Linux)
- ✅ Smartfonach (iOS, Android)
- ✅ Tabletach
- ✅ Każdej nowoczesnej przeglądarce

---

## 🔄 Automatyczne aktualizacje

Każdy `push` do brancha `main`:
1. Automatycznie buduje aplikację
2. Aktualizuje stronę na Vercel
3. Zachowuje bazę danych

---

## 💰 Koszty

**Vercel (plan Hobby):**
- ✅ Całkowicie darmowe
- ✅ Prywatne repozytoria
- ✅ Nielimitowany transfer
- ✅ HTTPS automatycznie
- ✅ Własna domena (opcjonalnie)

---

## 🆘 W razie problemów

### Aplikacja się nie ładuje:
1. Sprawdź logi w Vercel Dashboard
2. Upewnij się że wszystkie pliki są w repo
3. Sprawdź czy `package.json` ma poprawne zależności

### Błędy buildowania:
1. Sprawdź składnię `api/index.py`
2. Upewnij się że `flask-cors` jest w `requirements.txt`
3. Spróbuj lokalnie: `pip install -r requirements.txt`

### Problemy z dostępem:
1. Sprawdź czy hasło jest poprawne
2. Wyczyść cookies w przeglądarce
3. Sprawdź czy Twoje IP jest na białej liście

---

## 🎉 Gotowe!

Po tych krokach Twoja aplikacja:
- ✅ Działa 24/7 bez Twojego komputera
- ✅ Jest prywatna (tylko Ty i koleżanka macieście dostęp)
- ✅ Jest chroniona hasłem i zabezpieczeniami sieciowymi
- ✅ Działa na telefonach i komputerach
- ✅ Aktualizuje się automatycznie

**Adres aplikacji:** `https://twoja-domena.vercel.app`

---

## 📞 Kontakt i wsparcie

W razie problemów z deploymentem:
- Sprawdź [dokumentację Vercel](https://vercel.com/docs)
- Skontaktuj się z pomocą techniczną Vercel
- Sprawdź logi w dashboardzie Vercel

**Miłego użytkowania!** 📷✨
