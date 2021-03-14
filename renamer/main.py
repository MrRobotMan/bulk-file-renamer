import sys
import os
import time
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

files should show current name and new name
select which files in a directory we want to rename
sort by name, date modified

rename options include:
    replace x with y
    wholly rename
    change case (upper, lower, title, sentence)
    remove from start, end, position to y, exact of chars / words, crop before or after
    add prefix, insert at pos, suffix
    auto-numbering prefix, suffix, prefix + suffix, insert at
"""


def files(path: str, parent=None) -> QStandardItemModel:
    path = Path(path)
    model = QStandardItemModel(parent)
    model.setHorizontalHeaderLabels(['Name', 'New Name', 'Type', 'Modified'])
    rows = len(list(path.iterdir()))
    model.setRowCount(rows)
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


def format_time(path: Path) -> str:
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
    spin = QSpinBox(parent)
    spin.setSpecialValueText('-')
    spin.setFixedWidth(50)
    return spin


def directory_table(model: QStandardItemModel, parent=None) -> QTableView:
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


def directory_box(path: str, parent=None) -> tuple(QHBoxLayout, QLineEdit, QToolButton):
    box = QHBoxLayout(parent)
    entry = QLineEdit(path)
    btn = QToolButton()
    btn.setArrowType(Qt.RightArrow)
    box.addWidget(QLabel('Directory:'))
    box.addWidget(entry)
    box.addWidget(btn)

    return box, entry, btn


class directory_tree(QTreeView):
    def __init__(self, model, parent=None):
        super().__init__(parent)
        self.setModel(model)
        self.setIndentation(10)
        for col in range(1, 4):
            self.hideColumn(col)
        self.clicked.connect(self.expand_here)
        self.setFixedSize(175, 400)

    @Slot()
    def expand_here(self, index):
        self.expandRecursively(index, 0)


class rename_box(QGridLayout):
    def __init__(self, title: str, widgets: list, labels: list = None,
                 widgets2: list = None, labels2: list = None, parent=None) -> None:
        super().__init__(parent)
        self.widgets = widgets
        self.widgets2 = widgets2
        columns = sum(x is not None for x in [labels, widgets2, labels2])
        columns = max(1, columns)
        self.clear = QPushButton('X')
        self.clear.setFixedSize(15, 15)
        self.addWidget(QLabel(title), 0, 0)
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
        return None


class rename_options(QGridLayout):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.rename = QPushButton('Rename')

        self.name_entry = QLineEdit()
        name_box = rename_box('Name', [self.name_entry])

        self.replace_entry_search = QLineEdit()
        self.replace_entry_text = QLineEdit()
        replace_box = rename_box('Replace',
                                 [self.replace_entry_search, self.replace_entry_text],
                                 ['Replace', 'With'])

        self.case_select = QComboBox()
        self.case_select.addItems(['Upper', 'Lower', 'Title', 'Sentence'])
        self.case_select.setEditable(False)
        self.case_except = QLineEdit()
        case_box = rename_box('Case', [self.case_select, self.case_except],
                              ['', 'Except'])

        self.add_prefix = QLineEdit()
        self.add_insert = QLineEdit()
        self.add_insert_pos = blank_spinbox()
        self.add_suffix = QLineEdit()
        add_box = rename_box('Add',
                             [self.add_prefix, self.add_insert,
                              self.add_insert_pos, self.add_suffix],
                             ['Prefix', 'Insert', 'At', 'Suffix'])

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
        remove_box = rename_box('Remove',
                                [self.remove_first, self.remove_from,
                                 self.remove_chars, self.remove_crop_pos],
                                ['First', 'From', 'Chars', 'Crop'],
                                [self.remove_last, self.remove_to,
                                 self.remove_words, self.remove_crop],
                                ['Last', 'To', 'Words', ''])

        self.num_prefix = QCheckBox()
        self.num_suffix = QCheckBox()
        self.num_insert = QCheckBox()
        self.num_pos = blank_spinbox()
        self.num_start = blank_spinbox()
        self.num_incr = blank_spinbox()
        self.num_pad = blank_spinbox()
        self.num_sep = QLineEdit()
        num_box = rename_box('Auto Number',
                             [self.num_prefix, self.num_insert, self.num_start, self.num_pad],
                             ['Prefix', 'Insert', 'Start', 'Pad'],
                             [self.num_suffix, self.num_pos, self.num_incr, self.num_sep],
                             ['Suffix', 'At', 'Incr.', 'Sep.'])

        self.addLayout(name_box, 0, 0)
        self.addLayout(replace_box, 1, 0)
        self.addLayout(case_box, 2, 0)
        self.addLayout(add_box, 0, 1, 2, 1)
        self.addLayout(remove_box, 0, 2, 2, 1)
        self.addLayout(num_box, 0, 3, 2, 1)
        self.addWidget(self.rename, 2, 3)


class main_window(QMainWindow):
    def __init__(self, path):
        super().__init__()
        self.setWindowTitle('Bulk Rename')
        self.path = str(path)
        self.tree_model = QFileSystemModel()
        self.tree_model.setRootPath(self.path)
        self.tree_model.setFilter(QDir.AllDirs | QDir.NoDotAndDotDot)
        self.files_model = files(path)

        self.dir_box, self.dir_entry, self.dir_btn = directory_box(self.path)
        self.tree = directory_tree(self.tree_model)
        self.files = directory_table(self.files_model)
        self.rename_opts = rename_options()

        self.initUI()

        self.dir_btn.clicked.connect(self.set_tree)
        self.dir_entry.returnPressed.connect(self.set_tree)
        self.tree.clicked.connect(self.set_dir)
        self.rename_opts.rename.clicked.connect(self.show_data)

        self.set_tree()
        self.setMaximumSize(self.width(), self.height())

    def initUI(self):
        centralWidget = QWidget()
        grid = QGridLayout()
        grid.setColumnStretch(1, 1)
        grid.addLayout(self.dir_box, 0, 0, 1, 3)
        grid.addWidget(self.tree, 1, 0)
        grid.addWidget(self.files, 1, 1)
        grid.addLayout(self.rename_opts, 2, 0, 1, 3)

        centralWidget.setLayout(grid)
        self.setCentralWidget(centralWidget)

    @Slot()
    def set_tree(self, path=None):
        path = self.dir_entry.entry.text() if not path else path
        index = self.tree_model.index(path)
        self.tree.setCurrentIndex(index)
        self.tree.expandRecursively(index, 0)
        self.files.setModel(self.files_model)

    @Slot(QModelIndex)
    def set_dir(self, index):
        current = self.tree_model.filePath(index)
        self.files_model = files(current)
        self.dir_entry.entry.setText(current)
        self.tree.setCurrentIndex(index)
        self.files.setModel(self.files_model)

    @Slot()
    def show_data(self):
        for index in self.files.selectionModel().selectedRows():
            row = index.row()
            print(self.files_model.item(row, 1).text())


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
