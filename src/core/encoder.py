"""
Binary encoder for EEPROM data structures.
"""
import struct
from typing import Any, Dict, List, Union
from .schema import EepromSchema, StructDef, FieldDef, PrimitiveType


class BinaryEncoder:
    """Encode data structures back into binary EEPROM format."""

    def __init__(self, schema: EepromSchema):
        self.schema = schema

    def encode_to_binary(self, data: Dict[str, Any]) -> bytes:
        """
        Encode data structure to binary format.

        Args:
            data: Dictionary representing the data structure

        Returns:
            Binary data as bytes
        """
        # Create buffer of correct size
        buffer = bytearray(self.schema.total_size)

        # Encode root struct
        root_struct = self.schema.get_root_struct()
        if not root_struct:
            raise ValueError("No root struct found in schema")

        self._encode_struct(root_struct, data, buffer, 0)

        return bytes(buffer)

    def save_binary(self, data: Dict[str, Any], bin_path: str):
        """
        Encode and save data to a binary file.

        Args:
            data: Dictionary representing the data structure
            bin_path: Output file path
        """
        binary_data = self.encode_to_binary(data)

        with open(bin_path, 'wb') as f:
            f.write(binary_data)

    def _encode_struct(self, struct_def: StructDef, data: Dict[str, Any],
                       buffer: bytearray, offset: int):
        """
        Encode a struct into the binary buffer.

        Args:
            struct_def: Struct definition
            data: Data dictionary for this struct
            buffer: Binary buffer to write to
            offset: Starting offset in buffer
        """
        for field in struct_def.fields:
            if field.name not in data:
                print(f"Warning: Field {field.name} not found in data, skipping")
                continue

            field_offset = offset + field.offset
            field_value = data[field.name]
            self._encode_field(field, field_value, buffer, field_offset)

    def _encode_field(self, field: FieldDef, value: Any, buffer: bytearray, offset: int):
        """
        Encode a single field into the binary buffer.

        Args:
            field: Field definition
            value: Value to encode
            buffer: Binary buffer to write to
            offset: Starting offset in buffer
        """
        if field.is_struct:
            # Nested struct or struct array
            nested_struct = self.schema.get_struct(field.type_name)
            if not nested_struct:
                raise ValueError(f"Unknown struct type: {field.type_name}")

            if field.is_array:
                # Array of structs
                if not isinstance(value, list):
                    raise ValueError(f"Expected list for struct array {field.name}")

                for i, element in enumerate(value):
                    if i >= field.array_length:
                        break
                    element_offset = offset + (i * nested_struct.size)
                    self._encode_struct(nested_struct, element, buffer, element_offset)
            else:
                # Single nested struct
                if not isinstance(value, dict):
                    raise ValueError(f"Expected dict for struct {field.name}")
                self._encode_struct(nested_struct, value, buffer, offset)

        elif field.primitive_type:
            # Primitive type or array of primitives
            if field.is_array:
                self._encode_primitive_array(field, value, buffer, offset)
            else:
                self._encode_primitive(field.primitive_type, value, buffer, offset)

    def _encode_primitive(self, ptype: PrimitiveType, value: Any,
                         buffer: bytearray, offset: int):
        """Encode a single primitive value."""
        try:
            # Use little-endian format
            format_str = '<' + ptype.struct_format

            # Handle char type specially
            if ptype == PrimitiveType.CHAR:
                if isinstance(value, str):
                    value = ord(value[0]) if value else 0
                elif isinstance(value, bytes):
                    value = value[0] if len(value) > 0 else 0

            # Validate range for integer types
            value = self._validate_value(ptype, value)

            # Pack and write to buffer
            packed = struct.pack(format_str, value)
            buffer[offset:offset + len(packed)] = packed

        except struct.error as e:
            print(f"Error encoding {ptype.c_type} value {value} at offset {offset}: {e}")

    def _encode_primitive_array(self, field: FieldDef, value: Any,
                               buffer: bytearray, offset: int):
        """Encode an array of primitive values."""
        ptype = field.primitive_type

        # For char arrays (C strings)
        if ptype == PrimitiveType.CHAR:
            if isinstance(value, str):
                value = value.encode('utf-8')
            if isinstance(value, bytes):
                # Write string data, null-terminate if space allows
                length = min(len(value), field.size)
                buffer[offset:offset + length] = value[:length]
                # Add null terminator if there's space
                if length < field.size:
                    buffer[offset + length] = 0
            return

        # For uint8_t arrays (byte arrays)
        if ptype == PrimitiveType.UINT8:
            if isinstance(value, bytes):
                length = min(len(value), field.size)
                buffer[offset:offset + length] = value[:length]
            elif isinstance(value, list):
                for i, element in enumerate(value):
                    if i >= field.array_length:
                        break
                    element_offset = offset + i
                    buffer[element_offset] = int(element) & 0xFF
            return

        # For other primitive arrays
        if isinstance(value, list):
            element_size = ptype.size
            for i, element in enumerate(value):
                if i >= field.array_length:
                    break
                element_offset = offset + (i * element_size)
                self._encode_primitive(ptype, element, buffer, element_offset)

    def _validate_value(self, ptype: PrimitiveType, value: Any) -> int:
        """Validate and clamp value to valid range for type."""
        try:
            value = int(value)
        except (ValueError, TypeError):
            print(f"Warning: Invalid value {value} for {ptype.c_type}, using 0")
            return 0

        # Define ranges for each type
        ranges = {
            PrimitiveType.UINT8: (0, 255),
            PrimitiveType.UINT16: (0, 65535),
            PrimitiveType.UINT32: (0, 4294967295),
            PrimitiveType.INT8: (-128, 127),
            PrimitiveType.INT16: (-32768, 32767),
            PrimitiveType.INT32: (-2147483648, 2147483647),
            PrimitiveType.CHAR: (0, 255),
        }

        if ptype in ranges:
            min_val, max_val = ranges[ptype]
            if value < min_val or value > max_val:
                print(f"Warning: Value {value} out of range for {ptype.c_type} "
                      f"[{min_val}, {max_val}], clamping")
                value = max(min_val, min(max_val, value))

        return value
