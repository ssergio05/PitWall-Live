#pragma once
#ifndef WIN32_LEAN_AND_MEAN
#define WIN32_LEAN_AND_MEAN
#endif

#include <winsock2.h>
#include <ws2tcpip.h>
#include <thread>
#include <mutex>
#include <queue>
#include <condition_variable>
#include <atomic>
#include "Packets.hpp"
#include "Logger.hpp"

#pragma comment(lib, "Ws2_32.lib")

class TelemetryReceiver {
public:
    TelemetryReceiver(int port);
    ~TelemetryReceiver();
    void start();

private:
    SOCKET m_socket;
    int m_port;
    std::atomic<bool> m_running{ false };

    std::queue<PacketCarTelemetryData> m_dataQueue;
    std::mutex m_queueMutex;
    std::condition_variable m_cv;
    std::thread m_workerThread;

    TelemetryLogger m_logger{ "C:/Users/Sergio/Dropbox/Mi PC (DESKTOP-HGNK1S8)/Desktop/Sim-Racing Real-Time Telemetry Link/session_telemetry.csv" };

    uint32_t m_nextExpectedFrame = 0;
    uint32_t m_packetsLost = 0;
    float m_lastFuelLevel = -1.0f;
    float m_startFuel = -1.0f;
    float m_startDistance = -1.0f;
    float m_consumptionLPerKm = 0.0f;

    void initWinsock();
    void processRawPacket(char* buffer, int size);
    void loggerWorker();
};