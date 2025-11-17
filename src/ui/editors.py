"""
Field editor dialogs for different data types.
"""
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                             QSpinBox, QLineEdit, QTextEdit, QPushButton,
                             QDialogButtonBox, QFileDialog, QMessageBox)
from PyQt6.QtCore import Qt
from typing import Any, Optional
from ..core.schema import FieldDef, PrimitiveType


class FieldEditorDialog(QDialog):
    """Dialog for editing field values."""

    def __init__(self, field: FieldDef, current_value: Any, parent=None):
        super().__init__(parent)
        self.field = field
        self.current_value = current_value
        self.new_value = current_value
        self.editor_widget = None

        self.init_ui()

    def init_ui(self):
        """Initialize the UI."""
        self.setWindowTitle(f"Edit Field: {self.field.name}")
        self.setModal(True)
        self.setMinimumWidth(500)

        layout = QVBoxLayout()
        self.setLayout(layout)

        # Field info
        info_text = (f"Field: {self.field.name}\n"
                    f"Type: {self.field.type_name}\n"
                    f"Size: {self.field.size} bytes")
        info_label = QLabel(info_text)
        layout.addWidget(info_label)

        # Create appropriate editor based on field type
        if self.field.is_struct:
            layout.addWidget(QLabel("Struct fields cannot be edited directly.\n"
                                  "Navigate to the struct in the tree to edit its fields."))
        elif self.field.is_array:
            self.create_array_editor(layout)
        elif self.field.primitive_type:
            self.create_primitive_editor(layout)
        else:
            layout.addWidget(QLabel("Unknown field type"))

        # Buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def create_primitive_editor(self, layout):
        """Create editor for primitive types."""
        ptype = self.field.primitive_type

        if ptype in [PrimitiveType.UINT8, PrimitiveType.UINT16, PrimitiveType.UINT32]:
            # Unsigned integer spinbox
            self.editor_widget = QSpinBox()
            self.editor_widget.setMinimum(0)

            if ptype == PrimitiveType.UINT8:
                self.editor_widget.setMaximum(255)
            elif ptype == PrimitiveType.UINT16:
                self.editor_widget.setMaximum(65535)
            elif ptype == PrimitiveType.UINT32:
                self.editor_widget.setMaximum(2147483647)  # QSpinBox max

            self.editor_widget.setValue(int(self.current_value))
            layout.addWidget(QLabel("Value:"))
            layout.addWidget(self.editor_widget)

        elif ptype in [PrimitiveType.INT8, PrimitiveType.INT16, PrimitiveType.INT32]:
            # Signed integer spinbox
            self.editor_widget = QSpinBox()

            if ptype == PrimitiveType.INT8:
                self.editor_widget.setMinimum(-128)
                self.editor_widget.setMaximum(127)
            elif ptype == PrimitiveType.INT16:
                self.editor_widget.setMinimum(-32768)
                self.editor_widget.setMaximum(32767)
            elif ptype == PrimitiveType.INT32:
                self.editor_widget.setMinimum(-2147483648)
                self.editor_widget.setMaximum(2147483647)

            self.editor_widget.setValue(int(self.current_value))
            layout.addWidget(QLabel("Value:"))
            layout.addWidget(self.editor_widget)

        elif ptype == PrimitiveType.CHAR:
            # Character editor
            self.editor_widget = QLineEdit()
            self.editor_widget.setMaxLength(1)
            if isinstance(self.current_value, int):
                if 32 <= self.current_value < 127:
                    self.editor_widget.setText(chr(self.current_value))
            layout.addWidget(QLabel("Character:"))
            layout.addWidget(self.editor_widget)

    def create_array_editor(self, layout):
        """Create editor for array types."""
        ptype = self.field.primitive_type

        if ptype == PrimitiveType.CHAR:
            # String editor for char arrays
            self.editor_widget = QLineEdit()
            self.editor_widget.setMaxLength(self.field.array_length)

            if isinstance(self.current_value, bytes):
                try:
                    text = self.current_value.decode('utf-8')
                    self.editor_widget.setText(text)
                except:
                    self.editor_widget.setText(self.current_value.hex())
            else:
                self.editor_widget.setText(str(self.current_value))

            layout.addWidget(QLabel(f"String (max {self.field.array_length} chars):"))
            layout.addWidget(self.editor_widget)

        elif ptype == PrimitiveType.UINT8:
            # Hex editor for byte arrays
            self.create_hex_editor(layout)

        else:
            # Generic array editor
            self.editor_widget = QTextEdit()
            self.editor_widget.setMaximumHeight(200)

            if isinstance(self.current_value, list):
                text = ', '.join(str(v) for v in self.current_value)
                self.editor_widget.setPlainText(text)

            layout.addWidget(QLabel(f"Array values (comma-separated, {self.field.array_length} elements):"))
            layout.addWidget(self.editor_widget)

    def create_hex_editor(self, layout):
        """Create hex editor for byte arrays."""
        hex_layout = QVBoxLayout()

        self.editor_widget = QTextEdit()
        self.editor_widget.setMaximumHeight(200)
        self.editor_widget.setFont(self.editor_widget.font())

        # Display current value as hex
        if isinstance(self.current_value, bytes):
            hex_text = self.current_value.hex(' ')
            self.editor_widget.setPlainText(hex_text)

        hex_layout.addWidget(QLabel(f"Hex data ({self.field.size} bytes):"))
        hex_layout.addWidget(self.editor_widget)

        # Add load from file button
        button_layout = QHBoxLayout()
        load_button = QPushButton("Load from File")
        load_button.clicked.connect(self.load_hex_from_file)
        button_layout.addWidget(load_button)
        button_layout.addStretch()
        hex_layout.addLayout(button_layout)

        layout.addLayout(hex_layout)

    def load_hex_from_file(self):
        """Load hex data from a file."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Load Binary Data", "",
            "Binary Files (*.bin);;All Files (*)"
        )

        if file_path:
            try:
                with open(file_path, 'rb') as f:
                    data = f.read(self.field.size)

                if len(data) > self.field.size:
                    QMessageBox.warning(
                        self, "Warning",
                        f"File is larger than field size ({self.field.size} bytes). "
                        f"Only the first {self.field.size} bytes will be used."
                    )

                hex_text = data.hex(' ')
                self.editor_widget.setPlainText(hex_text)

            except Exception as e:
                QMessageBox.critical(
                    self, "Error",
                    f"Failed to load file:\n{str(e)}"
                )

    def get_value(self) -> Any:
        """Get the edited value."""
        if self.editor_widget is None:
            return self.current_value

        ptype = self.field.primitive_type

        # Handle primitives
        if not self.field.is_array:
            if isinstance(self.editor_widget, QSpinBox):
                return self.editor_widget.value()
            elif isinstance(self.editor_widget, QLineEdit):
                text = self.editor_widget.text()
                if ptype == PrimitiveType.CHAR:
                    return ord(text[0]) if text else 0
                return text
            return self.current_value

        # Handle arrays
        if ptype == PrimitiveType.CHAR:
            # String
            if isinstance(self.editor_widget, QLineEdit):
                return self.editor_widget.text().encode('utf-8')

        elif ptype == PrimitiveType.UINT8:
            # Hex data
            if isinstance(self.editor_widget, QTextEdit):
                hex_text = self.editor_widget.toPlainText().replace(' ', '').replace('\n', '')
                try:
                    data = bytes.fromhex(hex_text)
                    # Pad or truncate to correct size
                    if len(data) < self.field.size:
                        data += b'\x00' * (self.field.size - len(data))
                    elif len(data) > self.field.size:
                        data = data[:self.field.size]
                    return data
                except ValueError:
                    QMessageBox.warning(
                        self, "Invalid Hex",
                        "Invalid hexadecimal data. Using previous value."
                    )
                    return self.current_value

        else:
            # Generic array
            if isinstance(self.editor_widget, QTextEdit):
                text = self.editor_widget.toPlainText()
                try:
                    values = [int(v.strip()) for v in text.split(',') if v.strip()]
                    # Pad or truncate to correct length
                    if len(values) < self.field.array_length:
                        values += [0] * (self.field.array_length - len(values))
                    elif len(values) > self.field.array_length:
                        values = values[:self.field.array_length]
                    return values
                except ValueError:
                    QMessageBox.warning(
                        self, "Invalid Data",
                        "Invalid array data. Using previous value."
                    )
                    return self.current_value

        return self.current_value
