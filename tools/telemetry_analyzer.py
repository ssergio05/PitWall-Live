import pandas as pd
import matplotlib.pyplot as plt
import os
import glob

def analyze_telemetry():
    print("🔍 Searching for telemetry data...")
    found_files = glob.glob("**/session_telemetry.csv", recursive=True)
    
    if not found_files:
        print("❌ ERROR: 'session_telemetry.csv' not found.")
        return

    file_path = found_files[0]
    print(f"✅ File found!: {os.path.abspath(file_path)}")

    try:
        # Read the file. C++ already provides the correct header.
        df = pd.read_csv(file_path)

        if df.empty or len(df) < 5:
            print("⚠️ The file is empty or has very little data. Do a few more laps!")
            return

        # --- DRAW 4 PLOTS ---
        # Increase window size and create 4 axes
        fig, (ax1, ax2, ax3, ax4) = plt.subplots(4, 1, figsize=(12, 12), sharex=True)
        
        # 1. Speed
        ax1.plot(df['SessionTime'], df['Speed'], color='blue', linewidth=2, label='Speed (km/h)')
        ax1.set_title("Advanced F1 Telemetry Analysis", fontsize=14, fontweight='bold')
        ax1.set_ylabel("Km/h")
        ax1.legend(loc="upper right")
        ax1.grid(True, alpha=0.3)

        # 2. RPM and Gears
        ax2.plot(df['SessionTime'], df['RPM'], color='orange', label='RPM')
        ax2.set_ylabel("Revolutions")
        ax2.legend(loc="upper left")
        ax2.grid(True, alpha=0.3)
        
        # Secondary Y axis for gears
        ax2_gear = ax2.twinx()
        ax2_gear.step(df['SessionTime'], df['Gear'], color='black', linestyle='--', label='Gear')
        ax2_gear.set_ylabel("Gear (1-8)")
        ax2_gear.set_yticks(range(1, 9))
        ax2_gear.legend(loc="upper right")

        # 3. Pedals
        ax3.plot(df['SessionTime'], df['Throttle'], color='green', label='Throttle')
        ax3.plot(df['SessionTime'], df['Brake'], color='red', label='Brake')
        ax3.set_ylabel("Input (0-1)")
        ax3.legend(loc="upper right")
        ax3.grid(True, alpha=0.3)

        # 4. Steering
        ax4.plot(df['SessionTime'], df['Steer'], color='purple', label='Steering Angle')
        ax4.axhline(0, color='black', linewidth=1) 
        ax4.set_ylabel("Angle (-100 to 100)")
        ax4.set_xlabel("Time (s)")
        ax4.legend(loc="upper right")
        ax4.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.show()

    except Exception as e:
        print(f"❌ Failed to read the file: {e}")

if __name__ == "__main__":
    analyze_telemetry()