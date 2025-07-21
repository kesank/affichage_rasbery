from flask import Flask, render_template, jsonify
import requests
import urllib3
from datetime import datetime
from zoneinfo import ZoneInfo
import threading
import time

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

app = Flask(__name__)

API_KEY = "axCKhkMasBiMD8m6gByt7Y5lUJPS6qmu"
IDFM_URL = "https://prim.iledefrance-mobilites.fr/marketplace/stop-monitoring"
HEADERS = {"apiKey": API_KEY}

ARRETS = [
    {
        "nom": "🚋 T4 - Clichy-Montfermeil (vers Bondy)",
        "MonitoringRef": "STIF:StopPoint:Q:478661:",
        "LineRef": "STIF:Line::C01843:"
    },
    {
        "nom": "🚋 T4 - Clichy-Montfermeil (vers Hôpital)",
        "MonitoringRef": "STIF:StopPoint:Q:478664:",
        "LineRef": "STIF:Line::C01843:"
    },
    {
        "nom": "🚌 Bus 146 - Les Bosquets (Montfermeil)",
        "MonitoringRef": "STIF:StopPoint:Q:427606:",
        "LineRef": "STIF:Line::C01171:"
    }
]

METEO_API_KEY = "4df306d7abb37a6ff68e910b82269d69"
METEO_URL = "https://api.openweathermap.org/data/2.5/weather"
VILLES_METEO = ["La Défense", "Clichy-sous-Bois", "Bobigny", "Paris"]

FOOTBALL_API_KEY = "ce602f8687f443cea2129e15f88c2c23"
FOOTBALL_HEADERS = {"X-Auth-Token": FOOTBALL_API_KEY}
FOOTBALL_URL = "https://api.football-data.org/v4/competitions"
FOOTBALL_LEAGUES = {
    "PL": "Premier League",
    "SA": "Serie A",
    "BL1": "Bundesliga",
    "FL1": "Ligue 1",
    "PD": "Primera Division",
    "DED": "Eredivisie",
    "PPL": "Primeira Liga",
    "BSA": "Campeonato Brasileiro Série A"
}

standings_cache = {}

def kelvin_to_celsius(k):
    return round(k - 273.15, 1)

def format_datetime(dt_str):
    if dt_str:
        dt = datetime.fromisoformat(dt_str.replace("Z", "+00:00")).astimezone(ZoneInfo("Europe/Paris"))
        return dt.strftime("%Hh%M"), dt
    return "inconnu", None

def get_horaires():
    resultat = {"maj": datetime.now(ZoneInfo("Europe/Paris")).strftime("%H:%M:%S"), "arrets": []}

    for arret in ARRETS:
        horaires = []
        params = {
            "MonitoringRef": arret["MonitoringRef"],
            "LineRef": arret["LineRef"]
        }

        try:
            response = requests.get(IDFM_URL, params=params, headers=HEADERS, verify=False)

            if response.status_code == 200:
                data = response.json()
                visits = data.get("Siri", {}).get("ServiceDelivery", {}).get("StopMonitoringDelivery", [])[0].get("MonitoredStopVisit", [])

                for i, visit in enumerate(visits[:5]):
                    journey = visit["MonitoredVehicleJourney"]
                    call = journey["MonitoredCall"]
                    destination = journey.get("DestinationName", [{}])[0].get("value", "inconnu")

                    aimed_time = call.get("AimedDepartureTime")
                    expected_time = call.get("ExpectedDepartureTime")

                    heure_prev, _ = format_datetime(aimed_time)
                    heure_attendu, dt_reel = format_datetime(expected_time)

                    minutes_restantes = int((dt_reel - datetime.now(ZoneInfo("Europe/Paris"))).total_seconds() / 60) if dt_reel else -1

                    horaires.append({
                        "destination": destination,
                        "heure_prev": heure_prev,
                        "heure_attendu": heure_attendu,
                        "minutes_restantes": minutes_restantes,
                        "urgent": minutes_restantes <= 2,
                        "first": i == 0
                    })
            else:
                horaires.append({"erreur": f"Erreur {response.status_code}"})
        except Exception as e:
            horaires.append({"erreur": str(e)})

        resultat["arrets"].append({
            "nom": arret["nom"],
            "horaires": horaires
        })

    return resultat

def get_meteo():
    resultats = {"maj": datetime.now(ZoneInfo("Europe/Paris")).strftime("%H:%M:%S"), "villes": []}

    for ville in VILLES_METEO:
        params = {
            "q": ville,
            "appid": METEO_API_KEY,
            "lang": "fr"
        }

        try:
            response = requests.get(METEO_URL, params=params, verify=False)

            if response.status_code == 200:
                data = response.json()

                temperature = kelvin_to_celsius(data["main"]["temp"])
                feels_like = kelvin_to_celsius(data["main"]["feels_like"])
                description = data["weather"][0]["description"]
                icon = data["weather"][0]["icon"]
                vent = data.get("wind", {}).get("speed", 0)
                humidite = data["main"]["humidity"]

                resultats["villes"].append({
                    "ville": ville,
                    "temperature": temperature,
                    "ressenti": feels_like,
                    "description": description,
                    "icon": f"https://openweathermap.org/img/wn/{icon}@2x.png",
                    "vent": vent,
                    "humidite": humidite
                })
            else:
                resultats["villes"].append({
                    "ville": ville,
                    "erreur": f"Erreur {response.status_code}"
                })
        except Exception as e:
            resultats["villes"].append({
                "ville": ville,
                "erreur": str(e)
            })

    return resultats

def fetch_standings():
    global standings_cache
    while True:
        new_data = {}
        for code, name in FOOTBALL_LEAGUES.items():
            try:
                url = f"{FOOTBALL_URL}/{code}/standings"
                response = requests.get(url, headers=FOOTBALL_HEADERS, verify=False)
                if response.status_code == 200:
                    new_data[code] = response.json()
                else:
                    new_data[code] = {"error": f"Erreur {response.status_code}"}
            except Exception as e:
                new_data[code] = {"error": str(e)}
        standings_cache = new_data
        time.sleep(86400)  # toutes les 24 heures

threading.Thread(target=fetch_standings, daemon=True).start()

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/horaires")
def api_horaires():
    return jsonify(get_horaires())

@app.route("/api/meteo")
def api_meteo():
    return jsonify(get_meteo())

@app.route("/api/football")
def api_football():
    return jsonify(standings_cache)

if __name__ == "__main__":
    app.run(debug=True)
