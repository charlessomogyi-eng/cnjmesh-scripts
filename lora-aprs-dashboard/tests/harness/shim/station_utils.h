#pragma once
#include <Arduino.h>
struct LastHeardStation { uint32_t lastHeardTime; String station; };
namespace STATION_Utils {
    bool isIn25SegHashBuffer(const String&, const String&);
    void updateLastHeard(const String&);
    void addToOutputPacketBuffer(const String&, bool flag = false);
}
