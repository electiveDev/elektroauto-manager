⚡ EV Charge Manager

Ein leichter, selbst-gehosteter Web-Tracker für den Energieverbrauch von Elektrofahrzeugen.
Entwickelt mit Python (Flask) und Pandas, optimiert für den Betrieb auf Linux-Containern (LXC/Docker) oder Raspberry Pi.

(Platzhalter für deinen Screenshot)

💡 Hintergrund & Motivation

Warum dieses Tool?
Dieses Projekt entstand aus dem Bedarf heraus, da keine smarte Wallbox vorhanden ist. Wer sein E-Auto an einer einfachen Wallbox oder Steckdose mit vorgeschaltetem, analogen oder digitalen Zwischenzähler lädt, hat oft keinen digitalen Überblick über die Kosten und den Verlauf.

Der EV Charge Manager schließt diese Lücke:

Er ersetzt die fehlende "Smartheit" der Wallbox durch einfache manuelle Erfassung.

Er bietet volle Kostentransparenz und historische Daten.

Er funktioniert komplett offline und lokal (kein Cloud-Zwang, kein Abo).

✨ Features

CSV-basiert: Keine Datenbank-Einrichtung nötig. Einfaches Backup durch Kopieren der data.csv.

Intelligente Berechnung: Berechnet automatisch den Verbrauch (kWh) und die Kosten (€) durch Abgleich des aktuellen Zählerstands mit dem vorherigen.

Visualisierung: Interaktive Jahres- und Monatsvergleiche mit Chart.js.

Responsive Dark Mode: Modernes UI, optimiert für Desktop und Mobile (ideal, um Zählerstände direkt am Auto per Handy einzutragen).

Konfigurierbar: Standard-Fahrzeug und aktueller Strompreis können global festgelegt werden.

🛠 Tech Stack

Backend: Python 3.x, Flask

Datenverarbeitung: Pandas

Frontend: HTML5, CSS3 (Custom Dark Theme), Chart.js

Speicher: CSV (Daten), JSON (Einstellungen)

📂 Projektstruktur

ev-manager/
├── app.py              # Hauptanwendung (Flask Server & Logik)
├── data.csv            # Automatisch erstellt (Charge Logs)
├── settings.json       # Automatisch erstellt (Einstellungen)
├── static/
│   └── style.css       # Dark Mode Stylesheet
└── templates/
    ├── index.html      # Hauptdashboard (Eingabe & Liste)
    └── stats.html      # Statistik-Ansicht (Charts)


📝 Lizenz

Dieses Projekt ist unter der MIT Lizenz veröffentlicht. Feel free to fork!
