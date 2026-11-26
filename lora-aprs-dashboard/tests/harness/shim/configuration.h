// Only the Configuration fields that the compiled firmware files read.
#pragma once
#include <Arduino.h>

class Configuration {
public:
    String callsign;
    String tacticalCallsign;
    struct { bool active; String server; int port; bool logBeaconOverTCPIP; } syslog;
    struct { bool active; String server; String topic; String username; String password; int port; } mqtt;
    struct { double latitude; double longitude; String path; String symbol; String overlay;
             int ambiguityLevel; bool sendViaRF; bool sendViaAPRSIS; int beaconFreq; bool gpsActive; } beacon;
    struct { int mode; int ecoMode; bool backupDigiMode; } digi;
    struct { long txFreq; long rxFreq; bool txActive; } loramodule;
    struct { bool active; bool messagesToRF; bool objectsToRF; } aprs_is;
};
