import os
import uuid
import pandas as pd
from flask import Flask, render_template, request, redirect, url_for, flash
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'dev_secret_key_change_in_production'  # Nötig für Flash-Messages

CSV_FILE = 'data.csv'
COLUMNS = ['id', 'vehicle_id', 'date', 'meter_reading', 'price_per_kwh']

def init_csv():
    """Erstellt die CSV-Datei, falls sie nicht existiert."""
    if not os.path.exists(CSV_FILE):
        df = pd.DataFrame(columns=COLUMNS)
        df.to_csv(CSV_FILE, index=False)

def get_data():
    """Lädt Daten, berechnet Verbrauch/Kosten und sortiert sie."""
    init_csv()
    try:
        df = pd.read_csv(CSV_FILE)
    except pd.errors.EmptyDataError:
        return []

    if df.empty:
        return []

    # Typkonvertierung für saubere Berechnungen
    df['date'] = pd.to_datetime(df['date'])
    df['meter_reading'] = pd.to_numeric(df['meter_reading'])
    df['price_per_kwh'] = pd.to_numeric(df['price_per_kwh'])

    # Sortieren: Wichtig für korrekte Delta-Berechnung (Zeitreihe)
    df = df.sort_values(by=['vehicle_id', 'date'])

    # Business Logic: Verbrauch berechnen (Aktuell - Vorheriger) pro Fahrzeug
    # shift(1) holt den Wert der vorherigen Zeile innerhalb der Gruppe
    df['prev_meter'] = df.groupby('vehicle_id')['meter_reading'].shift(1)
    
    # Verbrauch: Wenn kein Vorgänger (erster Eintrag), dann 0
    df['consumption_kwh'] = df['meter_reading'] - df['prev_meter']
    df['consumption_kwh'] = df['consumption_kwh'].fillna(0)

    # Kostenberechnung
    df['cost_eur'] = df['consumption_kwh'] * df['price_per_kwh']

    # Formatierung für das Frontend (zurück zu Strings/schönen Zahlen)
    data = df.to_dict('records')
    return data

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        # Daten aus Formular
        vehicle_id = request.form.get('vehicle_id').strip()
        date_str = request.form.get('date')
        meter_reading = float(request.form.get('meter_reading'))
        price = float(request.form.get('price'))

        # Validierung: Negative Zählerstände verhindern (einfacher Check)
        if meter_reading < 0 or price < 0:
            flash("Fehler: Zählerstand und Preis müssen positiv sein.", "error")
            return redirect(url_for('index'))

        # Plausibilitäts-Check (Optional):
        # Hier könnte man prüfen, ob der neue Zählerstand niedriger ist als
        # ein existierender älterer Eintrag desselben Fahrzeugs.
        
        # Speichern
        new_entry = {
            'id': str(uuid.uuid4()),
            'vehicle_id': vehicle_id,
            'date': date_str,
            'meter_reading': meter_reading,
            'price_per_kwh': price
        }
        
        df_new = pd.DataFrame([new_entry])
        # Append mode, header nur wenn Datei leer (wird durch init_csv gehandhabt aber sicherheitshalber)
        df_new.to_csv(CSV_FILE, mode='a', header=not os.path.exists(CSV_FILE), index=False)
        
        flash("Eintrag erfolgreich gespeichert.", "success")
        return redirect(url_for('index'))

    # GET Request: Daten anzeigen
    entries = get_data()
    # Sortierung für Anzeige umkehren (neueste oben)
    entries.sort(key=lambda x: (x['vehicle_id'], x['date']), reverse=True)
    return render_template('index.html', entries=entries)

@app.route('/delete/<entry_id>')
def delete(entry_id):
    init_csv()
    df = pd.read_csv(CSV_FILE)
    # Zeile mit der ID entfernen
    df = df[df['id'] != entry_id]
    df.to_csv(CSV_FILE, index=False)
    flash("Eintrag gelöscht.", "info")
    return redirect(url_for('index'))

if __name__ == '__main__':
    init_csv()
    app.run(debug=True, port=5000)