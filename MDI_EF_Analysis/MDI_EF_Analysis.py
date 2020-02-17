import sys
import time
import argparse
import numpy as np
import pandas as pd

from copy import deepcopy

# Use local MDI build
import mdi.MDI_Library as mdi

try:
    from mpi4py import MPI
    use_mpi4py = True
except ImportError:
    use_mpi4py = False


# Get the MPI communicator
if use_mpi4py:
    mpi_world = MPI.COMM_WORLD
else:
    mpi_world = None

def mdi_checks(mdi_engine):
    """
    Perform checks on the MDI driver we have accepted to make sure it fits this analysis.
    """
    # Confirm that this code is being used as a driver
    role = mdi_engine.MDI_Get_Role()
    if not role == mdi_engine.MDI_DRIVER:
        raise Exception("Must run driver_py.py as a DRIVER")

    # Connect to the engine
    engine_comm = mdi_engine.MDI_NULL_COMM
    nengines = 1
    for iengine in range(nengines):
        comm = mdi.MDI_Accept_Communicator()

        # Determine the name of the engine
        mdi_engine.MDI_Send_Command("<NAME", comm)
        name = mdi_engine.MDI_Recv(mdi.MDI_NAME_LENGTH, mdi.MDI_CHAR, comm)
        print(F"Engine name: {name}")

        if name == "NO_EWALD":
            if engine_comm != mdi_engine.MDI_NULL_COMM:
                raise Exception("Accepted a communicator from a second NO_EWALD engine.")
            engine_comm = comm
        else:
            raise Exception("Unrecognized engine name", name)

    return engine_comm


