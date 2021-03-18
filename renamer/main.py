import os
import re
import sys
import time
from typing import Union
from pathlib import Path

from PySide6.QtCore import QDir, QModelIndex, Slot, Qt, Signal
from PySide6.QtGui import QStandardItem, QStandardItemModel
from PySide6.QtWidgets import (QAbstractItemView, QApplication, QCheckBox, QComboBox,
                               QFileSystemModel, QFrame, QGridLayout, QHBoxLayout,
                               QLabel, QLineEdit, QMainWindow, QMessageBox, QPushButton, QSpinBox, QTableView,
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
    These include the current file name, the new name (for use with RenameBox),
    the file type and the last modified date / time.
    """
    model = QStandardItemModel(parent)
    model.setHorizontalHeaderLabels(['Name', 'New Name', 'Type', 'Modified'])
    model.setColumnCount(4)
    path = Path(path)
    for row, child in enumerate(path.iterdir()):
        name = QStandardItem(str(child.stem))
        new_name = QStandardItem(str(child.stem))
        if child.is_dir():
            ext = QStandardItem('File Folder')
        else:
            ext = QStandardItem(str(child.suffix))
        modified = QStandardItem(format_time(child))
        ext.setTextAlignment(Qt.AlignCenter)
        modified.setTextAlignment(Qt.AlignCenter)
        row_data = [name, new_name, ext, modified]
        for col, item in enumerate(row_data):
            item.setEditable(False)
            model.setItem(row, col, item)
    return model


def format_time(path: Union[Path, str]) -> str:
    """
    Takes a path and returns the last modified time in m/d/YYYY H:mm:ss AM/PM format
    """
    mod = os.path.getmtime(path)
    formatted = time.localtime(mod)
    clean = time.strftime('%m/%d/%Y %I:%M:%S %p', formatted).replace('/0', '/')
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
    table.setShowGrid(False)
    table.verticalHeader().hide()
    table.setSelectionBehavior(QAbstractItemView.SelectRows)
    table.setSortingEnabled(True)
    table.setColumnWidth(0, 400)
    table.setColumnWidth(1, 400)
    table.setColumnWidth(2, 75)
    table.setColumnWidth(3, 175)
    table.setFixedSize(1050, 400)
    table.resizeRowsToContents()

    return table


class RenameBox(QFrame):
    change_signal = Signal(bool)
    """
    Creates a grid for each section of the rename options.
    """
    def __init__(self, title: str, widgets: list, labels: list = None,
                 widgets2: list = None, labels2: list = None, parent=None) -> None:
        super().__init__(parent)
        self.grid = QGridLayout()
        self.setLayout(self.grid)
        self.setFrameShape(QFrame.Box)
        self.setProperty('changed', False)
        self.setLineWidth(1)

        self.title = title
        self.widgets = widgets
        self.widgets2 = widgets2 if widgets2 else []
        self.all = self.widgets + self.widgets2
        columns = sum(x is not None for x in [labels, self.widgets2, labels2])
        # Sets the column for the clear button to be 1 or number of columns
        columns = max(1, columns)
        self.clear = QPushButton('X')
        self.clear.setFixedSize(15, 15)
        self.clear.setProperty('changed', False)
        self.clear.setObjectName('clear')
        self.clear.clicked.connect(self.clear_fields)
        self.grid.addWidget(QLabel(self.title), 0, 0)
        self.grid.addWidget(self.clear, 0, columns, Qt.AlignRight)
        for row, widget in enumerate(self.widgets, start=1):
            widget_col = 0
            col_span = 2
            label = labels[row - 1] if labels else ''
            if label:
                label_ = QLabel(label)
                label_.setFixedWidth(40)
                self.grid.addWidget(label_, row, 0)
                widget_col += 1
                col_span = 1
            self.grid.addWidget(widget, row, widget_col, 1, col_span)

        if self.widgets2:
            for row, widget in enumerate(self.widgets2, start=1):
                widget_col = 2 if labels else 1
                col_span = 2
                label = labels2[row - 1] if labels else ''
                if label:
                    label_ = QLabel(label)
                    label_.setFixedWidth(40)
                    self.grid.addWidget(label_, row, widget_col)
                    widget_col += 1
                    col_span = 1
                self.grid.addWidget(widget, row, widget_col, 1, col_span)

    def setChanged(self, state: bool = True):
        self.setProperty('changed', state)
        self.clear.setProperty('changed', state)
        self.style().unpolish(self)
        self.style().polish(self)
        self.update()
        self.change_signal.emit(state)

    def clear_fields(self) -> None:
        """
        Loops through the widgets and clears each.
        """
        self.setChanged(False)
        for widget in self.all:
            if isinstance(widget, QLineEdit):
                widget.clear()
            elif isinstance(widget, QComboBox):
                widget.setCurrentIndex(0)
            elif isinstance(widget, QSpinBox):
                widget.setValue(0)
            else:  # QCheckBox
                widget.setChecked(False)


class RenameOptions(QGridLayout):
    change_signal = Signal(bool)

    def __init__(self, model: QStandardItemModel, view: QTableView, path: str, parent=None) -> None:
        super().__init__(parent)
        self.path = Path(path)
        self.model = model
        self.view = view
        self.selection()
        self.reset = QPushButton('Reset')
        self.reset.clicked.connect(self.reset_all)
        self.rename = QPushButton('Rename')
        self.rename.clicked.connect(self.finalize)
        for btn in [self.reset, self.rename]:
            btn.setFixedWidth(50)

        self.name_entry = QLineEdit()
        self.name_box = RenameBox('Name', [self.name_entry])
        self.name_entry.textChanged.connect(lambda: self.changed(self.name_box))

        self.replace_entry_search = QLineEdit()
        self.replace_entry_text = QLineEdit()
        self.replace_box = RenameBox('Replace',
                                     [self.replace_entry_search, self.replace_entry_text],
                                     ['Replace', 'With'])
        self.replace_entry_search.textChanged.connect(lambda: self.changed(self.replace_box))
        self.replace_entry_text.textChanged.connect(lambda: self.changed(self.replace_box))

        self.case_select = QComboBox()
        self.case_select.addItems(['Same', 'Upper', 'Lower', 'Title', 'Sentence'])
        self.case_select.setEditable(False)
        self.case_except = QLineEdit()
        self.case_box = RenameBox('Case', [self.case_select, self.case_except],
                                  ['', 'Except'])
        self.case_select.currentIndexChanged.connect(lambda: self.changed(self.case_box))
        self.case_except.textChanged.connect(lambda: self.changed(self.case_box))

        self.add_prefix = QLineEdit()
        self.add_insert = QLineEdit()
        self.add_insert_pos = blank_spinbox()
        self.add_suffix = QLineEdit()
        self.add_box = RenameBox('Add',
                                 [self.add_prefix, self.add_insert,
                                  self.add_insert_pos, self.add_suffix],
                                 ['Prefix', 'Insert', 'At pos.', 'Suffix'])
        for widget in [self.add_prefix, self.add_insert, self.add_suffix]:
            widget.textChanged.connect(lambda: self.changed(self.add_box))
        self.add_insert_pos.valueChanged.connect(lambda: self.changed(self.add_box))

        self.remove_first = blank_spinbox()
        self.remove_last = blank_spinbox()
        self.remove_from = blank_spinbox()
        self.remove_to = blank_spinbox()
        self.remove_from.valueChanged.connect(self.min_remove)
        self.remove_chars = QLineEdit()
        self.remove_words = QLineEdit()
        self.remove_crop_pos = QComboBox()
        self.remove_crop_pos.addItems(['Before', 'After'])
        self.remove_crop_pos.setEditable(False)
        self.remove_crop = QLineEdit()
        self.remove_box = RenameBox('Remove',
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
            widget.textChanged.connect(lambda: self.changed(self.remove_box))
        self.remove_crop_pos.currentIndexChanged.connect(lambda: self.changed(self.remove_box))

        self.num_prefix = QCheckBox()
        self.num_suffix = QCheckBox()
        self.num_insert = QCheckBox()
        self.num_pos = blank_spinbox()
        self.num_start = QSpinBox()
        self.num_start.setValue(1)
        self.num_start.setFixedWidth(50)
        self.num_incr = blank_spinbox()
        self.num_incr.setValue(1)
        self.num_pad = blank_spinbox()
        self.num_sep = QLineEdit()
        self.num_sep.setFixedWidth(50)
        self.num_box = RenameBox('Auto Number',
                                  [self.num_prefix, self.num_insert, self.num_start, self.num_pad],
                                  ['Prefix', 'Insert', 'Start', 'Pad'],
                                  [self.num_suffix, self.num_pos, self.num_incr, self.num_sep],
                                  ['Suffix', 'At', 'Incr.', 'Sep.'])
        for widget in [self.num_prefix, self.num_suffix, self.num_insert]:
            widget.stateChanged.connect(lambda: self.changed(self.num_box))
        for widget in [self.num_pos, self.num_start, self.num_incr, self.num_pad]:
            widget.valueChanged.connect(lambda: self.changed(self.num_box))
        self.num_sep.textChanged.connect(lambda: self.changed(self.num_box))

        for box in [self.name_box, self.replace_box, self.case_box,
                    self.add_box, self.remove_box, self.num_box]:
            box.change_signal.connect(self.preview_changes)

        self.addWidget(self.name_box,    0, 0)
        self.addWidget(self.replace_box, 1, 0)
        self.addWidget(self.case_box,    2, 0, 2, 1)
        self.addWidget(self.add_box,     0, 1, 2, 1)
        self.addWidget(self.remove_box,  0, 2, 2, 1)
        self.addWidget(self.num_box,     0, 3, 2, 1)
        self.addWidget(self.reset,       2, 3, Qt.AlignRight)
        self.addWidget(self.rename,      3, 3, Qt.AlignRight)
        self.setColumnStretch(0, 1)
        self.setColumnStretch(1, 1)
        self.setColumnStretch(2, 0)
        self.setColumnStretch(3, 0)

    def selection(self):
        selection_model = self.view.selectionModel()
        selection_model.selectionChanged.connect(self.preview_changes)

    def change_dir(self, model, path):
        self.path = Path(path)
        self.model = model
        self.selection()

    def reset_all(self):
        for box in [self.name_box, self.replace_box, self.case_box,
                    self.add_box, self.remove_box, self.num_box]:
            box.clear_fields()
        for index in range(self.model.rowCount()):
            self.model.item(index, 1).setText(self.model.item(index, 0).text())

    def finalize(self):
        replacements = self.preview_changes()
        for index in self.view.selectionModel().selectedRows():
            row = index.row()
            ext = self.model.item(row, 2).text()
            original = self.path / f'{self.model.item(row, 0).text()}{ext}'
            new = self.path / f'{replacements[self.model.item(row, 0).text()]}{ext}'
            try:
                original.rename(new)
            except FileExistsError:
                error = QMessageBox()
                error.setIcon(error.Icon.Critical)
                error.setText(f'Could not rename {original}.\n{new} already exists.\nFile skipped')
                error.setWindowTitle('Error')
                error.exec_()
        self.change_signal.emit(True)
        self.reset_all()

    def preview_changes(self) -> dict[str, str]:
        replacements = {}

        # Values for auto-numbering
        sep = self.num_sep.text()
        pad = self.num_pad.value()
        start = self.num_start.value()
        incr = self.num_incr.value()
        for row in range(self.model.rowCount()):
            self.model.item(row, 1).setText(self.model.item(row, 0).text())

        for index in self.view.selectionModel().selectedRows():
            row = index.row()
            original = self.model.item(row, 0).text()
            new_text = self.model.item(row, 1).text()

            if self.name_box.property('changed'):
                new_text = self.name_entry.text()

            if self.replace_box.property('changed'):
                new_text = new_text.replace(self.replace_entry_search.text(), self.replace_entry_text.text())

            if self.case_box.property('changed'):
                cases = [str.upper, str.lower, str.title, str.capitalize]
                index = self.case_select.currentIndex() - 1
                case = cases[index]
                exceptions = self.case_except.text()
                exception_locs = [m.start() for m in re.finditer(exceptions, new_text)]
                exceptions_len = len(exceptions)
                new_text = case(new_text)
                for loc in exception_locs:
                    new_text = new_text[:loc] + exceptions + new_text[loc + exceptions_len:]

            if self.add_box.property('changed'):
                new_text = self.add_prefix.text() + new_text
                if self.add_insert_pos.value():
                    new_text = (new_text[:self.add_insert_pos.value()] +
                                self.add_insert.text() +
                                new_text[self.add_insert_pos.value():])
                new_text += self.add_suffix.text()

            if self.remove_box.property('changed'):
                if self.remove_first.value():
                    new_text = new_text[self.remove_first.value():]
                if self.remove_last.value():
                    new_text = new_text[:-self.remove_last.value()]
                if self.remove_from.value():
                    new_text = (new_text[:self.remove_from.value()] +
                                new_text[self.remove_to.value() + 1:])
                for char in self.remove_chars.text():
                    new_text = new_text.replace(char, '')
                for word in self.remove_words.text().split():
                    new_text = new_text.replace(word, '')
                if self.remove_crop.text():
                    pos = new_text.find(self.remove_crop.text())
                    if self.remove_crop_pos.currentText() == 'Before':
                        new_text = new_text[pos:]
                    else:
                        new_text = new_text[:pos + len(self.remove_crop.text())]

            if self.num_box.property('changed'):
                if self.num_prefix.isChecked():
                    new_text = f'{start:0>{pad}}{sep}{new_text}'
                if self.num_suffix.isChecked():
                    new_text = f'{new_text}{sep}{start:0>{pad}}'
                if self.num_insert.isChecked() and self.num_pos.value() > 0:
                    pos = self.num_pos.value()
                    new_text = f'{new_text[:pos]}{sep}{start:0>{pad}}{sep}{new_text[pos:]}'
                start += incr

            self.model.item(row, 1).setText(new_text)

            replacements[original] = new_text

        return replacements

    def changed(self, box):
        box.setChanged()
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
            box.setChanged(False)

    def min_remove(self):
        if self.remove_to.value() < self.remove_from.value():
            self.remove_to.setValue(self.remove_from.value())


class main_window(QMainWindow):
    def __init__(self, path):
        super().__init__()
        self.setWindowTitle('Bulk Rename')
        self.path = str(path)
        self.tree_model = QFileSystemModel()
        self.tree_model.setRootPath(self.path)
        self.tree_model.setFilter(QDir.AllDirs | QDir.NoDotAndDotDot)
        self.files_model = files(self.path)

        self.dir_entry = QLineEdit(self.path)
        self.dir_btn = QToolButton()
        self.dir_btn.setArrowType(Qt.RightArrow)
        self.tree = QTreeView()
        self.tree.setModel(self.tree_model)
        self.files = directory_table(self.files_model)
        self.rename_opts = RenameOptions(self.files_model, self.files, self.path)
        self.rename_opts.change_signal.connect(self.update_files)

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
        self.path = self.dir_entry.text()
        index = self.tree_model.index(self.path)
        self.tree.setCurrentIndex(index)
        self.tree.expandRecursively(index, 0)
        self.update_files()

    @Slot(QModelIndex)
    def set_dir(self, index):
        self.path = self.tree_model.filePath(index)
        self.dir_entry.setText(self.path)
        self.tree.setCurrentIndex(index)
        self.update_files()

    def update_files(self):
        self.files_model = files(self.path)
        self.files.setModel(self.files_model)
        self.rename_opts.change_dir(self.files_model, self.path)


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
