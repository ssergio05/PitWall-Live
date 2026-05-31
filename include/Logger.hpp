#pragma once
#include <fstream>
#include <string>
#include "Packets.hpp"

class TelemetryLogger {
public:
    TelemetryLogger(const std::string& filename);

    ~TelemetryLogger();

    void logRow(float sessionTime, const CarTelemetryData& data);

private:
    std::ofstream m_file;
};