# ratp_api.py
import requests
import certifi

API_KEY = "axCKhkMasBiMD8m6gByt7Y5lUJPS6qmu"
STOP_POINT_ID = "STIF:StopPoint:Q:463495"  # Clichy-Montfermeil T4 (ID corrigé)
LINE_REF = "STIF:Line::C01389"            # Ligne T4

def get_schedules():
    url = "https://prim.iledefrance-mobilites.fr/marketplace/stop-monitoring"
    headers = {"apikey": API_KEY, "Accept": "application/json"}
    params = {
        "MonitoringRef": STOP_POINT_ID,
        "LineRef": LINE_REF
    }
    
    # Utilisation du certificat SSL via certifi
    response = requests.get(url, headers=headers, params=params, verify=certifi.where())
    response.raise_for_status()
    
    return response.json()

if __name__ == "__main__":
    horaires = get_schedules()
    print("Prochains passages T4 à Clichy-Montfermeil :", horaires)
