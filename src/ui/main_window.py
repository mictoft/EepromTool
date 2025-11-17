"""
Main window for EEPROM Layout Editor.
"""
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QTreeWidget, QTreeWidgetItem, QTableView, QSplitter,
                             QMenuBar, QMenu, QFileDialog, QMessageBox, QHeaderView)
from PyQt6.QtCore import Qt
from typing import Optional, List
from ..core.schema import EepromSchema, StructDef, FieldDef
from ..core.model import EepromDataModel, FieldTableModel
from ..core.header_parser import HeaderParser
from ..core.binary_parser import BinaryParser
from ..core.encoder import BinaryEncoder
from .editors import FieldEditorDialog


class MainWindow(QMainWindow):
    """Main application window."""

    def __init__(self):
        super().__init__()
        self.schema: Optional[EepromSchema] = None
        self.data_model: Optional[EepromDataModel] = None
        self.current_binary_path: Optional[str] = None
        self.current_header_path: Optional[str] = None

        self.init_ui()

    def init_ui(self):
        """Initialize the user interface."""
        self.setWindowTitle("EEPROM Layout Editor")
        self.setGeometry(100, 100, 1200, 800)

        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Create main layout
        main_layout = QVBoxLayout()
        central_widget.setLayout(main_layout)

        # Create splitter for tree and table
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Create tree widget for struct hierarchy
        self.tree_widget = QTreeWidget()
        self.tree_widget.setHeaderLabel("EEPROM Structure")
        self.tree_widget.itemClicked.connect(self.on_tree_item_clicked)
        splitter.addWidget(self.tree_widget)

        # Create table view for fields
        self.table_view = QTableView()
        self.table_model = FieldTableModel()
        self.table_view.setModel(self.table_model)
        self.table_view.doubleClicked.connect(self.on_field_double_clicked)

        # Configure table view
        header = self.table_view.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)

        splitter.addWidget(self.table_view)

        # Set splitter sizes (30% tree, 70% table)
        splitter.setSizes([360, 840])

        main_layout.addWidget(splitter)

        # Create menu bar
        self.create_menu_bar()

        # Set status bar
        self.statusBar().showMessage("Ready")

    def create_menu_bar(self):
        """Create the menu bar."""
        menubar = self.menuBar()

        # File menu
        file_menu = menubar.addMenu("File")

        open_header_action = file_menu.addAction("Open Header...")
        open_header_action.triggered.connect(self.open_header)

        open_bin_action = file_menu.addAction("Open BIN...")
        open_bin_action.triggered.connect(self.open_binary)

        file_menu.addSeparator()

        save_bin_action = file_menu.addAction("Save BIN As...")
        save_bin_action.triggered.connect(self.save_binary)

        file_menu.addSeparator()

        exit_action = file_menu.addAction("Exit")
        exit_action.triggered.connect(self.close)

        # View menu
        view_menu = menubar.addMenu("View")

        reload_action = view_menu.addAction("Reload")
        reload_action.triggered.connect(self.reload_data)

        # Help menu
        help_menu = menubar.addMenu("Help")

        about_action = help_menu.addAction("About")
        about_action.triggered.connect(self.show_about)

    def open_header(self):
        """Open and parse a header file."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Open Header File", "",
            "Header Files (*.h);;All Files (*)"
        )

        if file_path:
            try:
                parser = HeaderParser()
                self.schema = parser.parse_header(file_path)
                self.current_header_path = file_path

                self.statusBar().showMessage(f"Loaded header: {file_path}")
                QMessageBox.information(
                    self, "Header Loaded",
                    f"Successfully parsed header file.\n"
                    f"Root struct: {self.schema.root_struct_name}\n"
                    f"Total size: {self.schema.total_size} bytes"
                )

                # If we already have binary data, reload it with new schema
                if self.current_binary_path:
                    self.load_binary(self.current_binary_path)

            except Exception as e:
                QMessageBox.critical(
                    self, "Error",
                    f"Failed to parse header file:\n{str(e)}"
                )

    def open_binary(self):
        """Open a binary file."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Open Binary File", "",
            "Binary Files (*.bin);;All Files (*)"
        )

        if file_path:
            if not self.schema:
                QMessageBox.warning(
                    self, "No Schema",
                    "Please load a header file first."
                )
                return

            self.load_binary(file_path)

    def load_binary(self, file_path: str):
        """Load and parse a binary file."""
        try:
            parser = BinaryParser(self.schema)

            # Validate file size
            is_valid, actual_size, expected_size = parser.validate_binary_size(file_path)
            if not is_valid:
                result = QMessageBox.warning(
                    self, "Size Mismatch",
                    f"Binary file size ({actual_size} bytes) does not match "
                    f"expected size ({expected_size} bytes).\n\n"
                    f"Continue anyway?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )
                if result == QMessageBox.StandardButton.No:
                    return

            # Parse binary
            data = parser.parse_binary(file_path)
            self.data_model = EepromDataModel(self.schema, data)
            self.current_binary_path = file_path

            # Update UI
            self.populate_tree()
            self.statusBar().showMessage(f"Loaded binary: {file_path}")

        except Exception as e:
            QMessageBox.critical(
                self, "Error",
                f"Failed to load binary file:\n{str(e)}"
            )

    def save_binary(self):
        """Save the current data to a binary file."""
        if not self.data_model:
            QMessageBox.warning(
                self, "No Data",
                "No data loaded to save."
            )
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save Binary File", "",
            "Binary Files (*.bin);;All Files (*)"
        )

        if file_path:
            try:
                encoder = BinaryEncoder(self.schema)
                encoder.save_binary(self.data_model.data, file_path)

                self.data_model.modified = False
                self.statusBar().showMessage(f"Saved binary: {file_path}")
                QMessageBox.information(
                    self, "Success",
                    f"Binary file saved successfully to:\n{file_path}"
                )

            except Exception as e:
                QMessageBox.critical(
                    self, "Error",
                    f"Failed to save binary file:\n{str(e)}"
                )

    def reload_data(self):
        """Reload the current binary file."""
        if self.current_binary_path and self.schema:
            self.load_binary(self.current_binary_path)

    def populate_tree(self):
        """Populate the tree widget with struct hierarchy."""
        self.tree_widget.clear()

        if not self.schema or not self.data_model:
            return

        root_struct = self.schema.get_root_struct()
        if not root_struct:
            return

        # Create root item
        root_item = QTreeWidgetItem(self.tree_widget)
        root_item.setText(0, root_struct.name)
        root_item.setData(0, Qt.ItemDataRole.UserRole, {
            'struct': root_struct,
            'path': []
        })

        # Populate children recursively
        self._populate_tree_node(root_item, root_struct, [])

        self.tree_widget.expandAll()

    def _populate_tree_node(self, parent_item: QTreeWidgetItem, struct_def: StructDef,
                           path: List[str]):
        """Recursively populate tree nodes."""
        for field in struct_def.fields:
            if field.is_struct:
                nested_struct = self.schema.get_struct(field.type_name)
                if nested_struct:
                    if field.is_array:
                        # Create array container
                        array_item = QTreeWidgetItem(parent_item)
                        array_item.setText(0, f"{field.name}[{field.array_length}]")
                        array_item.setData(0, Qt.ItemDataRole.UserRole, {
                            'struct': nested_struct,
                            'path': path + [field.name],
                            'is_array': True
                        })

                        # Create items for each array element
                        for i in range(field.array_length):
                            element_item = QTreeWidgetItem(array_item)
                            element_item.setText(0, f"[{i}]")
                            element_item.setData(0, Qt.ItemDataRole.UserRole, {
                                'struct': nested_struct,
                                'path': path + [field.name, str(i)]
                            })
                            self._populate_tree_node(element_item, nested_struct,
                                                    path + [field.name, str(i)])
                    else:
                        # Single nested struct
                        child_item = QTreeWidgetItem(parent_item)
                        child_item.setText(0, field.name)
                        child_item.setData(0, Qt.ItemDataRole.UserRole, {
                            'struct': nested_struct,
                            'path': path + [field.name]
                        })
                        self._populate_tree_node(child_item, nested_struct,
                                               path + [field.name])

    def on_tree_item_clicked(self, item: QTreeWidgetItem, column: int):
        """Handle tree item click."""
        data = item.data(0, Qt.ItemDataRole.UserRole)
        if data:
            struct_def = data['struct']
            path = data['path']

            # Update table view
            self.table_model.set_struct(struct_def, self.data_model, path)
            self.table_view.resizeColumnsToContents()

    def on_field_double_clicked(self, index):
        """Handle field double-click for editing."""
        if not index.isValid():
            return

        field = self.table_model.get_field(index.row())
        if not field:
            return

        field_path = self.table_model.get_field_path(index.row())
        current_value = self.data_model.get_value(field_path)

        # Open editor dialog
        dialog = FieldEditorDialog(field, current_value, self)
        if dialog.exec():
            new_value = dialog.get_value()
            self.data_model.set_value(field_path, new_value)

            # Refresh table
            self.table_model.dataChanged.emit(index, index, [Qt.ItemDataRole.DisplayRole])
            self.statusBar().showMessage(f"Updated {field.name}")

    def show_about(self):
        """Show about dialog."""
        QMessageBox.about(
            self, "About EEPROM Layout Editor",
            "EEPROM Layout Editor v1.0\n\n"
            "A tool for viewing and editing EEPROM binary files "
            "based on C header file layouts.\n\n"
            "Built with Python and PyQt6"
        )

    def closeEvent(self, event):
        """Handle window close event."""
        if self.data_model and self.data_model.modified:
            result = QMessageBox.question(
                self, "Unsaved Changes",
                "You have unsaved changes. Do you want to exit anyway?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )

            if result == QMessageBox.StandardButton.No:
                event.ignore()
                return

        event.accept()
