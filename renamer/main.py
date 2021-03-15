import sys
import os
import time
from typing import Union
from pathlib import Path

from PySide6.QtCore import QDir, QModelIndex, Slot, Qt
from PySide6.QtGui import QStandardItem, QStandardItemModel
from PySide6.QtWidgets import (QAbstractItemView, QApplication, QCheckBox, QComboBox,
                               QFileSystemModel, QGridLayout, QHBoxLayout,
                               QLabel, QLineEdit, QMainWindow, QPushButton, QSpinBox, QTableView,
                               QToolButton, QTreeView, QWidget)

"""
Planning:
    GUI window with panes for
    1. directory tree - Done
    2. files in directory - Done
    3. renaming options - Done
    4. Path bar - Done
    5. Rename logic / slots / etc

files should show current name and new name - done
select which files in a directory we want to rename - done
sort by name, date modified - done

rename options include:
    replace x with y
    wholly rename
    change case (upper, lower, title, sentence)
    remove from start, end, position to y, exact of chars / words, crop before or after
    add prefix, insert at pos, suffix
    auto-numbering prefix, suffix, prefix + suffix, insert at
"""


def files(path: str, parent=None) -> QStandardItemModel:
    """
    Creates a model listing for the files in a directory.
    These include the current file name, the new name (for use with rename_box),
    the file type and the last modified date / time.
    """
    path = Path(path)
    model = QStandardItemModel(parent)
    model.setHorizontalHeaderLabels(['Name', 'New Name', 'Type', 'Modified'])
    model.setColumnCount(4)
    for row, child in enumerate(path.iterdir()):
        name = QStandardItem(str(child.stem))
        new_name = QStandardItem(str(child.stem))
        if child.is_dir():
            ext = QStandardItem('File Folder')
        else:
            ext = QStandardItem(str(child.suffix))
        modified = QStandardItem(format_time(child))
        row_data = [name, new_name, ext, modified]
        for col, item in enumerate(row_data):
            model.setItem(row, col, item)
    return model


def format_time(path: Union[Path, str]) -> str:
    """
    Takes a path and returns the last modified time in D/M/YYYY H:mm:ss AM/PM format
    """
    mod = os.path.getmtime(path)
    formatted = time.localtime(mod)
    clean = time.strftime('%d/%m/%Y %I:%M:%S %p', formatted).replace('/0', '/')
    if clean.startswith('0'):
        return clean[1:]
    return clean


def blank_spinbox(parent=None) -> QSpinBox:
    """
    Creates a small spinbox of fixed size and '-' instead of 0.
    """
    spin = QSpinBox(parent)
    spin.setSpecialValueText('-')
    spin.setFixedWidth(50)
    return spin


def directory_table(model: QStandardItemModel, parent=None) -> QTableView:
    """
    Creates a new QTableView from a "files" model.
    """
    table = QTableView(parent)
    table.setModel(model)
    table.verticalHeader().hide()
    table.setSelectionBehavior(QAbstractItemView.SelectRows)
    table.setSortingEnabled(True)
    table.setColumnWidth(0, 300)
    table.setColumnWidth(1, 300)
    table.setColumnWidth(2, 150)
    table.setColumnWidth(3, 300)
    table.setFixedSize(1050, 400)

    return table


class rename_box(QGridLayout):
    """
    Creates a grid for each section of the rename options.
    """
    def __init__(self, title: str, widgets: list, labels: list = None,
                 widgets2: list = None, labels2: list = None, parent=None) -> None:
        super().__init__(parent)
        self.title = title
        self.changed = False
        self.widgets = widgets
        self.widgets2 = widgets2 if widgets2 else []
        self.all = self.widgets + self.widgets2
        columns = sum(x is not None for x in [labels, self.widgets2, labels2])
        # Sets the column for the clear button to be 1 or number of columns
        columns = max(1, columns)
        self.clear = QPushButton('X')
        self.clear.setFixedSize(15, 15)
        self.clear.clicked.connect(self.clear_fields)
        self.addWidget(QLabel(self.title), 0, 0)
        self.addWidget(self.clear, 0, columns, Qt.AlignRight)
        for row, widget in enumerate(self.widgets, start=1):
            widget_col = 0
            col_span = 2
            label = labels[row - 1] if labels else ''
            if label:
                self.addWidget(QLabel(label), row, 0)
                widget_col += 1
                col_span = 1
            self.addWidget(widget, row, widget_col, 1, col_span)

        if self.widgets2:
            for row, widget in enumerate(self.widgets2, start=1):
                widget_col = 2 if labels else 1
                col_span = 2
                label = labels2[row - 1] if labels else ''
                if label:
                    self.addWidget(QLabel(label), row, widget_col)
                    widget_col += 1
                    col_span = 1
                self.addWidget(widget, row, widget_col, 1, col_span)

    def clear_fields(self) -> None:
        """
        Loops through the widgets and clears each.
        """
        self.changed = False
        for widget in self.all:
            if isinstance(widget, QLineEdit):
                widget.clear()
            elif isinstance(widget, QComboBox):
                widget.setCurrentIndex(0)
            elif isinstance(widget, QSpinBox):
                widget.setValue(0)
            else:  # QCheckBox
                widget.setChecked(False)


