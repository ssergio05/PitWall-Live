import fastf1
import time
import pandas as pd
import os
import logging

# 1. Configurar caché de forma robusta
# Calculamos la ruta a la carpeta principal (un nivel por encima de 'tools')
script_dir = os.path.dirname(os.path.abspath(__file__))
cache_dir = os.path.join(script_dir, '..', 'fastf1_cache')

# Si la carpeta no existe, le decimos a Python que la cree
if not os.path.exists(cache_dir):
    os.makedirs(cache_dir)

fastf1.Cache.enable_cache(cache_dir)
fastf1.logger.set_log_level(logging.ERROR)

print("📡 Descargando datos de la FIA (Bahrein 2024 - Q)...")
session = fastf1.get_session(2024, 'Bahrain', 'Q')
session.load(telemetry=True, weather=False, messages=False)

# Coger TODAS las vueltas válidas de Piastri (quitando vueltas de salida/entrada a boxes)
laps = session.laps.pick_driver('PIA').pick_accurate()

csv_file = "session_telemetry.csv"
print(f"📝 Creando archivo de enlace en: {os.path.abspath(csv_file)}")

with open(csv_file, "w") as f:
    # 📌 NUEVO: Añadimos 'LapNumber' para saber cuándo limpiar la pantalla
    f.write("LapTime,Speed,RPM,Gear,Throttle,Brake,Steer,LapNumber\n")

print("🏁 ¡Iniciando Replay de Stint en Tiempo Real!")

for _, lap in laps.iterlaps():
    print(f"🏎️ Iniciando Vuelta {lap['LapNumber']} - Tiempo: {lap['LapTime']}")
    telemetry = lap.get_telemetry()
    
    # El tiempo ahora es relativo al inicio de ESTA vuelta
    telemetry['LapTime'] = telemetry['Time'].dt.total_seconds() - telemetry['Time'].dt.total_seconds().iloc[0]
    
    previous_time = 0.0
    
    for index, row in telemetry.iterrows():
        current_time = row['LapTime']
        
        time_to_wait = current_time - previous_time
        if time_to_wait > 0:
            time.sleep(time_to_wait)
            
        previous_time = current_time
        
        speed = row['Speed']
        rpm = row['RPM']
        gear = row['nGear']
        throttle = row['Throttle'] / 100.0
        brake = 1.0 if row['Brake'] else 0.0
        steer = 0.0 
        
        with open(csv_file, "a") as f:
            f.write(f"{current_time:.3f},{speed},{rpm},{gear},{throttle:.2f},{brake:.1f},{steer:.2f},{lap['LapNumber']}\n")

print("🛑 Replay terminado.")