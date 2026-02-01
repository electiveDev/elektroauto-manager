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
    """Initialisiert CSV und Settings Datei."""
    if not os.path.exists(CSV_FILE):
        pd.DataFrame(columns=COLUMNS).to_csv(CSV_FILE, index=False)
    
    if not os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, 'w') as f:
            json.dump({'default_vehicle': ''}, f)

def get_settings():
    """Lädt die Einstellungen."""
    with open(SETTINGS_FILE, 'r') as f:
        return json.load(f)

def save_settings(settings):
    """Speichert die Einstellungen."""
    with open(SETTINGS_FILE, 'w') as f:
        json.dump(settings, f)

def get_data():
    """Lädt und berechnet Verbrauchsdaten."""
    try:
        df = pd.read_csv(CSV_FILE)
    except pd.errors.EmptyDataError:
        return []

    if df.empty:
        return []

    df['date'] = pd.to_datetime(df['date'])
    df['meter_reading'] = pd.to_numeric(df['meter_reading'])
    df['price_per_kwh'] = pd.to_numeric(df['price_per_kwh'])

    df = df.sort_values(by=['vehicle_id', 'date'])
    df['prev_meter'] = df.groupby('vehicle_id')['meter_reading'].shift(1)
    df['consumption_kwh'] = df['meter_reading'] - df['prev_meter']
    df['consumption_kwh'] = df['consumption_kwh'].fillna(0)
    df['cost_eur'] = df['consumption_kwh'] * df['price_per_kwh']

    return df

# --- Routen ---

@app.route('/', methods=['GET', 'POST'])
def index():
    init_files()
    settings = get_settings()
    
    # Datum von heute vor-ausfüllen (Format YYYY-MM-DD für HTML Input)
    today_str = datetime.today().strftime('%Y-%m-%d')
    default_vehicle = settings.get('default_vehicle', '')

    if request.method == 'POST':
        vehicle_id = request.form.get('vehicle_id').strip()
        date_str = request.form.get('date')
        meter_reading = float(request.form.get('meter_reading'))
        price = float(request.form.get('price'))

        new_entry = {
            'id': str(uuid.uuid4()),
            'vehicle_id': vehicle_id,
            'date': date_str,
            'meter_reading': meter_reading,
            'price_per_kwh': price
        }
        
        # DataFrame Append workaround für Pandas 2.0+
        df_new = pd.DataFrame([new_entry])
        df_new.to_csv(CSV_FILE, mode='a', header=not os.path.exists(CSV_FILE), index=False)
        
        flash("Gespeichert.", "success")
        return redirect(url_for('index'))

    df = get_data()
    entries = df.to_dict('records') if not isinstance(df, list) else []
    # Neueste zuerst
    entries.sort(key=lambda x: (x['vehicle_id'], x['date']), reverse=True)
    
    return render_template('index.html', entries=entries, today=today_str, default_vehicle=default_vehicle)

@app.route('/settings', methods=['POST'])
def update_settings():
    """Route zum Speichern des Standard-Fahrzeugs."""
    vehicle = request.form.get('default_vehicle').strip()
    save_settings({'default_vehicle': vehicle})
    flash("Standard-Fahrzeug aktualisiert.", "success")
    return redirect(url_for('index'))

@app.route('/delete/<entry_id>')
def delete(entry_id):
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

    # -- 1. Jahresübersicht (Verbrauch) --
    # Wir gruppieren nach Jahr
    df['year'] = df['date'].dt.year
    df['month'] = df['date'].dt.strftime('%Y-%m') # Zum Sortieren
    
    yearly_grp = df.groupby('year')[['consumption_kwh', 'cost_eur']].sum().reset_index()
    
    # -- 2. Monatsvergleich (Jahr vs Jahr) --
    # Wir erstellen eine Pivot-Tabelle: Zeilen=Monat(1-12), Spalten=Jahr, Werte=Verbrauch
    df['month_num'] = df['date'].dt.month
    pivot_kwh = df.pivot_table(index='month_num', columns='year', values='consumption_kwh', aggfunc='sum', fill_value=0)
    
    # Daten für Chart.js aufbereiten
    years = sorted(df['year'].unique())
    datasets = []
    
    # Farben für die Linien (einfache Rotation)
    colors = ['#00d4ff', '#ff4d4d', '#00b894', '#fdcb6e']
    
    for i, year in enumerate(years):
        if year in pivot_kwh.columns:
            datasets.append({
                'label': str(year),
                'data': pivot_kwh[year].tolist(),
                'borderColor': colors[i % len(colors)],
                'fill': False
            })

    chart_data = {
        'labels': ['Jan', 'Feb', 'Mär', 'Apr', 'Mai', 'Jun', 'Jul', 'Aug', 'Sep', 'Okt', 'Nov', 'Dez'],
        'datasets': datasets
    }
    
    # Summen für KPI Kacheln
    total_kwh = df['consumption_kwh'].sum()
    total_cost = df['cost_eur'].sum()

    return render_template('stats.html', 
                           chart_data=chart_data, 
                           yearly_data=yearly_grp.to_dict('records'),
                           total_kwh=total_kwh,
                           total_cost=total_cost)

if __name__ == '__main__':
    init_files()
    app.run(host='0.0.0.0', debug=True, port=5000)
