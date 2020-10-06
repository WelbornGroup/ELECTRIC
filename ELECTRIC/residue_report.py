"""
Print out information about residues found in pdb file
"""

from util import print_info

import argparse


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument("pdb_file", help="The pdb file to analyze.")

    args = parser.parse_args()

    pdb_report = print_info(args.pdb_file)

    print(pdb_report)
