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
         2                    16                   DG         
         3                    38                   DC         
         4                    57                   DG         
         5                    79                   DA         
         6                   100                   DA         
         7                   121                   DT         
         8                   141                   DT         
         9                   161                   DC         
         10                  180                   DG         
         11                  202                   DC         
         12                  221                   DG         
         13                  243                   DC         
         14                  259                   DG         
         15                  281                   DC         
         16                  300                   DG         
         17                  322                   DA         
         18                  343                   DA         
         19                  364                   DT         
         20                  384                   DT         
         21                  404                   DC         
         22                  423                   DG         
         23                  445                   DC         
         24                  464                   DG         
         25                  486                solvent       '''

    num_lines_reference = len(reference_report.split('\n'))

    assert reference_report in report
    assert num_lines == num_lines_reference+3