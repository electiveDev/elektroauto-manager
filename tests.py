import unittest
import os
import pandas as pd
from app import app, init_csv, CSV_FILE

class EVAppTestCase(unittest.TestCase):

    def setUp(self):
        """Vor jedem Test: Saubere Umgebung schaffen."""
        self.app = app.test_client()
        self.app.testing = True
        # Nutze eine Test-CSV
        self.test_csv = 'test_data.csv'
        # Überschreibe den Dateinamen im app Modul temporär (Monkey Patching)
        import app as app_module
        app_module.CSV_FILE = self.test_csv
        if os.path.exists(self.test_csv):
            os.remove(self.test_csv)
        app_module.init_csv()

    def tearDown(self):
        """Nach jedem Test: Aufräumen."""
        if os.path.exists(self.test_csv):
            os.remove(self.test_csv)

    def test_csv_creation(self):
        """Prüft, ob die CSV automatisch erstellt wird."""
        self.assertTrue(os.path.exists(self.test_csv))

    def test_add_entry(self):
        """Prüft das Hinzufügen eines Eintrags."""
        response = self.app.post('/', data={
            'vehicle_id': 'TestCar',
            'date': '2023-01-01',
            'meter_reading': '100',
            'price': '0.30'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        
        df = pd.read_csv(self.test_csv)
        self.assertEqual(len(df), 1)
        self.assertEqual(df.iloc[0]['vehicle_id'], 'TestCar')

    def test_calculation_logic(self):
        """Prüft die Verbrauchsbrechnung über mehrere Einträge."""
        # 1. Eintrag (Baseline)
        self.app.post('/', data={'vehicle_id': 'CarA', 'date': '2023-01-01', 'meter_reading': '1000', 'price': '0.30'})
        # 2. Eintrag (100 kWh Verbrauch)
        self.app.post('/', data={'vehicle_id': 'CarA', 'date': '2023-01-08', 'meter_reading': '1100', 'price': '0.30'})
        
        # Manuelle Prüfung der Logik via get_data (muss importiert oder simuliert werden)
        # Hier nutzen wir direkt Pandas zur Verifikation der gespeicherten Daten
        # Die eigentliche Logik steckt in get_data(), rufen wir diese im Kontext auf:
        import app as app_module
        data = app_module.get_data()
        
        # Sortieren um sicherzugehen, dass Eintrag 2 der letzte ist
        data.sort(key=lambda x: x['date'])
        
        entry1 = data[0]
        entry2 = data[1]

        self.assertEqual(entry1['consumption_kwh'], 0.0, "Erster Eintrag sollte 0 Verbrauch haben")
        self.assertEqual(entry2['consumption_kwh'], 100.0, "Zweiter Eintrag sollte 100 Verbrauch haben")
        self.assertEqual(entry2['cost_eur'], 30.0, "Kosten sollten 30 EUR sein")

if __name__ == '__main__':
    unittest.main()