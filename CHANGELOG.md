# Senzera Performance Hub – Changelog

## v7.0 — 7. Mai 2026 — Google Reviews only

Schlanke Variante: alles außer Google-Bewertungen wurde entfernt.

### Was bleibt
- Sidebar-Filter (Regionalleitung, Berichtsmonat, Studio-Auswahl)
- KPI-Kacheln: **Google Ø-Rating** (mit Delta vs. Vormonat), **Neue Rezensionen**, **Rezensionen Gesamt**
- Alarm-Block für Studios unter 4,2 Sternen
- Tab 1 **Performance & Trends**: Ranking, Trend-Verlauf, Detail-Tabelle
- Tab 2 **Management-Bericht**: Auto-Bericht inkl. Trend, Top-Studios, Handlungsbedarf · Downloads (Bericht .txt, Snapshot CSV, alle Google-Daten)

### Was komplett raus ist
- Tab 2 Zenloop Deep-Dive (NPS, Sentiment, Themen-Radar, Segment-NPS)
- Tab 4 Team-Performer (Umsatz, Krankentage, verschlüsselter Datenstore)
- Tab 5 Datenpflege (In-App-Uploads, Encryption-UI)
- Erstgäste-KPIs
- Alle abhängigen Helper-Funktionen (calc_nps, calc_sentiment, top_labels, _decrypt_performer …)

### Aus dem Repo gelöscht
- `Zenloop_Antworten.csv`
- `performer_encrypted.bin`
- `performer_update.py`
- `Erstgaeste_Data.csv`
- `20260306_Performer_excerpt.xlsx`
- `monatliches_update.py`
- `update_daten.py`
- `Senzera_Dashboard_Data Kopie.csv`
- `senzera_dashboard (1) Kopie.py`

### Technisches
- `requirements.txt` reduziert auf `streamlit`, `pandas`, `plotly` (kein cryptography, kein openpyxl mehr nötig).
- Dashboard von 1588 → 808 Zeilen.
- Footer-Versionsstring: `v6` → `v7`.

### Deploy
1. `senzera_dashboard.py`, `requirements.txt`, `CHANGELOG.md` ins GitHub-Repo pushen (überschreiben).
2. Folgende Dateien im GitHub-Repo zusätzlich **manuell löschen** (über github.com → Datei öffnen → Mülleimer → Commit):
   - Zenloop_Antworten.csv
   - performer_encrypted.bin
   - performer_update.py
   - Erstgaeste_Data.csv
   - 20260306_Performer_excerpt.xlsx
   - monatliches_update.py
   - update_daten.py
3. Streamlit Cloud deployt automatisch nach 1–2 Minuten.

---

## v6.0 — 29. April 2026 — Zenloop-Zeitverlauf + Datenpflege-Tab

(Wurde durch v7.0 ersetzt — siehe oben.)

### Zenloop-Zeitverlauf
- Neuer Chart in Tab 2: NPS-Zeitverlauf über alle Monate, aktueller Monat hervorgehoben.
- Vormonats-Vergleich als drei kompakte Karten.
- KPI-Kachel `Zenloop NPS` zeigte Delta vs. Vormonat.

### Tab 5 — Datenpflege (Backup-Weg)
- Passwortgeschützter Tab für Drag-and-Drop-Uploads (Zenloop, Performer, Google).

### In-App-Hilfe
- `ℹ️ Was sehe ich hier?`-Expander pro Tab.

---

## v5.2 — vorher
Mobile-Optimierung, KPI-Layout 3+3, vier Tabs (Performance, Zenloop, Bericht, Performer).