class rename_options(QGridLayout):
    def __init__(self, model: QStandardItemModel, view: QTableView, parent=None) -> None:
        super().__init__(parent)
        self.model = model
        self.view = view
        self.reset = QPushButton('Reset')
        self.reset.clicked.connect(self.reset_all)
        self.preview = QPushButton('Preview')
        self.preview.clicked.connect(self.preview_changes)
        self.rename = QPushButton('Rename')
        self.rename.clicked.connect(self.finalize)
        for btn in [self.reset, self.preview, self.rename]:
            btn.setFixedWidth(50)

        self.name_entry = QLineEdit()
        self.name_box = rename_box('Name', [self.name_entry])
        self.name_entry.editingFinished.connect(lambda: self.changed(self.name_box))

        self.replace_entry_search = QLineEdit()
        self.replace_entry_text = QLineEdit()
        self.replace_box = rename_box('Replace',
                                      [self.replace_entry_search, self.replace_entry_text],
                                      ['Replace', 'With'])
        self.replace_entry_search.editingFinished.connect(lambda: self.changed(self.replace_box))
        self.replace_entry_text.editingFinished.connect(lambda: self.changed(self.replace_box))

        self.case_select = QComboBox()
        self.case_select.addItems(['Upper', 'Lower', 'Title', 'Sentence'])
        self.case_select.setEditable(False)
        self.case_except = QLineEdit()
        self.case_box = rename_box('Case', [self.case_select, self.case_except],
                                   ['', 'Except'])
        self.case_select.currentIndexChanged.connect(lambda: self.changed(self.case_box))
        self.case_except.editingFinished.connect(lambda: self.changed(self.case_box))

        self.add_prefix = QLineEdit()
        self.add_insert = QLineEdit()
        self.add_insert_pos = blank_spinbox()
        self.add_suffix = QLineEdit()
        self.add_box = rename_box('Add',
                                  [self.add_prefix, self.add_insert,
                                   self.add_insert_pos, self.add_suffix],
                                  ['Prefix', 'Insert', 'At', 'Suffix'])
        for widget in [self.add_prefix, self.add_insert, self.add_suffix]:
            widget.editingFinished.connect(lambda: self.changed(self.add_box))
        self.add_insert_pos.valueChanged.connect(lambda: self.changed(self.add_box))

        self.remove_first = blank_spinbox()
        self.remove_last = blank_spinbox()
        self.remove_from = blank_spinbox()
        self.remove_to = blank_spinbox()
        self.remove_chars = QLineEdit()
        self.remove_words = QLineEdit()
        self.remove_crop_pos = QComboBox()
        self.remove_crop_pos.addItems(['Before', 'After'])
        self.remove_crop_pos.setEditable(False)
        self.remove_crop = QLineEdit()
        self.remove_box = rename_box('Remove',
                                     [self.remove_first, self.remove_from,
                                      self.remove_chars, self.remove_crop_pos],
                                     ['First', 'From', 'Chars', 'Crop'],
                                     [self.remove_last, self.remove_to,
                                      self.remove_words, self.remove_crop],
                                     ['Last', 'To', 'Words', ''])
        for widget in [self.remove_first, self.remove_last,
                       self.remove_from, self.remove_to]:
            widget.valueChanged.connect(lambda: self.changed(self.remove_box))
        for widget in [self.remove_chars, self.remove_words, self.remove_crop]:
            widget.editingFinished.connect(lambda: self.changed(self.remove_box))
        self.remove_crop_pos.currentIndexChanged.connect(lambda: self.changed(self.remove_box))

        self.num_prefix = QCheckBox()
        self.num_suffix = QCheckBox()
        self.num_insert = QCheckBox()
        self.num_pos = blank_spinbox()
        self.num_start = blank_spinbox()
        self.num_incr = blank_spinbox()
        self.num_pad = blank_spinbox()
        self.num_sep = QLineEdit()
        self.num_box = rename_box('Auto Number',
                                  [self.num_prefix, self.num_insert, self.num_start, self.num_pad],
                                  ['Prefix', 'Insert', 'Start', 'Pad'],
                                  [self.num_suffix, self.num_pos, self.num_incr, self.num_sep],
                                  ['Suffix', 'At', 'Incr.', 'Sep.'])
        for widget in [self.num_prefix, self.num_suffix, self.num_insert]:
            widget.stateChanged.connect(lambda: self.changed(self.num_box))
        for widget in [self.num_pos, self.num_start, self.num_incr, self.num_pad]:
            widget.valueChanged.connect(lambda: self.changed(self.num_box))
        self.num_sep.editingFinished.connect(lambda: self.changed(self.num_box))

        self.addLayout(self.name_box, 0, 0)
        self.addLayout(self.replace_box, 1, 0)
        self.addLayout(self.case_box, 2, 0, 3, 1)
        self.addLayout(self.add_box, 0, 1, 2, 1)
        self.addLayout(self.remove_box, 0, 2, 2, 1)
        self.addLayout(self.num_box, 0, 3, 2, 1)
        self.addWidget(self.reset, 2, 3, Qt.AlignRight)
        self.addWidget(self.preview, 3, 3, Qt.AlignRight)
        self.addWidget(self.rename, 4, 3, Qt.AlignRight)

    def change_dir(self, model):
        self.model = model

    def reset_all(self):
        for box in [self.name_box, self.replace_box, self.case_box,
                    self.add_box, self.remove_box, self.num_box]:
            box.clear_fields()
        for index in range(self.model.rowCount()):
            self.model.item(index, 1).setText(self.model.item(index, 0).text())

    def finalize(self):
        for index in self.view.selectionModel().selectedRows():
            row = index.row()
            print(self.model.item(row, 1).text())

    def preview_changes(self) -> list[str]:
        new_strings = []
        for index in self.view.selectionModel().selectedRows():
            row = index.row
            new_text = self.model.item(row, 1).text()
            if self.name_box.changed:
                new_text = self.name_entry.text()
            if self.replace_box:
                pass
            if self.case_box:
                pass
            if self.add_box:
                pass
            if self.remove_box:
                pass
            if self.num_box:
                pass

            new_strings.append(new_text)

        return new_strings

    def changed(self, box):
        box.changed = True
        # Check if widgets are in default state
        for widget in box.all:
            if isinstance(widget, QLineEdit) and widget.text():
                break
            elif isinstance(widget, QComboBox) and widget.currentIndex():
                break
            elif isinstance(widget, QSpinBox) and widget.value():
                break
            elif isinstance(widget, QCheckBox) and widget.isChecked():
                break
        else:
            box.changed = False


