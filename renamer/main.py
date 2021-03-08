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
        self.path = path
        label = QLabel('Directory:')
        self.edit = QLineEdit(self.path)
        btn = QToolButton()
        btn.clicked.connect(self.set_dir)
        self.addWidget(label)
        self.addWidget(self.edit)
        self.addWidget(btn)

    def set_dir(self):
        self.path = self.edit.text()



class directory_tree(QTreeView):
    def __init__(self, path: str, parent=None):
        super().__init__(parent)
        self.path = path
        self.model = QFileSystemModel()
        self.model.setRootPath(self.path)
        self.model.setFilter(QDir.AllDirs | QDir.NoDotAndDotDot)
        self.setModel(self.model)
        self.setCurrentIndex(self.model.index(self.path))
        self.setIndentation(10)
        for col in range(1, 4):
            self.hideColumn(col)
        self.clicked.connect(self.show_dir)

    @Slot(QModelIndex)
    def show_dir(self, index):
        current = self.model.filePath(index)
        self.setCurrentIndex(index)
        self.path = current


class main_window(QMainWindow):
    def __init__(self, path):
        super().__init__()
        self.path = str(path)
        self.initUI()

    def initUI(self):
        self.setGeometry(300, 300, 300, 300)
        centralWidget = QWidget()
        grid = QGridLayout()
        dir_label = directory_box(self.path)
        tree = directory_tree(self.path)
        grid.addLayout(dir_label, 0, 0, 1, 3)
        grid.addWidget(tree, 1, 0)

        centralWidget.setLayout(grid)
        self.setCentralWidget(centralWidget)

        self.show()


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
