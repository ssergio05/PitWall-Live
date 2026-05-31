#pragma once
#include <cstdint>

#pragma pack(push, 1)
struct PacketHeader {
    uint16_t m_packetFormat; uint8_t m_gameYear; uint8_t m_gameMajorVersion;
    uint8_t m_gameMinorVersion; uint8_t m_packetVersion; uint8_t m_packetId;
    uint64_t m_sessionUID; float m_sessionTime; uint32_t m_frameIdentifier;
    uint32_t m_overallFrameIdentifier; uint8_t m_playerCarIndex; uint8_t m_secondaryPlayerCarIndex;
};

struct CarTelemetryData {
    uint16_t m_speed; float m_throttle; int8_t m_steer; float m_brake;
    uint8_t m_clutch; int8_t m_gear; uint16_t m_engineRPM; uint8_t m_drs;
    uint8_t m_revLightsPercent; uint16_t m_revLightsBitValue; uint16_t m_brakesTemperature[4];
    uint8_t m_tyresSurfaceTemperature[4]; uint8_t m_tyresInnerTemperature[4];
    uint16_t m_engineTemperature; float m_tyresPressure[4]; uint8_t m_surfaceType[4];
};

struct PacketCarTelemetryData {
    PacketHeader m_header;
    CarTelemetryData m_carTelemetryData[22];
    uint8_t m_mfdPanelIndex; uint8_t m_mfdPanelIndexSecondaryPlayer; int8_t m_suggestedGear;
};

struct LapData {
    uint32_t m_lastLapTimeInMS;
    uint32_t m_currentLapTimeInMS;
    float    m_lapDistance;
    float    m_totalDistance;
    uint8_t  m_unused[97];
};

struct PacketLapData {
    PacketHeader m_header;
    LapData      m_lapData[22];
};

struct CarStatusData {
    uint8_t m_tractionControl; uint8_t m_antiLockBrakes; uint8_t m_fuelMix;
    uint8_t m_frontBrakeBias; uint8_t m_pitLimiterStatus;
    float   m_fuelInTank; float m_fuelCapacity;
    uint16_t m_fuelRemainingLaps; uint16_t m_maxRPM; uint16_t m_idleRPM;
    uint8_t m_maxGears; uint8_t m_drsAllowed;
};

struct PacketCarStatusData {
    PacketHeader m_header;
    CarStatusData m_carStatusData[22];
};
#pragma pack(pop)