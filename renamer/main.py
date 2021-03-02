from pathlib import Path
import sys
from PySide6.QtCore import QDir, Slot, QObject, SIGNAL
from PySide6.QtWidgets import QApplication, QTreeView, QFileSystemModel

"""
Planning:
    GUI window with panes for
    1. directory tree
    2. files in directory
    3. renaming options

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
    def __init__(self, path):
        super(directory_tree, self).__init__()
        self.model = QFileSystemModel()
        self.model.setRootPath(path)
        self.model.setFilter(QDir.AllDirs | QDir.NoDotAndDotDot)
        self.setModel(self.model)
        self.setCurrentIndex(self.model.index(path))
        self.setIndentation(10)
        for col in range(1, 4):
            self.hideColumn(col)
        QObject.connect(self.selectionModel(),
                        SIGNAL('selectionChanged(QItemSelection, QItemSelection)'),
                        self.show_dir)

    @Slot("QItemSelection, QItemSelection")
    def show_dir(self, selected, deselected):
        print(selected.data())
        print(deselected)


class App(QApplication):
    def __init__(self, args):
        super().__init__()
        if len(args) > 1:
            path = args[1]
        else:
            path = QDir.currentPath()
        tree = directory_tree(path)
        tree.show()
        self.exec_()


if __name__ == "__main__":
    app = App(sys.argv)
    sys.exit()
