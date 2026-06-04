import customtkinter as ctk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import fastf1
import fastf1.plotting
import os
import logging

# 1. Configuración de Caché
script_dir = os.path.dirname(os.path.abspath(__file__))
cache_dir = os.path.join(script_dir, '..', 'fastf1_cache')
if not os.path.exists(cache_dir):
    os.makedirs(cache_dir)
fastf1.Cache.enable_cache(cache_dir)
fastf1.logger.set_log_level(logging.ERROR)

# 2. Configuración visual
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")
fastf1.plotting.setup_mpl(mpl_timedelta_support=False, misc_mpl_mods=False, color_scheme='fastf1')

# 3. Lista completa de circuitos del calendario
TRACKS = [
    "Bahrain", "Saudi Arabia", "Australia", "Japan", "China", "Miami",
    "Imola", "Monaco", "Canada", "Spain", "Austria", "Silverstone",
    "Hungary", "Spa", "Zandvoort", "Monza", "Baku", "Singapore",
    "Austin", "Mexico", "Interlagos", "Las Vegas", "Qatar", "Abu Dhabi"
]

class TelemetryAnalyzerPro(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Pit Wall - Análisis Comparativo Avanzado")
        self.geometry("1350x850")
        self.minsize(1100, 800)

        self.session = None # Aquí guardaremos los datos descargados

        # --- GRID LAYOUT ---
        self.grid_columnconfigure(1, weight=1) 
        self.grid_rowconfigure(0, weight=1)

        # ==========================================
        # 🎛️ PANEL LATERAL (CONTROLES)
        # ==========================================
        self.sidebar = ctk.CTkFrame(self, width=300, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_rowconfigure(13, weight=1) 

        self.logo_label = ctk.CTkLabel(self.sidebar, text="PIT WALL\nANALYZER", font=ctk.CTkFont(size=22, weight="bold"))
        self.logo_label.grid(row=0, column=0, padx=20, pady=(20, 20))

        # Año, Circuito y Sesión
        self.frame_config = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        self.frame_config.grid(row=1, column=0, padx=20, pady=0, sticky="ew")
        
        self.combo_year = ctk.CTkComboBox(self.frame_config, values=["2024", "2023", "2022"], width=70)
        self.combo_year.grid(row=0, column=0, padx=(0, 5), sticky="w")
        
        self.combo_session = ctk.CTkComboBox(self.frame_config, values=["FP1", "FP2", "FP3", "Q", "S", "SQ", "R"], width=70)
        self.combo_session.grid(row=0, column=1, padx=(5, 0), sticky="e")

        self.combo_track = ctk.CTkComboBox(self.sidebar, values=TRACKS)
        self.combo_track.grid(row=2, column=0, padx=20, pady=(10, 15), sticky="ew")

        # Botón Fase 1: Cargar Sesión
        self.btn_load = ctk.CTkButton(self.sidebar, text="1. Cargar Sesión", command=self.load_session, fg_color="#d46b08", hover_color="#ad5604")
        self.btn_load.grid(row=3, column=0, padx=20, pady=(0, 20), sticky="ew")

        # Separador visual
        self.separator = ctk.CTkFrame(self.sidebar, height=2, fg_color="gray30")
        self.separator.grid(row=4, column=0, padx=20, pady=(0, 20), sticky="ew")

        # Piloto 1 + Selector de Vuelta (Desactivados hasta cargar sesión)
        self.label_drivers = ctk.CTkLabel(self.sidebar, text="Piloto 1 / Vuelta:")
        self.label_drivers.grid(row=5, column=0, padx=20, pady=(0, 0), sticky="w")
        
        self.frame_d1 = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        self.frame_d1.grid(row=6, column=0, padx=20, pady=(0, 15), sticky="ew")
        self.frame_d1.grid_columnconfigure(0, weight=1)
        self.frame_d1.grid_columnconfigure(1, weight=1)

        # 📌 MAGIA: El 'command' hace que al cambiar de piloto, se actualicen sus vueltas
        self.combo_p1 = ctk.CTkComboBox(self.frame_d1, values=["-"], width=90, state="disabled", command=self.update_laps_p1)
        self.combo_p1.grid(row=0, column=0, padx=(0, 5), sticky="ew")
        
        self.combo_lap_p1 = ctk.CTkComboBox(self.frame_d1, values=["-"], width=90, state="disabled")
        self.combo_lap_p1.grid(row=0, column=1, padx=(5, 0), sticky="ew")

        # Piloto 2 + Selector de Vuelta (Desactivados hasta cargar sesión)
        self.label_drivers2 = ctk.CTkLabel(self.sidebar, text="Piloto 2 / Vuelta:")
        self.label_drivers2.grid(row=7, column=0, padx=20, pady=(0, 0), sticky="w")

        self.frame_d2 = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        self.frame_d2.grid(row=8, column=0, padx=20, pady=(0, 20), sticky="ew")
        self.frame_d2.grid_columnconfigure(0, weight=1)
        self.frame_d2.grid_columnconfigure(1, weight=1)

        self.combo_p2 = ctk.CTkComboBox(self.frame_d2, values=["-"], width=90, state="disabled", command=self.update_laps_p2)
        self.combo_p2.grid(row=0, column=0, padx=(0, 5), sticky="ew")

        self.combo_lap_p2 = ctk.CTkComboBox(self.frame_d2, values=["-"], width=90, state="disabled")
        self.combo_lap_p2.grid(row=0, column=1, padx=(5, 0), sticky="ew")

        # Botón Fase 2: Comparar
        self.btn_analyze = ctk.CTkButton(self.sidebar, text="2. Dibujar Telemetría", command=self.run_analysis, height=40, state="disabled")
        self.btn_analyze.grid(row=9, column=0, padx=20, pady=20, sticky="ew")

        # ==========================================
        # 📈 PANEL CENTRAL (GRÁFICOS)
        # ==========================================
        self.plot_frame = ctk.CTkFrame(self, corner_radius=10)
        self.plot_frame.grid(row=0, column=1, padx=20, pady=20, sticky="nsew")
        
        self.status_label = ctk.CTkLabel(self.plot_frame, text="Paso 1: Elige circuito y pulsa 'Cargar Sesión'", font=ctk.CTkFont(size=16))
        self.status_label.pack(expand=True)

        self.canvas = None

    def load_session(self):
        year = int(self.combo_year.get())
        track = self.combo_track.get()
        session_type = self.combo_session.get()

        self.status_label.configure(text=f"⏳ Descargando base de datos de {track} {year}...\n(Esto puede tardar unos segundos)", text_color="#ffa500")
        self.update()

        try:
            # Descargamos los datos pesados una sola vez
            self.session = fastf1.get_session(year, track, session_type)
            self.session.load(telemetry=True, weather=False, messages=False)

            # Extraemos los nombres de los pilotos que corrieron
            driver_abbrs = []
            for drv_num in self.session.drivers:
                drv_info = self.session.get_driver(drv_num)
                driver_abbrs.append(drv_info['Abbreviation'])

            # Activamos y rellenamos los menús de pilotos
            self.combo_p1.configure(state="normal", values=driver_abbrs)
            self.combo_p2.configure(state="normal", values=driver_abbrs)
            
            # Ponemos por defecto a los dos primeros
            if len(driver_abbrs) >= 2:
                self.combo_p1.set(driver_abbrs[0])
                self.combo_p2.set(driver_abbrs[1])
            
            self.combo_lap_p1.configure(state="normal")
            self.combo_lap_p2.configure(state="normal")

            # Actualizamos las vueltas disponibles para los pilotos por defecto
            self.update_laps_p1(self.combo_p1.get())
            self.update_laps_p2(self.combo_p2.get())

            # Activamos el botón de dibujar
            self.btn_analyze.configure(state="normal")
            self.status_label.configure(text="✅ Sesión cargada.\nPaso 2: Elige pilotos, vueltas y pulsa 'Dibujar Telemetría'", text_color="#00ff00")

        except Exception as e:
            self.status_label.configure(text=f"❌ Error al cargar sesión:\n{str(e)}", text_color="red")

    def update_laps_p1(self, choice):
        if not self.session: return
        try:
            laps = self.session.laps.pick_driver(choice)
            lap_nums = [str(int(l)) for l in laps['LapNumber'].unique()]
            self.combo_lap_p1.configure(values=["Fastest"] + lap_nums)
            self.combo_lap_p1.set("Fastest")
        except:
            pass

    def update_laps_p2(self, choice):
        if not self.session: return
        try:
            laps = self.session.laps.pick_driver(choice)
            lap_nums = [str(int(l)) for l in laps['LapNumber'].unique()]
            self.combo_lap_p2.configure(values=["Fastest"] + lap_nums)
            self.combo_lap_p2.set("Fastest")
        except:
            pass

    def run_analysis(self):
        d1 = self.combo_p1.get()
        d2 = self.combo_p2.get()
        lap_p1_sel = self.combo_lap_p1.get()
        lap_p2_sel = self.combo_lap_p2.get()

        try:
            laps_d1 = self.session.laps.pick_driver(d1)
            if lap_p1_sel == "Fastest":
                lap_d1 = laps_d1.pick_fastest()
            else:
                lap_d1 = laps_d1[laps_d1['LapNumber'] == int(lap_p1_sel)].iloc[0]

            laps_d2 = self.session.laps.pick_driver(d2)
            if lap_p2_sel == "Fastest":
                lap_d2 = laps_d2.pick_fastest()
            else:
                lap_d2 = laps_d2[laps_d2['LapNumber'] == int(lap_p2_sel)].iloc[0]

            tel_d1 = lap_d1.get_telemetry().add_distance()
            tel_d2 = lap_d2.get_telemetry().add_distance()

            try: color_d1 = fastf1.plotting.get_team_color(lap_d1['Team'], session=self.session)
            except: color_d1 = 'white'
                
            try: color_d2 = fastf1.plotting.get_team_color(lap_d2['Team'], session=self.session)
            except: color_d2 = 'gray'

            if self.canvas:
                self.canvas.get_tk_widget().destroy()
            self.status_label.pack_forget()

            plt.style.use('dark_background')
            fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(12, 8), sharex=True)
            fig.subplots_adjust(left=0.06, right=0.97, top=0.95, bottom=0.06, hspace=0.15)
            fig.patch.set_facecolor('#2b2b2b') 

            for ax in (ax1, ax2, ax3):
                ax.set_facecolor('#1e1e1e')
                ax.grid(True, alpha=0.2)

            # --- Velocidad ---
            label_d1 = f"{d1} (V.{int(lap_d1['LapNumber'])}: {lap_d1['LapTime'].total_seconds():.3f}s)"
            label_d2 = f"{d2} (V.{int(lap_d2['LapNumber'])}: {lap_d2['LapTime'].total_seconds():.3f}s)"

            ax1.plot(tel_d1['Distance'], tel_d1['Speed'], color=color_d1, label=label_d1, linewidth=1.5)
            ax1.plot(tel_d2['Distance'], tel_d2['Speed'], color=color_d2, label=label_d2, linewidth=1.5)
            ax1.set_ylabel("Speed (Km/h)", fontweight='bold')
            ax1.legend(loc="lower right", facecolor='black')

            # --- Acelerador ---
            ax2.plot(tel_d1['Distance'], tel_d1['Throttle'], color=color_d1, linewidth=1.5)
            ax2.plot(tel_d2['Distance'], tel_d2['Throttle'], color=color_d2, linewidth=1.5)
            ax2.set_ylabel("Throttle (%)", fontweight='bold')

            # --- Freno ---
            ax3.plot(tel_d1['Distance'], tel_d1['Brake'], color=color_d1, linewidth=1.5)
            ax3.plot(tel_d2['Distance'], tel_d2['Brake'], color=color_d2, linewidth=1.5)
            ax3.set_ylabel("Brake", fontweight='bold')
            ax3.set_xlabel("Track Distance (meters)", fontweight='bold')

            self.canvas = FigureCanvasTkAgg(fig, master=self.plot_frame)
            self.canvas.draw()
            self.canvas.get_tk_widget().pack(fill="both", expand=True)

        except Exception as e:
            self.status_label.pack(expand=True)
            self.status_label.configure(text=f"❌ Error al cargar los datos:\n{str(e)}", text_color="red")
            if self.canvas:
                self.canvas.get_tk_widget().destroy()
                self.canvas = None

if __name__ == "__main__":
    app = TelemetryAnalyzerPro()
    app.mainloop()