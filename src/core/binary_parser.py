"""
Binary parser for EEPROM .bin files.
"""
import struct
from typing import Any, Dict, List, Union
from .schema import EepromSchema, StructDef, FieldDef, PrimitiveType


class BinaryParser:
    """Parse binary EEPROM files based on schema."""

    def __init__(self, schema: EepromSchema):
        self.schema = schema

    def parse_binary(self, bin_path: str) -> Dict[str, Any]:
        """
        Parse a binary file and return decoded data structure.

        Args:
            bin_path: Path to .bin file

        Returns:
            Dictionary representing the parsed data
        """
        with open(bin_path, 'rb') as f:
            data = f.read()

        # Validate file size
        expected_size = self.schema.total_size
        if len(data) != expected_size:
            print(f"Warning: Binary file size ({len(data)} bytes) does not match "
                  f"expected size ({expected_size} bytes)")

        # Parse root struct
        root_struct = self.schema.get_root_struct()
        if not root_struct:
            raise ValueError("No root struct found in schema")

        result = self._parse_struct(root_struct, data, 0)
        return result

    def _parse_struct(self, struct_def: StructDef, data: bytes, offset: int) -> Dict[str, Any]:
        """
        Parse a struct from binary data.

        Args:
            struct_def: Struct definition
            data: Binary data
            offset: Starting offset in data

        Returns:
            Dictionary with field names as keys and parsed values
        """
        result = {}

        for field in struct_def.fields:
            field_offset = offset + field.offset
            value = self._parse_field(field, data, field_offset)
            result[field.name] = value

        return result

    def _parse_field(self, field: FieldDef, data: bytes, offset: int) -> Any:
        """
        Parse a single field from binary data.

        Args:
            field: Field definition
            data: Binary data
            offset: Starting offset in data

        Returns:
            Parsed value (primitive, list, or dict for nested struct)
        """
        if field.is_struct:
            # Nested struct or struct array
            nested_struct = self.schema.get_struct(field.type_name)
            if not nested_struct:
                raise ValueError(f"Unknown struct type: {field.type_name}")

            if field.is_array:
                # Array of structs
                result = []
                for i in range(field.array_length):
                    element_offset = offset + (i * nested_struct.size)
                    element = self._parse_struct(nested_struct, data, element_offset)
                    result.append(element)
                return result
            else:
                # Single nested struct
                return self._parse_struct(nested_struct, data, offset)

        elif field.primitive_type:
            # Primitive type or array of primitives
            if field.is_array:
                return self._parse_primitive_array(field, data, offset)
            else:
                return self._parse_primitive(field.primitive_type, data, offset)

        else:
            # Fallback: read as raw bytes
            return data[offset:offset + field.size]

    def _parse_primitive(self, ptype: PrimitiveType, data: bytes, offset: int) -> Union[int, bytes]:
        """Parse a single primitive value."""
        try:
            # Use little-endian format
            format_str = '<' + ptype.struct_format
            value = struct.unpack_from(format_str, data, offset)[0]

            # Convert char to int if needed
            if ptype == PrimitiveType.CHAR:
                if isinstance(value, bytes):
                    return ord(value) if len(value) > 0 else 0
                return value

            return value
        except struct.error as e:
            print(f"Error parsing {ptype.c_type} at offset {offset}: {e}")
            return 0

    def _parse_primitive_array(self, field: FieldDef, data: bytes, offset: int) -> Union[List, bytes]:
        """Parse an array of primitive values."""
        ptype = field.primitive_type

        # For char arrays, treat as byte string
        if ptype == PrimitiveType.CHAR:
            raw_bytes = data[offset:offset + field.size]
            # Find null terminator for C strings
            null_pos = raw_bytes.find(b'\x00')
            if null_pos >= 0:
                return raw_bytes[:null_pos]
            return raw_bytes

        # For uint8_t arrays, return as bytes for hex editing
        if ptype == PrimitiveType.UINT8:
            return data[offset:offset + field.size]

        # For other types, parse each element
        result = []
        element_size = ptype.size
        for i in range(field.array_length):
            element_offset = offset + (i * element_size)
            value = self._parse_primitive(ptype, data, element_offset)
            result.append(value)

        return result

    def validate_binary_size(self, bin_path: str) -> tuple[bool, int, int]:
        """
        Validate that binary file has correct size.

        Returns:
            (is_valid, actual_size, expected_size)
        """
        try:
            with open(bin_path, 'rb') as f:
                data = f.read()
            actual_size = len(data)
            expected_size = self.schema.total_size
            return (actual_size == expected_size, actual_size, expected_size)
        except Exception as e:
            print(f"Error validating binary: {e}")
            return (False, 0, self.schema.total_size)
