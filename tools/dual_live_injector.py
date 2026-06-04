import sys
import fastf1
import pandas as pd
import time
import os
import logging

script_dir = os.path.dirname(os.path.abspath(__file__))
cache_dir = os.path.join(script_dir, '..', 'fastf1_cache')
if not os.path.exists(cache_dir): os.makedirs(cache_dir)
fastf1.Cache.enable_cache(cache_dir)
fastf1.logger.set_log_level(logging.ERROR)

csv_file = os.path.join(script_dir, '..', 'live_telemetry.csv')

# 📌 NUEVO: Recibimos las órdenes directas desde el Pit Wall OS
year = int(sys.argv[1]) if len(sys.argv) > 1 else 2024
track = sys.argv[2] if len(sys.argv) > 2 else 'Bahrain'
session_type = sys.argv[3] if len(sys.argv) > 3 else 'Q'
driver1 = sys.argv[4] if len(sys.argv) > 4 else 'VER'
driver2 = sys.argv[5] if len(sys.argv) > 5 else 'PIA'

print(f"📡 CONECTANDO CON LA FIA: {track} {year} ({session_type})")
session = fastf1.get_session(year, track, session_type)
session.load(telemetry=True, weather=False, messages=False)

print(f"🏎️ Extrayendo telemetría de {driver1} y {driver2}...")

def get_driver_telemetry(driver_name):
    try:
        laps = session.laps.pick_driver(driver_name)
        df_list = []
        for index, lap in laps.iterlaps():
            try:
                tel = lap.get_telemetry().add_distance()
                tel = tel[['SessionTime', 'Distance', 'Speed', 'Throttle', 'Brake']]
                tel['Driver'] = driver_name
                tel['LapNumber'] = lap['LapNumber']
                df_list.append(tel)
            except:
                pass 
        if df_list:
            return pd.concat(df_list)
    except Exception as e:
        print(f"Error con {driver_name}: {e}")
    return pd.DataFrame()

tel_d1 = get_driver_telemetry(driver1)
tel_d2 = get_driver_telemetry(driver2)

all_tel = pd.concat([tel_d1, tel_d2]).sort_values(by='SessionTime')

with open(csv_file, 'w') as f:
    f.write("Driver,LapNumber,Distance,Speed,Throttle,Brake\n")

print(f"▶️ EMITIENDO EN DIRECTO: {driver1} vs {driver2}")

prev_time = None
for _, row in all_tel.iterrows():
    with open(csv_file, 'a') as f:
        f.write(f"{row['Driver']},{row['LapNumber']},{row['Distance']},{row['Speed']},{row['Throttle']},{row['Brake']}\n")
    
    curr_time = row['SessionTime'].total_seconds()
    if prev_time is not None:
        delta = curr_time - prev_time
        if delta > 0:
            time.sleep(min(delta, 1.0)) 
    prev_time = curr_time