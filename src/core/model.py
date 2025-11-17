"""
Qt data models for EEPROM data.
"""
from PyQt6.QtCore import Qt, QAbstractTableModel, QModelIndex, QVariant
from typing import Any, Dict, List, Optional
from .schema import EepromSchema, StructDef, FieldDef, PrimitiveType


class EepromDataModel:
    """Central data model holding the parsed EEPROM data."""

    def __init__(self, schema: EepromSchema, data: Dict[str, Any]):
        self.schema = schema
        self.data = data
        self.modified = False

    def get_value(self, path: List[str]) -> Any:
        """
        Get a value by field path.

        Args:
            path: List of field names forming a path (e.g., ['mem0', 'p0x'])

        Returns:
            The value at that path
        """
        current = self.data
        for key in path:
            if isinstance(current, dict):
                current = current.get(key)
            elif isinstance(current, list):
                try:
                    idx = int(key)
                    current = current[idx]
                except (ValueError, IndexError):
                    return None
            else:
                return None
        return current

    def set_value(self, path: List[str], value: Any):
        """
        Set a value by field path.

        Args:
            path: List of field names forming a path
            value: New value to set
        """
        if not path:
            return

        current = self.data
        for key in path[:-1]:
            if isinstance(current, dict):
                current = current.get(key)
            elif isinstance(current, list):
                try:
                    idx = int(key)
                    current = current[idx]
                except (ValueError, IndexError):
                    return
            else:
                return

        # Set the final value
        final_key = path[-1]
        if isinstance(current, dict):
            current[final_key] = value
            self.modified = True
        elif isinstance(current, list):
            try:
                idx = int(final_key)
                current[idx] = value
                self.modified = True
            except (ValueError, IndexError):
                pass


class FieldTableModel(QAbstractTableModel):
    """Table model for displaying struct fields."""

    COLUMNS = ['Field Name', 'Type', 'Offset', 'Abs Offset', 'Size', 'Value']

    def __init__(self, struct_def: Optional[StructDef] = None,
                 data_model: Optional[EepromDataModel] = None,
                 field_path: Optional[List[str]] = None):
        super().__init__()
        self.struct_def = struct_def
        self.data_model = data_model
        self.field_path = field_path or []

    def set_struct(self, struct_def: StructDef, data_model: EepromDataModel,
                   field_path: List[str]):
        """Update the model with a new struct."""
        self.beginResetModel()
        self.struct_def = struct_def
        self.data_model = data_model
        self.field_path = field_path
        self.endResetModel()

    def rowCount(self, parent=QModelIndex()):
        if not self.struct_def:
            return 0
        return len(self.struct_def.fields)

    def columnCount(self, parent=QModelIndex()):
        return len(self.COLUMNS)

    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        if role == Qt.ItemDataRole.DisplayRole:
            if orientation == Qt.Orientation.Horizontal:
                return self.COLUMNS[section]
        return QVariant()

    def data(self, index: QModelIndex, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid() or not self.struct_def:
            return QVariant()

        if role == Qt.ItemDataRole.DisplayRole or role == Qt.ItemDataRole.EditRole:
            field = self.struct_def.fields[index.row()]
            col = index.column()

            if col == 0:  # Field Name
                array_suffix = f"[{field.array_length}]" if field.is_array else ""
                return f"{field.name}{array_suffix}"
            elif col == 1:  # Type
                return field.type_name
            elif col == 2:  # Offset
                return f"0x{field.offset:04X}"
            elif col == 3:  # Absolute Offset
                return f"0x{field.absolute_offset:04X}"
            elif col == 4:  # Size
                return f"{field.size}"
            elif col == 5:  # Value
                if self.data_model:
                    value_path = self.field_path + [field.name]
                    value = self.data_model.get_value(value_path)
                    return self._format_value(field, value)
                return ""

        return QVariant()

    def flags(self, index: QModelIndex):
        if not index.isValid():
            return Qt.ItemFlag.NoItemFlags

        # Only the Value column (5) is editable for primitive non-array fields
        if index.column() == 5:
            field = self.struct_def.fields[index.row()]
            # Allow editing for simple primitives (not arrays, not structs)
            if field.primitive_type and not field.is_array and field.primitive_type != PrimitiveType.CHAR:
                return Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEditable

        return Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable

    def setData(self, index: QModelIndex, value: Any, role=Qt.ItemDataRole.EditRole):
        if not index.isValid() or index.column() != 5:
            return False

        if role == Qt.ItemDataRole.EditRole:
            field = self.struct_def.fields[index.row()]

            # Only allow editing simple primitive fields
            if field.primitive_type and not field.is_array:
                try:
                    # Convert value to appropriate type
                    if field.primitive_type in [PrimitiveType.UINT8, PrimitiveType.UINT16,
                                               PrimitiveType.UINT32, PrimitiveType.INT8,
                                               PrimitiveType.INT16, PrimitiveType.INT32]:
                        new_value = int(value)
                    else:
                        new_value = value

                    # Update the data model
                    value_path = self.field_path + [field.name]
                    self.data_model.set_value(value_path, new_value)

                    self.dataChanged.emit(index, index, [Qt.ItemDataRole.DisplayRole])
                    return True
                except (ValueError, TypeError):
                    return False

        return False

    def _format_value(self, field: FieldDef, value: Any) -> str:
        """Format a value for display."""
        if value is None:
            return ""

        # For nested structs, show indicator
        if field.is_struct:
            if field.is_array:
                return f"<struct array[{field.array_length}]>"
            return "<struct>"

        # For arrays
        if field.is_array:
            if isinstance(value, bytes):
                # Show hex preview for byte arrays
                preview = value[:16].hex(' ')
                if len(value) > 16:
                    preview += "..."
                return preview
            elif isinstance(value, list):
                return f"[{len(value)} elements]"
            return str(value)

        # For primitive types
        if field.primitive_type:
            if field.primitive_type == PrimitiveType.CHAR:
                return f"'{chr(value)}' ({value})" if 32 <= value < 127 else f"{value}"
            else:
                return str(value)

        return str(value)

    def get_field(self, row: int) -> Optional[FieldDef]:
        """Get field definition for a row."""
        if not self.struct_def or row < 0 or row >= len(self.struct_def.fields):
            return None
        return self.struct_def.fields[row]

    def get_field_path(self, row: int) -> List[str]:
        """Get the full path to a field."""
        field = self.get_field(row)
        if field:
            return self.field_path + [field.name]
        return []
