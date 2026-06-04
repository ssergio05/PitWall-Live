import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
import glob
import os

# 1. Locate the CSV file
paths = glob.glob("**/session_telemetry.csv", recursive=True)
if not paths: 
    paths = glob.glob("../**/session_telemetry.csv", recursive=True)

if not paths:
    print("❌ Cannot find session_telemetry.csv. Start the C++ receiver first.")
    exit()
    
csv_file = paths[0]
print(f"📡 Connecting to Live F1 Pit Wall... Reading: {os.path.abspath(csv_file)}")

# 2. Window Configuration (Professional Dark Mode)
plt.style.use('dark_background')
fig, (ax1, ax2, ax3, ax4) = plt.subplots(4, 1, figsize=(12, 10), sharex=True)
fig.canvas.manager.set_window_title('Pit Wall Live Telemetry - F1')

# IMPORTANT: Create the secondary axis for gears only once outside the loop
ax2_gear = ax2.twinx()

def update_graph(frame):
    try:
        df = pd.read_csv(csv_file)
        if len(df) < 2: return
        
        # 📌 MAGIA DEL BARRIDO: Filtramos para quedarnos SOLO con los datos de la vuelta actual
        current_lap_number = df['LapNumber'].iloc[-1]
        df = df[df['LapNumber'] == current_lap_number]

        # Limpiamos las gráficas
        ax1.clear()
        ax2.clear()
        ax2_gear.clear()
        ax3.clear()
        ax4.clear()

        # --- PANEL 1: Speed ---
        ax1.plot(df['LapTime'], df['Speed'], color='#00ffff', linewidth=2)
        ax1.set_ylim(0, 360)
        ax1.set_ylabel("Speed (Km/h)", fontsize=10, fontweight='bold')
        ax1.set_title(f"LIVE TELEMETRY - LAP {current_lap_number}", color='white', fontsize=12, loc='left')
        ax1.grid(True, alpha=0.2)

        # --- PANEL 2: RPM and Gear ---
        ax2.plot(df['LapTime'], df['RPM'], color='#ffa500', linewidth=1.5)
        ax2.set_ylim(6000, 12500)
        ax2.set_ylabel("RPM", color='#ffa500', fontsize=10, fontweight='bold')
        
        ax2_gear.step(df['LapTime'], df['Gear'], color='white', linestyle='--', linewidth=1.5)
        ax2_gear.set_ylim(0, 9)
        ax2_gear.set_yticks(range(1, 9))
        ax2_gear.set_ylabel("Gear", color='white', fontsize=10, fontweight='bold')
        ax2.grid(True, alpha=0.2)

        # --- PANEL 3: Pedals ---
        ax3.plot(df['LapTime'], df['Throttle'], color='#00ff00', linewidth=1.5, label='Throttle')
        ax3.plot(df['LapTime'], df['Brake'], color='#ff0000', linewidth=1.5, label='Brake')
        ax3.set_ylim(-0.1, 1.1)
        ax3.set_ylabel("Pedals (0-1)", fontsize=10, fontweight='bold')
        ax3.legend(loc='upper right', facecolor='black', edgecolor='white', fontsize=8)
        ax3.grid(True, alpha=0.2)

        # --- PANEL 4: Steering Angle ---
        ax4.plot(df['LapTime'], df['Steer'], color='#ff00ff', linewidth=1.5)
        ax4.axhline(0, color='gray', linewidth=1, linestyle='--')
        ax4.set_ylim(-100, 100)
        
        # 📌 EJE X FIJO: Siempre de 0 a 90 segundos. No hace scroll, hace "barrido"
        ax4.set_xlim(0, 90)

        ax4.set_ylabel("Steering", fontsize=10, fontweight='bold')
        ax4.set_xlabel("Lap Time (s)", fontsize=10, fontweight='bold')
        ax4.grid(True, alpha=0.2)

        plt.tight_layout()

    except Exception:
        pass

# Animation at 10 frames per second (interval=100ms)
anim = FuncAnimation(fig, update_graph, interval=100, cache_frame_data=False)
plt.show()