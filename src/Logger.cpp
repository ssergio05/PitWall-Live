#include "../include/Logger.hpp"
#include <iostream>

TelemetryLogger::TelemetryLogger(const std::string& filename) {
    m_file.open(filename, std::ios::out | std::ios::trunc);
    if (m_file.is_open()) {

        m_file << "SessionTime,Speed,RPM,Throttle,Brake,Gear,Steer\n";
    }
    else {
        std::cout << "\n[!] ERROR FATAL: No se ha podido crear el archivo CSV.\n";
    }
}

TelemetryLogger::~TelemetryLogger() {
    if (m_file.is_open()) {
        m_file.close();
    }
}

void TelemetryLogger::logRow(float sessionTime, const CarTelemetryData& data) {
    if (m_file.is_open()) {
        m_file << sessionTime << ","
            << data.m_speed << ","
            << data.m_engineRPM << ","
            << data.m_throttle << ","
            << data.m_brake << ","
            << (int)data.m_gear << ","
            << (int)data.m_steer << "\n";

        m_file.flush();
    }
}