if __name__ == "__main__":

    conversion_factor = 1440  # Conversion factor for Tinker units to Mv/cm.

    ###########################################################################
    #
    #   Handle user arguments
    #
    ###########################################################################

    start = time.time()
    # Handle arguments with argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("-mdi", help="flags for mdi", type=str, required=True)
    parser.add_argument("-snap", help="the snapshot file to process", type=str,
        required=True)
    parser.add_argument("-probes", help="indices of the probe atoms", type=str,
        required=True)
    parser.add_argument("--byres", help="give electric field at probe by residue")
    parser.add_argument("--bymol", help="give electric field at probe by molecule",
        action="store_true")
    parser.add_argument("--equil", help="number of equilibration frames to skip")
    parser.add_argument("--stride", help="number of frames between analysis", type=int)

    args = parser.parse_args()

    print("Initializing MDI")
    # Process args for MDI
    mdi.MDI_Init(args.mdi, mpi_world)
    print("MDI Initialized.")

    if use_mpi4py:
        mpi_world = mdi.MDI_Get_Intra_Code_MPI_Comm()
        world_rank = mpi_world.Get_rank()


    snapshot_filename = args.snap
    probes = [int(x) for x in args.probes.split()]

    if args.byres and args.bymol:
        parser.error("--byres and --bymol cannot be used together. Please only use one.")

    if not args.equil:
        equil = 0
    else:
        equil = args.equil

    if not args.stride:
        stride = 1
    else:
        stride = args.stride

    print("Checking MDI")
    engine_comm = mdi_checks(mdi)

    # Print the probe atoms
    print(F"Probes: {probes}")

    elapsed = time.time() - start
    print(F'Setup:\t {elapsed}')

    ###########################################################################
    #
    #   Get Information from Tinker
    #
    ###########################################################################

    start = time.time()
    # Get the number of atoms
    mdi.MDI_Send_Command("<NATOMS", engine_comm)
    natoms_engine = mdi.MDI_Recv(1, mdi.MDI_INT, engine_comm)
    print(F"natoms: {natoms_engine}")

    # Get the number of multipole centers
    mdi.MDI_Send_Command("<NPOLES", engine_comm)
    npoles = mdi.MDI_Recv(1, mdi.MDI_INT, engine_comm)
    print("npoles: " + str(npoles))

    # Get the indices of the mulitpole centers per atom
    mdi.MDI_Send_Command("<IPOLES", engine_comm)
    ipoles = mdi.MDI_Recv(natoms_engine, mdi.MDI_INT, engine_comm)

    # Get the molecule information
    mdi.MDI_Send_Command("<MOLECULES", engine_comm)
    molecules = np.array(mdi.MDI_Recv(natoms_engine, mdi.MDI_INT, engine_comm))

    # Get the residue information
    mdi.MDI_Send_Command("<RESIDUES", engine_comm)
    residues = np.array(mdi.MDI_Recv(natoms_engine, mdi.MDI_INT, engine_comm))
    elapsed = time.time() - start
    print(F'Initial Info to Tinker:\t {elapsed}')


    ###########################################################################
    #
    #   Calculate Indices
    #
    ###########################################################################

    ## Bookkeeping

    # Probe is given as atom number by user, but this may not correspond
    # to the pole index. We have to get it from ipoles which gives
    # the pole index for each atom. We subtract 1 because python
    # indexes from 0, but the original (fortran) indexes from one.
    # ipoles is length natom and gives the pole number for each atom.
    # probe_pole_indices gives the pole number (starts at 1 because we are passing)
    # to Tinker

    start = time.time()

    probe_pole_indices = [int(ipoles[atom_number-1]) for atom_number in probes]
    print(F'Probe pole indices {probe_pole_indices}')

    # Get the atom and pole numbers for the molecules/residues of interest.
    atoms_pole_numbers = []
    if args.bymol:
        by_type = 'molecule'
        from_fragment = np.unique(molecules)
        for mol in from_fragment:
            # These are the atom numbers for the atoms in the specified molecules
            molecule_atoms = np.array(np.where(molecules == mol)) + 1
            # The pole indices for the speified molecule
            pole_numbers = [ipoles[atom_index - 1] for atom_index in molecule_atoms[0]]
            atoms_pole_numbers.append(np.array(pole_numbers))
    elif args.byres:
        by_type = 'residue'
        from_fragment = np.unique(residues)
        for res in from_fragment:
            # These are the atom numbers for the atoms in the specified residues
            residue_atoms = np.array(np.where(residues == res)) + 1
            # The pole indices for the speified molecule
            pole_numbers = [ipoles[atom_index - 1] for atom_index in residue_atoms[0]]
            atoms_pole_numbers.append(np.array(pole_numbers))
    else:
        by_type = 'atom'
        # We are interested in all of the atoms.
        from_fragment = list(range(1,natoms_engine+1))
        atoms_pole_numbers = np.array([[x] for x in ipoles])

    elapsed = time.time() - start
    print(F'Bookkeeping:\t {elapsed}')

    ###########################################################################
    #
    #   Send Probe Information to Tinker
    #
    ###########################################################################
    start = time.time()
    # Inform Tinker of the probe atoms
    mdi.MDI_Send_Command(">NPROBES", engine_comm)
    mdi.MDI_Send(len(probes), 1, mdi.MDI_INT, engine_comm)
    mdi.MDI_Send_Command(">PROBES", engine_comm)
    mdi.MDI_Send(probe_pole_indices, len(probes), mdi.MDI_INT, engine_comm)

    angstrom_to_bohr = mdi.MDI_Conversion_Factor("angstrom","atomic_unit_of_length")
    elapsed - time.time() - start
    print(F'Sending info to tinker:\t {elapsed}')

    ###########################################################################
    #
    #   Engine and Trajectory File Compatibility Check.
    #
    ###########################################################################

    # Check that engine and trajectory are compatible.
    # Process first two lines of snapshot to get information.
    with open(snapshot_filename,"r") as snapshot_file:
        first_line = snapshot_file.readline()
        natoms = int(first_line.split()[0])
        second_line = snapshot_file.readline().split()
        if len(second_line) == 6:
            # This line gives box information if length is 6.
            # This means we will need to skip two lines for every frame.
            skip_line = 2
        else:
            skip_line = 1

    if natoms != natoms_engine:
        raise Exception(F"Snapshot file and engine have inconsistent number of atoms \
                            Engine : {natoms_engine} \n Snapshot File : {natoms}")

    ###########################################################################
    #
    #   Read Trajectory and do analysis.
    #
    ###########################################################################

    start = time.time()

    # Overallocate array since we don't know how many frames
    output = pd.DataFrame(index=range(len(from_fragment) * np.sum(range(len(probes)-1))))

    # Read trajectory and do analysis
    for snap_num, snapshot in enumerate(pd.read_csv(snapshot_filename, chunksize=natoms+skip_line,
        header=None, delim_whitespace=True, names=range(15),
        skiprows=skip_line, index_col=None)):

        if snap_num > equil - 1:
            if snap_num % stride == 0:

                # Pull out just coords, convert to numeric and use conversion factor.
                # columns 2-4 of the pandas dataframe are the coordinates.
                # Must create a copy to send to MDI.
                snapshot_coords = (snapshot.iloc[:natoms , 2:5].apply(pd.to_numeric) *
                    angstrom_to_bohr).to_numpy()

                mdi.MDI_Send_Command(">COORDS", engine_comm)
                mdi.MDI_Send(snapshot_coords.copy(), 3*natoms, mdi.MDI_DOUBLE, engine_comm)

                # Get the electric field information
                # mdi.MDI_Send_Command("<FIELD", engine_comm)
                # field = np.zeros(3 * npoles, dtype='float64')
                # mdi.MDI_Recv(3*npoles, mdi.MDI_DOUBLE, engine_comm, buf = field)
                # field = field.reshape(npoles,3)
