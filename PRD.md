# **Product Requirements Document (PRD)**

# **EEPROM Layout Editor – PyQt6 Desktop Application**

---

## **1. Overview**

The EEPROM Layout Editor is a cross‑platform (Linux + Windows) desktop application built with **Python** and **PyQt6**. It allows engineers and developers to **view, edit, and validate EEPROM binary files** based on a fixed, packed memory layout defined in a C header file (`eepromMemLayout.h`).

The application reads the EEPROM struct definitions directly from the header file, interprets binary data from `.bin` files, displays it in a structured GUI, and allows users to modify values and export updated binaries.

Encryption-related fields may be added later but are out of scope for the initial release.

---

## **2. Goals & Non‑Goals**

### **2.1 Goals**

* Parse the EEPROM memory layout from a fixed C header file.
* Support hierarchical packed structs containing:

  * uint8_t
  * uint16_t
  * uint32_t
  * byte arrays (fixed‑size)
  * struct arrays (optional if present)
* Display structure and values in a clear, navigable UI.
* Enable editing of EEPROM values with type‑appropriate widgets.
* Save modified values back into a `.bin` file.
* Work on Linux and Windows.
* Provide convenient UX for embedded engineers.

### **2.2 Non‑Goals**

* Parsing arbitrary header files (only the provided header is supported).
* Shell integration or command‑line interface.
* Real‑time device flashing.
* Handling encrypted EEPROM fields (future work).
* Support for unions or bitfields.

---

## **3. Target Users**

* Embedded engineers
* QA engineers testing firmware
* Field application engineers
* Developers maintaining systems using EEPROM-based configuration storage

Users understand embedded data types, EEPROM storage, and binary formats.

---

## **4. Functional Requirements**

### **4.1 Header Parsing**

The application must:

* Parse a single header file containing the full EEPROM memory definition.
* Detect:

  * `typedef struct __attribute__((__packed__)) { ... } NameType;`
  * Field names and types
  * Nested struct references
  * Arrays (e.g., `uint8_t myField[32];`)
* Build a recursive internal schema:

  * Struct name
  * Ordered field list
  * Field type
  * Field size (bytes)
  * Absolute offset in EEPROM map

### **4.2 Binary File Handling**

* Accept `.bin` file input (fixed 32 kB size).
* Display error for incorrect file sizes.
* Decode each struct and field according to the schema.
* Track values in a data model separate from the raw binary.
* Allow value editing and re-encoding into binary.

### **4.3 UI/UX Requirements**

#### **4.3.1 Main Window Layout**

* **Left Pane**: Hierarchical tree of EEPROM structs.
* **Right Pane**: Table view listing fields of the selected struct.
* **Menu Bar**:

  * File → Open Header
  * File → Open BIN
  * File → Save BIN As…
  * View → Reload
  * Help → About

#### **4.3.2 Table View Columns**

1. Field Name
2. Data Type
3. Offset (relative to struct)
4. Absolute Offset
5. Size (bytes)
6. Value (editable)

#### **4.3.3 Field Editing Widgets**

* **uint8/16/32:** QSpinBox/QDoubleSpinBox
* **bool:** QCheckBox
* **char[]:** QLineEdit
* **uint8_t[]:** Hex editor popup
* **enum (if present):** Dropdown combobox
* **Struct fields:** Navigated via tree on left

#### **4.3.4 Validation**

* Enforce min/max values for integer fields.
* Validate string lengths.
* Recalculate binary on save.
* Visual warnings when values exceed field size.

### **4.4 Saving/Exporting**

* Rebuild raw 32 kB binary from modified values.
* Write to user‑selected output file.
* Confirm success/failure.

### **4.5 Internal Architecture Requirements**

* Pure Python.
* PyQt6 UI.
* Data parsing using `struct` module.
* Use a Model/View design pattern.

---

## **5. Technical Architecture**

### **5.1 High-Level Architecture Diagram**

