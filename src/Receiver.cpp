#include "../include/Receiver.hpp"
#include <iostream>

TelemetryReceiver::TelemetryReceiver(int port) : m_port(port) {
    initWinsock();
    m_running = true;
    m_workerThread = std::thread(&TelemetryReceiver::loggerWorker, this);
}

TelemetryReceiver::~TelemetryReceiver() {
    m_running = false;
    m_cv.notify_all();
    if (m_workerThread.joinable()) m_workerThread.join();
    if (m_socket != INVALID_SOCKET) closesocket(m_socket);
    WSACleanup();
}

void TelemetryReceiver::initWinsock() {
    WSADATA wsaData;
    WSAStartup(MAKEWORD(2, 2), &wsaData);
    m_socket = socket(AF_INET, SOCK_DGRAM, IPPROTO_UDP);
    sockaddr_in addr{};
    addr.sin_family = AF_INET;
    addr.sin_addr.s_addr = INADDR_ANY;
    addr.sin_port = htons(m_port);
    bind(m_socket, (struct sockaddr*)&addr, sizeof(addr));
}

void TelemetryReceiver::start() {
    char buffer[4096];
    while (m_running) {
        int bytes = recvfrom(m_socket, buffer, sizeof(buffer), 0, nullptr, nullptr);
        if (bytes > 0) processRawPacket(buffer, bytes);
    }
}

void TelemetryReceiver::processRawPacket(char* buffer, int size) {
    auto* header = reinterpret_cast<PacketHeader*>(buffer);

    if (m_nextExpectedFrame != 0 && header->m_frameIdentifier > m_nextExpectedFrame) {
        m_packetsLost += (header->m_frameIdentifier - m_nextExpectedFrame);
    }
    m_nextExpectedFrame = header->m_frameIdentifier + 1;

    if (header->m_packetId == 6) {
        auto* packet = reinterpret_cast<PacketCarTelemetryData*>(buffer);
        {
            std::lock_guard<std::mutex> lock(m_queueMutex);
            m_dataQueue.push(*packet);
        }
        m_cv.notify_one();
    }
    else if (header->m_packetId == 7) {
        auto* packet = reinterpret_cast<PacketCarStatusData*>(buffer);
        float fuel = packet->m_carStatusData[header->m_playerCarIndex].m_fuelInTank;
        if (m_startFuel < 0) m_startFuel = fuel;
        m_lastFuelLevel = fuel;
    }
    else if (header->m_packetId == 2) {
        auto* packet = reinterpret_cast<PacketLapData*>(buffer);
        float dist = packet->m_lapData[header->m_playerCarIndex].m_totalDistance;

        if (m_startDistance < 0 && dist > 1.0f) m_startDistance = dist;

        if (m_startDistance > 0 && m_startFuel > 0) {
            float traveled = (dist - m_startDistance) / 1000.0f; // Km
            if (traveled > 0.01f) {
                m_consumptionLPerKm = (m_startFuel - m_lastFuelLevel) / traveled;
            }
        }
    }
}

void TelemetryReceiver::loggerWorker() {
    int count = 0;
    while (m_running || !m_dataQueue.empty()) {
        std::unique_lock<std::mutex> lock(m_queueMutex);
        m_cv.wait(lock, [this] { return !m_dataQueue.empty() || !m_running; });
        while (!m_dataQueue.empty()) {
            auto packet = m_dataQueue.front(); m_dataQueue.pop();
            lock.unlock();

            m_logger.logRow(packet.m_header.m_sessionTime, packet.m_carTelemetryData[packet.m_header.m_playerCarIndex]);

            if (++count >= 30) {
                std::cout << "\r[OK] Fuel: " << m_lastFuelLevel << "L | Consumo: " << m_consumptionLPerKm << " L/Km | Perdidos: " << m_packetsLost << "    " << std::flush;
                count = 0;
            }
            lock.lock();
        }
    }
}