import customtkinter as ctk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.animation import FuncAnimation
import pandas as pd
import fastf1
import fastf1.plotting
import os
import logging
import threading
import time

# Configuración inicial de FastF1
script_dir = os.path.dirname(os.path.abspath(__file__))
cache_dir = os.path.join(script_dir, '..', 'fastf1_cache')
if not os.path.exists(cache_dir): os.makedirs(cache_dir)
fastf1.Cache.enable_cache(cache_dir)
fastf1.logger.set_log_level(logging.ERROR)

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")
# 📌 CORREGIDO: Eliminado el parámetro obsoleto 'misc_mpl_mods' que daba el warning
fastf1.plotting.setup_mpl(mpl_timedelta_support=False, color_scheme='fastf1')

TRACKS = ["Bahrain", "Saudi Arabia", "Australia", "Japan", "China", "Miami", "Imola", "Monaco", "Canada", "Spain", "Austria", "Silverstone", "Hungary", "Spa", "Zandvoort", "Monza", "Baku", "Singapore", "Austin", "Mexico", "Interlagos", "Las Vegas", "Qatar", "Abu Dhabi"]
DRIVERS = ["VER", "PER", "LEC", "SAI", "NOR", "PIA", "HAM", "RUS", "ALO", "STR", "GAS", "OCO", "ALB", "SAR", "COL", "TSU", "RIC", "LAW", "BOT", "ZHO", "MAG", "HUL", "BEA"]

DRIVER_COLORS = {'VER': '#3671C6', 'PER': '#3671C6', 'LEC': '#E8002D', 'SAI': '#E8002D', 'BEA': '#E8002D', 'NOR': '#FF8000', 'PIA': '#FF8000', 'HAM': '#27F4D2', 'RUS': '#27F4D2', 'ALO': '#2293D1', 'STR': '#2293D1', 'GAS': '#0093CC', 'OCO': '#0093CC', 'ALB': '#64C4FF', 'SAR': '#64C4FF', 'COL': '#64C4FF', 'TSU': '#6692FF', 'RIC': '#6692FF', 'LAW': '#6692FF', 'BOT': '#52E252', 'ZHO': '#52E252', 'MAG': '#B6BABD', 'HUL': '#B6BABD'}

