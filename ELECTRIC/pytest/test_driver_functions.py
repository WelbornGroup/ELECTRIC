"""
Some functions to test the driver.
"""

import os
import sys

import numpy as np
import pytest

sys.path.append('../')
import util

@pytest.mark.parametrize("file_name, group_solvent, num_atom, num_res", [
    ('1bna.pdb', True, 566, 25),
    ('1bna.pdb', False, 566, 104),
    ('1bna_blank_line.pdb', True, 566, 25),
    ('ke15.pdb', True, 48051, 255),
    ('ke15_no_header.pdb', True, 48051, 255),
])
def test_process_pdb(file_name, group_solvent, num_atom, num_res):
    base_location = os.path.dirname(os.path.realpath(__file__))
    pdb_path = os.path.join(base_location, '..', '..', 'test', 'pytest_data', file_name)
    residues = util.process_pdb(pdb_path, group_solvent=group_solvent)[0]

    assert len(residues) == num_atom
    assert residues[-1] == num_res

def test_index_fragments():
    ipoles = list(range(1, 11))
    fragments = [1, 1, 1, 2, 2, 3, 3, 4, 4, 4]

    pole_index_by_fragment = util.index_fragments(fragments, ipoles)[0]

    print(pole_index_by_fragment)
    print(len(pole_index_by_fragment))

    expected_index = np.array([
        np.array([1, 2, 3]),
        np.array([4, 5]),
        np.array([6, 7]),
        np.array([8, 9, 10])])

    assert len(expected_index) == len(pole_index_by_fragment)

    for i in range(len(expected_index)):
        assert np.array_equal(pole_index_by_fragment[i], expected_index[i])


def test_report():
    base_location = os.path.dirname(os.path.realpath(__file__))
    pdb_path = os.path.join(base_location, '..', '..', 'test', 'pytest_data', '1bna.pdb')

    report = util.print_info(pdb_path)
    num_lines = len(report.split('\n'))

    reference_report = '''Found 566 atoms and 25 residues.
Residue Number       Starting atom        Residue Name        
         1                    1                    DC         
         2                    17                   DG         
         3                    39                   DC         
         4                    58                   DG         
         5                    80                   DA         
         6                   101                   DA         
         7                   122                   DT         
         8                   142                   DT         
         9                   162                   DC         
         10                  181                   DG         
         11                  203                   DC         
         12                  222                   DG         
         13                  244                   DC         
         14                  260                   DG         
         15                  282                   DC         
         16                  301                   DG         
         17                  323                   DA         
         18                  344                   DA         
         19                  365                   DT         
         20                  385                   DT         
         21                  405                   DC         
         22                  424                   DG         
         23                  446                   DC         
         24                  465                   DG         
         25                  487                solvent       '''

    num_lines_reference = len(reference_report.split('\n'))

    assert reference_report in report
    assert num_lines == num_lines_reference+3