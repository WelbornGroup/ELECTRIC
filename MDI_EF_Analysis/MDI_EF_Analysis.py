import sys
import os
import time
import argparse
import numpy as np
import pandas as pd


from util import process_pdb, index_fragments


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

def mdi_checks(mdi_engine, nengines):
    """
    Perform checks on the MDI driver we have accepted to make sure it fits this analysis.
    """
    # Confirm that this code is being used as a driver
    role = mdi_engine.MDI_Get_Role()
    if not role == mdi_engine.MDI_DRIVER:
        raise Exception("Must run driver_py.py as a DRIVER")

    # Connect to the engine
    engine_comm = []
    for iengine in range(nengines):
        comm = mdi.MDI_Accept_Communicator()

        # Determine the name of the engine
        mdi_engine.MDI_Send_Command("<NAME", comm)
        name = mdi_engine.MDI_Recv(mdi.MDI_NAME_LENGTH, mdi.MDI_CHAR, comm)
        print(F"Engine name: {name}")

        if name == "NO_EWALD":
            #if engine_comm != mdi_engine.MDI_NULL_COMM:
            #    raise Exception("Accepted a communicator from a second NO_EWALD engine.")
            #engine_comm = comm
            engine_comm.append(comm)
        else:
            raise Exception("Unrecognized engine name", name)

    return engine_comm

