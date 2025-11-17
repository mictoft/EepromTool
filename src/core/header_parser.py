"""
Parser for C header files containing EEPROM struct definitions.
"""
import re
from typing import List, Tuple, Optional
from .schema import EepromSchema, StructDef, FieldDef, PrimitiveType


class HeaderParser:
    """Parse C header files to extract struct definitions."""

    def __init__(self):
        self.schema = None
        self.current_offset = 0

    def parse_header(self, header_path: str) -> EepromSchema:
        """
        Parse a C header file and build an EEPROM schema.

        Args:
            header_path: Path to the C header file

        Returns:
            EepromSchema object
        """
        with open(header_path, 'r') as f:
            content = f.read()

        # Remove comments
        content = self._remove_comments(content)

        # Extract all struct definitions
        structs = self._extract_structs(content)

        if not structs:
            raise ValueError("No struct definitions found in header file")

        # Build schema
        schema = EepromSchema(root_struct_name="")

        # First pass: create all struct definitions
        for struct_name, struct_body in structs:
            struct_def = StructDef(name=struct_name, is_packed=True)
            schema.add_struct(struct_def)

        # Second pass: parse fields with known struct types
        for struct_name, struct_body in structs:
            struct_def = schema.get_struct(struct_name)
            self._parse_struct_fields(struct_def, struct_body, schema)

        # Determine root struct (usually the last/largest one or one containing others)
        root_struct = self._find_root_struct(schema)
        schema.root_struct_name = root_struct.name
        schema.total_size = root_struct.size

        # Calculate absolute offsets
        self._calculate_absolute_offsets(schema)

        return schema

    def _remove_comments(self, content: str) -> str:
        """Remove C-style comments from content."""
        # Remove single-line comments
        content = re.sub(r'//.*?$', '', content, flags=re.MULTILINE)
        # Remove multi-line comments
        content = re.sub(r'/\*.*?\*/', '', content, flags=re.DOTALL)
        return content

    def _extract_structs(self, content: str) -> List[Tuple[str, str]]:
        """
        Extract all struct definitions from header content.

        Returns:
            List of (struct_name, struct_body) tuples
        """
        structs = []

        # Pattern for packed struct typedef
        # Matches: typedef struct __attribute__((__packed__)) { ... } NameType;
        pattern = r'typedef\s+struct\s+__attribute__\s*\(\s*\(\s*__packed__\s*\)\s*\)\s*\{([^}]+)\}\s*(\w+)\s*;'

        matches = re.finditer(pattern, content, re.DOTALL)
        for match in matches:
            struct_body = match.group(1).strip()
            struct_name = match.group(2).strip()
            structs.append((struct_name, struct_body))

        return structs

    def _parse_struct_fields(self, struct_def: StructDef, struct_body: str, schema: EepromSchema):
        """Parse fields from struct body."""
        offset = 0

        # Split into lines and process each field declaration
        lines = struct_body.split(';')

        for line in lines:
            line = line.strip()
            if not line:
                continue

            field = self._parse_field(line, offset, schema)
            if field:
                struct_def.add_field(field)
                offset += field.size

    def _parse_field(self, line: str, offset: int, schema: EepromSchema) -> Optional[FieldDef]:
        """
        Parse a single field declaration.

        Examples:
            uint8_t myField
            uint16_t myArray[32]
            SomeStructType nestedStruct
        """
        # Remove extra whitespace
        line = ' '.join(line.split())

        # Pattern: type_name field_name or type_name field_name[array_size]
        pattern = r'(\w+)\s+(\w+)(?:\[(\d+)\])?'
        match = re.match(pattern, line)

        if not match:
            return None

        type_name = match.group(1)
        field_name = match.group(2)
        array_size_str = match.group(3)

        is_array = array_size_str is not None
        array_length = int(array_size_str) if is_array else 1

        # Determine if this is a primitive or struct type
        primitive_type = PrimitiveType.from_c_type(type_name)

        if primitive_type:
            # Primitive type
            field_size = primitive_type.size * array_length
            return FieldDef(
                name=field_name,
                type_name=type_name,
                size=field_size,
                offset=offset,
                absolute_offset=0,  # Will be calculated later
                is_array=is_array,
                array_length=array_length,
                is_struct=False,
                primitive_type=primitive_type
            )
        elif schema.is_struct_type(type_name):
            # Nested struct type
            nested_struct = schema.get_struct(type_name)
            field_size = nested_struct.size * array_length
            return FieldDef(
                name=field_name,
                type_name=type_name,
                size=field_size,
                offset=offset,
                absolute_offset=0,  # Will be calculated later
                is_array=is_array,
                array_length=array_length,
                is_struct=True,
                primitive_type=None
            )
        else:
            # Unknown type - treat as uint8_t
            print(f"Warning: Unknown type '{type_name}', treating as uint8_t")
            field_size = 1 * array_length
            return FieldDef(
                name=field_name,
                type_name=type_name,
                size=field_size,
                offset=offset,
                absolute_offset=0,
                is_array=is_array,
                array_length=array_length,
                is_struct=False,
                primitive_type=PrimitiveType.UINT8
            )

    def _find_root_struct(self, schema: EepromSchema) -> StructDef:
        """Find the root struct (typically the largest or last defined)."""
        if not schema.structs:
            raise ValueError("No structs found")

        # Return the largest struct (most likely the root containing all others)
        root = max(schema.structs.values(), key=lambda s: s.size)
        return root

    def _calculate_absolute_offsets(self, schema: EepromSchema):
        """Calculate absolute offsets for all fields in all structs."""
        root_struct = schema.get_root_struct()
        if root_struct:
            self._calculate_struct_absolute_offsets(root_struct, 0, schema)

    def _calculate_struct_absolute_offsets(self, struct_def: StructDef, base_offset: int, schema: EepromSchema):
        """Recursively calculate absolute offsets for struct fields."""
        for field in struct_def.fields:
            field.absolute_offset = base_offset + field.offset

            # If this is a nested struct, recursively calculate its fields' offsets
            if field.is_struct:
                nested_struct = schema.get_struct(field.type_name)
                if nested_struct:
                    if field.is_array:
                        # For struct arrays, calculate offset for each element
                        for i in range(field.array_length):
                            element_offset = field.absolute_offset + (i * nested_struct.size)
                            self._calculate_struct_absolute_offsets(nested_struct, element_offset, schema)
                    else:
                        self._calculate_struct_absolute_offsets(nested_struct, field.absolute_offset, schema)