class main_window(QMainWindow):
    def __init__(self, path):
        super().__init__()
        self.setWindowTitle('Bulk Rename')
        self.path = str(path)
        self.tree_model = QFileSystemModel()
        self.tree_model.setRootPath(self.path)
        self.tree_model.setFilter(QDir.AllDirs | QDir.NoDotAndDotDot)
        self.files_model = files(path)

        self.dir_entry = QLineEdit(self.path)
        self.dir_btn = QToolButton()
        self.dir_btn.setArrowType(Qt.RightArrow)
        self.tree = QTreeView()
        self.tree.setModel(self.tree_model)
        self.files = directory_table(self.files_model)
        self.rename_opts = rename_options(self.files_model, self.files)

        # Set tree to only show the directories, no other information.
        self.tree.setIndentation(10)
        for col in range(1, 4):
            self.tree.hideColumn(col)
        self.tree.setFixedSize(175, 400)

        self.initUI()

        # Add callbacks
        self.dir_btn.clicked.connect(self.set_tree)
        self.dir_entry.returnPressed.connect(self.set_tree)
        self.tree.clicked.connect(self.set_dir)

        self.set_tree()
        self.setMaximumSize(self.width(), self.height())

    def initUI(self):
        centralWidget = QWidget()
        grid = QGridLayout()
        grid.setColumnStretch(1, 1)
        dir_box = QHBoxLayout()
        dir_box.addWidget(QLabel('Directory:'))
        dir_box.addWidget(self.dir_entry)
        dir_box.addWidget(self.dir_btn)
        grid.addLayout(dir_box, 0, 0, 1, 3)
        grid.addWidget(self.tree, 1, 0)
        grid.addWidget(self.files, 1, 1)
        grid.addLayout(self.rename_opts, 2, 0, 1, 3)

        centralWidget.setLayout(grid)
        self.setCentralWidget(centralWidget)

    @Slot()
    def set_tree(self):
        current = self.dir_entry.text()
        index = self.tree_model.index(current)
        self.tree.setCurrentIndex(index)
        self.tree.expandRecursively(index, 0)
        self.files_model = files(current)
        self.files.setModel(self.files_model)
        self.rename_opts.change_dir(self.files_model)

    @Slot(QModelIndex)
    def set_dir(self, index):
        current = self.tree_model.filePath(index)
        self.dir_entry.setText(current)
        self.tree.setCurrentIndex(index)
        self.files_model = files(current)
        self.files.setModel(self.files_model)
        self.rename_opts.change_dir(self.files_model)


def main():
    try:
        path = Path(sys.argv[1])
    except IndexError:
        path = Path().absolute()
    app = QApplication(sys.argv)
    window = main_window(path)
    window.show()

    with open('renamer/style.qss', 'r') as f:
        _style = f.read()
        app.setStyleSheet(_style)
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
