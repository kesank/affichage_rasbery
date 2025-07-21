import tkinter as tk
import requests
from datetime import datetime
from dateutil import parser

# --- Chemin du certificat téléchargé ---
CERT_PATH = r"C:\Users\kelly.nkanabalomok\Downloads\certificat_idfm.pem"

# --- Identifiants API vérifiés dans le CSV ---
API_KEY = "axCKhkMasBiMD8m6gByt7Y5lUJPS6qmu"
STOP_POINT_ID = "STIF:StopPoint:Q:463495"  # Clichy-Montfermeil (T4)
LINE_REF = "STIF:Line::C01389:"           # Avec ":" final comme dans le CSV

def fetch_next_passages():
    url = "https://prim.iledefrance-mobilites.fr/marketplace/stop-monitoring"
    headers = {"apikey": API_KEY, "Accept": "application/json"}
    params = {"MonitoringRef": STOP_POINT_ID, "LineRef": LINE_REF}
    
    try:
        # Utilisation explicite du certificat téléchargé
        response = requests.get(
            url,
            headers=headers,
            params=params,
            verify=CERT_PATH,  # <-- Chemin du certificat IDFM
            timeout=10
        )
        response.raise_for_status()
        return parse_schedules(response.json())
    except Exception as e:
        return [f"Erreur : {str(e)}"]

def parse_schedules(data):
    try:
        visits = data['Siri']['ServiceDelivery']['StopMonitoringDelivery'][0]['MonitoredStopVisit']
        horaires = []
        now = datetime.now().astimezone()
        
        for visit in visits[:5]:  # 5 prochains passages
            dest = visit['MonitoredVehicleJourney']['DestinationName'][0]['value']
            expected = visit['MonitoredVehicleJourney']['MonitoredCall']['ExpectedArrivalTime']
            heure = parser.isoparse(expected).astimezone()
            minutes = int((heure - now).total_seconds() // 60)
            horaires.append(f"{heure.strftime('%H:%M')} ({minutes} min) → {dest}")
            
        return horaires if horaires else ["Aucun passage"]
    except KeyError:
        return ["Format de réponse inattendu"]

class HorairesApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Prochains T4 - Clichy-Montfermeil")
        self.geometry("600x400")
        self.configure(bg="#222")
        
        self.label_title = tk.Label(self, 
            text="T4 - Clichy-Montfermeil", 
            font=("Arial", 22, "bold"), 
            fg="#FFF", 
            bg="#222"
        )
        self.label_title.pack(pady=20)
        
        self.horaires_labels = [
            tk.Label(self, text="", font=("Arial", 18), fg="#FFF", bg="#222") 
            for _ in range(5)
        ]
        
        for lbl in self.horaires_labels:
            lbl.pack(pady=5)
            
        self.refresh()
    
    def refresh(self):
        try:
            horaires = fetch_next_passages()
            for i, lbl in enumerate(self.horaires_labels):
                lbl.config(text=horaires[i] if i < len(horaires) else "")
        except Exception as e:
            print(f"Erreur rafraîchissement : {e}")
        finally:
            self.after(30000, self.refresh)  # Rafraîchit toutes les 30s

if __name__ == "__main__":
    app = HorairesApp()
    app.mainloop()
