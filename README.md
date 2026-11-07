# Monolith_v2

Responsywna aplikacja operacyjna z czatem lokalnego Ollama, kanałami oryginalnych agentów, diagnostyką i narzędziami workspace. Backend pozostaje źródłem prawdy: aplikacja nie symuluje odpowiedzi, danych telemetrycznych ani transmisji.

## Uruchomienie w Codespaces

Uruchom w terminalu:

```bash
./scripts/start_codespaces.sh
```

W Codespaces serwer nasłuchuje na porcie 8000; [konfiguracja devcontainer](.devcontainer/devcontainer.json) przekazuje port jako prywatny i prosi VS Code o otwarcie podglądu. Dla lokalnego uruchomienia domyślny bind pozostaje `127.0.0.1`. Pierwszy start generuje hasło interfejsu w pliku poza repozytorium z uprawnieniami tylko dla właściciela (`~/.config/monolith/ui-password`). Wpisz je w formularzu logowania; odczytaj lokalnie poleceniem `cat ~/.config/monolith/ui-password`. Można zamiast tego ustawić `MONOLITH_UI_PASSWORD` w środowisku Codespaces/hosta. Hasło musi zawierać co najmniej 24 znaki.

Interfejs i jego API współdzielą origin, sesja jest podpisana przez backend, a ciasteczko sesyjne jest `HttpOnly` i `SameSite=Strict`. Nie umieszczaj haseł ani tokenów w Git. Ustaw `MONOLITH_AGENT_<ARIA|ALEX|ASTYRIA|AURELIUS>_URL` oraz odpowiadające `_TOKEN` jako sekrety środowiskowe, używając rzeczywistych HTTPS endpointów agentów. Żaden endpoint lub token nie został dostarczony w tym środowisku, więc kanały pozostają niepołączone do czasu ich konfiguracji.

## Funkcje i ograniczenia

- **Czat AI:** żądania do istniejącego routera Ollama; wymagany skonfigurowany model i działający lokalny serwer.
- **Kanały agentów:** rzeczywiste POST-y do skonfigurowanych uwierzytelnionych endpointów. Kanał zespołowy zwraca statusy każdego połączenia. Nie skonfigurowano połączeń zastępczych ani agentów pozornych.
- **Terminal:** bez powłoki i arbitralnych poleceń; dostępne są tylko jawnie ograniczone polecenia diagnostyczne.
- **Eksplorator plików:** odczyt plików tekstowych projektu; katalogi ukryte, dowiązania i pliki ponad limit są pomijane/odrzucane.
- **Procesy, diagnostyka i logi:** tylko lokalne odczyty; nie uruchamiają dowolnych usług ani poleceń. Logi nie zawierają treści czatu, haseł ani tokenów.
- **Ollama:** odczyt modeli oraz ręczne pobieranie wybranego modelu do skonfigurowanego endpointu. Operacja pobierania wymaga działającego lokalnego Ollama.
- **Synchronizacja:** WebSocket przesyła rzeczywisty stan diagnostyczny, co 3 sekundy, i niesensytywne zdarzenia pracy serwera. Klient powraca do odświeżania po HTTP, gdy WebSocket nie działa.
- **Hiperprzestrzeń:** tylko odczyt z HTTPS API z tokenem Bearer na serwerze. Wymagany kontrakt odpowiedzi i konfiguracja opisane w [konfiguracji transmisji](fleet_apps/TRANSMISSIONS_SETUP.md). Brak endpointu oznacza „brak połączenia”, a nie pustą lub wygenerowaną transmisję.

Skopiuj `.env.example` wyłącznie jako odniesienie do nazw zmiennych; nie wpisuj sekretów do tego śledzonego pliku.

## Testy

```bash
python3 -m unittest discover -s tests -v
python3 -m compileall -q web bridge codex core diagnostics vision tests
node --check web/app.js
```

Testy lokalne sprawdzają kontrakt i zabezpieczenia API. Rzeczywista odpowiedź Ollama, agentów i zewnętrznego API transmisji wymaga ich autentycznej konfiguracji oraz dostępności.
