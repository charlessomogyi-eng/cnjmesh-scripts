// Test harness: runs the real CA2RXU LoRa APRS iGate 3.2.4 code on a PC to
// produce the exact bytes the iGate would put on syslog and MQTT.
//
// Compiled unchanged from upstream: syslog_utils.cpp, mqtt_utils.cpp,
// gps_utils.cpp, digi_utils.cpp, plus the ESP32 Arduino String class,
// APRSPacketLib and TinyGPS++. Everything else is a stub in shim/.
//
// stdin, one case per line:  <op> <rssi> <snr> <freqerr> <hex of packet bytes>
//   op = rx    bytes are the on-air frame (including the 3 byte LoRa APRS header)
//   op = crc   same, but received with a CRC error
//   op = tx    bytes are the text the iGate transmits (no header)
//   op = digi  bytes are the on-air frame; prints what the digipeater would send
// stdout, one line per case:
//   <hex syslog datagram|-> <hex mqtt topic|-> <hex mqtt payload|-> <hex digi packet|->
#include <iostream>
#include <string>
#include "configuration.h"
#include "network_manager.h"
#include "syslog_utils.h"
#include "mqtt_utils.h"
#include "digi_utils.h"
#include "gps_utils.h"
#include "station_utils.h"
#include <PubSubClient.h>
#include <WiFiUdp.h>

HostSerial Serial;
std::string g_datagram, g_topic, g_payload;
bool g_published = false;

Configuration Config;
NetworkManager nm;
NetworkManager* networkManager = &nm;
WiFiClient mqttClient;
HardwareSerial gpsSerial;
#include <TinyGPS++.h>
TinyGPSPlus gps;
bool stationCallsignIsValid = true;
bool backupDigiMode = false;
uint32_t lastScreenOn = 0;
String versionDate = "2026-04-21";
String versionNumber = "3.2.4";
String iGateBeaconPacket_unused;
String firstLine, secondLine, thirdLine, fourthLine, fifthLine, sixthLine, seventhLine;

void displayToggle(bool) {}
namespace Utils {
    bool callsignIsValid(const String&) { return true; }
    void typeOfPacket(const String&, uint8_t) {}
    void println(const String&) {}
    void print(const String&) {}
}
namespace STATION_Utils {
    bool isIn25SegHashBuffer(const String&, const String&) { return false; }
    void updateLastHeard(const String&) {}
    void addToOutputPacketBuffer(const String&, bool) {}
}
namespace APRS_IS_Utils {
    // same logic as aprs_is_utils.cpp
    String checkForStartingBytes(const String& packet) {
        int index = packet.indexOf("\x3c\xff\x01");
        return (index != -1) ? packet.substring(0, index) : packet;
    }
    bool processReceivedLoRaMessage(const String&, const String&, bool) { return false; }
}

static std::string unhex(const std::string& h) {
    std::string o;
    for (size_t i = 0; i + 1 < h.size(); i += 2) o += (char)std::stoi(h.substr(i, 2), nullptr, 16);
    return o;
}
static std::string hex(const std::string& s) {
    if (s.empty()) return "-";
    static const char* d = "0123456789abcdef";
    std::string o;
    for (unsigned char c : s) { o += d[c >> 4]; o += d[c & 15]; }
    return o;
}

int main(int argc, char** argv) {
    if (argc != 4) { std::cerr << "usage: harness CALLSIGN LAT LON\n"; return 2; }
    Config.callsign = argv[1];
    Config.beacon.latitude = atof(argv[2]);
    Config.beacon.longitude = atof(argv[3]);
    Config.syslog.active = true; Config.syslog.server = "127.0.0.1"; Config.syslog.port = 1514;
    Config.mqtt.active = true; Config.mqtt.topic = "aprs-k2gia-10";
    Config.digi.mode = 3;                       // "WIDE2 (+WIDE1) Digi"
    Config.loramodule.txFreq = Config.loramodule.rxFreq = 433775000;

    std::string op, h; int rssi, ferr; float snr;
    while (std::cin >> op >> rssi >> snr >> ferr >> h) {
        std::string bytes = unhex(h);
        // RadioLib 7.6.0 builds the String from a NUL terminated buffer
        String packet(bytes.c_str());
        g_datagram.clear(); g_topic.clear(); g_payload.clear(); g_published = false;
        std::string digi;
        if (op == "rx") {
            SYSLOG_Utils::log(1, packet, rssi, snr, ferr);
            MQTT_Utils::sendToMqtt(packet);
        } else if (op == "crc") {
            SYSLOG_Utils::log(0, packet, rssi, snr, ferr);
        } else if (op == "tx") {
            SYSLOG_Utils::log(3, packet, 0, 0.0, 0);
        } else if (op == "digi") {
            String out = DIGI_Utils::generateDigipeatedPacket(packet.substring(3), false);
            digi = out.c_str();
        }
        std::cout << hex(g_datagram) << ' ' << hex(g_published ? g_topic : "") << ' '
                  << hex(g_published ? g_payload : "") << ' ' << hex(digi) << std::endl;
    }
}
