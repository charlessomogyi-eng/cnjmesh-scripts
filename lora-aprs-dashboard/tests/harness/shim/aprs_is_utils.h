#pragma once
#include <Arduino.h>
namespace APRS_IS_Utils {
    String checkForStartingBytes(const String&);
    bool processReceivedLoRaMessage(const String&, const String&, bool);
}
