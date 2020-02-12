import sys
import time
import argparse
import numpy as np
import pandas as pd

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

        print(" Engine name: {name}")

        if name == "NO_EWALD":
            if engine_comm != mdi_engine.MDI_NULL_COMM:
                raise Exception("Accepted a communicator from a second NO_EWALD engine.")
            engine_comm = comm
        else:
            raise Exception("Unrecognized engine name.")

    return engine_comm


if __name__ == "__main__":

    # Handle arguments with argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("-mdi", help="flags for mdi", type=str, required=True)
    parser.add_argument("-snap", help="the snapshot file to process", type=str, required=True)
    parser.add_argument("-probes", help="indices of the probe atoms", type=str, required=True)

    args = parser.parse_args()

    # Process args
    mdi.MDI_Init(args.mdi, mpi_world)
    if use_mpi4py:
        mpi_world = mdi.MDI_Get_Intra_Code_MPI_Comm()
        world_rank = mpi_world.Get_rank()

    snapshot_filename = args.snap
    probes = [int(x) for x in args.probes.split()]

    # For now add this until I get in command line specification
    from_molecule = [10, 100]

    engine_comm = mdi_checks(mdi)

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
    ipoles = mdi.MDI_Recv(natoms_engine, mdi.MDI_DOUBLE, engine_comm)

    # Inform Tinker of the probe atoms
    mdi.MDI_Send_Command(">NPROBES", engine_comm)
    mdi.MDI_Send(len(probes), 1, mdi.MDI_INT, engine_comm)
    mdi.MDI_Send_Command(">PROBES", engine_comm)
    mdi.MDI_Send(probes, len(probes), mdi.MDI_INT, engine_comm)

    # Get the residue information
    mdi.MDI_Send_Command("<MOLECULES", engine_comm)
    molecules = mdi.MDI_Recv(natoms_engine, mdi.MDI_DOUBLE, engine_comm)

    angstrom_to_bohr = mdi.MDI_Conversion_Factor("angstrom","atomic_unit_of_length")

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

    # Read trajectory and do analysis
    for snapshot in pd.read_csv(snapshot_filename, chunksize=natoms+skip_line,
        header=None, delim_whitespace=True, names=range(8), skiprows=skip_line, index_col=None):

        # Pull out just coords, convert to numeric and use conversion factor.
        # Using .values returns numpy array of values.
        snapshot_coords = (snapshot.iloc[:natoms , 2:5].apply(pd.to_numeric) * angstrom_to_bohr).values

        print(snapshot_coords.shape)

        # Send the coordinates of this snapshot
        mdi.MDI_Send_Command(">COORDS", engine_comm)
        mdi.MDI_Send(snapshot_coords, 3*natoms, mdi.MDI_DOUBLE, engine_comm)

        # Get the electric field information
        #mdi.MDI_Send_Command("<FIELD", engine_comm)
        #field = np.zeros(3 * npoles, dtype='float64')
        #mdi.MDI_Recv(3*npoles, mdi.MDI_DOUBLE, engine_comm, buf = field)
        #field = field.reshape(npoles,3)

        ## Get the pairwise DFIELD
        dfield = np.zeros((len(probes),npoles,3))
        mdi.MDI_Send_Command("<DFIELD", engine_comm)
        #mdi.MDI_Recv(3*npoles*len(probes), mdi.MDI_DOUBLE, engine_comm, buf = dfield)

        ## Get the pairwise UFIELD
        #ufield = np.zeros((len(probes),npoles,3))
        #mdi.MDI_Send_Command("<UFIELD", engine_comm)
        #mdi.MDI_Recv(3*npoles*len(probes), mdi.MDI_DOUBLE, engine_comm, buf = ufield)

        ## Print dfield for the first probe atom
        #print("DFIELD; UFIELD: ")
        #for ipole in range(min(npoles, 10)):
        #    print("   " + str(dfield[0][ipole]) + "; " + str(ufield[0][ipole]) )


    # Send the "EXIT" command to the engine
    mdi.MDI_Send_Command("EXIT", engine_comm)

    # Ensure that all ranks have terminated
    if use_mpi4py:
        MPI.COMM_WORLD.Barrier()
