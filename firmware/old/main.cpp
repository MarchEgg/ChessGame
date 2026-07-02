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

CRGB leds[NUM_LEDS];

// ---------- Board mapping ----------
// Fill these in from your calibration. [row][col] where [0][0] is top-left
// from your/the white player's perspective. sensorMatrix gives the flat
// sensor index (0-63) under that square; ledMatrix gives the LED index
// under that square.

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

uint8_t squareToSensor[64];
uint8_t squareToLed[64];

bool sensorState[64];
char lastOcc[65];

String inBuf;

// ---------- Forward declarations (required in .cpp) ----------
void mcpWriteRegister(uint8_t addr, uint8_t reg, uint8_t value);
uint8_t mcpReadRegister(uint8_t addr, uint8_t reg);
bool initMCP(uint8_t addr);
void scanModule(uint8_t addr, uint8_t moduleNum);
void buildMaps();
uint32_t parseHexColor(const String& s);
void handleCommand(String line);
void pollSerial();
void reportOccupancyIfChanged();

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

bool initMCP(uint8_t addr) {
    Wire.beginTransmission(addr);
    if (Wire.endTransmission() != 0) return false;
    mcpWriteRegister(addr, MCP_IODIRA, 0xFF);
    mcpWriteRegister(addr, MCP_GPPUA,  0xFF);
    mcpWriteRegister(addr, MCP_IODIRB, 0xFF);
    mcpWriteRegister(addr, MCP_GPPUB,  0xFF);
    return true;
}

void scanModule(uint8_t addr, uint8_t moduleNum) {
    uint8_t gpioA = mcpReadRegister(addr, MCP_GPIOA);
    uint8_t gpioB = mcpReadRegister(addr, MCP_GPIOB);
    uint8_t base = (moduleNum - 1) * 16;
    for (uint8_t i = 0; i < 8; i++) {
        sensorState[base + i]     = !((gpioA >> i) & 0x01);
        sensorState[base + 8 + i] = !((gpioB >> i) & 0x01);
    }
}

// ---------- Mapping setup ----------
void buildMaps() {
    for (uint8_t row = 0; row < 8; row++) {
        for (uint8_t col = 0; col < 8; col++) {
            uint8_t square = row * 8 + col;
            squareToSensor[square] = sensorMatrix[row][col];
            squareToLed[square]    = ledMatrix[row][col];
        }
    }
}

// ---------- Command parsing (from Python) ----------
// Supported commands, one per line:
//   CLEAR              -- turn all LEDs off (in buffer)
//   FILL RRGGBB        -- fill all LEDs with color (hex)
//   LED <sq> RRGGBB    -- set LED at square <sq> (0-63) to color
//   SHOW               -- push buffer to the strip
//   PING               -- reply with READY

uint32_t parseHexColor(const String& s) {
    return (uint32_t) strtoul(s.c_str(), nullptr, 16);
}

void handleCommand(String line) {
    line.trim();
    if (line.length() == 0) return;

    if (line == "CLEAR") {
        fill_solid(leds, NUM_LEDS, CRGB::Black);
    } else if (line == "SHOW") {
        FastLED.show();
    } else if (line == "PING") {
        Serial.println("READY");
    } else if (line.startsWith("FILL ")) {
        uint32_t c = parseHexColor(line.substring(5));
        fill_solid(leds, NUM_LEDS, CRGB(c));
    } else if (line.startsWith("LED ")) {
        int firstSpace = line.indexOf(' ', 4);
        if (firstSpace > 0) {
            int sq = line.substring(4, firstSpace).toInt();
            uint32_t c = parseHexColor(line.substring(firstSpace + 1));
            if (sq >= 0 && sq < 64) {
                leds[squareToLed[sq]] = CRGB(c);
            }
        }
    }
}

void pollSerial() {
    while (Serial.available()) {
        char c = (char)Serial.read();
        if (c == '\n') {
            handleCommand(inBuf);
            inBuf = "";
        } else if (c != '\r') {
            inBuf += c;
            if (inBuf.length() > 120) inBuf = ""; // safety
        }
    }
}

// ---------- Occupancy reporting ----------
void reportOccupancyIfChanged() {
    char occ[65];
    for (uint8_t sq = 0; sq < 64; sq++) {
        occ[sq] = sensorState[squareToSensor[sq]] ? '1' : '0';
    }
    occ[64] = '\0';
    if (strcmp(occ, lastOcc) != 0) {
        strcpy(lastOcc, occ);
        Serial.print("OCC ");
        Serial.println(occ);
    }
}

// ---------- Setup / loop ----------
void setup() {
    Serial.begin(115200);
    delay(500);

    Wire.begin(A4, A5);
    bool ok = true;
    ok &= initMCP(MCP1_ADDRESS);
    ok &= initMCP(MCP2_ADDRESS);
    ok &= initMCP(MCP3_ADDRESS);
    ok &= initMCP(MCP4_ADDRESS);
    if (!ok) {
        Serial.println("ERROR MCP init failed");
        while (1);
    }

    FastLED.addLeds<LED_TYPE, LED_PIN, COLOR_ORDER>(leds, NUM_LEDS);
    FastLED.setBrightness(BRIGHTNESS);
    fill_solid(leds, NUM_LEDS, CRGB::Black);
    FastLED.show();

    buildMaps();
    for (uint8_t i = 0; i < 64; i++) sensorState[i] = false;
    memset(lastOcc, 'x', 64);
    lastOcc[64] = '\0';

    Serial.println("READY");
}

void loop() {
    scanModule(MCP1_ADDRESS, 1);
    scanModule(MCP2_ADDRESS, 2);
    scanModule(MCP3_ADDRESS, 3);
    scanModule(MCP4_ADDRESS, 4);

    reportOccupancyIfChanged();
    pollSerial();

    delay(15); // ~60 Hz
}
