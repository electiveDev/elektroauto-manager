import os
import uuid
import json
import pandas as pd
from flask import Flask, render_template, request, redirect, url_for, flash
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'dev_secret_key_change_in_production'

CSV_FILE = 'data.csv'
SETTINGS_FILE = 'settings.json'
COLUMNS = ['id', 'vehicle_id', 'date', 'meter_reading', 'price_per_kwh']

# --- Hilfsfunktionen ---

def init_files():
    """Initialisiert CSV und Settings Datei, falls nicht vorhanden."""
    if not os.path.exists(CSV_FILE):
        pd.DataFrame(columns=COLUMNS).to_csv(CSV_FILE, index=False)
    
    if not os.path.exists(SETTINGS_FILE):
        # Standardwerte beim ersten Start
        with open(SETTINGS_FILE, 'w') as f:
            json.dump({'default_vehicle': '', 'default_price': 0.30}, f)

def get_settings():
    """Lädt die Einstellungen."""
    try:
        with open(SETTINGS_FILE, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def save_settings(settings):
    """Speichert die Einstellungen."""
    with open(SETTINGS_FILE, 'w') as f:
        json.dump(settings, f)

def get_data():
    """Lädt CSV, berechnet Verbrauch und Kosten."""
    try:
        df = pd.read_csv(CSV_FILE)
    except pd.errors.EmptyDataError:
        return []

    if df.empty:
        return []

    # Typkonvertierung
    df['date'] = pd.to_datetime(df['date'])
    df['meter_reading'] = pd.to_numeric(df['meter_reading'])
    df['price_per_kwh'] = pd.to_numeric(df['price_per_kwh'])

    # Sortieren & Berechnen
    df = df.sort_values(by=['vehicle_id', 'date'])
    
    # Delta zum Vorgänger berechnen (Gruppiert nach Fahrzeug)
    df['prev_meter'] = df.groupby('vehicle_id')['meter_reading'].shift(1)
    df['consumption_kwh'] = df['meter_reading'] - df['prev_meter']
    df['consumption_kwh'] = df['consumption_kwh'].fillna(0) # Erster Eintrag ist 0
    
    # Kosten
    df['cost_eur'] = df['consumption_kwh'] * df['price_per_kwh']

    return df

# --- Routen ---

@app.route('/', methods=['GET', 'POST'])
def index():
    init_files()
    settings = get_settings()
    
    # Standardwerte laden (Fallback, falls JSON leer/defekt)
    today_str = datetime.today().strftime('%Y-%m-%d')
    default_vehicle = settings.get('default_vehicle', '')
    default_price = settings.get('default_price', 0.30)

    if request.method == 'POST':
        # Daten aus dem "Neuer Eintrag" Formular
        vehicle_id = request.form.get('vehicle_id').strip()
        date_str = request.form.get('date')
        
        try:
            meter_reading = float(request.form.get('meter_reading'))
            price = float(request.form.get('price'))
        except ValueError:
            flash("Fehler: Ungültige Zahlenwerte.", "error")
            return redirect(url_for('index'))

        new_entry = {
            'id': str(uuid.uuid4()),
            'vehicle_id': vehicle_id,
            'date': date_str,
            'meter_reading': meter_reading,
            'price_per_kwh': price
        }
        
        # Speichern
        df_new = pd.DataFrame([new_entry])
        df_new.to_csv(CSV_FILE, mode='a', header=not os.path.exists(CSV_FILE), index=False)
        
        flash("Eintrag gespeichert.", "success")
        return redirect(url_for('index'))

    # Datenanzeige
    df = get_data()
    entries = df.to_dict('records') if not isinstance(df, list) else []
    
    # Sortierung: Neueste oben
    entries.sort(key=lambda x: (x['vehicle_id'], x['date']), reverse=True)
    
    return render_template('index.html', 
                           entries=entries, 
                           today=today_str, 
                           default_vehicle=default_vehicle, 
                           default_price=default_price)

@app.route('/settings', methods=['POST'])
def update_settings():
    """Speichert Standard-Fahrzeug UND Standard-Preis."""
    vehicle = request.form.get('default_vehicle', '').strip()
    price_str = request.form.get('default_price', '0.30').replace(',', '.')
    
    try:
        price = float(price_str)
    except ValueError:
        price = 0.30
        
    save_settings({
        'default_vehicle': vehicle,
        'default_price': price
    })
    
    flash("Standardwerte aktualisiert.", "success")
    return redirect(url_for('index'))

@app.route('/delete/<entry_id>')
def delete(entry_id):
    init_files()
    df = pd.read_csv(CSV_FILE)
    df = df[df['id'] != entry_id]
    df.to_csv(CSV_FILE, index=False)
    flash("Eintrag gelöscht.", "info")
    return redirect(url_for('index'))

@app.route('/stats')
def stats():
    df = get_data()
    if isinstance(df, list) or df.empty:
        flash("Keine Daten für Statistiken vorhanden.", "info")
        return redirect(url_for('index'))

    # Vorbereitung für Jahresvergleich
    df['year'] = df['date'].dt.year
    df['month_num'] = df['date'].dt.month
    
    # 1. KPI Summen
    total_kwh = df['consumption_kwh'].sum()
    total_cost = df['cost_eur'].sum()
    
    # 2. Jahresübersicht Tabelle
    yearly_grp = df.groupby('year')[['consumption_kwh', 'cost_eur']].sum().reset_index()

    # 3. Pivot für Chart (Monate vs Jahre)
    pivot_kwh = df.pivot_table(index='month_num', columns='year', values='consumption_kwh', aggfunc='sum', fill_value=0)
    
    # ChartJS Daten bauen
    years = sorted(df['year'].unique())
    datasets = []
    colors = ['#00d4ff', '#ff4d4d', '#00b894', '#fdcb6e', '#6c5ce7']
    
    for i, year in enumerate(years):
        if year in pivot_kwh.columns:
            datasets.append({
                'label': str(year),
                'data': pivot_kwh[year].tolist(),
                'borderColor': colors[i % len(colors)],
                'fill': False,
                'tension': 0.3
            })

    chart_data = {
        'labels': ['Jan', 'Feb', 'Mär', 'Apr', 'Mai', 'Jun', 'Jul', 'Aug', 'Sep', 'Okt', 'Nov', 'Dez'],
        'datasets': datasets
    }

    return render_template('stats.html', 
                           chart_data=chart_data, 
                           yearly_data=yearly_grp.to_dict('records'),
                           total_kwh=total_kwh,
                           total_cost=total_cost)

if __name__ == '__main__':
    init_files()
    # Läuft auf allen Interfaces (für LXC Zugriff)
    app.run(host='0.0.0.0', debug=True, port=5000)
