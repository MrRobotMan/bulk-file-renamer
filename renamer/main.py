from pathlib import Path
import sys
import os
from PySide6.QtCore import QDir, QModelIndex, Slot, QObject, SIGNAL
from PySide6.QtWidgets import QApplication, QTreeView, QFileSystemModel

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


class directory_tree(QTreeView):
    def __init__(self, path, parent=None):
        super(directory_tree, self).__init__(parent)
        self.path = QDir(path)
        self.model = QFileSystemModel()
        self.model.setRootPath(path)
        self.model.setFilter(QDir.AllDirs | QDir.NoDotAndDotDot)
        self.setModel(self.model)
        self.setCurrentIndex(self.model.index(path))
        self.setIndentation(10)
        for col in range(1, 4):
            self.hideColumn(col)
        self.clicked.connect(self.show_dir)

    @Slot(QModelIndex)
    def show_dir(self, index):
        index = self.model.index(index.row(), 0, index.parent())
        path = QDir(self.model.filePath(index))
        try:
            common = os.path.commonpath([self.path.absolutePath(), path.absolutePath()])
            self.setExpanded(self.model.index(common), False)
        except ValueError:
            self.collapseAll()
        if path.isEmpty(filters=QDir.Filters(QDir.AllDirs | QDir.NoDotAndDotDot)):
            current = Path(self.model.filePath(index))
            self.setExpanded(self.model.index(str(current.parent)), True)
        else:
            self.setExpanded(index, True)
        self.path = path


class App(QApplication):
    def __init__(self, args):
        super().__init__()
        try:
            path = Path(sys.argv[1])
        except IndexError:
            path = Path().absolute()
        tree = directory_tree(str(path))
        tree.show()
        self.exec_()


if __name__ == "__main__":
    app = App(sys.argv)
    sys.exit()
