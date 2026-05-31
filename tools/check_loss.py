import pandas as pd

def check_packet_loss(filename):
    df = pd.read_csv(filename)

    df['delta'] = df['Time'].diff()
    

    threshold = 0.03
    losses = df[df['delta'] > threshold]
    
    if losses.empty:
        print("✅ ¡Perfecto! No se detectan saltos en el tiempo de la sesión.")
    else:
        print(f"❌ Se han detectado {len(losses)} posibles pérdidas de datos.")
        print(losses[['Time', 'delta']])

check_packet_loss('session_telemetry.csv')