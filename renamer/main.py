#! C:/Users/David.Weiss/Programming/Python/bulk-renamer/.env/scripts

from pathlib import Path
import sys
from PySide6.QtCore import QDir, QModelIndex, Slot
from PySide6.QtWidgets import (QApplication, QGridLayout, QHBoxLayout,
                               QLineEdit, QLabel, QMainWindow, QToolButton, QTreeView,
                               QFileSystemModel, QWidget)

"""
Planning:
    GUI window with panes for
    1. directory tree
    2. files in directory
    3. renaming options
    4. Path bar

files should show current name and new name
select which files in a directory we want to rename
sort by name, date modified

rename options include:
    replace x with y
    remove from start, end, position to y or num of chars / words
    add prefix, insert at pos, suffix
    full rename
    auto-numbering
"""


class directory_box(QHBoxLayout):
    def __init__(self, path: str, parent=None):
        super().__init__(parent)
        self.edit = QLineEdit(path)
        self.btn = QToolButton()
        self.addWidget(QLabel('Directory:'))
        self.addWidget(self.edit)
        self.addWidget(self.btn)

    def set_dir(self):
        self.path = self.edit.text()


class directory_tree(QTreeView):
    def __init__(self, path: str, parent=None):
        super().__init__(parent)
        self.model = QFileSystemModel()
        self.model.setRootPath(path)
        self.model.setFilter(QDir.AllDirs | QDir.NoDotAndDotDot)
        self.setModel(self.model)
        self.setIndentation(10)
        for col in range(1, 4):
            self.hideColumn(col)

        self.init_dir(path)

    def init_dir(self, path):
        self.setCurrentIndex(self.model.index(path))


class main_window(QMainWindow):
    def __init__(self, path):
        super().__init__()
        self.path = str(path)
        self.dir_entry = directory_box(self.path)
        self.tree = directory_tree(self.path)

        self.dir_entry.btn.clicked.connect(self.set_tree)
        self.tree.clicked.connect(self.set_dir)
        self.initUI()

    def initUI(self):
        centralWidget = QWidget()
        grid = QGridLayout()
        grid.addLayout(self.dir_entry, 0, 0, 1, 3)
        grid.addWidget(self.tree, 1, 0)

        centralWidget.setLayout(grid)
        self.setCentralWidget(centralWidget)

        self.show()

    def set_tree(self):
        new_dir = self.dir_entry.edit.text()
        index = self.tree.model.index(new_dir)
        self.tree.setCurrentIndex(index)

    @Slot(QModelIndex)
    def set_dir(self, index):
        current = self.tree.model.filePath(index)
        self.dir_entry.edit.setText(current)


def main():
    try:
        path = Path(sys.argv[1])
    except IndexError:
        path = Path().absolute()
    app = QApplication(sys.argv)
    win =  main_window(path)
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
