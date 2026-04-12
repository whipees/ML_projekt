# Dokumentace projektu: AI OS Telemetry Profiler

**Autor:** Sebastian Janíček 
**E-mail:** janicek@spsejecna.cz 
**Datum vypracování:** 31. března 2026  
**Škola:** Střední průmyslová škola elektrotechnická, Ječná 30, Praha 2  
**Předmět:** Programové vybavení (PV)  


---

## 1. Specifikace požadavků (Business & Functional Requirements)
Cílem projektu bylo vytvořit inteligentní analytický nástroj schopný v reálném čase klasifikovat aktuální zátěž a chování operačního systému.
* **FR1 (Sběr dat):** Aplikace musí v reálném čase (1x za vteřinu) číst telemetrii OS (využití CPU, RAM, disku a síťového rozhraní).
* **FR2 (AI Klasifikace):** Aplikace nesmí spoléhat na statické podmínky (IF-ELSE), ale musí využívat model strojového učení natrénovaný na reálných datech uživatele.
* **FR3 (Detekce anomálií):** Systém musí rozeznat 3 základní stavy: Klid/Kancelářská práce, Extrémní CPU zátěž a Masivní síťový tok.
* **FR4 (Logování):** Změny stavu z klidu do hardwarové či síťové zátěže musí být automaticky logovány s přesným časovým razítkem.
* **FR5 (UI a Vlákna):** Uživatelské rozhraní musí být odděleno od blokujících I/O operací, aby nedocházelo k zasekávání okna při zpoždění senzorů.

## 2. Popis architektury
Aplikace využívá modulární návrh a asynchronní vzor s využitím multithreadingu. Lze ji rozdělit do 3 hlavních komponent:
1.  **Data Collection & Preprocessing Pipeline (Offline fáze):** Skripty slouží k extrakci, transformaci a loadingu (ETL) trénovacích dat ze systémových senzorů.
2.  **Machine Learning Model:** Uložený Serializovaný objekt (`system_usage_model.pkl`), který obsahuje natrénovanou instanci algoritmu Random Forest s předřazeným modulem `StandardScaler` (Pipeline vzor).
3.  **Live Detection GUI (Online fáze):** Real-time vrstva složená ze dvou vláken:
    * *Worker Thread (Pozadí):* Zajišťuje sběr `psutil` metrik a dotazování ML modelu.
    * *Main Thread (UI):* Vykresluje `tkinter` rozhraní a reaguje na změny stavů dodaných z Worker vlákna.

## 3. Popis běhu aplikace (Behaviorální chování)
**Activity Flow (Typický případ užití):**
1. Uživatel spustí `system_usage.ai.py`.
2. Aplikace načte `config.json` a deserializuje AI model z disku.
3. Hlavní vlákno inicializuje GUI a spustí Worker vlákno na pozadí.
4. Uživatel začne stahovat velký soubor.
5. Worker vlákno přečte senzory (`network_recv_mb` prudce vzroste) a předá hodnoty do ML modelu.
6. Model predikuje stav `3` (Síťová zátěž).
7. Worker vlákno zapíše anomálii do `security_log.txt`.
8. UI vlákno plynule podbarví panel č. 3 zelenou barvou (`active_color` z konfigurace).

## 4. Použitá rozhraní a knihovny třetích stran
Aplikace je napsána v jazyce Python (verze 3.10+) a striktně spoléhá na externí balíčky definované v `requirements.txt`.
* **psutil (v6.0.0):** Multiplatformní knihovna pro nízkoúrovňový přístup k senzorům OS (CPU, RAM, disky, sítě).
* **scikit-learn (v1.6.1):** Obsahuje implementaci algoritmu `RandomForestClassifier` a nástroje pro předzpracování.
* **pandas (v2.2.1):** Datové struktury pro formátování vstupů do ML modelu.
* **joblib (v1.3.2):** Služba pro efektivní serializaci a deserializaci natrénovaného ML modelu.
* **tkinter:** Standardní vestavěná knihovna Pythonu pro tvorbu grafického uživatelského rozhraní.

