"""
Print out information about residues found in pdb file
"""

from util import process_pdb

import argparse
import numpy as np

if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument('pdb_file', help='The pdb file to analyze.')

    args = parser.parse_args()

    atom_residues, names = process_pdb(args.pdb_file)

    atom_residues = np.array(atom_residues)

    report = F'''
    {args.pdb_file} processed. 
    Found {len(atom_residues)} atoms and {atom_residues[-1]} residues.\n'''

    residue_index = np.where(atom_residues[:-1] != atom_residues[1:])[0]+1

    report += F'{"Residue Number":<20} {"Starting atom":<20} {"Residue Name":<20}\n'
    report += F'{"1":^20} {"1":^20} {names[0]:^20}\n'

    for count, residue in enumerate(residue_index):
        report += F"{count+2:^20} {residue:^20} {names[residue]:^20}\n"


    print(report)