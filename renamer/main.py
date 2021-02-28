from pathlib import Path
import sys
from PySide6.QtWidgets import QApplication, QLabel

import tkinter as tk
import tkinter.ttk as ttk
from tkinter import filedialog

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


class CurrentDir(tk.Frame):
    def __init__(self, parent):
        """
        Shows the path of the current directory in use
        """
        super().__init__(parent)
        cwd = Path().absolute()
        self.current_path = tk.StringVar(value=cwd)

        up_one_folder_btn = ttk.Button(self, command=self.up_one)
        up_one_folder_btn.grid(row=0, column=0)

        current_path_box = ttk.Entry(self, textvariable=self.current_path, width=50)
        current_path_box.grid(row=0, column=1)

        select_dir_btn = ttk.Button(self, command=self.select_dir)
        select_dir_btn.grid(row=0, column=2)

    def up_one(self):
        """
        Moves the directory up one level
        """
        parent_dir = Path(self.current_path.get()).parent
        self.current_path.set(parent_dir)

    def select_dir(self):
        """
        Selects a new directory
        """
        new_dir = filedialog.askdirectory()
        self.current_path.set(new_dir)


class DirectoryTree(tk.Frame):
    def __init__(self, parent, path):
        super().__init__(parent)
        self.tree = ttk.Treeview(self)
        self.path = path
        self.path.trace_add('write', self.update_tree)
        ysb = ttk.Scrollbar(self, orient='vertical', command=self.tree.yview)
        xsb = ttk.Scrollbar(self, orient='horizontal', command=self.tree.xview)
        self.tree.configure(yscroll=ysb.set, xscroll=xsb.set)
        self.tree.heading('#0', text=self.path.get(), anchor='w')

        abspath = Path(self.path.get()).absolute()
        root_node = self.tree.insert('', 'end', text=abspath, open=True)
        self.process_directory(root_node, abspath)

        self.tree.grid(row=0, column=0)
        ysb.grid(row=0, column=1, sticky='ns')
        xsb.grid(row=1, column=0, sticky='ew')

    def update_tree(self, *args):
        """
        Clears the tress and processes the new directory
        """
        self.tree.delete(*self.tree.get_children())
        self.tree.heading('#0', text=self.path.get(), anchor='w')
        abspath = Path(self.path.get()).absolute()
        root_node = self.tree.insert('', 'end', text=abspath, open=True)
        self.process_directory(root_node, abspath)

    def process_directory(self, parent, path):
        """
        Creates a new tree
        """
        for p in path.iterdir():
            abspath = path / p
            oid = self.tree.insert(parent, 'end', text=p, open=False)
            if abspath.is_dir():
                self.process_directory(oid, abspath)


class App(tk.Frame):
    def __init__(self, master, default_directory=None):
        super().__init__(master)

        directory = CurrentDir(self, default_directory)
        path = directory.current_path
        directory.grid(row=0, column=0, columnspan=2, sticky='nsw')

        tree_frame = DirectoryTree(self, path)
        tree_frame.grid(row=1, column=0)

        directory_frame = tk.Frame(self)
        ttk.Label(directory_frame, text='Show files here').grid(sticky='nsew')
        directory_frame.grid(row=1, column=1)

        options_frame = tk.Frame(self)
        ttk.Label(options_frame, text='Show rename opiions here').grid(sticky='nsew')
        options_frame.grid(row=2, column=1, columnspan=2)

        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=1)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    label = QLabel("Hello World!")
    label.show()
    app.exec_()
    sys.exit()
    # root = tk.Tk()
    # App(root, args.directory).grid()
    # root.mainloop()
