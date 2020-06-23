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
    ('ke15_noheader.pdb', True, 48051, 255),
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
