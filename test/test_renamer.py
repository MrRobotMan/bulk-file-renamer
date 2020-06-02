import unittest
from unittest.mock import patch
from renamer import renamer


@patch('renamer.loc.iterdir')
def test(mock_loc):
    mock_loc = ['file1.dwg', 'file1.pdf', 'file2.pdf']
    old = 'file1'
    new = 'newfile1'

    # Output
    correct = ['newfile1.dwg', 'newfile1.pdf', 'file2.pdf']

    # test