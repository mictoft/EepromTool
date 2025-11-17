"""
Schema definitions for EEPROM memory layout structures.
"""
from typing import List, Dict, Optional, Union
from dataclasses import dataclass, field
from enum import Enum


class PrimitiveType(Enum):
    """Supported primitive C types."""
    UINT8 = ('uint8_t', 1, 'B')
    UINT16 = ('uint16_t', 2, 'H')
    UINT32 = ('uint32_t', 4, 'I')
    INT8 = ('int8_t', 1, 'b')
    INT16 = ('int16_t', 2, 'h')
    INT32 = ('int32_t', 4, 'i')
    CHAR = ('char', 1, 'c')

    def __init__(self, c_type: str, size: int, struct_format: str):
        self.c_type = c_type
        self.size = size
        self.struct_format = struct_format

    @classmethod
    def from_c_type(cls, c_type: str) -> Optional['PrimitiveType']:
        """Get PrimitiveType from C type string."""
        for ptype in cls:
            if ptype.c_type == c_type:
                return ptype
        return None


@dataclass
class FieldDef:
    """Definition of a single field in a struct."""
    name: str
    type_name: str  # Either primitive type or struct name
    size: int  # Size in bytes
    offset: int  # Relative offset within parent struct
    absolute_offset: int  # Absolute offset in EEPROM
    is_array: bool = False
    array_length: int = 1
    is_struct: bool = False
    primitive_type: Optional[PrimitiveType] = None

    def __repr__(self):
        array_str = f"[{self.array_length}]" if self.is_array else ""
        return f"FieldDef({self.name}: {self.type_name}{array_str} @ {self.offset})"


@dataclass
class StructDef:
    """Definition of a C struct."""
    name: str
    fields: List[FieldDef] = field(default_factory=list)
    size: int = 0  # Total size in bytes
    is_packed: bool = True

    def add_field(self, field_def: FieldDef):
        """Add a field to this struct."""
        self.fields.append(field_def)
        self.size += field_def.size

    def get_field(self, name: str) -> Optional[FieldDef]:
        """Get field by name."""
        for f in self.fields:
            if f.name == name:
                return f
        return None

    def __repr__(self):
        return f"StructDef({self.name}, {len(self.fields)} fields, {self.size} bytes)"


@dataclass
class EepromSchema:
    """Complete EEPROM memory layout schema."""
    root_struct_name: str
    structs: Dict[str, StructDef] = field(default_factory=dict)
    total_size: int = 0

    def add_struct(self, struct_def: StructDef):
        """Add a struct definition to the schema."""
        self.structs[struct_def.name] = struct_def

    def get_struct(self, name: str) -> Optional[StructDef]:
        """Get struct definition by name."""
        return self.structs.get(name)

    def get_root_struct(self) -> Optional[StructDef]:
        """Get the root struct definition."""
        return self.structs.get(self.root_struct_name)

    def is_struct_type(self, type_name: str) -> bool:
        """Check if a type name is a struct."""
        return type_name in self.structs

    def __repr__(self):
        return f"EepromSchema({self.root_struct_name}, {len(self.structs)} structs, {self.total_size} bytes)"
