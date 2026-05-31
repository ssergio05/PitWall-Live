# 🏎️ F1 Live Telemetry Suite

A high-performance, full-stack telemetry acquisition and visualization system built for Sim-Racing and Motorsport data analysis. 

This project simulates realistic Formula 1 car physics, transmits the data via a UDP network stream to a high-speed C++ backend, and renders a live, dark-mode Pit Wall dashboard in real-time using Python.

---

## 📌 Features

* **Custom Physics Engine:** Simulates real-world F1 dynamics including aerodynamic drag, trail braking, human pedal interpolation, and realistic gear ratios for the *Circuit de Barcelona-Catalunya*.
* **High-Speed Data Receiver:** A robust C++ backend that listens to UDP socket streams (Port 20777), processes raw binary packets, manages memory buffers, and flushes data instantly to a CSV log.
* **Live Pit Wall Dashboard:** A real-time, animated `matplotlib` dashboard displaying Speed, RPM, Gears, Throttle/Brake application, and Steering Angle at 60Hz.

---

## ⚙️ Architecture

The project is divided into three agnostic modules that communicate in real-time:

1. **Telemetry Provider (Python):** Acts as the "Car". Calculates physics and packages the data into C-struct binary arrays, broadcasting them via UDP.
2. **Telemetry Receiver (C++):** Acts as the "Server". Listens for incoming UDP packets, prevents data loss, and writes the decoded telemetry to `session_telemetry.csv`.
3. **Live Dashboard (Python):** Acts as the "Pit Wall". Continuously reads the CSV stream and updates the graphical interface.

---

## 🛠️ Prerequisites

Before you begin, ensure you have the following installed:
* **Python 3.8+**
* A **C++ Compiler** (e.g., MSVC via Visual Studio, or GCC/MinGW)
* Git

---

## 🚀 Installation & Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/ssergio05/PitWall-Live.git
   cd [PitWall-Live]
   ```

2. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Compile the C++ Receiver:**
   Open the `src/` folder in your preferred C++ IDE (like Visual Studio) and build the project to generate the `f1_receiver.exe` executable.

---

## 🏁 How to Run (The "Pit Wall" Sequence)

To see the system in action, you need to launch the components in **three separate terminal windows** to avoid blocking processes. 

**Follow this exact order:**

**Terminal 1: Start the Data Receiver**
Run your compiled C++ executable to open the UDP port and start listening.
   ```bash
   # Example for Windows:
   .\build\x64-Debug\f1_receiver.exe
   ```

**Terminal 2: Open the Live Dashboard**
Launch the graphical interface. It will open a black window waiting for data.
   ```bash
   python tools/live_dashboard.py
   ```

**Terminal 3: Start the Car Simulator**
Launch the physics engine to start broadcasting telemetry.
   ```bash
   python tools/telemetry_provider.py
   ```

Watch your Live Dashboard come to life with real-time racing data! To stop the simulation, press `Ctrl+C` in the Python terminals and close the C++ program.

---

## 📂 Project Structure

```text
├── include/                 # C++ Header files
│   ├── Logger.hpp
│   ├── Packets.hpp
│   └── Receiver.hpp
├── src/                     # C++ Source code
│   ├── Logger.cpp
│   ├── main.cpp
│   └── Receiver.cpp
├── tools/                   # Python tools (Simulator & Visualizer)
│   ├── live_dashboard.py
│   ├── telemetry_analyzer.py
│   └── telemetry_provider.py
├── .gitignore               
├── README.md                
└── requirements.txt         
```

---

## 🤝 Contributing
Feel free to fork this project, submit pull requests, or open issues if you want to add new sensors, track maps, or integrate real F1 Live Timing API data.