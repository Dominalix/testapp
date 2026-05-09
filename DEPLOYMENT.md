# 🚀 Prywatny Deployment na GitHub Pages

## 📋 Wymagania
- Konto GitHub
- Repozytorium z kodem aplikacji

## 🔧 Krok po kroku

### 1. Przygotowanie repozytorium
1. Upewnij się że wszystkie pliki są w repozytorium
2. Sprawdź czy folder `.github/workflows` istnieje
3. Zatwierdź zmiany (`git add .` i `git commit -m "Add deployment config"`)

### 2. Włączanie GitHub Pages
1. Wejdź w swoje repozytorium na GitHubie
2. Idź do `Settings` → `Pages`
3. Wybierz `Deploy from a branch`
4. Ustaw `main` jako branch
5. Zapisz zmiany

### 3. Pierwszy deployment
1. Przejdź do `Actions` w swoim repozytorium
2. Kliknij `Deploy to GitHub Pages`
3. Kliknij `Run workflow`
4. Poczekaj na zakończenie budowania

### 4. Dostęp do aplikacji
- Po udanym deploymentu aplikacja będzie dostępna pod adresem:
  `https://[twoja-nazwa-użytkownika].github.io/fotograf-app`

## 🔒 Bezpieczeństwo i prywatność

### Dostęp tylko dla wybranych osób
Aby ograniczyć dostęp tylko dla Ciebie i koleżanki:

1. Idź do `Settings` → `Pages`
2. W sekcji `Custom domain` dodaj subdomenę (opcjonalnie)
3. Skontaktuj się z administratorem GitHub Pages w razie potrzeby

### Ochrona hasłem (opcjonalnie)
Możesz dodać prostą ochronę hasłem:
1. Dodaj na początku `index.html`:
```javascript
<script>
const correctPassword = 'wasze-haslo';
const password = prompt('Podaj hasło dostępu:');
if (password !== correctPassword) {
    document.body.innerHTML = '<h1>Błędne hasło</h1>';
    throw new Error('Unauthorized access');
}
</script>
```

## 🔄 Automatyczne aktualizacje

Każdy `push` do brancha `main` automatycznie:
- Buduje aplikację
- Aktualizuje stronę
- Zachowuje bazę danych

## 📱 Dostęp mobilny
Aplikacja działa na:
- Komputerach
- Smartfonach
- Tabletach
- Każdej przeglądarce internetowej

## ⚠️ Ważne uwagi

- Baza danych jest kopiowana przy każdym deploymentu
- Wszystkie zmiany w bazie danych są synchronizowane
- Aplikacja działa w trybie produkcyjnym (bez debugowania)
- Hostowanie jest **całkowicie darmowe**

## 🆘 W razie problemów

1. Sprawdź logi w `Actions` → `Deploy to GitHub Pages`
2. Upewnij się że wszystkie pliki są w repozytorium
3. Sprawdź czy workflow ma odpowiednie uprawnienia

---

**Gotowe! Teraz tylko Ty i Twoja koleżanka macie dostęp do aplikacji 24/7** 🎉
