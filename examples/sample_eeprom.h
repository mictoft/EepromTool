/**
 * Sample EEPROM Memory Layout Header
 * This is an example header file showing the expected format.
 */

#ifndef EEPROM_MEM_LAYOUT_H
#define EEPROM_MEM_LAYOUT_H

#include <stdint.h>

// Configuration struct for device settings
typedef struct __attribute__((__packed__)) {
    uint16_t deviceId;
    uint8_t firmwareVersion;
    uint8_t hardwareVersion;
    uint32_t serialNumber;
} DeviceConfigType;

// Calibration data struct
typedef struct __attribute__((__packed__)) {
    uint16_t offsetX;
    uint16_t offsetY;
    uint16_t gainX;
    uint16_t gainY;
    int16_t temperatureCoeff;
} CalibrationDataType;

// User settings struct
typedef struct __attribute__((__packed__)) {
    uint8_t brightness;
    uint8_t contrast;
    uint8_t volume;
    uint8_t language;
    char userName[32];
} UserSettingsType;

// Main EEPROM memory map (32 KB = 32768 bytes)
typedef struct __attribute__((__packed__)) {
    DeviceConfigType deviceConfig;       // 8 bytes
    CalibrationDataType calibration;     // 10 bytes
    UserSettingsType userSettings;       // 36 bytes
    uint8_t reserved[32714];             // Pad to 32 KB total (32768 - 54 = 32714)
} EepromMemoryMapType;

#endif // EEPROM_MEM_LAYOUT_H
