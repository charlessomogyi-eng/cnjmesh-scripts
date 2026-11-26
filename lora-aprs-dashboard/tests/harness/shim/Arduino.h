// Minimal host stand-in for Arduino.h, just enough to compile the firmware
// files used by the test harness. Not part of the firmware.
#pragma once
#include <stdint.h>
#include <stddef.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <ctype.h>
#include <vector>
#include <pgmspace.h>
#include "WString.h"

typedef uint8_t byte;
#define PI 3.1415926535897932384626433832795
#define TWO_PI 6.283185307179586476925286766559
#define DEG_TO_RAD 0.017453292519943295769236907684886
#define RAD_TO_DEG 57.295779513082320876798154814105
#define radians(deg) ((deg) * DEG_TO_RAD)
#define degrees(rad) ((rad) * RAD_TO_DEG)
#define sq(x) ((x) * (x))
inline unsigned long millis() { return 100000UL; }
inline void delay(unsigned long) {}

struct HostSerial {
    template <class T> void print(const T&) {}
    template <class T> void println(const T&) {}
    void println() {}
};
extern HostSerial Serial;
class HardwareSerial {
public:
    int available() { return 0; }
    int read() { return -1; }
    void begin(...) {}
};
