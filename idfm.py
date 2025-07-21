import requests
import urllib3
from datetime import datetime
from zoneinfo import ZoneInfo
import tkinter as tk
from tkinter import scrolledtext

# Ne pas afficher les avertissements SSL
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Clé API et URL IDFM
api_key = "axCKhkMasBiMD8m6gByt7Y5lUJPS6qmu"
url = "https://prim.iledefrance-mobilites.fr/marketplace/stop-monitoring"

# Liste des arrêts à surveiller
arrets = [
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

headers = {"apiKey": api_key}

# Initialisation de l'application Tkinter
root = tk.Tk()
root.title("🕒 Horaires IDFM - Clichy Montfermeil")
root.config(bg="#f0f0f0")

# Zone de texte défilante
text_area = scrolledtext.ScrolledText(root, width=80, height=25, wrap=tk.WORD,
                                      font=("Helvetica", 11), bg="#ffffff", fg="#333333", bd=2, relief="solid")
text_area.pack(padx=20, pady=10)

# Définition des tags pour le style
text_area.tag_configure("t4", foreground="#FF9933", font=("Helvetica", 13, "bold"))
text_area.tag_configure("bus146", foreground="#9370DB", font=("Helvetica", 13, "bold"))
text_area.tag_configure("texte", font=("Helvetica", 10))
text_area.tag_configure("maj", foreground="gray", font=("Helvetica", 10, "italic"))
text_area.tag_configure("urgent", foreground="red", font=("Helvetica", 10, "bold"))
text_area.tag_configure("centered", justify="center")

# Fonction pour formater la date et heure
def format_datetime(dt_str):
    if dt_str:
        dt = datetime.fromisoformat(dt_str.replace("Z", "+00:00")).astimezone(ZoneInfo("Europe/Paris"))
        return dt.strftime("%Hh%M"), dt
    return "inconnu", None

# Fonction pour faire clignoter le texte
def clignoter_tag(tag, index, color1, color2):
    # Change de couleur toutes les 800ms
    current_color = text_area.tag_cget(tag, "foreground")
    new_color = color1 if current_color == color2 else color2
    text_area.tag_configure(tag, foreground=new_color)
    text_area.after(800, clignoter_tag, tag, index, color1, color2)

# Fonction pour afficher les horaires
def afficher_horaires():
    text_area.configure(state='normal')
    text_area.delete("1.0", tk.END)

    # Afficher la mise à jour
    maj = f"Dernière mise à jour : {datetime.now().strftime('%H:%M:%S')}\n\n"
    text_area.insert(tk.END, maj, ("maj", "centered"))

    for arret in arrets:
        nom_arret = arret["nom"]
        monitoring_ref = arret["MonitoringRef"]
        line_ref = arret["LineRef"]

        # Identifier le tag en fonction du nom de l'arrêt
        if "T4" in nom_arret:
            tag = "t4"
        elif "146" in nom_arret:
            tag = "bus146"
        else:
            tag = "texte"

        # Afficher le nom de l'arrêt
        text_area.insert(tk.END, f"{nom_arret}\n", (tag, "centered"))

        params = {
            "MonitoringRef": monitoring_ref,
            "LineRef": line_ref
        }

        try:
            response = requests.get(url, params=params, headers=headers, verify=False)

            if response.status_code == 200:
                data = response.json()
                visits = data.get("Siri", {}).get("ServiceDelivery", {}).get("StopMonitoringDelivery", [])[0].get("MonitoredStopVisit", [])

                if not visits:
                    text_area.insert(tk.END, "Aucun passage prochainement.\n\n", ("texte", "centered"))
                    continue

                for i, visit in enumerate(visits[:5]):
                    journey = visit["MonitoredVehicleJourney"]
                    call = journey["MonitoredCall"]
                    destination = journey.get("DestinationName", [{}])[0].get("value", "inconnu")

                    aimed_time = call.get("AimedDepartureTime")
                    expected_time = call.get("ExpectedDepartureTime")

                    heure_prev, dt_expected = format_datetime(aimed_time)
                    heure_attendu, dt_reel = format_datetime(expected_time)

                    if dt_reel:
                        minutes_restantes = int((dt_reel - datetime.now(ZoneInfo("Europe/Paris"))).total_seconds() / 60)
                        urgence = minutes_restantes <= 2
                        ligne = f"→ Vers {destination} | Prévu : {heure_prev} | Attendu : {heure_attendu} | ⏱ {minutes_restantes} min\n"

                        # Afficher la première ligne avec clignotement si moins de 2 minutes
                        if i == 0 and urgence:
                            text_area.insert(tk.END, ligne, ("urgent", "centered"))
                            # Faire clignoter le texte
                            clignoter_tag("urgent", i, "red", "white")
                        else:
                            text_area.insert(tk.END, ligne, ("texte", "centered"))

                text_area.insert(tk.END, "\n")

            else:
                erreur = f"❌ Erreur {response.status_code} : {response.text}\n\n"
                text_area.insert(tk.END, erreur, ("texte", "centered"))

        except Exception as e:
            text_area.insert(tk.END, f"Erreur : {e}\n\n", ("texte", "centered"))

    text_area.configure(state='disabled')

    # Replanifier la mise à jour dans 30 secondes
    root.after(30000, afficher_horaires)

# Bouton d’actualisation manuel
btn = tk.Button(root, text="🔄 Actualiser les horaires", command=afficher_horaires,
                bg="#4CAF50", fg="white", relief="flat", padx=10, pady=5, font=("Helvetica", 10, "bold"))
btn.pack(pady=5)

# Lancement initial
afficher_horaires()
root.mainloop()
