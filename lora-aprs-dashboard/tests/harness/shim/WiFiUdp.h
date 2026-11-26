// Captures the datagram the firmware would send.
#pragma once
#include <Arduino.h>
#include <string>
extern std::string g_datagram;
class WiFiUDP {
public:
    void begin(int) {}
    int beginPacket(const char*, int) { g_datagram.clear(); return 1; }
    size_t write(const uint8_t* b, size_t n) { g_datagram.append((const char*)b, n); return n; }
    int endPacket() { return 1; }
};