```
┌────────────────────────┐
│ eepromMemLayout.h      │
└───────────┬────────────┘
            │ Header Parser
            ▼
┌────────────────────────┐
│ Internal Struct Schema │
└───────────┬────────────┘
            │ Binary Parser
            ▼
┌───────────────────────────────┐
│ Python Object Model (Tree)    │
└───────────┬───────────────────┘
            │ Bound to Qt Model
            ▼
┌───────────────────────────────┐
│ PyQt6 GUI (Tree + Table View) │
└───────────┬───────────────────┘
            │ Changes Stored
            ▼
┌────────────────────────┐
│ Modified EEPROM Binary │
└────────────────────────┘
```

---

## **6. Detailed Architecture**

### **6.1 Modules**

#### **6.1.1 header_parser.py**

* Regex-based extraction of struct definitions
* Builds a nested Python schema
* Determines field size from C types
* Calculates offsets for all fields

#### **6.1.2 schema.py**

Defines classes:

* `StructDef`
* `FieldDef`
* `ArrayDef`
* `PrimitiveType`
* `EepromSchema`

#### **6.1.3 binary_parser.py**

* Reads `.bin` file
* Performs recursive decoding using `struct.unpack_from`
* Produces nested dict-like objects

#### **6.1.4 model.py**

* Qt data model (`QAbstractTableModel`)
* Holds decoded values
* Communicates changes to encoder

#### **6.1.5 encoder.py**

* Reverse of binary_parser
* Packs Python values back into binary
* Enforces limits and sizes

#### **6.1.6 ui/**

* PyQt6 window definitions
* Editors for each field type
* Hex editor popup

### **6.2 Data Flow**

```
header_parser → schema → binary_parser → model → encoder → save
```

### **6.3 Binary Handling Rules**

* All structs are packed (no padding)
* Little-endian encoding for all fields
* Arrays serialized sequentially

---

## **7. UX / Wireframes**

### **7.1 Main Window Layout**

```
┌─────────────────────────────────────────────────────────────┐
│ File | View | Help                                           │
├───────────────────────┬──────────────────────────────────────┤
│ EEPROM Struct Tree    │ Field Table                         │
│                       │                                      │
│ [EepromMemoryMapType] │ Name     | Type    | Offset | Value  │
│   ├ mem0              │--------------------------------------│
│   ├ mem1              │ p0x      | uint16  | 0x0004 | 123    │
│   ├ mem2              │ p0y      | uint16  | 0x0006 | 456    │
│   └ ...               │ ...                                    │
└───────────────────────┴──────────────────────────────────────┘
```

### **7.2 Field Editing Modal**

```
┌─────────────────────────────┐
│ Edit Field: mem4.pumpSpeed  │
├─────────────────────────────┤
│ Value: [  45 ]              │ (spinbox)
│ Type:  uint16               │
│ Size:  2 bytes              │
├─────────────────────────────┤
│ [  OK  ]   [ Cancel ]       │
└─────────────────────────────┘
```

### **7.3 Hex Editor for Byte Arrays**

```
┌─────────────────────────────┐
│ Edit: mem8.rawBytes[256]    │
├─────────────────────────────┤
│ 00 11 22 33 44 55 66 77 ... │
│ ...                         │
├─────────────────────────────┤
│ [ Load From File ] [ OK ]   │
└─────────────────────────────┘
```

---

## **8. Performance Requirements**

* Parse header under 200 ms
* Load `.bin` under 50 ms
* GUI actions respond under 100 ms
* Editing arrays up to 1024 bytes should remain smooth

---

## **9. Error Handling**

* Invalid header format → user-friendly message
* Incorrect `.bin` size → error dialog
* Out-of-range values → blocking validation
* Missing struct types → error on load
* Corrupt `.bin` → fallback to hex inspection mode

---

## **10. Security Considerations**

* No external network access
* No remote code execution
* Sensitive encrypted fields not processed
* Binary files processed locally only

---

## **11. Future Enhancements**

* AES encryption/decryption of specific fields
* Undo/Redo stack
* Hex-diff viewer
* Direct flashing to embedded hardware
* Automated validation for EEPROM files
* YAML export/import for easy editing

---

## **12. Acceptance Criteria**

The application is considered complete when:

* The header file is parsed correctly
* A `.bin` can be opened, viewed, edited
* Modified values persist and save correctly
* UI is stable under Linux and Windows
* Users can navigate structs and edit fields without confusion

---

# **End of PRD**
