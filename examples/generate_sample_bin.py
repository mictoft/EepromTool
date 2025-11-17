#!/usr/bin/env python3
"""
Generate a sample EEPROM binary file for testing.
"""
import struct


def generate_sample_eeprom():
    """Generate a sample 32 KB EEPROM binary file."""
    data = bytearray(32768)  # 32 KB
    offset = 0

    # DeviceConfigType (10 bytes)
    struct.pack_into('<H', data, offset, 0x1234)  # deviceId
    offset += 2
    struct.pack_into('<B', data, offset, 1)  # firmwareVersion
    offset += 1
    struct.pack_into('<B', data, offset, 2)  # hardwareVersion
    offset += 1
    struct.pack_into('<I', data, offset, 12345678)  # serialNumber
    offset += 4

    # CalibrationDataType (10 bytes)
    struct.pack_into('<H', data, offset, 100)  # offsetX
    offset += 2
    struct.pack_into('<H', data, offset, 200)  # offsetY
    offset += 2
    struct.pack_into('<H', data, offset, 1000)  # gainX
    offset += 2
    struct.pack_into('<H', data, offset, 2000)  # gainY
    offset += 2
    struct.pack_into('<h', data, offset, -50)  # temperatureCoeff (signed)
    offset += 2

    # UserSettingsType (36 bytes)
    struct.pack_into('<B', data, offset, 75)  # brightness
    offset += 1
    struct.pack_into('<B', data, offset, 50)  # contrast
    offset += 1
    struct.pack_into('<B', data, offset, 60)  # volume
    offset += 1
    struct.pack_into('<B', data, offset, 0)  # language
    offset += 1

    # userName (32 bytes char array)
    user_name = b"Test User"
    data[offset:offset + len(user_name)] = user_name
    offset += 32

    # Rest is reserved (already zeroed in bytearray)

    # Write to file
    with open('sample_eeprom.bin', 'wb') as f:
        f.write(data)

    print(f"Generated sample_eeprom.bin ({len(data)} bytes)")
    print(f"DeviceId: 0x1234")
    print(f"FirmwareVersion: 1")
    print(f"SerialNumber: 12345678")
    print(f"UserName: Test User")


if __name__ == "__main__":
    generate_sample_eeprom()