class PitWallOS(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Pit Wall OS - Centro de Mando Táctico")
        self.geometry("1400x900")
        self.minsize(1200, 800)

        # LA CAJA NEGRA (BÚFER EN VIVO)
        self.live_buffer = {drv: pd.DataFrame(columns=['Distance', 'Speed', 'Throttle', 'Brake', 'LapNumber']) for drv in DRIVERS}
        self.is_listening_stream = False 
        self.stream_thread = None

        self.tabview = ctk.CTkTabview(self, corner_radius=10)
        self.tabview.pack(fill="both", expand=True, padx=15, pady=15)
        self.tab_live = self.tabview.add("🔴 Live Timing & Lap Viewer")
        self.tab_history = self.tabview.add("📚 Analizador Histórico")
        self.tabview.set("🔴 Live Timing & Lap Viewer") 

        self.vuelta_en_pantalla = 1
        self.build_live_tab()
        self.build_history_tab()

    # ==========================================
    # 🔴 PESTAÑA 1: LIVE TIMING
    # ==========================================
    def build_live_tab(self):
        self.tab_live.grid_columnconfigure(0, weight=1)
        self.tab_live.grid_rowconfigure(2, weight=1)

        conn_frame = ctk.CTkFrame(self.tab_live, fg_color="transparent")
        conn_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=(5, 0))
        
        ctk.CTkLabel(conn_frame, text="Sesión:").pack(side="left", padx=(0,5))
        self.live_year = ctk.CTkComboBox(conn_frame, values=["2024", "2023"], width=70)
        self.live_year.pack(side="left", padx=5)
        self.live_track = ctk.CTkComboBox(conn_frame, values=TRACKS, width=150)
        self.live_track.pack(side="left", padx=5)
        self.live_sess = ctk.CTkComboBox(conn_frame, values=["Q", "R", "S", "SQ", "FP1", "FP2", "FP3"], width=60)
        self.live_sess.pack(side="left", padx=5)

        ctk.CTkLabel(conn_frame, text="Pilotos:").pack(side="left", padx=(20,5))
        self.live_p1 = ctk.CTkComboBox(conn_frame, values=["-"] + DRIVERS, width=70)
        self.live_p1.set("VER")
        self.live_p1.pack(side="left", padx=5)
        ctk.CTkLabel(conn_frame, text="vs").pack(side="left")
        self.live_p2 = ctk.CTkComboBox(conn_frame, values=["-"] + DRIVERS, width=70)
        self.live_p2.set("PIA")
        self.live_p2.pack(side="left", padx=5)

        self.btn_live_start = ctk.CTkButton(conn_frame, text="▶ Conectar API / Stream", command=self.start_api_listener, fg_color="#8b0000", hover_color="#ff0000")
        self.btn_live_start.pack(side="right", padx=10)

        control_frame = ctk.CTkFrame(self.tab_live, height=50, corner_radius=10)
        control_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=(10, 5))
        control_frame.grid_columnconfigure((0, 4), weight=1) 
        ctk.CTkButton(control_frame, text="◀ Vuelta Ant.", width=120, command=self.lap_prev).grid(row=0, column=1, padx=10, pady=10)
        self.lbl_lap = ctk.CTkLabel(control_frame, text=f"Mostrando Vuelta: {self.vuelta_en_pantalla}", font=ctk.CTkFont(size=16, weight="bold"))
        self.lbl_lap.grid(row=0, column=2, padx=20, pady=10)
        ctk.CTkButton(control_frame, text="Vuelta Sig. ▶", width=120, command=self.lap_next).grid(row=0, column=3, padx=10, pady=10)

        self.live_plot_frame = ctk.CTkFrame(self.tab_live, corner_radius=10)
        self.live_plot_frame.grid(row=2, column=0, sticky="nsew", padx=10, pady=(5, 10))
        
        plt.style.use('dark_background')
        self.fig_live, (self.ax1_l, self.ax2_l, self.ax3_l) = plt.subplots(3, 1, figsize=(10, 6), sharex=True)
        self.fig_live.subplots_adjust(left=0.06, right=0.97, top=0.95, bottom=0.08, hspace=0.15)
        self.fig_live.patch.set_facecolor('#2b2b2b')
        self.canvas_live = FigureCanvasTkAgg(self.fig_live, master=self.live_plot_frame)
        self.canvas_live.get_tk_widget().pack(fill="both", expand=True)

        self.ani = FuncAnimation(self.fig_live, self.update_live_plot, interval=100, cache_frame_data=False)

    def start_api_listener(self):
        if self.is_listening_stream: 
            self.is_listening_stream = False
            time.sleep(0.5)

        self.btn_live_start.configure(text="⏳ Conectando...", fg_color="#ffa500", state="disabled")
        self.live_buffer = {drv: pd.DataFrame(columns=['Distance', 'Speed', 'Throttle', 'Brake', 'LapNumber']) for drv in DRIVERS}
        self.vuelta_en_pantalla = 1
        self.lbl_lap.configure(text=f"Mostrando Vuelta: {self.vuelta_en_pantalla}")

        y, t, s = self.live_year.get(), self.live_track.get(), self.live_sess.get()
        
        self.is_listening_stream = True
        # 📌 CORREGIDO: Ahora el lanzador coincide perfectamente con la función del Obrero (3 argumentos)
        self.stream_thread = threading.Thread(target=self._mock_websocket_stream, args=(y, t, s), daemon=True)
        self.stream_thread.start()

    def _mock_websocket_stream(self, year, track, session_type):
        try:
            session = fastf1.get_session(int(year), track, session_type)
            session.load(telemetry=True, weather=False, messages=False)

            full_data_cache = {}

            def sync_fetch_driver(drv):
                try:
                    laps = session.laps.pick_driver(drv)
                    df_list = []
                    for _, lap in laps.iterlaps():
                        try:
                            # 📌 EL TRUCO: Usamos get_car_data() en lugar de get_telemetry().
                            # Al ignorar los datos del GPS (X, Y, Z) evitamos el procesado pesado.
                            # La carga pasa de tardar 30 segundos a ser casi instantánea.
                            tel = lap.get_car_data().add_distance()[['SessionTime', 'Distance', 'Speed', 'Throttle', 'Brake']]
                            tel['LapNumber'] = lap['LapNumber']
                            df_list.append(tel)
                        except: pass
                    return pd.concat(df_list).sort_values('SessionTime') if df_list else pd.DataFrame()
                except:
                    return pd.DataFrame()

            def fetch_driver_data_if_needed(drv):
                if drv == "-" or drv in full_data_cache: 
                    return
                
                full_data_cache[drv] = "LOADING" 
                
                def background_worker():
                    full_data_cache[drv] = sync_fetch_driver(drv)
                    
                threading.Thread(target=background_worker, daemon=True).start()

            p1_start = self.live_p1.get()
            p2_start = self.live_p2.get()
            if p1_start != "-": full_data_cache[p1_start] = sync_fetch_driver(p1_start)
            if p2_start != "-": full_data_cache[p2_start] = sync_fetch_driver(p2_start)

            self.btn_live_start.configure(text="✅ Recibiendo Stream", fg_color="#006400", state="normal")

            valid_starts = [full_data_cache[d]['SessionTime'].min() for d in full_data_cache if isinstance(full_data_cache[d], pd.DataFrame) and not full_data_cache[d].empty]
            start_time = min(valid_starts) if valid_starts else pd.Timedelta(seconds=0)
            current_time = start_time

            while self.is_listening_stream:
                current_time += pd.Timedelta(seconds=0.1) 
                
                for drv in [self.live_p1.get(), self.live_p2.get()]:
                    if drv != "-":
                        fetch_driver_data_if_needed(drv)
                        
                        drv_data = full_data_cache.get(drv)
                        if isinstance(drv_data, pd.DataFrame) and not drv_data.empty:
                            incoming_packets = drv_data[drv_data['SessionTime'] <= current_time]
                            self.live_buffer[drv] = incoming_packets
                
                time.sleep(0.1) 

        except Exception as e:
            self.btn_live_start.configure(text="❌ Conexión Perdida", fg_color="#8b0000", state="normal")
            self.is_listening_stream = False

    def lap_prev(self):
        if self.vuelta_en_pantalla > 1:
            self.vuelta_en_pantalla -= 1
            self.lbl_lap.configure(text=f"Mostrando Vuelta: {self.vuelta_en_pantalla}")

    def lap_next(self):
        self.vuelta_en_pantalla += 1
        self.lbl_lap.configure(text=f"Mostrando Vuelta: {self.vuelta_en_pantalla}")

    def update_live_plot(self, frame):
        if not self.is_listening_stream: return

        try:
            p1 = self.live_p1.get()
            p2 = self.live_p2.get()

            for ax in (self.ax1_l, self.ax2_l, self.ax3_l):
                ax.clear(); ax.grid(True, alpha=0.2); ax.set_facecolor('#1e1e1e')

            self.ax1_l.set_ylabel("Speed (Km/h)", fontweight='bold')
            self.ax2_l.set_ylabel("Throttle (%)", fontweight='bold')
            self.ax3_l.set_ylabel("Brake", fontweight='bold')
            self.ax1_l.set_ylim(0, 360)
            self.ax2_l.set_ylim(-5, 105)
            self.ax3_l.set_ylim(-0.1, 1.1)
            self.ax3_l.set_yticks([0, 1])
            self.ax3_l.set_yticklabels(['OFF', 'ON'])

            max_dists = []
            for p in [p1, p2]:
                if p != "-":
                    df_p = self.live_buffer.get(p, pd.DataFrame())
                    if not df_p.empty and 'Distance' in df_p.columns:
                        max_dists.append(df_p['Distance'].max())
            track_length = max(max_dists + [7500]) if max_dists else 7500
            self.ax3_l.set_xlim(0, track_length)

            has_data = False
            for drv in [p1, p2]:
                if drv == "-": continue 
                
                df_drv = self.live_buffer.get(drv, pd.DataFrame())
                if df_drv.empty: continue
                
                df_lap = df_drv[df_drv['LapNumber'] == self.vuelta_en_pantalla]
                
                if not df_lap.empty:
                    has_data = True
                    c = DRIVER_COLORS.get(drv, '#ffffff')
                    self.ax1_l.plot(df_lap['Distance'], df_lap['Speed'], color=c, label=drv, linewidth=1.5)
                    self.ax2_l.plot(df_lap['Distance'], df_lap['Throttle'], color=c, linewidth=1.5)
                    self.ax3_l.plot(df_lap['Distance'], df_lap['Brake'], color=c, linewidth=1.5)

            if not has_data:
                self.ax1_l.text(0.5, 0.5, f"Esperando paquetes de telemetría de la Vuelta {self.vuelta_en_pantalla}...", ha='center', va='center', transform=self.ax1_l.transAxes, color='gray')
            else:
                self.ax1_l.legend(loc="lower right", facecolor='black')

        except Exception: pass

    # ==========================================
    # 📚 PESTAÑA 2: ANALIZADOR HISTÓRICO
    # ==========================================
    def build_history_tab(self):
        self.tab_history.grid_columnconfigure(1, weight=1); self.tab_history.grid_rowconfigure(0, weight=1)
        self.session_hist = None

        self.sidebar = ctk.CTkFrame(self.tab_history, width=300, corner_radius=10)
        self.sidebar.grid(row=0, column=0, sticky="nsew", padx=(10, 5), pady=10)
        self.sidebar.grid_rowconfigure(13, weight=1) 

        self.logo_label = ctk.CTkLabel(self.sidebar, text="HISTORICAL\nANALYZER", font=ctk.CTkFont(size=20, weight="bold"))
        self.logo_label.grid(row=0, column=0, padx=20, pady=20)

        self.frame_config = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        self.frame_config.grid(row=1, column=0, padx=20, pady=0, sticky="ew")
        self.combo_year = ctk.CTkComboBox(self.frame_config, values=["2024", "2023", "2022"], width=70)
        self.combo_year.grid(row=0, column=0, padx=(0, 5), sticky="w")
        self.combo_session = ctk.CTkComboBox(self.frame_config, values=["FP1", "FP2", "FP3", "Q", "S", "SQ", "R"], width=70)
        self.combo_session.grid(row=0, column=1, padx=(5, 0), sticky="e")

        self.combo_track = ctk.CTkComboBox(self.sidebar, values=TRACKS)
        self.combo_track.grid(row=2, column=0, padx=20, pady=(10, 15), sticky="ew")

        self.btn_load = ctk.CTkButton(self.sidebar, text="1. Cargar Sesión", command=self.load_session, fg_color="#d46b08", hover_color="#ad5604")
        self.btn_load.grid(row=3, column=0, padx=20, pady=(0, 20), sticky="ew")

        self.separator = ctk.CTkFrame(self.sidebar, height=2, fg_color="gray30")
        self.separator.grid(row=4, column=0, padx=20, pady=(0, 20), sticky="ew")

        ctk.CTkLabel(self.sidebar, text="Piloto 1 / Vuelta:").grid(row=5, column=0, padx=20, pady=0, sticky="w")
        self.frame_d1 = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        self.frame_d1.grid(row=6, column=0, padx=20, pady=(0, 15), sticky="ew")
        self.frame_d1.grid_columnconfigure(0, weight=1); self.frame_d1.grid_columnconfigure(1, weight=1)
        self.combo_p1 = ctk.CTkComboBox(self.frame_d1, values=["-"], width=90, state="disabled", command=self.update_laps_p1)
        self.combo_p1.grid(row=0, column=0, padx=(0, 5), sticky="ew")
        self.combo_lap_p1 = ctk.CTkComboBox(self.frame_d1, values=["-"], width=90, state="disabled")
        self.combo_lap_p1.grid(row=0, column=1, padx=(5, 0), sticky="ew")

        ctk.CTkLabel(self.sidebar, text="Piloto 2 / Vuelta:").grid(row=7, column=0, padx=20, pady=0, sticky="w")
        self.frame_d2 = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        self.frame_d2.grid(row=8, column=0, padx=20, pady=(0, 20), sticky="ew")
        self.frame_d2.grid_columnconfigure(0, weight=1); self.frame_d2.grid_columnconfigure(1, weight=1)
        self.combo_p2 = ctk.CTkComboBox(self.frame_d2, values=["-"], width=90, state="disabled", command=self.update_laps_p2)
        self.combo_p2.grid(row=0, column=0, padx=(0, 5), sticky="ew")
        self.combo_lap_p2 = ctk.CTkComboBox(self.frame_d2, values=["-"], width=90, state="disabled")
        self.combo_lap_p2.grid(row=0, column=1, padx=(5, 0), sticky="ew")

        self.btn_analyze = ctk.CTkButton(self.sidebar, text="2. Dibujar Telemetría", command=self.run_analysis, height=40, state="disabled")
        self.btn_analyze.grid(row=9, column=0, padx=20, pady=20, sticky="ew")

        self.plot_frame_hist = ctk.CTkFrame(self.tab_history, corner_radius=10)
        self.plot_frame_hist.grid(row=0, column=1, padx=(5, 10), pady=10, sticky="nsew")
        self.status_label = ctk.CTkLabel(self.plot_frame_hist, text="Paso 1: Elige circuito y pulsa 'Cargar Sesión'", font=ctk.CTkFont(size=16))
        self.status_label.pack(expand=True)
        self.canvas_hist = None

    def load_session(self):
        y, t, s = int(self.combo_year.get()), self.combo_track.get(), self.combo_session.get()
        self.status_label.configure(text=f"⏳ Descargando base de datos de {t} {y}...", text_color="#ffa500")
        self.update()
        try:
            self.session_hist = fastf1.get_session(y, t, s)
            self.session_hist.load(telemetry=True, weather=False, messages=False)
            
            driver_abbrs = ["-"] + [self.session_hist.get_driver(d)['Abbreviation'] for d in self.session_hist.drivers]
            for combo in (self.combo_p1, self.combo_p2):
                combo.configure(state="normal", values=driver_abbrs)
            if len(driver_abbrs) >= 3:
                self.combo_p1.set(driver_abbrs[1]); self.combo_p2.set(driver_abbrs[2])
            
            self.combo_lap_p1.configure(state="normal"); self.combo_lap_p2.configure(state="normal")
            self.update_laps_p1(self.combo_p1.get()); self.update_laps_p2(self.combo_p2.get())
            self.btn_analyze.configure(state="normal")
            self.status_label.configure(text="✅ Sesión cargada.\nPaso 2: Elige pilotos, vueltas y pulsa 'Dibujar Telemetría'", text_color="#00ff00")
        except Exception as e:
            self.status_label.configure(text=f"❌ Error al cargar sesión:\n{str(e)}", text_color="red")

    def update_laps_p1(self, choice):
        if not self.session_hist or choice == "-": return
        try:
            laps = self.session_hist.laps.pick_driver(choice)
            self.combo_lap_p1.configure(values=["Fastest"] + [str(int(l)) for l in laps['LapNumber'].unique()])
            self.combo_lap_p1.set("Fastest")
        except: pass

    def update_laps_p2(self, choice):
        if not self.session_hist or choice == "-": return
        try:
            laps = self.session_hist.laps.pick_driver(choice)
            self.combo_lap_p2.configure(values=["Fastest"] + [str(int(l)) for l in laps['LapNumber'].unique()])
            self.combo_lap_p2.set("Fastest")
        except: pass

    def run_analysis(self):
        d1, d2, lp1, lp2 = self.combo_p1.get(), self.combo_p2.get(), self.combo_lap_p1.get(), self.combo_lap_p2.get()
        if d1 == "-" and d2 == "-": return

        try:
            if self.canvas_hist: self.canvas_hist.get_tk_widget().destroy()
            self.status_label.pack_forget()

            plt.style.use('dark_background')
            fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(12, 8), sharex=True)
            fig.subplots_adjust(left=0.06, right=0.97, top=0.95, bottom=0.06, hspace=0.15)
            fig.patch.set_facecolor('#2b2b2b') 
            for ax in (ax1, ax2, ax3): ax.set_facecolor('#1e1e1e'); ax.grid(True, alpha=0.2)
            
            ax1.set_ylabel("Speed (Km/h)", fontweight='bold')
            ax2.set_ylabel("Throttle (%)", fontweight='bold')
            ax3.set_ylabel("Brake", fontweight='bold'); ax3.set_xlabel("Track Distance (meters)", fontweight='bold')

            def plot_driver(drv, lap_sel):
                if drv == "-": return
                l_drv = self.session_hist.laps.pick_driver(drv)
                lap_d = l_drv.pick_fastest() if lap_sel == "Fastest" else l_drv[l_drv['LapNumber'] == int(lap_sel)].iloc[0]
                tel_d = lap_d.get_telemetry().add_distance()
                try: c = fastf1.plotting.get_team_color(lap_d['Team'], session=self.session_hist)
                except: c = 'white'
                
                lbl = f"{drv} (V.{int(lap_d['LapNumber'])}: {lap_d['LapTime'].total_seconds():.3f}s)" if pd.notnull(lap_d['LapTime']) else f"{drv} (V.{int(lap_d['LapNumber'])})"
                ax1.plot(tel_d['Distance'], tel_d['Speed'], color=c, label=lbl, linewidth=1.5)
                ax2.plot(tel_d['Distance'], tel_d['Throttle'], color=c, linewidth=1.5)
                ax3.plot(tel_d['Distance'], tel_d['Brake'], color=c, linewidth=1.5)

            plot_driver(d1, lp1)
            plot_driver(d2, lp2)

            ax1.legend(loc="lower right", facecolor='black')

            self.canvas_hist = FigureCanvasTkAgg(fig, master=self.plot_frame_hist)
            self.canvas_hist.draw()
            self.canvas_hist.get_tk_widget().pack(fill="both", expand=True)
        except Exception as e:
            self.status_label.pack(expand=True)
            self.status_label.configure(text=f"❌ Error al cargar los datos:\n{str(e)}", text_color="red")
            if self.canvas_hist: self.canvas_hist.get_tk_widget().destroy(); self.canvas_hist = None

if __name__ == "__main__":
    app = PitWallOS()
    app.mainloop()