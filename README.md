# ⚡ EV Charge Manager

Ein leichter, selbst-gehosteter Web-Tracker für den Energieverbrauch von Elektrofahrzeugen.  
Entwickelt mit **Python (Flask)** und **Pandas**, optimiert für den Betrieb auf Linux-Containern (LXC/Docker) oder Raspberry Pi. Speichert Daten in **CSV-Dateien**, benötigt keine externe Datenbank.


## ✨ Features

* **CSV-basiert:** Keine Datenbank-Einrichtung nötig. Einfaches Backup durch Kopieren der `data.csv`.
* **Automatische Berechnung:** Berechnet Verbrauch (kWh) und Kosten (€) basierend auf Zählerstand-Deltas.
* **Visualisierung:** Interaktive Jahres- und Monatsvergleiche mit [Chart.js](https://www.chartjs.org/).
* **Responsive Dark Mode:** Modernes UI, optimiert für Desktop und Mobile.
* **Konfigurierbar:** Standard-Fahrzeug und Strompreis können über das UI gesetzt werden.
* **Datenschutz:** Daten bleiben zu 100% auf deinem Server.

## 🛠 Tech Stack

* **Backend:** Python 3.x, Flask
* **Datenverarbeitung:** Pandas
* **Frontend:** HTML5, CSS3 (Custom Dark Theme), Chart.js
* **Speicher:** CSV, JSON (für Settings)
