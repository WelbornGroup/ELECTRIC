import numpy as np
import pandas as pd

import argparse


def create_parser():
    """
    Create parser to get command line arguments.
    """

    # Handle arguments with argparse
    parser = argparse.ArgumentParser(
        add_help=False, formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    required = parser.add_argument_group("Required Arguments")
    optional = parser.add_argument_group("optional arguments")

    # Add back help
    optional.add_argument(
        "-h", "--help", action="help", help="show this help message and exit"
    )

    required.add_argument(
        "-mdi",
        help='flags for mdi. When in doubt, `-mdi "-role ENGINE -name NO_EWALD -method TCP -port 8021 -hostname localhost", type=str, required=True` is a good option.',
    )
    required.add_argument(
        "-snap",
        help="The file name of the trajectory to analyze.",
        type=str,
        required=True,
    )

    required.add_argument(
        "-probes",
        help="""
                Atom indices which are probes for the electric field calculations. 
                For example, if you would like to calculate the electric field along 
                the bond between atoms 1 and 2, you would use `-probes "1 2"`.""",
        type=str,
        required=True,
    )

    optional.add_argument(
        "--nengines",
        help="""
                This option allows the driver to farm tasks out to multiple Tinker 
                engines simultaneously, enabling parallelization of the electric field analysis 
                computation. The argument to this option **must** be equal to the number of
                Tinker engines that are launched along with the driver.""",
        type=int,
        default=1,
    )

    optional.add_argument(
        "--equil",
        help="""
                'The number of frames to skip performing analysis on
                at the beginning of the trajectory file (given by the -snap argument)
                For example, using --equil 50 will result in analysis starting after frame 50 of the trajectory, 
                (in other words, the first frame which will be analyzed is frame 50 + stride).""",
        type=int,
        default=0,
    )

    optional.add_argument(
        "--stride",
        help="""
                The number of frames to skip between analysis calculations. For example, using --stride 2 would
                result in analysis of every other frame in the trajectory.""",
        type=int,
        default=1,
    )

    optional.add_argument(
        "--byres",
        help="""
                Flag which indicates electric field
                at the probe atoms should be calculated with electric field contributions given
                per residue. If --byres is indicated, the argument should be followed
                by the filename for a pdb file which gives residues.""",
    )

    optional.add_argument(
        "--bymol",
        help="""
                Flag which indicates electric field
                at the probe atoms should be calculated with electric field contributions given
                per molecule.""",
        action="store_true",
    )

    optional.add_argument(
        "--components-only",
        help="""
                Flag which indicates that only the electric field components should be calculated.
                If this flag is set, the electric field projection will not be calculated.""",
        action="store_true",
    )

    return parser


def process_pdb(file_path, group_solvent=True):
    """
    Process pdb and return residues.

    Parameters
    ----------
    file_path : str
        The path to the file

    group_solvent : bool, optional
        groups sequential solvent molecules into residues when True.

    Returns
    -------
    residues : list
        A list of size n_atoms where each element gives the residue number that atom belongs to.

    residue_names : list
        A list of residue names.
    """

    solvent_residues = ["wat", "na+", "cl-", "hoh", "na", "cl"]
    accepted_names = ["HETATM", "ATOM"]

    # Determine the number of lines to skip.
    with open(file_path) as f:
        found = False
        line_number = 0
        while not found:
            line = f.readline().split()
            if len(line) > 0:
                line = line[0]
            if "ATOM" in line or "HETATM" in line:
                found = True
            else:
                line_number += 1

    pdb = pd.read_fwf(
        file_path,
        skiprows=line_number,
        header=None,
        colspecs=(
            (0, 6),
            (6, 12),
            (12, 16),
            (16, 17),
            (17, 20),
            (21, 22),
            (22, 27),
            (27, 28),
        ),
        dtype=str,
        keep_default_na=False,
    )
    pdb = pdb[[0, 4, 6]]
    pdb.columns = ["record type", "res name", "residue number"]
    pdb.dropna(inplace=True)

    residue_number = 1
    previous = None
    previous_name = None
    residues = []
    residue_names = []
    for row in pdb.iterrows():
        now_number = row[1]["residue number"]
        now_name = row[1]["res name"]
        record_type = row[1]["record type"]
        if record_type in accepted_names:
            if previous != now_number and previous is not None:
                if (
                    not (group_solvent)
                    or (group_solvent and previous_name.lower() not in solvent_residues)
                    or (group_solvent and now_name.lower() not in solvent_residues)
                ):
                    residue_number += 1

            if now_name.lower() in solvent_residues:
                residue_names.append("solvent")
            else:
                residue_names.append(now_name)

            residues.append(residue_number)
        previous = now_number
        previous_name = now_name

    return residues, residue_names


def print_info(pdb_file):
    """
    Print residue information for pdb file.

    Parameters
    ----------
    pdb_file : str
        The path to the pdb file for which to print residue information.

    Returns
    -------
    report : str
        A string containing information about the residues in the pdb.
    """
    atom_residues, names = process_pdb(pdb_file)

    atom_residues = np.array(atom_residues)

    report = f"""
    {pdb_file} processed. 
    Found {len(atom_residues)} atoms and {atom_residues[-1]} residues.\n"""

    # Add two because this gives the index before the change (1), another because atom numbering starts at 1, and indexing starts at 0.
    residue_index = np.where(atom_residues[:-1] != atom_residues[1:])[0] + 2

    report += f'{"Residue Number":<20} {"Starting atom":<20} {"Residue Name":<20}\n'
    report += f'{"1":^20} {"1":^20} {names[0]:^20}\n'

    for count, residue in enumerate(residue_index):
        report += f"{count+2:^20} {residue:^20} {names[residue]:^20}\n"

    return report


def index_fragments(fragment_list, ipoles):
    """
    Calculates the pole index of atom numbers given in fragment list.

    Parameters
    ----------
    fragment_list : list
        a list of size natom containing the fragment number for each atom.

    ipoles : list
        a list of size natom containing the pole indices from Tinker.

    Returns
    -------
    atoms_pole_numbers : list
        A multidimensional list where each element gives the pole indices in that fragment.

    fragments : list
        A list of the fragment numbers.
    """
    # Get the atom and pole numbers for the molecules/residues of interest.
    atoms_pole_numbers = []

    fragments = np.unique(fragment_list)

    for fragment in fragments:
        # These are the atom numbers for the atoms in the specified molecules
        fragment_atoms = np.array(np.where(fragment_list == fragment)) + 1
        # The pole indices for the specified molecule
        pole_numbers = [ipoles[atom_index - 1] for atom_index in fragment_atoms[0]]
        atoms_pole_numbers.append(np.array(pole_numbers))

    return atoms_pole_numbers, fragments
