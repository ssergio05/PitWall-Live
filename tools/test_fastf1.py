import fastf1
import os

# 1. Configurar la caché (¡MUY IMPORTANTE!)
# FastF1 descarga muchos megas de datos. La caché evita que la API te bloquee por descargar lo mismo varias veces.
cache_dir = '../fastf1_cache'
if not os.path.exists(cache_dir):
    os.makedirs(cache_dir)
fastf1.Cache.enable_cache(cache_dir)

print("📡 Conectando con los servidores de la FIA...")

# 2. Cargar una sesión histórica (Año 2024, Gran Premio de Bahréin, Clasificación 'Q')
session = fastf1.get_session(2024, 'Bahrain', 'Q')
session.load()

# 3. Elegir un piloto (VER = Verstappen, PIA = Piastri, ALO = Alonso)
piloto = 'PIA'
print(f"\n🏎️ Buscando la vuelta más rápida de {piloto}...")
lap = session.laps.pick_driver(piloto).pick_fastest()

# 4. Extraer la telemetría cruda de esa vuelta
telemetry = lap.get_telemetry()

# 5. Mostrar la estructura de los datos
print("\n📊 ¡Datos recibidos! Aquí tienes las primeras 5 filas:")
print(telemetry[['Time', 'Speed', 'RPM', 'nGear', 'Throttle', 'Brake']].head())

print("\n📋 Columnas disponibles en la API de la F1:")
print(telemetry.columns.tolist())