#
                start_dfield = time.time()

                # Get the pairwise DFIELD
                dfield = np.zeros((len(probes),npoles,3))
                mdi.MDI_Send_Command("<DFIELD", engine_comm)
                mdi.MDI_Recv(3*npoles*len(probes), mdi.MDI_DOUBLE, engine_comm, buf=dfield)
                elapsed_dfield = time.time() - start_dfield
                print(F"DField Retrieval:\t {elapsed_dfield}")

#
#                # Get the pairwise UFIELD
                ufield = np.zeros((len(probes),npoles,3))
                mdi.MDI_Send_Command("<UFIELD", engine_comm)
                mdi.MDI_Recv(3*npoles*len(probes), mdi.MDI_DOUBLE, engine_comm, buf=ufield)

                # Sum the appropriate values

                start_sum = time.time()

                columns = ['Probe Atom', 'Probe Coordinates']
                columns += [F'{by_type} {x}' for x in from_fragment]
                dfield_df = pd.DataFrame(columns=columns, index=range(len(probes)))
                ufield_df = pd.DataFrame(columns=columns, index=range(len(probes)))
                totfield_df = pd.DataFrame(columns=columns, index=range(len(probes)))

                # Get sum at each probe from fragment.
                for i in range(len(probes)):
                    dfield_df.loc[i, 'Probe Atom'] = probes[i]
                    dfield_df.loc[i, 'Probe Coordinates'] = snapshot_coords[probes[i]-1]
                    ufield_df.loc[i, 'Probe Atom'] = probes[i]
                    ufield_df.loc[i, 'Probe Coordinates'] = snapshot_coords[probes[i]-1]
                    totfield_df.loc[i, 'Probe Coordinates'] = snapshot_coords[probes[i]-1]

                    for fragment_index, fragment in enumerate(atoms_pole_numbers):
                        fragment_string = F'{by_type} {from_fragment[fragment_index]}'
                        dfield_df.loc[i, fragment_string] = dfield[i, fragment-1].sum(axis=0)
                        ufield_df.loc[i, fragment_string] = ufield[i, fragment-1].sum(axis=0)
                        totfield_df.loc[i, fragment_string] = dfield_df.loc[i, fragment_string] + \
                            ufield_df.loc[i, fragment_string]

                # Pairwise probe calculation - Get avg electric field
                count = 0
                for i in range(len(probes)):
                    for j in range(i+1, len(probes)):
                        avg_field = (totfield_df.iloc[i, 2:] - totfield_df.iloc[j, 2:]) / 2

                        coord1 = totfield_df.loc[i, 'Probe Coordinates']
                        coord2 = totfield_df.loc[j, 'Probe Coordinates']
                        # Unit vector
                        dir_vec = (coord2 - coord1) / np.linalg.norm(coord2 - coord1)

                        efield_at_point = []
                        label = []
                        for column_name, column_value in avg_field.iteritems():
                            output.loc[count,'Atom 1'] = probes[i]
                            output.loc[count, 'Atom 2'] = probes[j]
                            output.loc[count, 'From'] = column_name
                            output.loc[count, F'Frame {snap_num}'] = np.dot(column_value, dir_vec)*conversion_factor
                            count += 1


        elapsed_sum = time.time() - start_sum

        print(F"Elapsed sum: {elapsed_sum}")

    dfield_df.to_csv('dfield.csv', index=False)
    ufield_df.to_csv('ufield.csv', index=False)

    output['Atom 1'] = output['Atom 1'].astype(int)
    output['Atom 2'] = output['Atom 2'].astype(int)


    output.to_csv('ouput.csv', index=False)

    elapsed = time.time() - start
    print(F'Elapsed loop:{elapsed}')#

    # Send the "EXIT" command to the engine
    mdi.MDI_Send_Command("EXIT", engine_comm)

    # Ensure that all ranks have terminated
    if use_mpi4py:
        MPI.COMM_WORLD.Barrier()