def receive_from_engine(comm, snapshot_coords, snap_num, output):
    mdi.MDI_Recv(3*npoles*len(probes), mdi.MDI_DOUBLE, comm, buf=dfield)

    # Get the pairwise UFIELD
    ufield = np.zeros((len(probes),npoles,3))
    mdi.MDI_Send_Command("<UFIELD", comm)
    mdi.MDI_Recv(3*npoles*len(probes), mdi.MDI_DOUBLE, comm, buf=ufield)

    # Sum the appropriate values

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
        totfield_df.loc[i, 'Probe Atom'] = probes[i]
        totfield_df.loc[i, 'Probe Coordinates'] = snapshot_coords[probes[i]-1]

        for fragment_index, fragment in enumerate(atoms_pole_numbers):
            fragment_string = F'{by_type} {from_fragment[fragment_index]}'
            # This uses a numpy array (fragments) for indexing. The fragments
            # array lists pole indices in that fragment. We subtract 1 because
            # python indexes from zero.
            dfield_df.loc[i, fragment_string] = dfield[i, fragment-1].sum(axis=0)
            ufield_df.loc[i, fragment_string] = ufield[i, fragment-1].sum(axis=0)
            totfield_df.loc[i, fragment_string] = dfield_df.loc[i, fragment_string] + \
                                                                      ufield_df.loc[i, fragment_string]

    # Pairwise probe calculation - Get avg electric field
    count = 0
    for i in range(len(probes)):
        for j in range(i+1, len(probes)):
            avg_field = (totfield_df.iloc[i, 2:] + totfield_df.iloc[j, 2:]) / 2

            coord1 = totfield_df.loc[i, 'Probe Coordinates']
            coord2 = totfield_df.loc[j, 'Probe Coordinates']
            # Unit vector
            dir_vec = (coord2 - coord1) / np.linalg.norm(coord2 - coord1)

            #print(avg_field)

            efield_at_point = []
            label = []
            for column_name, column_value in avg_field.iteritems():
                efield_at_point.append(np.dot(column_value, dir_vec)*conversion_factor)
                label.append(column_name)
                count += 1
            series = pd.Series(efield_at_point, index=label)
            output = pd.concat([output, series], axis=1)
            cols = list(output.columns)
            cols[-1] = F'{probes[i]} and {probes[j]} - frame {snap_num}'
            output.columns = cols

    return output


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
    parser.add_argument("-nengines", help="number of frames between analysis", type=int)
    parser.add_argument("--byres", help="give electric field at probe by residue")
    parser.add_argument("--bymol", help="give electric field at probe by molecule",
        action="store_true")
    parser.add_argument("--equil", help="number of equilibration frames to skip", type=int)
    parser.add_argument("--stride", help="number of frames between analysis", type=int)

    args = parser.parse_args()

    # Process args for MDI
    mdi.MDI_Init(args.mdi, mpi_world)

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

    if args.byres:
        residues = process_pdb(args.byres)

    if not args.nengines:
        nengines = 1
    else:
        nengines = args.nengines

    print("Checking MDI")
    engine_comm = mdi_checks(mdi, nengines)

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
    mdi.MDI_Send_Command("<NATOMS", engine_comm[0])
    natoms_engine = mdi.MDI_Recv(1, mdi.MDI_INT, engine_comm[0])
    print(F"natoms: {natoms_engine}")

    # Get the number of multipole centers
    mdi.MDI_Send_Command("<NPOLES", engine_comm[0])
    npoles = mdi.MDI_Recv(1, mdi.MDI_INT, engine_comm[0])
    print("npoles: " + str(npoles))

    # Get the indices of the mulitpole centers per atom
    mdi.MDI_Send_Command("<IPOLES", engine_comm[0])
    ipoles = mdi.MDI_Recv(natoms_engine, mdi.MDI_INT, engine_comm[0])

    # Get the molecule information
    mdi.MDI_Send_Command("<MOLECULES", engine_comm[0])
    molecules = np.array(mdi.MDI_Recv(natoms_engine, mdi.MDI_INT, engine_comm[0]))

    # Get the residue information
    # Residue information comes from pdb.
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
        fragment_list = molecules
    elif args.byres:
        by_type = 'residue'
        fragment_list = residues
    else:
        by_type = 'atom'
        # We are interested in all of the atoms.
        fragment_list = list(range(1,natoms_engine+1))

    atoms_pole_numbers, from_fragment = index_fragments(fragment_list, ipoles)

    elapsed = time.time() - start
    print(F'Bookkeeping:\t {elapsed}')

    ###########################################################################
    #
    #   Send Probe Information to Tinker
    #
    ###########################################################################
    start = time.time()
    # Inform Tinker of the probe atoms
    for comm in engine_comm:
        mdi.MDI_Send_Command(">NPROBES", comm)
        mdi.MDI_Send(len(probes), 1, mdi.MDI_INT, comm)
        mdi.MDI_Send_Command(">PROBES", comm)
        mdi.MDI_Send(probe_pole_indices, len(probes), mdi.MDI_INT, comm)

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
    output = pd.DataFrame()

    itask = 0
    itask_to_snap_num = {}
    snapshot_coords = [ None for iengine in range(nengines) ]

    # Read trajectory and do analysis
    for snap_num, snapshot in enumerate(pd.read_csv(snapshot_filename, chunksize=natoms+skip_line,
        header=None, delim_whitespace=True, names=range(15),
        skiprows=skip_line, index_col=None)):

        if snap_num > equil - 1:
            if snap_num % stride == 0:

                icomm = itask % nengines
                itask_to_snap_num[itask] = snap_num
                itask += 1

                start_dfield = time.time()

                # Pull out just coords, convert to numeric and use conversion factor.
                # columns 2-4 of the pandas dataframe are the coordinates.
                # Must create a copy to send to MDI.
                snapshot_coords[icomm] = (snapshot.iloc[:natoms , 2:5].apply(pd.to_numeric) *
                    angstrom_to_bohr).to_numpy().copy()

                mdi.MDI_Send_Command(">COORDS", engine_comm[icomm])
                mdi.MDI_Send(snapshot_coords[icomm], 3*natoms, mdi.MDI_DOUBLE, engine_comm[icomm])

                # Get the electric field information
                # mdi.MDI_Send_Command("<FIELD", engine_comm)
                # field = np.zeros(3 * npoles, dtype='float64')
                # mdi.MDI_Recv(3*npoles, mdi.MDI_DOUBLE, engine_comm, buf = field)
                # field = field.reshape(npoles,3)

                # Get the pairwise DFIELD
                # Note: We only send the command here; we do NOT wait for Tinker to finish the calculation
                # This allows us to farm out tasks to each of the engines simultaneously
                dfield = np.zeros((len(probes),npoles,3))
                mdi.MDI_Send_Command("<DFIELD", engine_comm[icomm])

                # After every engine has received a task, collect the data
                if (icomm % nengines) == (nengines - 1):
                    for jcomm in range(nengines):
                        output = receive_from_engine(engine_comm[jcomm], snapshot_coords[jcomm], 
                                                     itask_to_snap_num[itask - nengines + jcomm], 
                                                     output)

                    elapsed_dfield = time.time() - start_dfield
                    print(F"DField Retrieval:\t {elapsed_dfield}")

    # Collect any tasks that have not yet been collected
    for icomm in range ( itask % nengines ):
        output = receive_from_engine(engine_comm[icomm], snapshot_coords[icomm], 
                                     itask_to_snap_num[itask - nengines + jcomm], 
                                     output)

    output.to_csv('proj_totfield.csv')

    elapsed = time.time() - start
    print(F'Elapsed loop:{elapsed}')#

    # Send the "EXIT" command to the engine
    for comm in engine_comm:
        mdi.MDI_Send_Command("EXIT", comm)

    # Ensure that all ranks have terminated
    if use_mpi4py:
        MPI.COMM_WORLD.Barrier()
