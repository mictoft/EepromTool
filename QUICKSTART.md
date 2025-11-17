# Quick Start Guide

Get up and running with the EEPROM Layout Editor in 5 minutes.

## 1. Install Dependencies

```bash
pip install -r requirements.txt
```

## 2. Try the Example

### Generate Sample Data

```bash
cd examples
python generate_sample_bin.py
cd ..
```

This creates `examples/sample_eeprom.bin` - a 32KB EEPROM binary file with sample data.

### Run the Application

```bash
python main.py
```

### Load and Edit

1. Click **File → Open Header...**
   - Select `examples/sample_eeprom.h`
   - You should see a success message showing the parsed schema

2. Click **File → Open BIN...**
   - Select `examples/sample_eeprom.bin`
   - The tree view will populate with the EEPROM structure

3. **Navigate the Structure**:
   - Click `EepromMemoryMapType` in the tree
   - You'll see the main struct fields in the table
   - Click `deviceConfig` to see device configuration fields
   - Click `userSettings` to see user settings

4. **Edit a Value**:
   - Click on `deviceConfig` in the tree
   - In the table, find the `deviceId` field (currently `4660` or `0x1234`)
   - Double-click the value
   - Change it to a new value (e.g., `5000`)
   - Click OK

5. **Edit a String**:
   - Click on `userSettings` in the tree
   - Find the `userName` field
   - Double-click to edit
   - Enter a new name
   - Click OK

6. **Save Your Changes**:
   - Click **File → Save BIN As...**
   - Choose a location (e.g., `my_modified.bin`)
   - Click Save

## 3. Use with Your Own Files

### Prepare Your Header File

Ensure your C header file follows this format:

```c
typedef struct __attribute__((__packed__)) {
    uint8_t myField;
    uint16_t myValue;
    char myString[32];
} MyStructType;
```

### Load and Edit

1. Open your header file: **File → Open Header...**
2. Open your binary file: **File → Open BIN...**
3. Navigate, edit, and save as needed

## Field Types

### Simple Values (Double-click to edit)
- **uint8_t, uint16_t, uint32_t**: Integer spin box
- **int8_t, int16_t, int32_t**: Signed integer spin box
- **char**: Single character input

### Arrays (Double-click to edit)
- **char[]**: String editor
- **uint8_t[]**: Hex editor with "Load from File" option
- **Other arrays**: Comma-separated value editor

### Structs (Click in tree to navigate)
- Navigate to the struct in the tree view
- View and edit individual fields

## Keyboard Shortcuts

- **File → Open Header**: Open and parse a C header file
- **File → Open BIN**: Load a binary file
- **File → Save BIN As**: Export modified binary
- **View → Reload**: Reload the current binary file
- **Help → About**: Application information

## Tips

1. **Always load the header first**, then the binary
2. **Check the status bar** for confirmation messages
3. **Size mismatches**: If your binary size doesn't match the header, check your struct definitions
4. **Unsaved changes**: The app will warn you when closing with unsaved changes
5. **Validation**: Values are automatically clamped to valid ranges for their types

## Troubleshooting

### "No struct definitions found"
- Check that your structs use `__attribute__((__packed__))`
- Ensure proper typedef syntax

### "Binary file size mismatch"
- Verify your struct sizes add up correctly
- Check for missing padding fields

### Values not saving
- Make sure to click OK in the editor dialog
- Use File → Save BIN As to export changes

## What's Next?

- Read the full [README.md](README.md) for detailed documentation
- Check [PRD.md](PRD.md) for technical specifications
- Modify the example header and binary to experiment
- Create your own EEPROM layouts

## Support

For issues, feature requests, or questions, please refer to the main README.md file.
