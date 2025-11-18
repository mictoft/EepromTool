# EEPROM Layout Editor - Technical Implementation Guide

**Version:** 1.0.0
**Last Updated:** 2025-11-18
**Audience:** Developers working on codebase modifications and extensions

---

## Table of Contents

1. [Implementation Architecture](#1-implementation-architecture)
2. [Core Module Deep Dive](#2-core-module-deep-dive)
3. [UI Layer Implementation](#3-ui-layer-implementation)
4. [Data Flow & State Management](#4-data-flow--state-management)
5. [Binary Format Handling](#5-binary-format-handling)
6. [Extension Points](#6-extension-points)
7. [Performance Optimization](#7-performance-optimization)
8. [Testing Guidelines](#8-testing-guidelines)

---

## 1. Implementation Architecture

### 1.1 Layer Architecture

The application follows a strict layered architecture:

```
┌──────────────────────────────────────────────┐
│  Presentation Layer (src/ui/)                │
│  - PyQt6 widgets and dialogs                 │
│  - Event handlers                            │
│  - User interaction                          │
├──────────────────────────────────────────────┤
│  Application Layer (src/core/model.py)       │
│  - Qt data models                            │
│  - UI state management                       │
│  - Modification tracking                     │
├──────────────────────────────────────────────┤
│  Business Logic Layer (src/core/)            │
│  - Header parsing (header_parser.py)         │
│  - Binary I/O (binary_parser.py, encoder.py) │
│  - Schema validation (schema.py)             │
├──────────────────────────────────────────────┤
│  Data Layer (schema.py data classes)         │
│  - PrimitiveType enum                        │
│  - FieldDef, StructDef, EepromSchema         │
└──────────────────────────────────────────────┘
```

**Layer Dependencies:**
- Presentation → Application → Business Logic → Data
- **No upward dependencies** (strict unidirectional)
- UI layer **never directly accesses** parser or encoder

### 1.2 Module Dependency Graph

```
main.py
  └─→ src/ui/main_window.py
       ├─→ src/ui/editors.py
       ├─→ src/core/model.py
       │    └─→ src/core/schema.py
       ├─→ src/core/header_parser.py
       │    └─→ src/core/schema.py
       ├─→ src/core/binary_parser.py
       │    └─→ src/core/schema.py
       └─→ src/core/encoder.py
            └─→ src/core/schema.py
```

**Key Design Principle:**
All core modules depend only on `schema.py`. This creates a hub-and-spoke pattern where schema is the central contract.

---

## 2. Core Module Deep Dive

### 2.1 schema.py - Data Structure Definitions

**Purpose:** Define the internal representation of EEPROM memory layouts.

#### 2.1.1 PrimitiveType Enum

```python
class PrimitiveType(Enum):
    UINT8 = ('uint8_t', 1, 'B')
    UINT16 = ('uint16_t', 2, 'H')
    UINT32 = ('uint32_t', 4, 'I')
    INT8 = ('int8_t', 1, 'b')
    INT16 = ('int16_t', 2, 'h')
    INT32 = ('int32_t', 4, 'i')
    CHAR = ('char', 1, 'c')
```

**Enum Structure:**
- **Value 1 (c_type):** C language type name for header file matching
- **Value 2 (size):** Size in bytes (used for offset calculation)
- **Value 3 (struct_format):** Python `struct` module format character

**Format Characters Explained:**
| Format | Type | Size | Byte Order |
|--------|------|------|------------|
| `B` | unsigned char | 1 | N/A |
| `H` | unsigned short | 2 | Little-endian (with `<` prefix) |
| `I` | unsigned int | 4 | Little-endian (with `<` prefix) |
| `b` | signed char | 1 | N/A |
| `h` | signed short | 2 | Little-endian (with `<` prefix) |
| `i` | signed int | 4 | Little-endian (with `<` prefix) |
| `c` | char | 1 | N/A |

**Why Little-Endian?**
- Most embedded systems (ARM Cortex-M, x86) use little-endian
- Python's `struct` module uses `<` prefix for little-endian
- Matches most EEPROM hardware implementations

**Example Usage:**
```python
# Get PrimitiveType from C type string
ptype = PrimitiveType.from_c_type('uint16_t')
# Returns: PrimitiveType.UINT16

# Access enum properties
ptype.c_type        # 'uint16_t'
ptype.size          # 2
ptype.struct_format # 'H'
```

#### 2.1.2 FieldDef Dataclass

**Complete Field Definition:**

```python
@dataclass
class FieldDef:
    name: str                          # Field name from C struct
    type_name: str                     # C type name (e.g., 'uint16_t' or 'MyStructType')
    size: int                          # Total size in bytes
    offset: int                        # Relative offset within parent struct
    absolute_offset: int               # Absolute position in EEPROM binary
    is_array: bool = False             # True if declared with [N] syntax
    array_length: int = 1              # Number of elements (1 if not array)
    is_struct: bool = False            # True if type is a nested struct
    primitive_type: Optional[PrimitiveType] = None  # Set if primitive
```

**Offset Calculation Example:**

Given this C struct:
```c
typedef struct __attribute__((__packed__)) {
    uint8_t a;         // offset=0, size=1
    uint16_t b;        // offset=1, size=2 (NOT padded to 2!)
    uint32_t c;        // offset=3, size=4
} PackedStruct;        // total size=7
```

The `FieldDef` objects would be:
```python
FieldDef(name='a', offset=0, size=1, absolute_offset=0)
FieldDef(name='b', offset=1, size=2, absolute_offset=1)  # NOT offset=2!
FieldDef(name='c', offset=3, size=4, absolute_offset=3)  # NOT offset=4!
```

**Critical Implementation Detail:**
Packed structs have **NO alignment padding**. Each field starts immediately after the previous one.

#### 2.1.3 StructDef Dataclass

```python
@dataclass
class StructDef:
    name: str                          # Struct type name
    fields: List[FieldDef]             # Ordered list of fields
    size: int = 0                      # Total struct size (sum of field sizes)
    is_packed: bool = True             # Always True (unpacked not supported)
```

**Key Methods:**

```python
def add_field(self, field_def: FieldDef):
    """
    Add field and increment struct size.

    IMPORTANT: This modifies size in-place!
    """
    self.fields.append(field_def)
    self.size += field_def.size

def get_field(self, name: str) -> Optional[FieldDef]:
    """Linear search through fields (acceptable for small struct sizes)."""
    for f in self.fields:
        if f.name == name:
            return f
    return None
```

**Performance Note:**
`get_field()` is O(n) but acceptable because:
- Typical structs have <50 fields
- Only called during UI navigation (not in tight loops)

#### 2.1.4 EepromSchema Dataclass

```python
@dataclass
class EepromSchema:
    root_struct_name: str              # Name of top-level struct
    structs: Dict[str, StructDef]      # All struct definitions by name
    total_size: int = 0                # Expected binary file size
```

**Schema Validation:**
- Root struct must exist in `structs` dict
- All nested struct types must be defined
- No circular struct references allowed (not validated - user responsibility)

### 2.2 header_parser.py - C Header File Parser

**Purpose:** Parse C header files using regex to extract struct definitions.

#### 2.2.1 Parser State Machine

The parser operates in two passes:

**Pass 1: Struct Discovery**
```python
def _extract_structs(self, content: str) -> List[Tuple[str, str]]:
    """
    Extract all packed struct definitions.

    Regex pattern:
    typedef struct __attribute__((__packed__)) { ... } NameType;

    Groups:
    1. Struct body (between braces)
    2. Struct name (after closing brace)
    """
    pattern = r'typedef\s+struct\s+__attribute__\s*\(\s*\(\s*__packed__\s*\)\s*\)\s*\{([^}]+)\}\s*(\w+)\s*;'
```

**Why This Pattern?**
- `\s+` allows flexible whitespace
- `\(\s*\(\s*__packed__\s*\)\s*\)` handles `(( __packed__ ))` variations
- `[^}]+` greedily captures body (doesn't handle nested structs in body - limitation!)
- `\w+` captures struct name

**Pass 2: Field Parsing**
```python
def _parse_field(self, line: str, offset: int, schema: EepromSchema) -> Optional[FieldDef]:
    """
    Parse single field declaration.

    Regex: (\w+)\s+(\w+)(?:\[(\d+)\])?

    Groups:
    1. Type name
    2. Field name
    3. Array size (optional)
    """
```

**Field Parsing Algorithm:**

1. **Match regex** against field line
2. **Extract** type_name, field_name, array_size
3. **Lookup** type_name in PrimitiveType enum
4. **If primitive:**
   - Calculate size = primitive.size * array_length
   - Create FieldDef with primitive_type set
5. **If struct type:**
   - Look up struct in schema.structs
   - Calculate size = struct.size * array_length
   - Create FieldDef with is_struct=True
6. **If unknown:**
   - Print warning
   - Treat as uint8_t (fallback)

#### 2.2.2 Offset Calculation Algorithm

**Relative Offsets:**
```python
def _parse_struct_fields(self, struct_def: StructDef, struct_body: str, schema: EepromSchema):
    offset = 0  # Start at 0 for each struct

    for line in struct_body.split(';'):
        field = self._parse_field(line, offset, schema)
        if field:
            struct_def.add_field(field)
            offset += field.size  # Increment by field size
```

**Absolute Offsets (Recursive):**
```python
def _calculate_struct_absolute_offsets(self, struct_def: StructDef, base_offset: int, schema: EepromSchema):
    """
    Recursively calculate absolute offsets.

    Args:
        struct_def: Current struct being processed
        base_offset: Starting offset of this struct in parent
        schema: Full schema (needed to look up nested structs)
    """
    for field in struct_def.fields:
        # Set absolute offset
        field.absolute_offset = base_offset + field.offset

        # Recurse into nested structs
        if field.is_struct:
            nested_struct = schema.get_struct(field.type_name)
            if field.is_array:
                # For arrays, process each element
                for i in range(field.array_length):
                    element_offset = field.absolute_offset + (i * nested_struct.size)
                    self._calculate_struct_absolute_offsets(nested_struct, element_offset, schema)
            else:
                self._calculate_struct_absolute_offsets(nested_struct, field.absolute_offset, schema)
```

**Example Calculation:**

```c
typedef struct __attribute__((__packed__)) {
    uint16_t x;  // 2 bytes
    uint16_t y;  // 2 bytes
} Point;         // total: 4 bytes

typedef struct __attribute__((__packed__)) {
    uint8_t id;       // offset=0, abs_offset=0, size=1
    Point location;   // offset=1, abs_offset=1, size=4
    uint8_t status;   // offset=5, abs_offset=5, size=1
} Device;             // total: 6 bytes
```

After processing:
```
Device.id:       offset=0, absolute_offset=0
Device.location: offset=1, absolute_offset=1
  Point.x:       offset=0, absolute_offset=1  (base_offset=1)
  Point.y:       offset=2, absolute_offset=3  (base_offset=1)
Device.status:   offset=5, absolute_offset=5
```

### 2.3 binary_parser.py - Binary Decoder

**Purpose:** Read binary EEPROM files and convert to Python data structures.

#### 2.3.1 Decoding Strategy

**Top-Level Algorithm:**
```python
def parse_binary(self, bin_path: str) -> Dict[str, Any]:
    # 1. Read entire file into memory
    with open(bin_path, 'rb') as f:
        data = f.read()

    # 2. Validate size (warn but continue)
    if len(data) != self.schema.total_size:
        print("Warning: size mismatch")

    # 3. Parse root struct
    root_struct = self.schema.get_root_struct()
    result = self._parse_struct(root_struct, data, offset=0)

    return result
```

**Why Read Entire File?**
- EEPROM files are small (typically 32KB-1MB)
- Random access is simpler than streaming
- Entire schema is needed anyway (can't parse incrementally)

#### 2.3.2 Struct Parsing (Recursive)

```python
def _parse_struct(self, struct_def: StructDef, data: bytes, offset: int) -> Dict[str, Any]:
    """
    Parse struct from binary data.

    Args:
        struct_def: Struct schema
        data: Full binary data
        offset: Where this struct starts

    Returns:
        Dict mapping field names to values
    """
    result = {}

    for field in struct_def.fields:
        field_offset = offset + field.offset
        value = self._parse_field(field, data, field_offset)
        result[field.name] = value

    return result
```

**Return Value Structure:**

For this schema:
```c
typedef struct __attribute__((__packed__)) {
    uint8_t a;
    uint16_t b;
} MyStruct;
```

Parsing returns:
```python
{
    'a': 5,      # int
    'b': 1000    # int
}
```

For nested structs:
```c
typedef struct __attribute__((__packed__)) {
    MyStruct nested;
    uint8_t c;
} Outer;
```

Parsing returns:
```python
{
    'nested': {
        'a': 5,
        'b': 1000
    },
    'c': 42
}
```

#### 2.3.3 Primitive Parsing

```python
def _parse_primitive(self, ptype: PrimitiveType, data: bytes, offset: int) -> Union[int, bytes]:
    """
    Parse single primitive value.

    Uses struct.unpack_from for efficiency.
    """
    format_str = '<' + ptype.struct_format  # '<' = little-endian
    value = struct.unpack_from(format_str, data, offset)[0]

    # Special handling for char type
    if ptype == PrimitiveType.CHAR:
        if isinstance(value, bytes):
            return ord(value) if len(value) > 0 else 0
        return value

    return value
```

**struct.unpack_from Explained:**

```python
import struct

data = b'\x34\x12\x00\x00'  # Little-endian bytes

# Parse uint16_t at offset 0
value = struct.unpack_from('<H', data, 0)[0]
# '<' = little-endian
# 'H' = unsigned short (2 bytes)
# Returns: 0x1234 (4660 decimal)
```

**Performance:**
- `struct.unpack_from` is implemented in C (very fast)
- No memory allocation (reads directly from bytes object)
- Typical 32KB file parses in <10ms

#### 2.3.4 Array Parsing Strategies

**Strategy 1: Character Arrays (C strings)**
```python
if ptype == PrimitiveType.CHAR:
    raw_bytes = data[offset:offset + field.size]
    # Find null terminator
    null_pos = raw_bytes.find(b'\x00')
    if null_pos >= 0:
        return raw_bytes[:null_pos]  # Strip trailing nulls
    return raw_bytes
```

**Strategy 2: Byte Arrays (hex data)**
```python
if ptype == PrimitiveType.UINT8:
    return data[offset:offset + field.size]  # Return as bytes object
```

**Strategy 3: Numeric Arrays**
```python
result = []
element_size = ptype.size
for i in range(field.array_length):
    element_offset = offset + (i * element_size)
    value = self._parse_primitive(ptype, data, element_offset)
    result.append(value)
return result
```

**Why Different Strategies?**
- **char[]**: Usually represents strings (null-terminated)
- **uint8_t[]**: Usually represents raw binary data (hex editing)
- **Other arrays**: Usually represent numeric sequences

### 2.4 encoder.py - Binary Encoder

**Purpose:** Convert Python data structures back to binary format.

#### 2.4.1 Encoding Algorithm

```python
def encode_to_binary(self, data: Dict[str, Any]) -> bytes:
    """
    Main encoding entry point.

    Strategy:
    1. Create zero-filled buffer of correct size
    2. Recursively write fields into buffer
    3. Return final bytes
    """
    buffer = bytearray(self.schema.total_size)  # Zero-filled
    root_struct = self.schema.get_root_struct()
    self._encode_struct(root_struct, data, buffer, offset=0)
    return bytes(buffer)
```

**Why bytearray?**
- Mutable (can write to specific offsets)
- Automatically zero-filled on creation
- Efficient conversion to bytes

#### 2.4.2 Value Validation & Clamping

```python
def _validate_value(self, ptype: PrimitiveType, value: Any) -> int:
    """
    Validate and clamp value to type's range.

    Example:
    - uint8_t can only hold 0-255
    - If value=300, clamp to 255 and warn
    """
    value = int(value)  # Convert to int

    ranges = {
        PrimitiveType.UINT8: (0, 255),
        PrimitiveType.UINT16: (0, 65535),
        PrimitiveType.UINT32: (0, 4294967295),
        PrimitiveType.INT8: (-128, 127),
        PrimitiveType.INT16: (-32768, 32767),
        PrimitiveType.INT32: (-2147483648, 2147483647),
    }

    if ptype in ranges:
        min_val, max_val = ranges[ptype]
        if value < min_val or value > max_val:
            print(f"Warning: Clamping {value} to [{min_val}, {max_val}]")
            value = max(min_val, min(max_val, value))

    return value
```

**Design Rationale:**
- **Clamp instead of error:** More user-friendly (data corruption is worse than clamping)
- **Print warnings:** User is informed of issues
- **Future improvement:** Show warnings in GUI dialog

#### 2.4.3 Primitive Encoding

```python
def _encode_primitive(self, ptype: PrimitiveType, value: Any, buffer: bytearray, offset: int):
    """
    Encode single primitive value.

    Uses struct.pack to convert to bytes.
    """
    format_str = '<' + ptype.struct_format

    # Validate value
    value = self._validate_value(ptype, value)

    # Pack and write
    packed = struct.pack(format_str, value)
    buffer[offset:offset + len(packed)] = packed
```

**struct.pack Example:**

```python
import struct

# Encode uint16_t value 0x1234
packed = struct.pack('<H', 0x1234)
# Result: b'\x34\x12' (little-endian)

# Write to buffer
buffer = bytearray(10)
buffer[5:7] = packed
# buffer now contains: b'\x00\x00\x00\x00\x00\x34\x12\x00\x00\x00'
```

---

## 3. UI Layer Implementation

### 3.1 main_window.py - Main Application Window

#### 3.1.1 Widget Hierarchy

```
QMainWindow (MainWindow)
├── QMenuBar
│   ├── QMenu ("File")
│   │   ├── QAction ("Open Header...")
│   │   ├── QAction ("Open BIN...")
│   │   ├── QAction ("Save BIN As...")
│   │   └── QAction ("Exit")
│   ├── QMenu ("View")
│   │   └── QAction ("Reload")
│   └── QMenu ("Help")
│       └── QAction ("About")
├── QWidget (central widget)
│   └── QVBoxLayout
│       └── QSplitter (Horizontal)
│           ├── QTreeWidget (left pane)
│           └── QTableView (right pane)
│               └── FieldTableModel (model)
└── QStatusBar
```

#### 3.1.2 State Management

**Application State:**
```python
class MainWindow(QMainWindow):
    def __init__(self):
        # Core state
        self.schema: Optional[EepromSchema] = None
        self.data_model: Optional[EepromDataModel] = None

        # File tracking
        self.current_binary_path: Optional[str] = None
        self.current_header_path: Optional[str] = None

        # UI models
        self.table_model: FieldTableModel
        self.tree_widget: QTreeWidget
```

**State Transitions:**

```
[Initial]
    ↓ (Open Header)
[Header Loaded] (schema != None)
    ↓ (Open Binary)
[Data Loaded] (schema != None, data_model != None)
    ↓ (Edit Field)
[Data Modified] (data_model.modified == True)
    ↓ (Save Binary)
[Data Saved] (data_model.modified == False)
```

#### 3.1.3 Tree Population Algorithm

```python
def populate_tree(self):
    """
    Build tree structure from schema.

    Algorithm:
    1. Clear existing tree
    2. Create root item for root struct
    3. Recursively populate children
    4. Expand all nodes
    """
    self.tree_widget.clear()

    root_struct = self.schema.get_root_struct()
    root_item = QTreeWidgetItem(self.tree_widget)
    root_item.setText(0, root_struct.name)
    root_item.setData(0, Qt.ItemDataRole.UserRole, {
        'struct': root_struct,
        'path': []
    })

    self._populate_tree_node(root_item, root_struct, [])
    self.tree_widget.expandAll()
```

**Field Path Tracking:**

Each tree item stores a `path` list that identifies the field location:

```python
# Root struct
path = []

# Nested struct field "deviceConfig"
path = ['deviceConfig']

# Field in nested struct: deviceConfig.deviceId
# (This is shown in table, not tree)

# Array element: calibration[0]
path = ['calibration', '0']
```

**Why Store Path?**
- Allows navigation back to exact field in data model
- Supports nested struct arrays
- Required for table model to find values

### 3.2 editors.py - Field Editors

#### 3.2.1 Editor Selection Logic

```python
class FieldEditorDialog(QDialog):
    def init_ui(self):
        if self.field.is_struct:
            # Show message: navigate in tree
            layout.addWidget(QLabel("Navigate to struct in tree"))

        elif self.field.is_array:
            self.create_array_editor(layout)

        elif self.field.primitive_type:
            self.create_primitive_editor(layout)

        else:
            layout.addWidget(QLabel("Unknown field type"))
```

#### 3.2.2 Spinbox Editor (Integers)

```python
def create_primitive_editor(self, layout):
    if ptype in [PrimitiveType.UINT8, UINT16, UINT32]:
        self.editor_widget = QSpinBox()
        self.editor_widget.setMinimum(0)

        if ptype == PrimitiveType.UINT8:
            self.editor_widget.setMaximum(255)
        elif ptype == PrimitiveType.UINT16:
            self.editor_widget.setMaximum(65535)
        elif ptype == PrimitiveType.UINT32:
            self.editor_widget.setMaximum(2147483647)  # QSpinBox limit

        self.editor_widget.setValue(int(self.current_value))
```

**QSpinBox Limitation:**
- Maximum value is 2^31-1 (2,147,483,647)
- uint32_t can hold up to 4,294,967,295
- **Workaround:** Use QLineEdit with validation for large uint32 values

#### 3.2.3 Hex Editor (Byte Arrays)

```python
def create_hex_editor(self, layout):
    """
    Create hex editor for uint8_t arrays.

    Features:
    - QTextEdit for hex input
    - "Load from File" button
    - Automatic validation on save
    """
    self.editor_widget = QTextEdit()

    # Display current value as hex string
    if isinstance(self.current_value, bytes):
        hex_text = self.current_value.hex(' ')  # Space-separated hex
        self.editor_widget.setPlainText(hex_text)
```

**Hex Format:**
```
Input:  b'\x01\x02\x03\x04'
Display: "01 02 03 04"

User edits to: "FF EE DD CC"
Parsed back to: b'\xFF\xEE\xDD\xCC'
```

### 3.3 model.py - Qt Data Models

#### 3.3.1 EepromDataModel

```python
class EepromDataModel:
    """
    Non-Qt model for holding parsed data.

    Responsibilities:
    - Store parsed data (nested dicts/lists)
    - Track modifications
    - Provide get/set by path
    """
    def __init__(self, schema: EepromSchema, data: Dict[str, Any]):
        self.schema = schema
        self.data = data
        self.modified = False
```

**Path-based Access:**

```python
def get_value(self, path: List[str]) -> Any:
    """
    Get value by path.

    Example:
    path = ['deviceConfig', 'deviceId']
    Returns: data['deviceConfig']['deviceId']

    path = ['calibration', '0', 'offsetX']
    Returns: data['calibration'][0]['offsetX']
    """
    current = self.data
    for key in path:
        if isinstance(current, dict):
            current = current.get(key)
        elif isinstance(current, list):
            idx = int(key)
            current = current[idx]
    return current
```

#### 3.3.2 FieldTableModel (QAbstractTableModel)

**Column Definitions:**

```python
COLUMNS = ['Field Name', 'Type', 'Offset', 'Abs Offset', 'Size', 'Value']

def data(self, index: QModelIndex, role):
    col = index.column()
    field = self.struct_def.fields[index.row()]

    if col == 0:  # Field Name
        return f"{field.name}[{field.array_length}]" if field.is_array else field.name

    elif col == 1:  # Type
        return field.type_name

    elif col == 2:  # Offset (relative)
        return f"0x{field.offset:04X}"

    elif col == 3:  # Absolute Offset
        return f"0x{field.absolute_offset:04X}"

    elif col == 4:  # Size
        return f"{field.size}"

    elif col == 5:  # Value
        value = self.data_model.get_value(self.field_path + [field.name])
        return self._format_value(field, value)
```

**Editable Cells:**

```python
def flags(self, index: QModelIndex):
    if index.column() == 5:  # Value column
        field = self.struct_def.fields[index.row()]

        # Only simple primitives are directly editable
        if field.primitive_type and not field.is_array:
            return ItemIsEnabled | ItemIsSelectable | ItemIsEditable

    return ItemIsEnabled | ItemIsSelectable
```

**Design Decision:**
Only simple integer fields are editable directly in table. Arrays and structs require dedicated editors (double-click).

---

## 4. Data Flow & State Management

### 4.1 Load Header Workflow

```
User: File → Open Header
    ↓
MainWindow.open_header()
    ↓
QFileDialog.getOpenFileName()
    ↓
HeaderParser.parse_header(path)
    ├─→ _remove_comments()
    ├─→ _extract_structs()
    ├─→ _parse_struct_fields()
    └─→ _calculate_absolute_offsets()
    ↓
Returns: EepromSchema object
    ↓
self.schema = schema
self.current_header_path = path
    ↓
QMessageBox.information("Header Loaded")
```

### 4.2 Load Binary Workflow

```
User: File → Open BIN
    ↓
MainWindow.open_binary()
    ↓
Check: self.schema exists? (if not, show warning)
    ↓
QFileDialog.getOpenFileName()
    ↓
MainWindow.load_binary(path)
    ↓
BinaryParser(schema).validate_binary_size(path)
    ↓ (if mismatch)
QMessageBox.warning("Continue?")
    ↓
BinaryParser.parse_binary(path)
    ├─→ Read file
    ├─→ _parse_struct(root)
    └─→ Recursively decode
    ↓
Returns: Dict[str, Any]
    ↓
self.data_model = EepromDataModel(schema, data)
self.current_binary_path = path
    ↓
self.populate_tree()  ← Build UI tree
    ↓
QStatusBar.showMessage("Loaded binary")
```

### 4.3 Edit Field Workflow

```
User: Double-click value in table
    ↓
MainWindow.on_field_double_clicked(index)
    ↓
Get field: table_model.get_field(row)
Get path: table_model.get_field_path(row)
Get value: data_model.get_value(path)
    ↓
FieldEditorDialog(field, value).exec()
    ├─→ Create appropriate editor widget
    ├─→ User modifies value
    └─→ User clicks OK
    ↓
Returns: new_value
    ↓
data_model.set_value(path, new_value)
    ↓
data_model.modified = True
    ↓
table_model.dataChanged.emit(index, index)
    ↓
Table cell refreshes with new value
```

### 4.4 Save Binary Workflow

```
User: File → Save BIN As
    ↓
MainWindow.save_binary()
    ↓
Check: data_model exists? (if not, show warning)
    ↓
QFileDialog.getSaveFileName()
    ↓
BinaryEncoder(schema).save_binary(data, path)
    ├─→ encode_to_binary(data)
    │   ├─→ Create bytearray buffer
    │   ├─→ _encode_struct(root, data, buffer, 0)
    │   └─→ Return bytes
    └─→ Write to file
    ↓
data_model.modified = False
    ↓
QMessageBox.information("Saved successfully")
```

---

## 5. Binary Format Handling

### 5.1 Struct Packing Details

**Standard C Struct (WITH padding):**
```c
struct NormalStruct {
    uint8_t a;   // offset 0
    uint16_t b;  // offset 2 (padded!)
    uint32_t c;  // offset 4
};  // size = 8 bytes
```

Memory layout:
```
Offset: 0  1  2  3  4  5  6  7
Value:  AA XX BB BB CC CC CC CC
        ^  ^  ^~~~~ ^~~~~~~~~~~
        a  pad   b       c
```

**Packed Struct (NO padding):**
```c
struct __attribute__((__packed__)) PackedStruct {
    uint8_t a;   // offset 0
    uint16_t b;  // offset 1 (NO padding!)
    uint32_t c;  // offset 3
};  // size = 7 bytes
```

Memory layout:
```
Offset: 0  1  2  3  4  5  6
Value:  AA BB BB CC CC CC CC
        ^  ^~~~~ ^~~~~~~~~~~
        a    b       c
```

**Critical for EEPROM:**
- Every byte matters (EEPROM is expensive)
- No wasted space on alignment
- **All structs MUST be packed**

### 5.2 Endianness Handling

**Little-Endian (Used in this application):**

```
Value: 0x12345678 (uint32_t)

Memory layout:
Address:  0x00  0x01  0x02  0x03
Value:    0x78  0x56  0x34  0x12
          LSB                 MSB
```

**Big-Endian (NOT supported):**

```
Value: 0x12345678 (uint32_t)

Memory layout:
Address:  0x00  0x01  0x02  0x03
Value:    0x12  0x34  0x56  0x78
          MSB                 LSB
```

**Python struct Module:**

```python
import struct

value = 0x1234

# Little-endian
packed = struct.pack('<H', value)
# Result: b'\x34\x12'

# Big-endian
packed = struct.pack('>H', value)
# Result: b'\x12\x34'

# Native (platform-dependent)
packed = struct.pack('H', value)
# Result: depends on CPU architecture
```

**Why Always Use `<` Prefix?**
- Ensures consistent behavior across platforms
- Matches most embedded systems
- Explicit is better than implicit

### 5.3 Array Serialization

**Primitive Array:**

C code:
```c
uint16_t values[4] = {0x1111, 0x2222, 0x3333, 0x4444};
```

Binary layout (little-endian):
```
Offset: 0    1    2    3    4    5    6    7
Value:  0x11 0x11 0x22 0x22 0x33 0x33 0x44 0x44
        [0]       [1]       [2]       [3]
```

**Struct Array:**

C code:
```c
typedef struct __attribute__((__packed__)) {
    uint8_t x;
    uint8_t y;
} Point;  // size = 2

Point points[3] = {{1,2}, {3,4}, {5,6}};
```

Binary layout:
```
Offset: 0  1  2  3  4  5
Value:  01 02 03 04 05 06
        [0]   [1]   [2]
        x y   x y   x y
```

Python representation:
```python
[
    {'x': 1, 'y': 2},
    {'x': 3, 'y': 4},
    {'x': 5, 'y': 6}
]
```

---

## 6. Extension Points

### 6.1 Adding a New Primitive Type

**Example: Add `float` support**

**Step 1:** Add to PrimitiveType enum (schema.py)
```python
class PrimitiveType(Enum):
    # ... existing types ...
    FLOAT = ('float', 4, 'f')
```

**Step 2:** Update encoder validation (encoder.py)
```python
def _validate_value(self, ptype, value):
    if ptype == PrimitiveType.FLOAT:
        return float(value)
    # ... existing code ...
```

**Step 3:** Update editor (editors.py)
```python
def create_primitive_editor(self, layout):
    if ptype == PrimitiveType.FLOAT:
        self.editor_widget = QDoubleSpinBox()
        self.editor_widget.setRange(-1e10, 1e10)
        self.editor_widget.setDecimals(6)
        self.editor_widget.setValue(float(self.current_value))
```

**Step 4:** Test with header file
```c
typedef struct __attribute__((__packed__)) {
    float temperature;
} SensorData;
```

### 6.2 Adding Big-Endian Support

**Approach 1: Global Setting**

Add to schema:
```python
@dataclass
class EepromSchema:
    root_struct_name: str
    structs: Dict[str, StructDef]
    total_size: int = 0
    endianness: str = 'little'  # NEW: 'little' or 'big'
```

Update parsers:
```python
# binary_parser.py
def _parse_primitive(self, ptype, data, offset):
    prefix = '<' if self.schema.endianness == 'little' else '>'
    format_str = prefix + ptype.struct_format
    return struct.unpack_from(format_str, data, offset)[0]

# encoder.py (same pattern)
```

**Approach 2: Per-Field Setting**

Add to FieldDef:
```python
@dataclass
class FieldDef:
    # ... existing fields ...
    endianness: str = 'little'  # Per-field override
```

### 6.3 Adding Export to JSON

**Create new module: `src/core/exporter.py`**

```python
import json
from typing import Dict, Any
from .schema import EepromSchema

class JsonExporter:
    def __init__(self, schema: EepromSchema):
        self.schema = schema

    def export_to_json(self, data: Dict[str, Any], output_path: str):
        """Export EEPROM data to JSON format."""
        with open(output_path, 'w') as f:
            json.dump(data, f, indent=2, default=self._serialize)

    def _serialize(self, obj):
        """Handle non-JSON-serializable types."""
        if isinstance(obj, bytes):
            return obj.hex()  # Convert bytes to hex string
        raise TypeError(f"Type {type(obj)} not JSON serializable")
```

**Add to main_window.py:**

```python
def create_menu_bar(self):
    # ... existing menus ...

    export_json = file_menu.addAction("Export to JSON...")
    export_json.triggered.connect(self.export_json)

def export_json(self):
    if not self.data_model:
        QMessageBox.warning(self, "No Data", "Load a binary file first")
        return

    path, _ = QFileDialog.getSaveFileName(self, "Export JSON", "", "JSON Files (*.json)")
    if path:
        from src.core.exporter import JsonExporter
        exporter = JsonExporter(self.schema)
        exporter.export_to_json(self.data_model.data, path)
        QMessageBox.information(self, "Success", "Exported to JSON")
```

### 6.4 Adding Undo/Redo

**Implement Command Pattern:**

```python
# src/core/commands.py
from abc import ABC, abstractmethod
from typing import Any, List

class Command(ABC):
    @abstractmethod
    def execute(self):
        pass

    @abstractmethod
    def undo(self):
        pass

class SetValueCommand(Command):
    def __init__(self, data_model, path: List[str], old_value: Any, new_value: Any):
        self.data_model = data_model
        self.path = path
        self.old_value = old_value
        self.new_value = new_value

    def execute(self):
        self.data_model.set_value(self.path, self.new_value)

    def undo(self):
        self.data_model.set_value(self.path, self.old_value)

class UndoStack:
    def __init__(self):
        self.commands = []
        self.current_index = -1

    def execute(self, command: Command):
        # Remove any commands after current index
        self.commands = self.commands[:self.current_index + 1]

        command.execute()
        self.commands.append(command)
        self.current_index += 1

    def undo(self):
        if self.current_index >= 0:
            self.commands[self.current_index].undo()
            self.current_index -= 1

    def redo(self):
        if self.current_index < len(self.commands) - 1:
            self.current_index += 1
            self.commands[self.current_index].execute()
```

**Integrate in main_window.py:**

```python
class MainWindow(QMainWindow):
    def __init__(self):
        # ... existing code ...
        self.undo_stack = UndoStack()

    def on_field_double_clicked(self, index):
        field = self.table_model.get_field(index.row())
        path = self.table_model.get_field_path(index.row())
        old_value = self.data_model.get_value(path)

        dialog = FieldEditorDialog(field, old_value, self)
        if dialog.exec():
            new_value = dialog.get_value()

            # Create and execute command
            cmd = SetValueCommand(self.data_model, path, old_value, new_value)
            self.undo_stack.execute(cmd)

            self.table_model.dataChanged.emit(index, index)
```

---

## 7. Performance Optimization

### 7.1 Current Performance Characteristics

**Measured on Sample File (32KB EEPROM):**

| Operation | Time (ms) | Notes |
|-----------|-----------|-------|
| Parse header | ~50 | Regex-based, 4 structs |
| Load binary | ~5 | Read file + parse |
| Populate tree | ~100 | Create Qt widgets |
| Switch struct in table | ~20 | Table model refresh |
| Edit field | ~10 | Show dialog |
| Save binary | ~5 | Encode + write file |

**Bottlenecks:**
1. Tree widget population (Qt overhead)
2. Regex compilation (minor)

### 7.2 Optimization Strategies

**Strategy 1: Lazy Tree Population**

Current: Populate entire tree on load
Optimized: Populate only visible nodes

```python
def populate_tree(self):
    # Only create root node
    root_item = QTreeWidgetItem(self.tree_widget)
    root_item.setText(0, root_struct.name)

    # Set "has children" flag but don't create them yet
    root_item.setChildIndicatorPolicy(QTreeWidgetItem.ShowIndicator)

    # Connect to expansion event
    self.tree_widget.itemExpanded.connect(self.on_item_expanded)

def on_item_expanded(self, item):
    # Populate children only when expanded
    if item.childCount() == 0:
        self._populate_tree_node(item, struct_def, path)
```

**Strategy 2: Cache Regex Patterns**

Current: Compile regex on each parse
Optimized: Compile once, reuse

```python
class HeaderParser:
    # Class-level compiled patterns
    STRUCT_PATTERN = re.compile(
        r'typedef\s+struct\s+__attribute__\s*\(\s*\(\s*__packed__\s*\)\s*\)\s*\{([^}]+)\}\s*(\w+)\s*;'
    )
    FIELD_PATTERN = re.compile(r'(\w+)\s+(\w+)(?:\[(\d+)\])?')

    def _extract_structs(self, content):
        return self.STRUCT_PATTERN.findall(content)
```

**Strategy 3: Binary Memory Mapping**

Current: Read entire file into memory
Optimized: Use memory mapping for very large files

```python
import mmap

def parse_binary(self, bin_path: str):
    with open(bin_path, 'rb') as f:
        # Memory-map the file
        mmapped = mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ)

        # Parse using mmapped object (behaves like bytes)
        result = self._parse_struct(root_struct, mmapped, 0)

        mmapped.close()

    return result
```

**When to use:**
- File > 10 MB
- Only reading specific sections
- Not needed for typical EEPROM sizes

---

## 8. Testing Guidelines

### 8.1 Unit Test Structure

**Create `tests/` directory:**

```bash
mkdir tests
touch tests/__init__.py
touch tests/test_schema.py
touch tests/test_header_parser.py
touch tests/test_binary_parser.py
touch tests/test_encoder.py
```

**Example: test_schema.py**

```python
import pytest
from src.core.schema import PrimitiveType, FieldDef, StructDef, EepromSchema

class TestPrimitiveType:
    def test_from_c_type_valid(self):
        ptype = PrimitiveType.from_c_type('uint16_t')
        assert ptype == PrimitiveType.UINT16
        assert ptype.size == 2
        assert ptype.struct_format == 'H'

    def test_from_c_type_invalid(self):
        ptype = PrimitiveType.from_c_type('invalid_type')
        assert ptype is None

class TestFieldDef:
    def test_field_creation(self):
        field = FieldDef(
            name='test',
            type_name='uint8_t',
            size=1,
            offset=0,
            absolute_offset=0,
            primitive_type=PrimitiveType.UINT8
        )
        assert field.name == 'test'
        assert not field.is_array
        assert field.array_length == 1

class TestStructDef:
    def test_add_field(self):
        struct = StructDef(name='TestStruct')
        assert struct.size == 0

        field = FieldDef(
            name='field1',
            type_name='uint16_t',
            size=2,
            offset=0,
            absolute_offset=0
        )
        struct.add_field(field)

        assert struct.size == 2
        assert len(struct.fields) == 1
```

**Example: test_header_parser.py**

```python
import pytest
import tempfile
import os
from src.core.header_parser import HeaderParser

class TestHeaderParser:
    @pytest.fixture
    def temp_header(self):
        """Create temporary header file for testing."""
        content = """
        typedef struct __attribute__((__packed__)) {
            uint8_t a;
            uint16_t b;
        } TestStruct;
        """

        with tempfile.NamedTemporaryFile(mode='w', suffix='.h', delete=False) as f:
            f.write(content)
            temp_path = f.name

        yield temp_path

        os.unlink(temp_path)

    def test_parse_simple_struct(self, temp_header):
        parser = HeaderParser()
        schema = parser.parse_header(temp_header)

        assert schema is not None
        assert 'TestStruct' in schema.structs

        test_struct = schema.structs['TestStruct']
        assert test_struct.size == 3  # 1 + 2
        assert len(test_struct.fields) == 2

    def test_invalid_header(self):
        parser = HeaderParser()

        with tempfile.NamedTemporaryFile(mode='w', suffix='.h', delete=False) as f:
            f.write("invalid content")
            temp_path = f.name

        try:
            with pytest.raises(ValueError, match="No struct definitions found"):
                parser.parse_header(temp_path)
        finally:
            os.unlink(temp_path)
```

**Example: test_binary_parser.py**

```python
import pytest
import struct
from src.core.binary_parser import BinaryParser
from src.core.schema import *

class TestBinaryParser:
    @pytest.fixture
    def simple_schema(self):
        """Create a simple test schema."""
        schema = EepromSchema(root_struct_name='TestStruct')

        test_struct = StructDef(name='TestStruct')
        test_struct.add_field(FieldDef(
            name='a',
            type_name='uint8_t',
            size=1,
            offset=0,
            absolute_offset=0,
            primitive_type=PrimitiveType.UINT8
        ))
        test_struct.add_field(FieldDef(
            name='b',
            type_name='uint16_t',
            size=2,
            offset=1,
            absolute_offset=1,
            primitive_type=PrimitiveType.UINT16
        ))

        schema.add_struct(test_struct)
        schema.total_size = 3

        return schema

    def test_parse_simple_binary(self, simple_schema, tmp_path):
        """Test parsing simple binary file."""
        # Create test binary
        binary_data = struct.pack('<BH', 42, 1000)

        bin_file = tmp_path / "test.bin"
        bin_file.write_bytes(binary_data)

        # Parse
        parser = BinaryParser(simple_schema)
        result = parser.parse_binary(str(bin_file))

        assert result['a'] == 42
        assert result['b'] == 1000
```

### 8.2 Integration Test Strategy

**Test Workflow:**

```python
# tests/test_integration.py
import pytest
from src.core.header_parser import HeaderParser
from src.core.binary_parser import BinaryParser
from src.core.encoder import BinaryEncoder

def test_round_trip(tmp_path):
    """Test: parse header → parse binary → modify → encode → verify"""

    # Step 1: Create header file
    header_file = tmp_path / "test.h"
    header_file.write_text("""
    typedef struct __attribute__((__packed__)) {
        uint16_t value;
    } TestStruct;
    """)

    # Step 2: Parse header
    parser = HeaderParser()
    schema = parser.parse_header(str(header_file))

    # Step 3: Create original binary
    original_bin = tmp_path / "original.bin"
    original_bin.write_bytes(struct.pack('<H', 100))

    # Step 4: Parse binary
    bin_parser = BinaryParser(schema)
    data = bin_parser.parse_binary(str(original_bin))
    assert data['value'] == 100

    # Step 5: Modify data
    data['value'] = 200

    # Step 6: Encode modified data
    encoder = BinaryEncoder(schema)
    modified_bin = tmp_path / "modified.bin"
    encoder.save_binary(data, str(modified_bin))

    # Step 7: Parse modified binary and verify
    data2 = bin_parser.parse_binary(str(modified_bin))
    assert data2['value'] == 200
```

### 8.3 Running Tests

```bash
# Install pytest
pip install pytest

# Run all tests
pytest tests/

# Run with coverage
pip install pytest-cov
pytest --cov=src tests/

# Run specific test file
pytest tests/test_schema.py

# Run specific test
pytest tests/test_schema.py::TestPrimitiveType::test_from_c_type_valid

# Verbose output
pytest -v tests/

# Show print statements
pytest -s tests/
```

---

## 9. Code Quality Tools

### 9.1 Type Checking with mypy

```bash
# Install mypy
pip install mypy

# Run type checking
mypy src/

# Create mypy.ini configuration
cat > mypy.ini << EOF
[mypy]
python_version = 3.8
warn_return_any = True
warn_unused_configs = True
disallow_untyped_defs = True
EOF
```

### 9.2 Linting with pylint

```bash
# Install pylint
pip install pylint

# Run linter
pylint src/

# Create .pylintrc configuration
pylint --generate-rcfile > .pylintrc

# Customize settings
# - Line length: 100
# - Disable specific warnings if needed
```

### 9.3 Code Formatting with black

```bash
# Install black
pip install black

# Format all files
black src/

# Check without modifying
black --check src/

# Set line length
black --line-length 100 src/
```

---

## 10. Debugging Techniques

### 10.1 Enabling Debug Logging

**Add to main.py:**

```python
import logging

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('eeprom_tool.log'),
        logging.StreamHandler()
    ]
)

# Use in modules
logger = logging.getLogger(__name__)

# In code
logger.debug(f"Parsing field: {field_name}")
logger.info(f"Loaded binary: {file_path}")
logger.warning(f"Size mismatch: {actual} != {expected}")
logger.error(f"Failed to parse: {error}", exc_info=True)
```

### 10.2 Using Python Debugger (pdb)

```python
# Insert breakpoint in code
import pdb; pdb.set_trace()

# Python 3.7+ built-in breakpoint
breakpoint()
```

**Run with debugger:**

```bash
python -m pdb main.py
```

**Useful pdb commands:**
- `n` - Next line
- `s` - Step into function
- `c` - Continue until breakpoint
- `p variable` - Print variable
- `pp variable` - Pretty-print variable
- `l` - List source code
- `b file.py:123` - Set breakpoint
- `bt` - Backtrace (call stack)

### 10.3 Qt Debugging

**Enable Qt debug messages:**

```python
import os
os.environ['QT_DEBUG_PLUGINS'] = '1'

from PyQt6.QtCore import qDebug, qWarning
qDebug("Debug message")
qWarning("Warning message")
```

---

## 11. Future Architecture Improvements

### 11.1 Plugin System

**Design:**

```python
# src/core/plugin_interface.py
from abc import ABC, abstractmethod

class EepromPlugin(ABC):
    @abstractmethod
    def name(self) -> str:
        """Plugin name."""
        pass

    @abstractmethod
    def export(self, data: Dict, schema: EepromSchema, path: str):
        """Export data to custom format."""
        pass

    @abstractmethod
    def import_data(self, path: str) -> Dict:
        """Import data from custom format."""
        pass

# Example plugin
class JsonPlugin(EepromPlugin):
    def name(self):
        return "JSON Exporter"

    def export(self, data, schema, path):
        with open(path, 'w') as f:
            json.dump(data, f, indent=2)

    def import_data(self, path):
        with open(path) as f:
            return json.load(f)
```

### 11.2 Configuration File

**Use YAML/JSON for user preferences:**

```yaml
# eeprom_config.yaml
recent_files:
  headers:
    - /path/to/header1.h
    - /path/to/header2.h
  binaries:
    - /path/to/binary1.bin

preferences:
  auto_reload: true
  warn_on_size_mismatch: true
  default_export_format: json

window:
  width: 1200
  height: 800
  splitter_pos: [360, 840]
```

---

**End of Technical Implementation Guide**

This guide provides deep technical details for developers working on the EEPROM Layout Editor codebase. For user-facing documentation, see README.md and QUICKSTART.md. For architectural overview, see SoftwareDoc.md.
