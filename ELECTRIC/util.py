
import numpy as np
import pandas as pd


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
    """

    solvent_residues = ['wat', 'na+', 'cl-', 'hoh', 'na', 'cl']
    accepted_names = ['HETATM', 'ATOM']

    # Determine the number of lines to skip.
    with open(file_path) as f:
        found = False
        line_number = 0
        while not found:
            line = f.readline().split()
            if len(line)>0:
                line = line[0]
            if 'ATOM' in line or 'HETATM' in line:
                found = True
            else:
                line_number +=1

    pdb = pd.read_fwf(file_path, skiprows=line_number, header=None, colspecs=((0,6),
                                                          (6,12), (12, 16), (16,17),
                                                          (17,20), (21, 22), (22, 27),
                                                          (27,28)), dtype=str, keep_default_na=False)
    pdb = pdb[[0,4,6]]
    pdb.columns = ['record type','res name', 'residue number']
    pdb.dropna(inplace=True)

    residue_number = 1
    previous = None
    previous_name = None
    residues = []
    residue_names = []
    for row in pdb.iterrows():
        now_number = row[1]['residue number']
        now_name = row[1]['res name']
        record_type = row[1]['record type']
        if record_type in accepted_names:
            if previous != now_number and previous is not None:
                if not (group_solvent) or \
                            (group_solvent and previous_name.lower() not in solvent_residues) or \
                                (group_solvent and now_name.lower() not in solvent_residues):
                    residue_number += 1

            if now_name.lower() in solvent_residues:
                residue_names.append('solvent')
            else:
                residue_names.append(now_name)

            residues.append(residue_number)
        previous = now_number
        previous_name = now_name
    
    return residues, residue_names


def print_info(pdb_file):
    """
    Print info from process_pdb function.
    """
    atom_residues, names = process_pdb(pdb_file)


    atom_residues = np.array(atom_residues)

    report = F'''
    {pdb_file} processed. 
    Found {len(atom_residues)} atoms and {atom_residues[-1]} residues.\n'''

    residue_index = np.where(atom_residues[:-1] != atom_residues[1:])[0]+1

    report += F'{"Residue Number":<20} {"Starting atom":<20} {"Residue Name":<20}\n'
    report += F'{"1":^20} {"1":^20} {names[0]:^20}\n'

    for count, residue in enumerate(residue_index):
        report += F"{count+2:^20} {residue:^20} {names[residue]:^20}\n"
    
    return report


def index_fragments(fragment_list, ipoles):
    '''
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
    '''
    # Get the atom and pole numbers for the molecules/residues of interest.
    atoms_pole_numbers = []

    fragments = np.unique(fragment_list)

    for fragment in fragments:
        # These are the atom numbers for the atoms in the specified molecules
        fragment_atoms = np.array(np.where(fragment_list == fragment)) + 1
        # The pole indices for the speified molecule
        pole_numbers = [ipoles[atom_index - 1] for atom_index in fragment_atoms[0]]
        atoms_pole_numbers.append(np.array(pole_numbers))

    return atoms_pole_numbers, fragments
