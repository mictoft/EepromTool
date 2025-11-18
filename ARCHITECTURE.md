# EEPROM Layout Editor - Architecture Documentation

**Version:** 1.0.0
**Last Updated:** 2025-11-18
**Purpose:** System architecture, design patterns, and structural decisions

---

## Table of Contents

1. [System Overview](#1-system-overview)
2. [Architectural Patterns](#2-architectural-patterns)
3. [Component Diagrams](#3-component-diagrams)
4. [Data Flow](#4-data-flow)
5. [Design Decisions](#5-design-decisions)
6. [Module Interface Contracts](#6-module-interface-contracts)
7. [Deployment Architecture](#7-deployment-architecture)

---

## 1. System Overview

### 1.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                       EEPROM Layout Editor                          │
│                     Desktop Application (PyQt6)                     │
└─────────────────────────────────────────────────────────────────────┘
                                  │
                    ┌─────────────┼─────────────┐
                    │             │             │
          ┌─────────▼──────┐ ┌───▼────┐ ┌──────▼─────┐
          │ C Header Files │ │ Binary │ │   User     │
          │     (.h)       │ │ Files  │ │ Interaction│
          │                │ │ (.bin) │ │            │
          └────────────────┘ └────────┘ └────────────┘
                INPUT         INPUT/      OUTPUT
                             OUTPUT
```

### 1.2 System Context Diagram

```
┌──────────────┐
│   Engineer   │
│  (User Role) │
└──────┬───────┘
       │ Uses
       │
       ▼
┌──────────────────────────────────────────┐
│    EEPROM Layout Editor Application      │
│  ┌────────────────────────────────────┐  │
│  │  • Parse C header files            │  │
│  │  • Read/write EEPROM binaries      │  │
│  │  • Display/edit structured data    │  │
│  │  • Validate data types             │  │
│  └────────────────────────────────────┘  │
└────┬────────────────┬────────────────────┘
     │                │
     │ Reads          │ Reads/Writes
     │                │
┌────▼────────┐  ┌────▼───────┐
│  Header     │  │  EEPROM    │
│  Files      │  │  Binary    │
│  (.h)       │  │  Files     │
│             │  │  (.bin)    │
└─────────────┘  └────────────┘
```

### 1.3 Technology Stack

```
┌───────────────────────────────────────────────────┐
│             Application Layer                     │
│                                                   │
│  ┌─────────────────────────────────────────────┐ │
│  │           PyQt6 6.4.0+                      │ │
│  │  - QMainWindow, QTreeWidget, QTableView     │ │
│  │  - QDialog, QFileDialog, QMessageBox        │ │
│  │  - QAbstractTableModel (MVC pattern)        │ │
│  └─────────────────────────────────────────────┘ │
│                                                   │
│  ┌─────────────────────────────────────────────┐ │
│  │           Python 3.8+                       │ │
│  │  - dataclasses (schema definitions)         │ │
│  │  - struct (binary encoding/decoding)        │ │
│  │  - re (regex parsing)                       │ │
│  │  - typing (type hints)                      │ │
│  └─────────────────────────────────────────────┘ │
└───────────────────────────────────────────────────┘
                      │
                      │ Runs on
                      ▼
┌───────────────────────────────────────────────────┐
│           Operating System                        │
│  - Linux (primary)                                │
│  - Windows (supported)                            │
│  - macOS (theoretically compatible)               │
└───────────────────────────────────────────────────┘
```

---

## 2. Architectural Patterns

### 2.1 Layered Architecture

The application follows a strict 4-layer architecture:

```
┌─────────────────────────────────────────────────────────┐
│  Layer 4: Presentation (UI)                             │
│  ────────────────────────────────────────────────────   │
│  • main_window.py - Main application window             │
│  • editors.py - Field editor dialogs                    │
│  • Qt widgets and event handlers                        │
│  • User input/output                                    │
│                                                          │
│  Dependencies: Layer 3 (Application)                    │
│  Forbidden: Direct access to parsers/encoders           │
└─────────────────────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────┐
│  Layer 3: Application (Models)                          │
│  ────────────────────────────────────────────────────   │
│  • model.py - Qt data models                            │
│  • EepromDataModel - Application state                  │
│  • FieldTableModel - Table view adapter                 │
│                                                          │
│  Dependencies: Layer 2 (Business Logic), Layer 1 (Data) │
│  Forbidden: Direct UI widget manipulation               │
└─────────────────────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────┐
│  Layer 2: Business Logic (Core)                         │
│  ────────────────────────────────────────────────────   │
│  • header_parser.py - Parse C headers                   │
│  • binary_parser.py - Decode binaries                   │
│  • encoder.py - Encode binaries                         │
│  • Pure business logic, no UI dependencies              │
│                                                          │
│  Dependencies: Layer 1 (Data)                           │
│  Forbidden: Qt imports, UI logic                        │
└─────────────────────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────┐
│  Layer 1: Data (Schema)                                 │
│  ────────────────────────────────────────────────────   │
│  • schema.py - Data structure definitions               │
│  • PrimitiveType enum                                   │
│  • FieldDef, StructDef, EepromSchema dataclasses        │
│  • Pure data, no logic                                  │
│                                                          │
│  Dependencies: None (Python stdlib only)                │
│  Forbidden: Business logic, UI code                     │
└─────────────────────────────────────────────────────────┘
```

**Key Principle:** Dependencies flow downward only. No circular dependencies.

### 2.2 Model-View Pattern (Qt MVC)

```
┌─────────────────────────────────────────────────┐
│                   VIEW                          │
│  ┌───────────────────────────────────────────┐  │
│  │  QTreeWidget                              │  │
│  │  - Displays struct hierarchy              │  │
│  │  - Emits itemClicked signal               │  │
│  └───────────────────────────────────────────┘  │
│  ┌───────────────────────────────────────────┐  │
│  │  QTableView                               │  │
│  │  - Displays field details                 │  │
│  │  - Emits doubleClicked signal             │  │
│  │  - Uses FieldTableModel                   │  │
│  └───────────────────────────────────────────┘  │
└──────────────┬──────────────────────────────────┘
               │
               │ Observes
               ▼
┌─────────────────────────────────────────────────┐
│                   MODEL                         │
│  ┌───────────────────────────────────────────┐  │
│  │  FieldTableModel (QAbstractTableModel)    │  │
│  │  - Implements Qt model interface          │  │
│  │  - Provides data() for display            │  │
│  │  - Provides setData() for editing         │  │
│  │  - Emits dataChanged signal               │  │
│  └───────────────────────────────────────────┘  │
│  ┌───────────────────────────────────────────┐  │
│  │  EepromDataModel                          │  │
│  │  - Holds actual data (nested dicts)       │  │
│  │  - Tracks modifications                   │  │
│  │  - Provides path-based get/set            │  │
│  └───────────────────────────────────────────┘  │
└─────────────────────────────────────────────────┘
```

**Benefits:**
- Separation of concerns (data vs. display)
- Multiple views can share same model
- Easy to test models independently

### 2.3 Repository Pattern (Data Access)

```
┌─────────────────────────────────────────────────┐
│           Application Layer                     │
└──────────┬──────────────────────────────────────┘
           │ Uses
           ▼
┌─────────────────────────────────────────────────┐
│     Data Access Layer (Repositories)            │
│  ┌───────────────────────────────────────────┐  │
│  │  HeaderParser                             │  │
│  │  + parse_header(path) -> Schema           │  │
│  └───────────────────────────────────────────┘  │
│  ┌───────────────────────────────────────────┐  │
│  │  BinaryParser                             │  │
│  │  + parse_binary(path) -> Dict             │  │
│  └───────────────────────────────────────────┘  │
│  ┌───────────────────────────────────────────┐  │
│  │  BinaryEncoder                            │  │
│  │  + save_binary(data, path)                │  │
│  └───────────────────────────────────────────┘  │
└──────────┬──────────────────────────────────────┘
           │ Accesses
           ▼
┌─────────────────────────────────────────────────┐
│              File System                        │
│  - Header files (.h)                            │
│  - Binary files (.bin)                          │
└─────────────────────────────────────────────────┘
```

**Benefits:**
- Abstraction over file I/O
- Easy to mock for testing
- Can be replaced with database/network access

### 2.4 Strategy Pattern (Field Editing)

```
┌──────────────────────────────────────┐
│     FieldEditorDialog                │
│                                      │
│  + __init__(field, value)            │
│  + init_ui()                         │
│  + get_value() -> Any                │
└────────┬─────────────────────────────┘
         │
         │ Delegates to
         │
    ┌────┴────┬────────┬────────┬────────┐
    │         │        │        │        │
    ▼         ▼        ▼        ▼        ▼
┌────────┐ ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐
│Spinbox │ │String│ │ Hex  │ │Array │ │Struct│
│Editor  │ │Editor│ │Editor│ │Editor│ │ Msg  │
└────────┘ └──────┘ └──────┘ └──────┘ └──────┘
  uint8      char[]   uint8[]  Others  (nav)
```

**Selection Logic:**
```python
if field.is_struct:
    show_navigation_message()
elif field.is_array:
    create_array_editor()  # Selects hex/string/numeric
elif field.primitive_type:
    create_primitive_editor()  # Selects spinbox/char
```

**Benefits:**
- Single dialog class, multiple editing strategies
- Easy to add new editor types
- Type-safe editing enforcement

---

## 3. Component Diagrams

### 3.1 Core Module Dependencies

```
                    schema.py
                (PrimitiveType,
                 FieldDef,
                 StructDef,
                 EepromSchema)
                      │
        ┌─────────────┼─────────────┬──────────────┐
        │             │             │              │
        ▼             ▼             ▼              ▼
  header_parser   binary_parser   encoder       model.py
        │             │             │              │
        │             │             │              │
        └─────────────┴─────────────┴──────────────┘
                          │
                          │ All depend on schema
                          │
                          ▼
                  (No mutual dependencies)
```

**Dependency Rules:**
1. All core modules depend on `schema.py`
2. No core module depends on another core module
3. This creates a **hub-and-spoke** pattern
4. Schema is the central contract

### 3.2 UI Module Dependencies

```
                    main_window.py
                          │
                ┌─────────┼─────────┐
                │         │         │
                ▼         ▼         ▼
            editors    model    core/*
                │         │         │
                └─────────┴─────────┘
                          │
                    All UI modules
                 can access core modules
```

### 3.3 Full System Component Diagram

```
┌───────────────────────────────────────────────────────────┐
│                     main.py                               │
│  • QApplication initialization                            │
│  • MainWindow creation                                    │
│  • Event loop                                             │
└────────────────────────┬──────────────────────────────────┘
                         │
                         ▼
┌───────────────────────────────────────────────────────────┐
│                  src/ui/main_window.py                    │
│  ┌─────────────────────────────────────────────────────┐  │
│  │  MainWindow (QMainWindow)                           │  │
│  │  • Menu bar                                         │  │
│  │  • Tree widget (struct navigation)                  │  │
│  │  • Table view (field display)                       │  │
│  │  • Status bar                                       │  │
│  │  • State: schema, data_model, file paths            │  │
│  └─────────────────────────────────────────────────────┘  │
└───┬──────────────┬──────────────┬────────────────┬────────┘
    │              │              │                │
    │ Uses         │ Uses         │ Uses           │ Uses
    ▼              ▼              ▼                ▼
┌─────────┐  ┌──────────┐  ┌──────────────┐  ┌─────────┐
│ editors │  │  model   │  │header_parser │  │ binary  │
│   .py   │  │   .py    │  │     .py      │  │_parser  │
└─────────┘  └──────────┘  └──────────────┘  │  .py    │
                  │              │            └─────────┘
                  │ Uses         │ Uses            │
                  │              │                 │ Uses
                  ▼              ▼                 ▼
             ┌─────────────────────────────────────────┐
             │           src/core/schema.py            │
             │  • PrimitiveType enum                   │
             │  • FieldDef dataclass                   │
             │  • StructDef dataclass                  │
             │  • EepromSchema dataclass               │
             └─────────────────────────────────────────┘
```

---

## 4. Data Flow

### 4.1 Load Header File Sequence

```
User                MainWindow         HeaderParser        EepromSchema
  │                     │                    │                  │
  │  File→Open Header   │                    │                  │
  ├────────────────────>│                    │                  │
  │                     │                    │                  │
  │                     │ parse_header(path) │                  │
  │                     ├───────────────────>│                  │
  │                     │                    │                  │
  │                     │                    │ create schema    │
  │                     │                    ├─────────────────>│
  │                     │                    │                  │
  │                     │                    │<─────────────────┤
  │                     │                    │                  │
  │                     │<───────────────────┤                  │
  │                     │  return schema     │                  │
  │                     │                    │                  │
  │    Success dialog   │                    │                  │
  │<────────────────────┤                    │                  │
  │                     │                    │                  │
```

### 4.2 Load Binary File Sequence

```
User        MainWindow    BinaryParser   EepromDataModel    TreeWidget
  │             │              │                │               │
  │ File→Open   │              │                │               │
  │    BIN      │              │                │               │
  ├────────────>│              │                │               │
  │             │              │                │               │
  │             │ parse_binary │                │               │
  │             ├─────────────>│                │               │
  │             │              │                │               │
  │             │<─────────────┤                │               │
  │             │  return data │                │               │
  │             │              │                │               │
  │             │ new EepromDataModel(data)     │               │
  │             ├──────────────────────────────>│               │
  │             │              │                │               │
  │             │ populate_tree()               │               │
  │             ├──────────────────────────────────────────────>│
  │             │              │                │               │
  │  Tree       │              │                │               │
  │ populated   │              │                │               │
  │<────────────┤              │                │               │
  │             │              │                │               │
```

### 4.3 Edit Field Sequence

```
User    TableView   MainWindow   EditorDialog   DataModel   TableModel
  │         │           │             │             │            │
  │ Double  │           │             │             │            │
  │  click  │           │             │             │            │
  ├────────>│           │             │             │            │
  │         │           │             │             │            │
  │         │ doubleClick            │             │            │
  │         │   signal  │             │             │            │
  │         ├──────────>│             │             │            │
  │         │           │             │             │            │
  │         │           │ get_value() │             │            │
  │         │           ├────────────────────────────┤            │
  │         │           │             │             │            │
  │         │           │ show dialog │             │            │
  │         │           ├────────────>│             │            │
  │         │           │             │             │            │
  │    Edit value in dialog           │             │            │
  │<──────────────────────────────────┤             │            │
  │         │           │             │             │            │
  │  Click OK                         │             │            │
  ├──────────────────────────────────>│             │            │
  │         │           │             │             │            │
  │         │           │ get_value() │             │            │
  │         │           │<────────────┤             │            │
  │         │           │             │             │            │
  │         │           │ set_value(new)            │            │
  │         │           ├────────────────────────────┤            │
  │         │           │             │             │            │
  │         │           │ dataChanged signal         │            │
  │         │           ├────────────────────────────────────────>│
  │         │           │             │             │            │
  │         │   Table refreshes       │             │            │
  │<─────────────────────────────────────────────────────────────┤
  │         │           │             │             │            │
```

### 4.4 Save Binary Sequence

```
User      MainWindow    BinaryEncoder    DataModel    FileSystem
  │           │              │               │            │
  │ File→Save │              │               │            │
  │    BIN As │              │               │            │
  ├──────────>│              │               │            │
  │           │              │               │            │
  │           │ encode_to_binary(data)       │            │
  │           ├─────────────>│               │            │
  │           │              │               │            │
  │           │              │ get all data  │            │
  │           │              ├──────────────>│            │
  │           │              │               │            │
  │           │              │<──────────────┤            │
  │           │              │               │            │
  │           │<─────────────┤               │            │
  │           │  return bytes│               │            │
  │           │              │               │            │
  │           │ write(path, bytes)           │            │
  │           ├────────────────────────────────────────────>│
  │           │              │               │            │
  │  Success  │              │               │            │
  │<──────────┤              │               │            │
  │           │              │               │            │
```

---

## 5. Design Decisions

### 5.1 Why Python?

**Decision:** Use Python instead of C++

**Alternatives Considered:**
- C++ with Qt
- JavaScript with Electron
- Rust with Qt bindings

**Rationale:**

| Criterion | Python | C++ | JavaScript | Rust |
|-----------|--------|-----|------------|------|
| Development Speed | ✅ Fast | ❌ Slow | ✅ Fast | ⚠️ Medium |
| Binary Parsing | ✅ struct module | ✅ Native | ❌ Complex | ✅ Native |
| Regex Support | ✅ Built-in | ✅ std::regex | ✅ Built-in | ✅ crates |
| Cross-platform | ✅ PyQt6 | ✅ Qt | ✅ Electron | ⚠️ Bindings |
| Performance | ⚠️ Adequate | ✅ Excellent | ⚠️ Adequate | ✅ Excellent |
| Deployment | ❌ Needs Python | ✅ Native | ✅ Packaged | ✅ Native |

**Conclusion:** Python provides the best balance of development speed and functionality for EEPROM file sizes (KB-MB range).

### 5.2 Why PyQt6?

**Decision:** Use PyQt6 instead of alternatives

**Alternatives Considered:**
- PySide6 (Qt for Python)
- Tkinter (Python built-in)
- wxPython
- Kivy

**Rationale:**

| Feature | PyQt6 | PySide6 | Tkinter | wxPython |
|---------|-------|---------|---------|----------|
| License | GPL/Commercial | LGPL | Free | wxWindows |
| Performance | ✅ Excellent | ✅ Excellent | ⚠️ Basic | ✅ Good |
| Look & Feel | ✅ Native | ✅ Native | ❌ Old | ✅ Native |
| Table/Tree | ✅ Advanced | ✅ Advanced | ⚠️ Basic | ✅ Good |
| Documentation | ✅ Extensive | ✅ Good | ✅ Good | ⚠️ Limited |

**Conclusion:** PyQt6 provides professional desktop UI with excellent Model/View components.

### 5.3 Why Regex for Parsing?

**Decision:** Use regex instead of C parser library

**Alternatives Considered:**
- libclang + Python bindings
- pycparser
- Manual lexer/parser
- ANTLR grammar

**Rationale:**

**Pros of Regex:**
- ✅ Simple implementation (~200 lines)
- ✅ No external C dependencies
- ✅ Adequate for limited scope (packed structs only)
- ✅ Easy to debug and modify

**Cons of Regex:**
- ❌ Cannot handle complex C features (macros, conditionals)
- ❌ Fragile for unusual formatting
- ❌ No syntax tree

**Conclusion:** Regex is sufficient for the constrained input format (simple packed structs).

### 5.4 Why Little-Endian Only?

**Decision:** Support only little-endian byte order

**Alternatives Considered:**
- Support both little and big-endian
- Auto-detect endianness
- Make it configurable

**Rationale:**

**Market Analysis:**
- 95%+ of embedded systems use little-endian (ARM, x86)
- Big-endian mostly legacy (older PowerPC, SPARC)
- Mixed endianness is rare

**Implementation Impact:**
- Supporting both requires extra complexity
- Need UI setting or header annotation
- Testing burden doubles

**Conclusion:** YAGNI principle - add big-endian only when needed.

### 5.5 In-Memory vs. Streaming

**Decision:** Load entire binary into memory

**Alternatives Considered:**
- Memory-mapped files
- Streaming parser
- Lazy loading

**Rationale:**

**File Size Analysis:**
- Typical EEPROM: 32KB - 1MB
- Large EEPROM: Up to 8MB
- Modern RAM: GB range

**Performance:**
- Loading 1MB file: <10ms
- Parsing in memory: Fast random access
- No I/O during parsing

**Conclusion:** In-memory processing is simpler and faster for typical file sizes.

---

## 6. Module Interface Contracts

### 6.1 schema.py Interface

**Purpose:** Define data structures (no logic)

**Exports:**
```python
class PrimitiveType(Enum)
    + from_c_type(str) -> Optional[PrimitiveType]

@dataclass FieldDef
    name: str
    type_name: str
    size: int
    offset: int
    absolute_offset: int
    is_array: bool
    array_length: int
    is_struct: bool
    primitive_type: Optional[PrimitiveType]

@dataclass StructDef
    name: str
    fields: List[FieldDef]
    size: int
    is_packed: bool
    + add_field(FieldDef)
    + get_field(str) -> Optional[FieldDef]

@dataclass EepromSchema
    root_struct_name: str
    structs: Dict[str, StructDef]
    total_size: int
    + add_struct(StructDef)
    + get_struct(str) -> Optional[StructDef]
    + get_root_struct() -> Optional[StructDef]
    + is_struct_type(str) -> bool
```

**Invariants:**
- All offsets are non-negative
- Field sizes match type sizes
- Struct size = sum of field sizes

### 6.2 header_parser.py Interface

**Purpose:** Parse C headers into schema

**Exports:**
```python
class HeaderParser
    + parse_header(path: str) -> EepromSchema
        Raises: ValueError, FileNotFoundError
```

**Contract:**
- **Preconditions:**
  - File must exist
  - File must contain at least one packed struct
- **Postconditions:**
  - Returns valid EepromSchema
  - All offsets calculated correctly
  - Root struct identified
- **Side Effects:**
  - Prints warnings to stdout for unknown types

### 6.3 binary_parser.py Interface

**Purpose:** Decode binary files

**Exports:**
```python
class BinaryParser
    + __init__(schema: EepromSchema)
    + parse_binary(path: str) -> Dict[str, Any]
    + validate_binary_size(path: str) -> Tuple[bool, int, int]
```

**Contract:**
- **Preconditions:**
  - Schema must be valid
  - Binary file must exist
- **Postconditions:**
  - Returns nested dict matching schema structure
  - All primitive values correctly decoded
  - Arrays returned as lists or bytes
- **Side Effects:**
  - Prints warnings for size mismatches

### 6.4 encoder.py Interface

**Purpose:** Encode Python data to binary

**Exports:**
```python
class BinaryEncoder
    + __init__(schema: EepromSchema)
    + encode_to_binary(data: Dict[str, Any]) -> bytes
    + save_binary(data: Dict[str, Any], path: str)
```

**Contract:**
- **Preconditions:**
  - Schema must be valid
  - Data structure must match schema
- **Postconditions:**
  - Returns bytes of correct size (schema.total_size)
  - All values encoded in little-endian
  - Out-of-range values clamped
- **Side Effects:**
  - Prints warnings for clamped values
  - Creates/overwrites file on disk

---

## 7. Deployment Architecture

### 7.1 Development Deployment

```
┌──────────────────────────────────┐
│   Developer Machine              │
│                                  │
│  ┌────────────────────────────┐  │
│  │  Python 3.8+ Environment   │  │
│  │  - PyQt6 from pip          │  │
│  │  - Source code from git    │  │
│  └────────────────────────────┘  │
│                                  │
│  Run: python main.py             │
│                                  │
│  Files:                          │
│  - /home/user/EepromTool/        │
│    - main.py                     │
│    - src/                        │
│    - examples/                   │
└──────────────────────────────────┘
```

### 7.2 End-User Deployment (Future)

**Option A: Python Required**

```
┌──────────────────────────────────┐
│   End User Machine               │
│                                  │
│  1. Install Python 3.8+          │
│  2. pip install -r requirements  │
│  3. Run: python main.py          │
│                                  │
│  Pros: Simple distribution       │
│  Cons: Python required           │
└──────────────────────────────────┘
```

**Option B: Standalone Executable**

```
┌──────────────────────────────────┐
│   End User Machine               │
│                                  │
│  1. Download .exe (Windows) or   │
│     .app bundle (macOS)          │
│  2. Double-click to run          │
│                                  │
│  Created with: PyInstaller       │
│  Size: ~50MB (includes Python)   │
│                                  │
│  Pros: No Python needed          │
│  Cons: Large file size           │
└──────────────────────────────────┘
```

### 7.3 System Requirements

**Minimum:**
- CPU: 1 GHz processor
- RAM: 512 MB
- Disk: 100 MB for application
- OS: Linux/Windows/macOS with Python 3.8+

**Recommended:**
- CPU: 2 GHz multi-core
- RAM: 2 GB
- Disk: 500 MB for application + data
- Display: 1280x800 or higher

---

**End of Architecture Documentation**

This document provides comprehensive architectural information for the EEPROM Layout Editor. For implementation details, see TECHNICAL_GUIDE.md. For user documentation, see README.md.
