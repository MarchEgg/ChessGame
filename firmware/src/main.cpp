#include <Arduino.h>
#include <Wire.h>
#include <FastLED.h>

// ---------- MCP23017 config ----------
#define MCP1_ADDRESS 0x27
#define MCP2_ADDRESS 0x26
#define MCP3_ADDRESS 0x25
#define MCP4_ADDRESS 0x23

#define MCP_IODIRA   0x00
#define MCP_IODIRB   0x01
#define MCP_GPPUA    0x0C
#define MCP_GPPUB    0x0D
#define MCP_GPIOA    0x12
#define MCP_GPIOB    0x13

// ---------- LED config ----------
#define LED_PIN     5
#define NUM_LEDS    166
#define BRIGHTNESS  64
#define LED_TYPE    WS2812B
#define COLOR_ORDER GRB
#define LED_COLOR   CRGB::Green

CRGB leds[NUM_LEDS];

// ---------- Board mapping ----------
// Both matrices are laid out as [row][col], where [0][0] is the top-left
// square of the board as you see it. Fill in with your measured values.
//
// sensorMatrix[row][col] = sensor index (0-63) under that square
// ledMatrix[row][col]    = LED index (0-63) under that square

const uint8_t sensorMatrix[8][8] = {
    { 1,  3,  5,  7,  17,  19,  21,  22},
    { 0,  2,  4,  6,  16,  18,  20,  23},
    { 15, 13, 11, 9,  30,  29,  27,  25},
    { 14, 12, 10, 8,  31,  28,  26,  24},
    { 56, 58, 60, 62, 40,  42,  44,  46},
    { 57, 59, 61, 63, 41,  43,  45,  47},
    { 54, 52, 50, 48, 39,  36,  34,  32},
    { 55, 53, 51, 49, 38,  37,  35,  33}
};

const uint8_t ledMatrix[8][8] = {
    { 0,  33,  34,  77,  78,  131,  132,  165 },
    { 2,  31,  36,  73,  81,  127,  134,  163 },
    { 5,  28,  39,  69,  85,  123,  136,  160 },
    { 7,  26,  41,  65,  89,  120,  139,  158 },
    { 9,  24,  43,  62,  93,  116,  141,  156 },
    { 12, 21,  46,  58,  97,  112,  143,  153 },
    { 14, 19,  48,  54,  100, 108,  146,  151 },
    { 16, 17,  50,  51,  104, 105,  148,  149 }
};

// Built at startup: sensorToLed[sensorIndex] = LED index for that sensor
uint8_t sensorToLed[64];

// Current state of each sensor (true = magnet present)
bool sensorState[64];

// ---------- MCP23017 helpers ----------
void mcpWriteRegister(uint8_t addr, uint8_t reg, uint8_t value) {
    Wire.beginTransmission(addr);
    Wire.write(reg);
    Wire.write(value);
    Wire.endTransmission();
}

uint8_t mcpReadRegister(uint8_t addr, uint8_t reg) {
    Wire.beginTransmission(addr);
    Wire.write(reg);
    Wire.endTransmission();
    Wire.requestFrom(addr, (uint8_t)1);
    return Wire.read();
}

bool initMCP(uint8_t addr, const char* name) {
    Wire.beginTransmission(addr);
    if (Wire.endTransmission() != 0) {
        Serial.print("ERROR: ");
        Serial.print(name);
        Serial.println(" not found!");
        return false;
    }
    Serial.print(name);
    Serial.println(" found!");
    mcpWriteRegister(addr, MCP_IODIRA, 0xFF);
    mcpWriteRegister(addr, MCP_GPPUA,  0xFF);
    mcpWriteRegister(addr, MCP_IODIRB, 0xFF);
    mcpWriteRegister(addr, MCP_GPPUB,  0xFF);
    return true;
}

// Read all 16 inputs from a module and update sensorState[] for those sensors.
void scanModule(uint8_t addr, uint8_t moduleNum) {
    uint8_t gpioA = mcpReadRegister(addr, MCP_GPIOA);
    uint8_t gpioB = mcpReadRegister(addr, MCP_GPIOB);
    uint8_t base = (moduleNum - 1) * 16;
    for (uint8_t i = 0; i < 8; i++) {
        sensorState[base + i]     = !((gpioA >> i) & 0x01);
        sensorState[base + 8 + i] = !((gpioB >> i) & 0x01);
    }
}

// ---------- Mapping ----------
void buildSensorToLed() {
    for (uint8_t row = 0; row < 8; row++) {
        for (uint8_t col = 0; col < 8; col++) {
            uint8_t s = sensorMatrix[row][col];
            uint8_t l = ledMatrix[row][col];
            sensorToLed[s] = l;
        }
    }
}

// ---------- Setup / loop ----------
void setup() {
    Serial.begin(115200);
    delay(1000);
    Serial.println("Starting chessboard sensor + LED system...");

    Wire.begin(A4, A5);
    bool ok = true;
    ok &= initMCP(MCP1_ADDRESS, "Module 1 (0x27)");
    ok &= initMCP(MCP2_ADDRESS, "Module 2 (0x26)");
    ok &= initMCP(MCP3_ADDRESS, "Module 3 (0x25)");
    ok &= initMCP(MCP4_ADDRESS, "Module 4 (0x24)");
    if (!ok) {
        Serial.println("One or more modules missing. Halting.");
        while (1);
    }

    FastLED.addLeds<LED_TYPE, LED_PIN, COLOR_ORDER>(leds, NUM_LEDS);
    FastLED.setBrightness(BRIGHTNESS);
    fill_solid(leds, NUM_LEDS, CRGB::Black);
    FastLED.show();

    buildSensorToLed();
    for (uint8_t i = 0; i < 64; i++) sensorState[i] = false;

    Serial.println("Ready.");
    Serial.println("------------------------------------------");
}

void loop() {
    scanModule(MCP1_ADDRESS, 1);
    scanModule(MCP2_ADDRESS, 2);
    scanModule(MCP3_ADDRESS, 3);
    scanModule(MCP4_ADDRESS, 4);

    fill_solid(leds, NUM_LEDS, CRGB::Black);
    for (uint8_t s = 0; s < 64; s++) {
        if (sensorState[s]) {
            leds[sensorToLed[s]] = LED_COLOR;
        }
    }
    FastLED.show();

    delay(20);
}