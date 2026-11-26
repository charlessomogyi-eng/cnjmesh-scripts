// Stand-in for PubSubClient 2.8. publish() applies the same size limit as the
// real library (MQTT_MAX_PACKET_SIZE 256, MQTT_MAX_HEADER_SIZE 5) and captures
// what would be sent.
#pragma once
#include <Arduino.h>
#include <string>
#include "WiFiClient.h"
typedef unsigned char byte;
extern std::string g_topic, g_payload;
extern bool g_published;
class PubSubClient {
public:
    bool connected() { return true; }
    bool publish(const char* topic, const char* payload) {
        size_t plen = strlen(payload);
        if (256 < 5 + 2 + strlen(topic) + plen) return false;
        g_topic = topic; g_payload = payload; g_published = true;
        return true;
    }
    void setClient(WiFiClient&) {}
    void setCallback(void (*)(char*, byte*, unsigned int)) {}
    void setServer(const char*, int) {}
    bool connect(const char*) { return true; }
    bool connect(const char*, const char*, const char*) { return true; }
    bool subscribe(const char*) { return true; }
    void loop() {}
};