## 5. Právní a licenční aspekty
Tento software je vydán jako Open-Source pro vzdělávací účely (školní projekt). Veškeré využité knihovny třetích stran (psutil, scikit-learn, pandas) podléhají svobodným licencím (MIT, BSD-3-Clause), které komerční i nekomerční užití ve vlastním kódu dovolují. Autorství celého zdrojového kódu ve složce `/src` náleží autorovi tohoto dokumentu.

## 6. Konfigurace programu
Konfigurace probíhá výhradně formou modifikace souboru `config.json` v kořenové složce projektu. Aplikace tento soubor dynamicky čte při startu.
**Struktura config.json:**
* `model_path` (string): Relativní nebo absolutní cesta k natrénovanému `.pkl` modelu.
* `poll_interval_seconds` (float): Frekvence, s jakou Worker vlákno čte senzory (výchozí: 1.0 s).
* `ui_theme.bg_color` (string): HEX kód barvy pozadí aplikace.
* `ui_theme.active_color` (string): HEX kód barvy aktivního (detekovaného) panelu.

## 7. Instalace a spuštění
1. Nainstalujte interpreter jazyka Python (verze 3.10 nebo vyšší).
2. Otevřete terminál ve složce projektu a vytvořte virtuální prostředí:
   `python -m venv .venv`
3. Aktivujte prostředí:
   `source .venv/bin/activate` (Linux/Mac) nebo `.venv\Scripts\activate` (Windows).
4. Nainstalujte závislosti:
   `pip install -r requirements.txt`
5. Pro spuštění monitoringu zadejte do terminálu:
   `python model/system_usage_ai.py`

## 8. Chybové stavy a jejich řešení
* **`FileNotFoundError: Model file not found...`**
    * *Příčina:* Soubor modelu neexistuje v cestě specifikované v `config.json`.
    * *Řešení:* Zkontrolujte strukturu složek, případně natrénujte nový model pomocí nasbíraných dat v Colabu.
* **`psutil.AccessDenied` / `PermissionError`**
    * *Příčina:* OS zakazuje čtení určitých senzorových matrik běžnému uživateli.
    * *Řešení:* Skript ošetřuje tuto chybu vynecháním blokovaného procesu, případně spusťte aplikaci jako Administrátor.
* **`Config load error, using defaults`**
    * *Příčina:* Poškozený formát JSON souboru.
    * *Řešení:* Program chybu zachytí a automaticky použije bezpečné tovární hodnoty, aby nedošlo k pádu. Zkontrolujte syntaxi `config.json`.

## 9. Testování a validace
**Testování Modelu (Validation):** Model Random Forest byl validován metodou Train-Test Split (80/20) na nasbíraném datasetu. Úspěšnost na testovacích datech (Accuracy) dosáhla **99,48 %**. Precision a Recall metriky vykazovaly 100% přesnost při detekci CPU zátěže. 
Byl úspěšně vyřešen problém *Domain Shift* – model je navržen k detekci hardwarových vzorců extrémní zátěže nezávisle na konkrétním hardwarovém výkonu stroje.


## 10. Verze a známé chyby
* **Verze:** 1.0.0 (Release)
* **Známé Issues:** Na některých linuxových distribucích může čtení `disk_io_counters()` vracet nulové hodnoty, pokud balíček `psutil` nemá v systému root práva. Není kritické pro přesnost modelu, protože váha diskových metrik při rozhodování je AI modelem stanovena na < 4 %.

## 11. Databázový model a Síťová konfigurace
*Poznámka dle zadání: Aplikace z principu své funkce nevyužívá relační databázi (naměřená trénovací data ukládá do lokálního CSV) a neposkytuje žádnou vlastní síťovou vrstvu, porty ani webový server.*

## 12. Import a Export (Datová schémata)
Program využívá následující souborová rozhraní:
* **Trénovací dataset (`telemetry_dataset.csv`):** Importní/Exportní schéma obsahuje 7 fixních sloupců: `label_id` (Integer), `cpu_usage_percent` (Float), `ram_usage_percent` (Float), `disk_read_mb` (Float), `disk_write_mb` (Float), `network_sent_mb` (Float), `network_recv_mb` (Float).
* **Bezpečnostní log (`security_log.txt`):** Jednosměrný export událostí obsahující normovaný zápis struktury: `[YYYY-MM-DD HH:MM:SS] ALERT: <Zpráva>`.
