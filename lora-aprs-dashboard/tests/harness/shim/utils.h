#pragma once
#include <Arduino.h>
namespace Utils {
    bool callsignIsValid(const String&);
    void typeOfPacket(const String&, uint8_t);
    void println(const String&);
    void print(const String&);
}
