import sys
import os
import time
from pathlib import Path

from PySide6.QtCore import QDir, QModelIndex, Slot, Qt
from PySide6.QtGui import QStandardItem, QStandardItemModel
from PySide6.QtWidgets import (QAbstractItemView, QApplication,
                               QFileSystemModel, QGridLayout, QHBoxLayout,
                               QLabel, QLineEdit, QMainWindow, QPushButton, QTableView,
                               QToolButton, QTreeView, QWidget)

"""
Planning:
    GUI window with panes for
    1. directory tree - Done
    2. files in directory - Done
    3. renaming options
    4. Path bar - Done

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


class files(QStandardItemModel):
    def __init__(self, path, parent=None):
        super().__init__(parent)
        self.path = Path(path)
        self.setHorizontalHeaderLabels(['Name', 'New Name', 'Type', 'Modified'])
        rows = len(list(self.path.iterdir()))
        self.setRowCount(rows)
        self.setColumnCount(4)
        for row, child in enumerate(self.path.iterdir()):
            name = QStandardItem(str(child.stem))
            new_name = QStandardItem(str(child.stem))
            if child.is_dir():
                ext = QStandardItem('File Folder')
            else:
                ext = QStandardItem(str(child.suffix))
            modified = QStandardItem(self.format_time(child))
            row_data = [name, new_name, ext, modified]
            for col, item in enumerate(row_data):
                self.setItem(row, col, item)

    def format_time(self, path):
        """
        Takes a path and returns the last modified time in D/M/YYYY H:mm:ss AM/PM format
        """
        mod = os.path.getmtime(path)
        formatted = time.localtime(mod)
        clean = time.strftime('%d/%m/%Y %I:%M:%S %p', formatted).replace('/0', '/')
        if clean.startswith('0'):
            return clean[1:]
        return clean


class directory_table(QTableView):
    def __init__(self, path, parent=None):
        super().__init__(parent)
        self.update_view(path)
        self.verticalHeader().hide()
        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.setSortingEnabled(True)
        self.model = files(path)
        self.setModel(self.model)
        self.setColumnWidth(0, 300)
        self.setColumnWidth(1, 300)
        self.setColumnWidth(2, 150)
        self.setColumnWidth(3, 300)
        self.setFixedSize(1050, 400)

    def update_view(self, path):
        self.model = files(path)
        self.setModel(self.model)


class directory_box(QHBoxLayout):
    def __init__(self, path, parent=None):
        super().__init__(parent)
        self.entry = QLineEdit(path)
        self.btn = QToolButton()
        self.btn.setArrowType(Qt.RightArrow)
        self.addWidget(QLabel('Directory:'))
        self.addWidget(self.entry)
        self.addWidget(self.btn)

    def set_dir(self):
        self.path = self.entry.text()


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


class rename_options(QGridLayout):
    def __init__(self, parent=None):
        super().__init__(parent)
        name_label = QLabel('Name')
        name_entry = QLineEdit()
        self.addWidget(name_label, 0, 0)
        self.addWidget(name_entry, 1, 0)


class main_window(QMainWindow):
    def __init__(self, path):
        super().__init__()
        self.setWindowTitle('Bulk Rename')
        self.path = str(path)
        self.model = QFileSystemModel()
        self.model.setRootPath(self.path)
        self.model.setFilter(QDir.AllDirs | QDir.NoDotAndDotDot)

        self.dir_entry = directory_box(self.path)
        self.tree = directory_tree(self.model)
        self.files = directory_table(self.path)
        self.go_button = QPushButton("Get Data")

        self.initUI()

        self.dir_entry.btn.clicked.connect(self.set_tree)
        self.dir_entry.entry.returnPressed.connect(self.set_tree)
        self.tree.clicked.connect(self.set_dir)
        self.go_button.clicked.connect(self.show_data)

        self.set_tree()
        self.setMaximumSize(self.width(), self.height())

    def initUI(self):
        centralWidget = QWidget()
        grid = QGridLayout()
        grid.setColumnStretch(1, 1)
        grid.addLayout(self.dir_entry, 0, 0, 1, 3)
        grid.addWidget(self.tree, 1, 0)
        grid.addWidget(self.files, 1, 1)
        grid.addWidget(self.go_button, 2, 0, 1, 3)

        centralWidget.setLayout(grid)
        self.setCentralWidget(centralWidget)

    @Slot()
    def set_tree(self, path=None):
        path = self.dir_entry.entry.text() if not path else path
        index = self.model.index(path)
        self.tree.setCurrentIndex(index)
        self.tree.expandRecursively(index, 0)
        self.files.update_view(path)

    @Slot(QModelIndex)
    def set_dir(self, index):
        current = self.model.filePath(index)
        self.dir_entry.entry.setText(current)
        self.tree.setCurrentIndex(index)
        self.files.update_view(current)

    @Slot()
    def show_data(self):
        for index in self.files.selectionModel().selectedRows():
            row = index.row()
            print(self.files.model.item(row, 1).text())


def main():
    try:
        path = Path(sys.argv[1])
    except IndexError:
        path = Path().absolute()
    app = QApplication(sys.argv)
    window = main_window(path)
    window.show()

    # with open('renamer/style.qss', 'r') as f:
    #     _style = f.read()
    #     app.setStyleSheet(_style)
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
