# EEPROM Layout Editor - Software Documentation

**Version:** 1.0
**Last Updated:** 2025-11-17
**Project Type:** Cross-Platform Desktop Application
**Primary Language:** Python 3.8+

---

## Table of Contents

1. [High-Level Overview](#1-high-level-overview)
2. [Developer's Guide](#2-developers-guide)
3. [System Architecture & Internal APIs](#3-system-architecture--internal-apis)
4. [Handover & Maintenance Plan](#4-handover--maintenance-plan)

---

## 1. High-Level Overview

### 1.1 Project Purpose

**Problem Statement:**
Embedded systems engineers need to view, edit, and validate EEPROM binary files based on complex packed C struct layouts. Manual hex editing is error-prone and time-consuming. Existing tools don't support automatic parsing of C header files or hierarchical struct navigation.

**Solution:**
The EEPROM Layout Editor is a desktop GUI application that:
- Automatically parses C header files containing packed struct definitions
- Interprets binary EEPROM files based on the parsed schema
- Provides an intuitive tree/table interface for navigating and editing values
- Validates data types and re-encodes modified values back to binary format

**Target Users:**
- Embedded systems engineers
- QA/Test engineers working with firmware
- Field application engineers
- Hardware developers managing device configuration storage

### 1.2 Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                         USER INTERFACE (PyQt6)                  │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────┐ │
│  │  Main Window     │  │  Field Editors   │  │  Dialogs     │ │
│  │  - Tree View     │  │  - Spin Boxes    │  │  - File Open │ │
│  │  - Table View    │  │  - Hex Editor    │  │  - Messages  │ │
│  └────────┬─────────┘  └────────┬─────────┘  └──────────────┘ │
└───────────┼────────────────────┼─────────────────────────────┘
            │                    │
            └────────┬───────────┘
                     │
            ┌────────▼────────────────────────┐
            │   DATA MODEL (Qt Models)        │
            │   - EepromDataModel             │
            │   - FieldTableModel             │
            └────────┬────────────────────────┘
                     │
            ┌────────▼────────────────────────┐
            │   CORE LOGIC                    │
            │  ┌──────────────────────────┐   │
            │  │  Header Parser           │   │
            │  │  (Regex-based C parser)  │   │
            │  └──────────┬───────────────┘   │
            │             │                    │
            │  ┌──────────▼───────────────┐   │
            │  │  Schema (Data Structure) │   │
            │  │  - StructDef             │   │
            │  │  - FieldDef              │   │
            │  └──────────┬───────────────┘   │
            │             │                    │
            │  ┌──────────▼───────────────┐   │
            │  │  Binary Parser           │   │
            │  │  (struct.unpack)         │   │
            │  └──────────┬───────────────┘   │
            │             │                    │
            │  ┌──────────▼───────────────┐   │
            │  │  Binary Encoder          │   │
            │  │  (struct.pack)           │   │
            │  └──────────────────────────┘   │
            └─────────────────────────────────┘
                     │
            ┌────────▼────────────────────────┐
            │   FILE SYSTEM                   │
            │   - .h header files (input)     │
            │   - .bin binary files (I/O)     │
            └─────────────────────────────────┘
```

**Data Flow:**

1. **Load Phase:**
   - User opens `.h` header file → Header Parser → Schema (in-memory struct definitions)
   - User opens `.bin` file → Binary Parser + Schema → Data Model (Python dicts/lists)

2. **Display Phase:**
   - Data Model → Qt Table/Tree Models → UI Widgets

3. **Edit Phase:**
   - User edits value in UI → Field Editor → Data Model (modified in place)

4. **Save Phase:**
   - Data Model → Binary Encoder + Schema → `.bin` file written to disk

### 1.3 Technology Stack

| Component | Technology | Version | Purpose |
|-----------|-----------|---------|---------|
| **Language** | Python | 3.8+ | Core application logic |
| **GUI Framework** | PyQt6 | 6.4.0+ | Cross-platform desktop UI |
| **Binary Parsing** | struct (stdlib) | - | Pack/unpack binary data |
| **Regex** | re (stdlib) | - | C header file parsing |
| **Data Classes** | dataclasses (stdlib) | - | Schema definitions |
| **Version Control** | Git | - | Source control |

**External Dependencies:**
- `PyQt6` - Only external dependency (see `requirements.txt`)

**Platform Support:**
- Linux (primary development platform)
- Windows (fully supported via PyQt6)
- macOS (should work but untested)

### 1.4 Key Features

✅ **Implemented:**
- C header file parsing (packed structs only)
- Hierarchical struct navigation
- Support for nested structs and arrays
- Type-safe editing with validation
- Binary encoding/decoding (little-endian)
- Hex editor for byte arrays
- File size validation
- Cross-platform desktop GUI

❌ **Out of Scope (v1.0):**
- Unions and bitfields
- Encryption/decryption
- Real-time device flashing
- Command-line interface
- Big-endian support
- Undo/redo functionality

---

## 2. Developer's Guide

### 2.1 Detailed Setup

#### Prerequisites

- **Python 3.8 or higher** (verify: `python --version`)
- **pip** package manager
- **Qt6 runtime libraries** (usually auto-installed with PyQt6)
- **Git** for version control

#### Initial Setup

```bash
# Clone the repository
git clone <repository-url>
cd EepromTool

# Create a virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Generate sample data for testing
cd examples
python generate_sample_bin.py
cd ..

# Run the application
python main.py
```

#### Development Environment Variables

No environment variables are required. All configuration is file-based.

#### IDE Recommendations

- **VS Code** with Python extension
- **PyCharm** (Community or Professional)
- **Sublime Text** with Python plugins

**Recommended VS Code Extensions:**
- Python (Microsoft)
- Pylance
- Python Docstring Generator

### 2.2 Coding Standards

#### Style Guide

This project follows **PEP 8** Python style guide with the following specifics:

- **Line Length:** 100 characters (soft limit), 120 (hard limit)
- **Indentation:** 4 spaces (no tabs)
- **Quotes:** Single quotes for strings, double quotes for docstrings
- **Imports:** Grouped by stdlib, third-party, local (separated by blank lines)
- **Naming Conventions:**
  - Classes: `PascalCase` (e.g., `HeaderParser`)
  - Functions/Methods: `snake_case` (e.g., `parse_header()`)
  - Constants: `UPPER_SNAKE_CASE` (e.g., `MAX_FILE_SIZE`)
  - Private methods: prefix with `_` (e.g., `_parse_field()`)

#### Docstring Format

```python
def parse_field(self, line: str, offset: int) -> Optional[FieldDef]:
    """
    Parse a single field declaration from C struct.

    Args:
        line: The field declaration line (e.g., "uint8_t myField")
        offset: Current offset in bytes within the struct

    Returns:
        FieldDef object if parsed successfully, None if parsing fails

    Example:
        >>> parser._parse_field("uint16_t deviceId", 0)
        FieldDef(name='deviceId', type_name='uint16_t', size=2, offset=0)
    """
```

#### Type Hints

- Use type hints for all function signatures
- Use `Optional[T]` for nullable returns
- Use `Union[T1, T2]` for multiple return types
- Use `List`, `Dict`, etc. from `typing` module

### 2.3 Source Code Structure

```
EepromTool/
├── src/                          # All source code
│   ├── __init__.py              # Package marker
│   ├── core/                    # Core business logic (no UI)
│   │   ├── __init__.py
│   │   ├── schema.py            # Data structure definitions (StructDef, FieldDef, etc.)
│   │   ├── header_parser.py     # C header file parser (regex-based)
│   │   ├── binary_parser.py     # Binary file decoder (reads .bin → Python objects)
│   │   ├── encoder.py           # Binary file encoder (Python objects → .bin)
│   │   └── model.py             # Qt data models (EepromDataModel, FieldTableModel)
│   └── ui/                      # User interface components
│       ├── __init__.py
│       ├── main_window.py       # Main application window (tree + table layout)
│       └── editors.py           # Field editor dialogs (spinbox, hex editor, etc.)
├── examples/                    # Sample files for testing
│   ├── sample_eeprom.h          # Example C header file (32KB EEPROM layout)
│   ├── sample_eeprom.bin        # Generated sample binary (created by script)
│   └── generate_sample_bin.py   # Script to generate test binary
├── main.py                      # Application entry point (launches PyQt6 app)
├── requirements.txt             # Python dependencies (PyQt6)
├── .gitignore                   # Git ignore patterns
├── README.md                    # User-facing documentation
├── QUICKSTART.md                # Quick start guide
├── PRD.md                       # Product Requirements Document
└── SoftwareDoc.md               # This file
```

#### Module Responsibilities

**`src/core/schema.py`**
Defines the internal representation of EEPROM structures. No file I/O or UI logic.

- `PrimitiveType`: Enum of supported C types (uint8_t, uint16_t, etc.)
- `FieldDef`: Represents a single struct field (name, type, size, offset)
- `StructDef`: Represents a C struct (collection of FieldDef)
- `EepromSchema`: Root schema containing all structs

**`src/core/header_parser.py`**
Parses C header files using regex. Builds `EepromSchema` from source text.

- **Input:** Path to `.h` file
- **Output:** `EepromSchema` object
- **Key Method:** `parse_header(header_path: str) -> EepromSchema`

**`src/core/binary_parser.py`**
Decodes binary EEPROM files using Python's `struct` module.

- **Input:** Path to `.bin` file + `EepromSchema`
- **Output:** Nested Python dict/list representing parsed data
- **Key Method:** `parse_binary(bin_path: str) -> Dict[str, Any]`

**`src/core/encoder.py`**
Encodes Python data back into binary format.

- **Input:** Python dict + `EepromSchema`
- **Output:** Binary bytes (written to `.bin` file)
- **Key Method:** `save_binary(data: Dict, bin_path: str)`

**`src/core/model.py`**
Qt data models for UI binding. Bridges core logic and UI.

- `EepromDataModel`: Wraps parsed data, tracks modifications
- `FieldTableModel`: `QAbstractTableModel` for displaying struct fields in table view

**`src/ui/main_window.py`**
Main application window. Handles menu actions, file operations, UI layout.

- Tree widget (left pane): Shows struct hierarchy
- Table view (right pane): Shows fields of selected struct
- Menu bar: File, View, Help menus

**`src/ui/editors.py`**
Custom dialogs for editing different field types.

- `FieldEditorDialog`: Base dialog that dispatches to type-specific editors
- Spinbox editor for integers
- Line edit for strings
- Hex editor for byte arrays

### 2.4 Key Concepts & Business Logic

#### Packed Structs

All structs must be declared with `__attribute__((__packed__))` in C. This means:
- **No padding** between fields
- Fields are laid out sequentially in memory
- Total struct size = sum of all field sizes

Example:
```c
typedef struct __attribute__((__packed__)) {
    uint8_t a;   // Offset 0, size 1
    uint16_t b;  // Offset 1, size 2 (not padded to offset 2!)
    uint32_t c;  // Offset 3, size 4
} MyStruct;      // Total size: 7 bytes (not 8!)
```

#### Little-Endian Encoding

All binary data is interpreted as **little-endian** (LSB first).

Example: `uint16_t value = 0x1234`
- Binary representation: `34 12` (0x34 at lower address)
- This is the native byte order for x86/x64 systems

#### Offset Calculation

Offsets are calculated in two ways:

1. **Relative Offset:** Position within the parent struct (starts at 0)
2. **Absolute Offset:** Position in the entire EEPROM binary (accounts for nesting)

```python
# Relative: deviceConfig.deviceId is at offset 0 within deviceConfig
# Absolute: deviceConfig.deviceId is at offset 0 in the entire EEPROM

# Relative: calibration.offsetX is at offset 0 within calibration
# Absolute: calibration.offsetX is at offset 8 in the entire EEPROM
#           (because deviceConfig is 8 bytes)
```

#### Array Handling

Arrays are handled differently based on type:

- **`char[]`**: Treated as null-terminated C strings
- **`uint8_t[]`**: Treated as raw byte arrays (hex editor)
- **Other primitives[]**: Treated as numeric arrays (comma-separated editor)
- **Struct[]**: Each element is a nested struct

#### Struct vs. Primitive Detection

The parser determines if a type is a struct by checking:
1. Is it in `PrimitiveType` enum? → Primitive
2. Is it in `schema.structs` dict? → Struct
3. Otherwise → Unknown (treat as `uint8_t` with warning)

### 2.5 Testing Strategy

#### Manual Testing

```bash
# 1. Generate test data
cd examples
python generate_sample_bin.py

# 2. Run application
cd ..
python main.py

# 3. Test workflow:
#    - Open examples/sample_eeprom.h
#    - Open examples/sample_eeprom.bin
#    - Navigate tree (click deviceConfig, calibration, userSettings)
#    - Edit a value (double-click deviceId, change value)
#    - Save as test_output.bin
#    - Reload test_output.bin to verify changes persisted
```

#### Unit Testing (Future)

To add unit tests:

```bash
# Install pytest
pip install pytest

# Create tests/ directory
mkdir tests
touch tests/__init__.py
touch tests/test_parser.py
touch tests/test_encoder.py

# Run tests
pytest tests/
```

Example test structure:
```python
# tests/test_parser.py
from src.core.header_parser import HeaderParser

def test_parse_simple_struct():
    parser = HeaderParser()
    # Create temp header file
    # Parse it
    # Assert correct schema
```

### 2.6 Change Log

**v1.0 (2025-11-17) - Initial Release**
- ✅ C header file parsing
- ✅ Binary file loading and saving
- ✅ Tree and table navigation
- ✅ Field editors for all supported types
- ✅ Hex editor for byte arrays
- ✅ Sample files and documentation

**Future Enhancements (Not Scheduled):**
- Undo/redo functionality
- Search/filter fields
- Binary diff viewer
- Export to YAML/JSON
- AES encryption support

---

## 3. System Architecture & Internal APIs

### 3.1 Module Interfaces

#### HeaderParser API

```python
class HeaderParser:
    """Parse C header files containing packed struct definitions."""

    def parse_header(self, header_path: str) -> EepromSchema:
        """
        Main entry point: Parse header file and return schema.

        Raises:
            ValueError: If no structs found or parsing fails
            FileNotFoundError: If header file doesn't exist
        """
```

**Internal Methods:**
- `_remove_comments(content: str) -> str`: Strip C/C++ comments
- `_extract_structs(content: str) -> List[Tuple[str, str]]`: Find all packed structs
- `_parse_struct_fields(struct_def, struct_body, schema)`: Parse fields within a struct
- `_parse_field(line, offset, schema) -> FieldDef`: Parse a single field line
- `_calculate_absolute_offsets(schema)`: Recursively calculate absolute positions

#### BinaryParser API

```python
class BinaryParser:
    """Decode binary EEPROM files based on schema."""

    def __init__(self, schema: EepromSchema):
        """Initialize with a parsed schema."""

    def parse_binary(self, bin_path: str) -> Dict[str, Any]:
        """
        Parse binary file and return nested Python data structure.

        Returns:
            Dict with keys matching struct field names,
            values as primitives, lists, or nested dicts
        """

    def validate_binary_size(self, bin_path: str) -> Tuple[bool, int, int]:
        """
        Check if binary size matches schema.

        Returns:
            (is_valid, actual_size, expected_size)
        """
```

**Internal Methods:**
- `_parse_struct(struct_def, data, offset) -> Dict`: Parse a struct at given offset
- `_parse_field(field, data, offset) -> Any`: Parse a single field
- `_parse_primitive(ptype, data, offset) -> int`: Parse primitive value
- `_parse_primitive_array(field, data, offset) -> List/bytes`: Parse array

#### BinaryEncoder API

```python
class BinaryEncoder:
    """Encode Python data structures back to binary format."""

    def __init__(self, schema: EepromSchema):
        """Initialize with a parsed schema."""

    def encode_to_binary(self, data: Dict[str, Any]) -> bytes:
        """Encode data structure to binary bytes."""

    def save_binary(self, data: Dict[str, Any], bin_path: str):
        """Encode and save to file."""
```

**Internal Methods:**
- `_encode_struct(struct_def, data, buffer, offset)`: Encode struct to buffer
- `_encode_field(field, value, buffer, offset)`: Encode single field
- `_encode_primitive(ptype, value, buffer, offset)`: Encode primitive
- `_validate_value(ptype, value) -> int`: Clamp value to valid range

### 3.2 Data Structures

#### EepromSchema

```python
@dataclass
class EepromSchema:
    root_struct_name: str              # Name of root struct (e.g., "EepromMemoryMapType")
    structs: Dict[str, StructDef]      # All struct definitions by name
    total_size: int                    # Total EEPROM size in bytes
```

#### StructDef

```python
@dataclass
class StructDef:
    name: str                          # Struct name (e.g., "DeviceConfigType")
    fields: List[FieldDef]             # Ordered list of fields
    size: int                          # Total struct size in bytes
    is_packed: bool = True             # Always True (unpacked not supported)
```

#### FieldDef

```python
@dataclass
class FieldDef:
    name: str                          # Field name (e.g., "deviceId")
    type_name: str                     # C type name (e.g., "uint16_t")
    size: int                          # Size in bytes
    offset: int                        # Relative offset within parent struct
    absolute_offset: int               # Absolute offset in EEPROM
    is_array: bool = False             # True if field is an array
    array_length: int = 1              # Array size (1 if not array)
    is_struct: bool = False            # True if nested struct
    primitive_type: Optional[PrimitiveType] = None  # Primitive type enum
```

### 3.3 Error Handling Strategy

#### Parser Errors

**Strategy:** Fail fast with descriptive error messages.

```python
# header_parser.py
if not structs:
    raise ValueError("No struct definitions found in header file")

# Unknown types are treated as uint8_t with warning
print(f"Warning: Unknown type '{type_name}', treating as uint8_t")
```

#### Binary Errors

**Strategy:** Warn but continue when possible.

```python
# binary_parser.py
if len(data) != expected_size:
    print(f"Warning: Binary file size ({len(data)} bytes) does not match "
          f"expected size ({expected_size} bytes)")
    # Continue parsing anyway
```

#### Encoding Errors

**Strategy:** Clamp values and warn.

```python
# encoder.py
if value < min_val or value > max_val:
    print(f"Warning: Value {value} out of range for {ptype.c_type}, clamping")
    value = max(min_val, min(max_val, value))
```

#### UI Errors

**Strategy:** Show user-friendly dialogs.

```python
# main_window.py
try:
    parser = HeaderParser()
    self.schema = parser.parse_header(file_path)
except Exception as e:
    QMessageBox.critical(self, "Error", f"Failed to parse header file:\n{str(e)}")
```

### 3.4 Performance Considerations

| Operation | Expected Time | Notes |
|-----------|---------------|-------|
| Parse header (<100 structs) | <200ms | Regex-based, single-threaded |
| Load 32KB binary | <50ms | `struct.unpack` is fast |
| UI update (select struct) | <100ms | Qt model refresh |
| Save binary | <100ms | Write is fast for small files |
| Hex editor (1KB array) | <500ms | Text rendering is bottleneck |

**Optimization Notes:**
- No need for lazy loading at 32KB file size
- All data kept in memory (acceptable for EEPROM sizes)
- No background threads needed (all operations are fast)

---

## 4. Handover & Maintenance Plan

### 4.1 Key Contacts & Roles

| Role | Responsibility | Contact |
|------|----------------|---------|
| **Product Owner** | Requirements, priority decisions | TBD |
| **Lead Developer** | Architecture, code review | TBD |
| **Domain Expert** | Embedded systems knowledge | TBD |
| **QA Lead** | Test strategy, validation | TBD |

### 4.2 Decision Log

#### Why Python + PyQt6?

**Decision:** Use Python with PyQt6 instead of C++/Qt or Electron.

**Rationale:**
- ✅ Rapid development (Python is concise)
- ✅ Cross-platform GUI with native look & feel
- ✅ Easy regex and binary parsing with stdlib
- ✅ No complex build system required
- ❌ Slower than native C++, but acceptable for file sizes involved

**Date:** 2025-11-17

#### Why Regex Parsing Instead of a C Parser Library?

**Decision:** Use regex to parse C headers instead of libclang or pycparser.

**Rationale:**
- ✅ Simpler implementation (no external C dependencies)
- ✅ We only support packed structs (limited scope)
- ✅ Full C parsing not needed (no macros, preprocessor, etc.)
- ❌ Less robust for complex headers
- ❌ Must manually update regex for new patterns

**Constraint:** Users must provide **simple, packed struct definitions only**. Complex C features are not supported.

**Date:** 2025-11-17

#### Why Little-Endian Only?

**Decision:** Only support little-endian byte order.

**Rationale:**
- ✅ Covers 95% of target use cases (x86/ARM embedded systems)
- ✅ Simpler implementation
- ❌ Won't work for big-endian systems (rare in modern embedded)

**Future:** Could add endianness selection in UI if needed.

**Date:** 2025-11-17

#### Why No Undo/Redo in v1.0?

**Decision:** Defer undo/redo to future version.

**Rationale:**
- ✅ Reduces initial complexity
- ✅ Users can reload file if they make mistakes
- ✅ "Save As" workflow prevents data loss
- ❌ Less convenient for exploratory editing

**Future:** Implement command pattern for undo/redo in v2.0.

**Date:** 2025-11-17

### 4.3 Common Issues & Troubleshooting

#### Issue: "No struct definitions found"

**Symptoms:** Error dialog when opening header file.

**Root Cause:** Header doesn't contain properly formatted packed structs.

**Solution:**
1. Check struct syntax: Must use `__attribute__((__packed__))`
2. Ensure proper typedef format: `typedef struct __attribute__((__packed__)) { ... } NameType;`
3. Remove any preprocessor directives that might interfere (e.g., `#ifdef`)

**Example Fix:**
```c
// ❌ Wrong (no packed attribute)
typedef struct {
    uint8_t field;
} MyStruct;

// ✅ Correct
typedef struct __attribute__((__packed__)) {
    uint8_t field;
} MyStructType;
```

#### Issue: "Binary file size mismatch"

**Symptoms:** Warning dialog about size mismatch when loading binary.

**Root Cause:** Struct sizes don't add up to expected binary size.

**Solution:**
1. Calculate expected size manually: sum all field sizes
2. Add padding field if needed: `uint8_t reserved[N];`
3. Check for missing fields in header definition

**Example Fix:**
```c
// If EEPROM is 32KB (32768 bytes) but structs only total 100 bytes:
typedef struct __attribute__((__packed__)) {
    DeviceConfigType config;   // 10 bytes
    CalibrationDataType calib; // 20 bytes
    UserSettingsType settings; // 70 bytes
    uint8_t reserved[32668];   // Pad to 32KB (32768 - 100 = 32668)
} EepromMemoryMapType;
```

#### Issue: PyQt6 fails to import

**Symptoms:** `ModuleNotFoundError: No module named 'PyQt6'`

**Root Cause:** PyQt6 not installed or wrong Python environment.

**Solution:**
```bash
# Check Python version
python --version  # Must be 3.8+

# Install PyQt6
pip install PyQt6

# If using virtual environment, make sure it's activated
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

#### Issue: Application doesn't start on Windows

**Symptoms:** Double-clicking `main.py` does nothing.

**Root Cause:** Python not associated with `.py` files or missing dependencies.

**Solution:**
```cmd
REM Run from command prompt instead
cd path\to\EepromTool
python main.py

REM Or create a batch file (run.bat):
@echo off
python main.py
pause
```

#### Issue: Values not saving

**Symptoms:** Edit values in UI, save file, but changes don't persist.

**Root Cause:** Didn't click OK in editor dialog, or selected wrong struct.

**Solution:**
1. Double-click field to open editor
2. Modify value
3. **Click OK** (not Cancel or X button)
4. Use File → Save BIN As to export
5. Reload to verify changes

#### Issue: Hex editor shows wrong data

**Symptoms:** Hex editor displays unexpected values.

**Root Cause:** Interpreting signed values as unsigned, or offset calculation error.

**Solution:**
1. Check field type in table view (column 2)
2. Verify absolute offset (column 4) matches expectation
3. Use external hex editor (e.g., HxD) to validate binary file

### 4.4 Logging & Monitoring

#### Current Logging

**Method:** Print statements to stdout/stderr.

```python
# Examples from code:
print(f"Warning: Unknown type '{type_name}', treating as uint8_t")
print(f"Error parsing {ptype.c_type} at offset {offset}: {e}")
```

**Location:** Console output (visible when running from terminal).

**Limitations:** No log levels, no file output, no timestamps.

#### Future Logging (Recommendation)

Use Python's `logging` module for better diagnostics:

```python
import logging

# Configure in main.py
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('eeprom_tool.log'),
        logging.StreamHandler()
    ]
)

# Use in modules
logger = logging.getLogger(__name__)
logger.warning(f"Unknown type '{type_name}', treating as uint8_t")
logger.error(f"Failed to parse field at offset {offset}", exc_info=True)
```

#### Monitoring

**For Desktop Apps:** No active monitoring needed (runs locally).

**If Deployed as Service:** Consider:
- File access errors
- Memory usage (large EEPROM files)
- Crash reports (use Sentry)

### 4.5 Backup & Recovery

#### User Data

**What to Back Up:**
- Modified `.bin` files (EEPROM binaries)
- Custom `.h` header files (if not in version control)

**Backup Strategy:**
- Application has no automatic backup (by design)
- Users should use "Save BIN As" with versioned filenames (e.g., `eeprom_v1.bin`, `eeprom_v2.bin`)

#### Source Code

**What to Back Up:**
- Entire `EepromTool/` directory
- `.git/` directory (commit history)

**Backup Strategy:**
- Primary: Git repository (push to remote regularly)
- Secondary: Automated backups of development machine

**Recovery:**
```bash
# If local repo is corrupted, re-clone:
git clone <repository-url>
cd EepromTool
pip install -r requirements.txt
```

### 4.6 Deployment & Releases

#### Desktop Deployment Options

**Option 1: Source Distribution (Current)**

Users clone/download repo and run with Python:
```bash
git clone <repo-url>
cd EepromTool
pip install -r requirements.txt
python main.py
```

**Pros:** Simple, easy to modify
**Cons:** Requires Python knowledge

**Option 2: Standalone Executable (Future)**

Use PyInstaller to create `.exe` (Windows) or `.app` (Mac):

```bash
# Install PyInstaller
pip install pyinstaller

# Create executable
pyinstaller --onefile --windowed --name "EEPROM_Layout_Editor" main.py

# Output in dist/ directory
```

**Pros:** No Python required for end users
**Cons:** Larger file size, platform-specific builds

**Option 3: Installer Package (Future)**

Create `.msi` (Windows) or `.dmg` (Mac) installer:

- Use tools like NSIS (Windows) or create-dmg (Mac)
- Includes desktop shortcuts, Start menu entries
- Professional appearance

#### Release Checklist

Before releasing a new version:

- [ ] Update version number in code and documentation
- [ ] Update CHANGELOG.md with all changes
- [ ] Run manual test suite with sample files
- [ ] Test on Windows and Linux
- [ ] Create Git tag: `git tag v1.0 && git push --tags`
- [ ] Build standalone executables (if applicable)
- [ ] Create release notes
- [ ] Upload to release platform (GitHub Releases, etc.)

### 4.7 Disaster Recovery

#### Scenario: Source Code Lost

**Prevention:**
- Push to remote Git repository daily
- Use GitHub/GitLab/Bitbucket for redundancy

**Recovery:**
- Clone from remote: `git clone <repo-url>`
- If remote is also lost, rebuild from PRD.md and this document

#### Scenario: Corrupt EEPROM Binary

**Prevention:**
- Always use "Save BIN As" (never overwrite original)
- Keep backups of known-good binaries

**Recovery:**
- Restore from backup
- If no backup, regenerate from device (if possible)
- Manually reconstruct in hex editor

#### Scenario: PyQt6 No Longer Supported

**Prevention:**
- Pin PyQt6 version in `requirements.txt`
- Consider migration to PyQt6 alternatives (PySide6)

**Recovery:**
- Fork PyQt6 if necessary
- Migrate to PySide6 (mostly compatible API)
- Rewrite UI layer with different framework (last resort)

### 4.8 Security Considerations

#### Threat Model

**Attack Surface:**
- Malicious `.h` header files (regex parsing vulnerabilities)
- Malicious `.bin` files (buffer overflows during parsing)
- Path traversal in file dialogs

**Risk Level:** Low (desktop application, processes local files only)

#### Security Measures

1. **Input Validation:**
   - Header parser uses regex (no code execution)
   - Binary parser uses `struct.unpack` (memory-safe)
   - File dialogs use Qt (prevents path traversal)

2. **No Network Access:**
   - Application is offline-only
   - No telemetry or update checks

3. **No Privilege Escalation:**
   - Runs with user privileges
   - No system file access

#### Future Security Enhancements

- Add file signature validation (magic bytes check)
- Implement max file size limits (prevent DoS)
- Sandbox file operations (use temp directory)

### 4.9 Known Limitations

| Limitation | Impact | Workaround | Future Fix |
|-----------|--------|------------|------------|
| No big-endian support | Won't work for PowerPC/SPARC systems | Manual byte swapping | Add endianness toggle |
| No unions/bitfields | Can't parse complex C structs | Split into separate structs | Add union support |
| Regex-based parser | Fragile for complex headers | Simplify header files | Use libclang |
| No undo/redo | Mistakes require reload | Save often with versions | Implement command pattern |
| 32-bit uint limit in spinbox | Can't edit large uint32 values | Use hex editor | Use QLineEdit for uint32 |

### 4.10 Maintenance Schedule

**Weekly:**
- Check for PyQt6 security updates
- Review open issues/bug reports

**Monthly:**
- Update dependencies: `pip list --outdated`
- Review and clean up temporary files

**Quarterly:**
- Review and update documentation
- Consider new feature requests
- Performance profiling

**Yearly:**
- Major version update
- Refactor/cleanup technical debt
- User survey for feedback

### 4.11 Useful Commands Reference

```bash
# Development
python main.py                          # Run application
python examples/generate_sample_bin.py  # Generate test data

# Dependency Management
pip install -r requirements.txt         # Install dependencies
pip freeze > requirements.txt           # Update requirements
pip list --outdated                     # Check for updates

# Git Operations
git status                              # Check changes
git add -A                              # Stage all changes
git commit -m "message"                 # Commit changes
git push origin <branch>                # Push to remote
git tag v1.0 && git push --tags         # Create release tag

# Code Quality
pylint src/                             # Lint code
black src/                              # Auto-format code
mypy src/                               # Type checking

# Packaging (Future)
pyinstaller --onefile main.py           # Create executable
python setup.py sdist bdist_wheel       # Create Python package

# Debugging
python -m pdb main.py                   # Run with debugger
python -c "import PyQt6; print(PyQt6.__version__)"  # Check PyQt6 version
```

### 4.12 Resources & References

#### External Documentation

- **PyQt6 Official Docs:** https://www.riverbankcomputing.com/static/Docs/PyQt6/
- **Python struct module:** https://docs.python.org/3/library/struct.html
- **PEP 8 Style Guide:** https://peps.python.org/pep-0008/
- **GCC Packed Attribute:** https://gcc.gnu.org/onlinedocs/gcc/Common-Type-Attributes.html

#### Internal Documentation

- `README.md` - User-facing quick start
- `QUICKSTART.md` - 5-minute getting started guide
- `PRD.md` - Product requirements and specifications
- This file (`SoftwareDoc.md`) - Comprehensive technical documentation

#### Sample Files

- `examples/sample_eeprom.h` - Working example of supported header format
- `examples/sample_eeprom.bin` - Test binary file (generated)
- `examples/generate_sample_bin.py` - Shows how to create test data

---

## Appendix A: File Format Specifications

### C Header File Format

**Required Pattern:**
```c
typedef struct __attribute__((__packed__)) {
    [field_declarations]
} StructNameType;
```

**Supported Field Types:**
- `uint8_t`, `uint16_t`, `uint32_t` (unsigned integers)
- `int8_t`, `int16_t`, `int32_t` (signed integers)
- `char` (single character)
- `type_name[N]` (fixed-size arrays)
- `NestedStructType` (nested structs)

**Unsupported:**
- Unpacked structs (without `__attribute__((__packed__))`)
- Unions (`union { ... }`)
- Bitfields (`uint8_t flag : 1;`)
- Flexible array members (`type_name[];`)
- Pointers (`type_name*`)

### Binary File Format

**Encoding:** Little-endian, packed (no padding)

**Example Layout:**
```
Offset  | Size | Field Name           | Type     | Value
--------|------|----------------------|----------|-------
0x0000  |  2   | deviceId             | uint16_t | 0x1234
0x0002  |  1   | firmwareVersion      | uint8_t  | 0x01
0x0003  |  1   | hardwareVersion      | uint8_t  | 0x02
0x0004  |  4   | serialNumber         | uint32_t | 0x00BC614E
...
```

---

## Appendix B: Extending the Application

### Adding a New Primitive Type

1. **Update `PrimitiveType` enum** in `src/core/schema.py`:
```python
class PrimitiveType(Enum):
    # ... existing types ...
    FLOAT32 = ('float', 4, 'f')  # Add new type
```

2. **Update validation** in `src/core/encoder.py`:
```python
def _validate_value(self, ptype, value):
    if ptype == PrimitiveType.FLOAT32:
        return float(value)  # Add validation logic
    # ... existing code ...
```

3. **Update editor** in `src/ui/editors.py`:
```python
def create_primitive_editor(self, layout):
    if ptype == PrimitiveType.FLOAT32:
        self.editor_widget = QDoubleSpinBox()
        # Configure widget...
```

### Adding Export to JSON

Create new module `src/core/exporter.py`:

```python
import json

class JsonExporter:
    def export_to_json(self, data: Dict, schema: EepromSchema, output_path: str):
        """Export EEPROM data to JSON format."""
        with open(output_path, 'w') as f:
            json.dump(data, f, indent=2, default=self._json_serializer)

    def _json_serializer(self, obj):
        """Handle bytes serialization."""
        if isinstance(obj, bytes):
            return obj.hex()
        raise TypeError(f"Object of type {type(obj)} is not JSON serializable")
```

Add menu action in `main_window.py`:
```python
export_json_action = file_menu.addAction("Export to JSON...")
export_json_action.triggered.connect(self.export_json)
```

---

## Document Control

**Version:** 1.0
**Created:** 2025-11-17
**Last Updated:** 2025-11-17
**Author:** Development Team
**Review Date:** 2026-01-17 (2 months)

**Change History:**

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2025-11-17 | Dev Team | Initial release |

---

**End of Software Documentation**
