import socket
import time
import struct
import math
import random

# Network configuration
UDP_IP = "127.0.0.1"
UDP_PORT = 20777
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# Telemetry session state
fuel = 50.0          
total_distance = 0.0 
frame_id = 0
start_time = time.time()

# Initial car physics state
current_speed = 80.0
current_throttle = 0.0
current_brake = 0.0
current_steer = 0.0

def create_header(packet_id, frame):
    # F1 UDP standard header formatting
    return struct.pack('<HBBBBBQfIIBB', 
        2024, 24, 1, 1, 1, packet_id, 8888, 
        (time.time() - start_time), frame, frame, 0, 0)

# Circuit Map: Barcelona-Catalunya (Montmeló)
# Format: (Duration_seconds, Target_Gas, Target_Brake, Target_Steer, Target_Speed)
track_barcelona = [
    (9.0,  1.0, 0.0,  0.0, 335.0), # 0. Main straight
    (2.5,  0.0, 1.0,  0.7, 140.0), # 1. Heavy braking T1
    (1.5,  0.4, 0.0, -0.6, 160.0), # 2. T2 flick
    (4.0,  1.0, 0.0,  0.5, 250.0), # 3. T3 (Renault long right)
    (3.0,  1.0, 0.0,  0.0, 290.0), # 4. Straight to Repsol
    (2.5,  0.0, 0.8,  0.6, 150.0), # 5. T4 (Repsol braking)
    (2.0,  1.0, 0.0,  0.0, 220.0), # 6. Downhill to T5
    (3.0,  0.0, 1.0, -0.8,  85.0), # 7. T5 (Seat hairpin)
    (4.0,  1.0, 0.0,  0.0, 260.0), # 8. Uphill to T7
    (1.5,  0.2, 0.5, -0.6, 170.0), # 9. T7
    (2.0,  0.7, 0.0,  0.5, 210.0), # 10. T8
    (3.0,  1.0, 0.0,  0.4, 260.0), # 11. T9 (Campsa blind apex)
    (8.0,  1.0, 0.0,  0.0, 320.0), # 12. Back straight (DRS zone)
    (3.0,  0.0, 1.0, -0.9,  90.0), # 13. T10 (La Caixa heavy braking)
    (3.0,  0.6, 0.0,  0.4, 160.0), # 14. T11-T12 stadium section
    (5.0,  1.0, 0.0,  0.5, 250.0), # 15. T13-T14 fast right sweepers
    (15.0, 1.0, 0.0,  0.0, 335.0)  # 16. Exit to main straight
]

LAP_TIME = sum([sector[0] for sector in track_barcelona])

def get_current_sector(lap_time):
    accumulated = 0.0
    for sector in track_barcelona:
        if lap_time < accumulated + sector[0]:
            return sector
        accumulated += sector[0]
    return track_barcelona[0]

def send_telemetry(frame):
    global current_speed, current_throttle, current_brake, current_steer
    header = create_header(6, frame)
    
    current_lap_time = (time.time() - start_time) % LAP_TIME
    sector = get_current_sector(current_lap_time)
    
    target_throttle = sector[1]
    target_brake = sector[2]
    target_steer = sector[3]
    
    # --- ADVANCED PHYSICS ENGINE ---
    
    # 1. Human input simulation (Smooth linear interpolation)
    current_throttle += (target_throttle - current_throttle) * 0.08
    current_brake += (target_brake - current_brake) * 0.15 
    current_steer += (target_steer - current_steer) * 0.10
    
    # 2. Aerodynamic Drag (Scales exponentially with speed)
    aero_drag = 0.000015 * (current_speed ** 2)
    
    # 3. Acceleration and Braking physics (Trail braking simulation)
    if current_brake > 0.05:
        brake_power = 2.5 * current_brake
        current_speed -= (brake_power + aero_drag)
    elif current_throttle > 0.05:
        # Engine power curve (more torque at lower speeds)
        engine_power = (10.0 / (current_speed / 50.0 + 1)) * current_throttle
        current_speed += engine_power - aero_drag
    else:
        # Engine braking and aero drag when coasting
        current_speed -= (0.1 + aero_drag)

    # Strict physical limits
    if current_speed < 65.0: current_speed = 65.0
    if current_speed > 340.0: current_speed = 340.0

    # --- Realistic F1 Drivetrain Calculations ---
    # Top speeds for each F1 gear (approximate)
    gear_max_speeds = [0, 85, 125, 165, 205, 250, 290, 325, 360]
    
    gear = 1
    for i in range(1, 9):
        if current_speed <= gear_max_speeds[i]:
            gear = i
            break
    else:
        gear = 8
        
    # Calculate RPM within the power band of the current gear
    min_gear_speed = gear_max_speeds[gear - 1]
    max_gear_speed = gear_max_speeds[gear]
    
    # How far along are we in the current gear? (0.0 to 1.0)
    speed_progress = (current_speed - min_gear_speed) / (max_gear_speed - min_gear_speed)
    
    # F1 engines stay high in RPM. Gear 1 drops lower, the rest stay in the sweet spot (9500-12500)
    base_rpm = 6000 if gear == 1 else 9500
    rpm = base_rpm + (speed_progress * (12500 - base_rpm))
    
    # Add minor RPM fluctuations based on throttle/brake to make it look organic
    if current_throttle < 1.0 and current_brake == 0.0:
        rpm -= 500 * (1.0 - current_throttle)
    
    # Pack data into C-struct binary format
    my_car = struct.pack('<HfbfBbHBBBBH4H4B4BH4f4B',
        int(current_speed), current_throttle, int(current_steer * 100), current_brake, 0, gear, int(rpm), 
        0, 0, 0, 0, 0, 0,0,0,0, 0,0,0,0, 0,0,0,0, 90, 2.1,2.1,2.1,2.1, 1,1,1,1)

    others = b'\x00' * (60 * 21) + b'\x00' * 3
    packet = header + my_car + others + b'\x00' * 500
    
    sock.sendto(packet, (UDP_IP, UDP_PORT))
    return current_speed

def send_status(frame, fuel_level):
    header = create_header(7, frame)
    my_status = struct.pack('<BBBBBffHHHBB',
        2, 1, 2, 55, 0, fuel_level, 100.0, 15, 12000, 1000, 8, 1)
    others = b'\x00' * (21 * 21)
    sock.sendto(header + my_status + others + b'\x00' * 500, (UDP_IP, UDP_PORT))

print(f">>> F1 Advanced Physics Simulator (Circuit: Barcelona) running. Transmitting to {UDP_IP}:{UDP_PORT}")

try:
    while True:
        speed_val = send_telemetry(frame_id)
        if frame_id % 6 == 0:
            send_status(frame_id, fuel)
            fuel -= (speed_val * 0.00001) 
        frame_id += 1
        time.sleep(1/60)
except KeyboardInterrupt:
    print("\n>>> Car boxed. Simulation terminated.")