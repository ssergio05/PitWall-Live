def start_api_listener(self):
        if self.is_listening_stream: 
            self.is_listening_stream = False # Apagar stream anterior
            time.sleep(0.5)

        self.btn_live_start.configure(text="⏳ Escuchando Servidores...", fg_color="#ffa500", state="disabled")
        
        # Limpiamos el búfer para la nueva sesión
        self.live_buffer = {drv: pd.DataFrame(columns=['Distance', 'Speed', 'Throttle', 'Brake', 'LapNumber']) for drv in DRIVERS}
        self.vuelta_en_pantalla = 1
        self.lbl_lap.configure(text=f"Mostrando Vuelta: {self.vuelta_en_pantalla}")

        y, t, s = self.live_year.get(), self.live_track.get(), self.live_sess.get()
        p1, p2 = self.live_p1.get(), self.live_p2.get()
        
        self.is_listening_stream = True
        # Aquí es donde el día de mañana enchufarías tu hilo de WebSockets real.
        # Por ahora, usamos el Mock Simulator.
        self.stream_thread = threading.Thread(target=self._mock_websocket_stream, args=(y, t, s, [p1, p2]), daemon=True)
        self.stream_thread.start()