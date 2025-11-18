# EEPROM Layout Editor

The EEPROM Layout Editor is a cross-platform (Linux + Windows) desktop application built with **Python** and **PyQt6**. It allows engineers and developers to **view, edit, and validate EEPROM binary files** based on a fixed, packed memory layout defined in a C header file.

The application reads the EEPROM struct definitions directly from the header file, interprets binary data from `.bin` files, displays it in a structured GUI, and allows users to modify values and export updated binaries.

## Features

- Parse C header files with packed struct definitions
- Support for hierarchical nested structs
- Display EEPROM layout in an interactive tree view
- Edit field values with type-appropriate editors
- Hex editor for byte arrays
- Save modified data back to binary files
- Cross-platform support (Linux and Windows)

## Installation

### Prerequisites

- Python 3.8 or higher
- pip package manager

### Install Dependencies

```bash
pip install -r requirements.txt
```

## Usage

### Running the Application

```bash
python main.py
```

### Workflow

1. **Open Header File**: File → Open Header...
   - Select your C header file containing packed struct definitions
   - The application will parse the structs and calculate offsets

2. **Open Binary File**: File → Open BIN...
   - Select your `.bin` EEPROM file
   - The data will be parsed according to the header schema

3. **Navigate and Edit**:
   - Use the tree view (left pane) to navigate struct hierarchy
   - Click on a struct to view its fields in the table (right pane)
   - Double-click on a field value to edit it

4. **Save Changes**: File → Save BIN As...
   - Export the modified data to a new binary file

### Example

Sample files are provided in the `examples/` directory:

1. Generate a sample binary file:
```bash
cd examples
python generate_sample_bin.py
```

2. Open the application:
```bash
python main.py
```

3. Load `examples/sample_eeprom.h` (File → Open Header)
4. Load `examples/sample_eeprom.bin` (File → Open BIN)
5. Edit values and save changes

## Header File Format

The application expects C header files with the following format:

```c
typedef struct __attribute__((__packed__)) {
    uint8_t field1;
    uint16_t field2;
    uint32_t field3;
    char name[32];
    NestedStructType nested;
} MyStructType;
```

### Supported Types

- **Primitive types**: `uint8_t`, `uint16_t`, `uint32_t`, `int8_t`, `int16_t`, `int32_t`, `char`
- **Arrays**: Fixed-size arrays of any supported type (e.g., `uint8_t data[256]`)
- **Nested structs**: Structs containing other structs
- **Struct arrays**: Arrays of structs

### Requirements

- All structs must use `__attribute__((__packed__))`
- Little-endian byte order is assumed
- No unions or bitfields support

## Project Structure

```
EepromTool/
├── src/
│   ├── core/
│   │   ├── schema.py          # Data structure definitions
│   │   ├── header_parser.py   # C header file parser
│   │   ├── binary_parser.py   # Binary file decoder
│   │   ├── encoder.py         # Binary file encoder
│   │   └── model.py           # Qt data models
│   └── ui/
│       ├── main_window.py     # Main application window
│       └── editors.py         # Field editor dialogs
├── examples/
│   ├── sample_eeprom.h        # Sample header file
│   └── generate_sample_bin.py # Sample binary generator
├── main.py                    # Application entry point
├── requirements.txt           # Python dependencies
│
├── Documentation:
├── README.md                  # This file - User quick start
├── QUICKSTART.md              # 5-minute getting started guide
├── PRD.md                     # Product requirements document
├── SoftwareDoc.md             # Comprehensive software documentation
├── TECHNICAL_GUIDE.md         # Deep technical implementation guide
├── ARCHITECTURE.md            # System architecture and design patterns
└── CHANGELOG.md               # Version history and changes
```

## Development

### Running Tests

Tests can be performed using the sample files:

```bash
cd examples
python generate_sample_bin.py
cd ..
python main.py
```

### Extending the Application

- **Adding new field types**: Extend `PrimitiveType` enum in `src/core/schema.py`
- **Custom editors**: Add new editor widgets in `src/ui/editors.py`
- **Validation rules**: Modify `encoder.py` validation methods

## Troubleshooting

### Binary file size mismatch
If the binary file size doesn't match the expected size from the header, the application will warn you but allow you to continue. Check your header file struct definitions.

### Parse errors
Ensure your header file uses the exact format with `__attribute__((__packed__))` and supported types.

### Value out of range
The encoder will automatically clamp values to valid ranges for the field type and display a warning.

## Documentation

### For Users
- **[README.md](README.md)** (this file) - Quick start guide for end users
- **[QUICKSTART.md](QUICKSTART.md)** - 5-minute tutorial with examples
- **[PRD.md](PRD.md)** - Product requirements and specifications

### For Developers
- **[SoftwareDoc.md](SoftwareDoc.md)** - Comprehensive software documentation
  - High-level overview
  - Developer's guide
  - System architecture & APIs
  - Maintenance and handover plan
- **[TECHNICAL_GUIDE.md](TECHNICAL_GUIDE.md)** - Deep technical implementation guide
  - Module implementation details
  - Data flow and algorithms
  - Extension points
  - Testing guidelines
- **[ARCHITECTURE.md](ARCHITECTURE.md)** - System architecture
  - Architecture patterns
  - Component diagrams
  - Design decisions
  - Deployment architecture
- **[CHANGELOG.md](CHANGELOG.md)** - Version history and release notes

## License

See project documentation for license information.

## Contributing

Contributions are welcome! Please ensure all changes maintain cross-platform compatibility. Before contributing:

1. Read [SoftwareDoc.md](SoftwareDoc.md) for development guidelines
2. Review [TECHNICAL_GUIDE.md](TECHNICAL_GUIDE.md) for implementation details
3. Follow the coding standards defined in the documentation
4. Update [CHANGELOG.md](CHANGELOG.md) with your changes
