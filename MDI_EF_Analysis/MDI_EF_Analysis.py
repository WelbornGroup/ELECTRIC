import sys
import time
import numpy as np

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

# Read through the command-line arguments
has_mdi_arg = False
has_snapshot_arg = False
has_probes_arg = False
snapshot_filename = None
iarg = 1
while iarg < len(sys.argv):
    arg = sys.argv[iarg]
    if arg == "-mdi":
        # Initialize MDI
        if len(sys.argv) <= iarg+1:
            raise Exception("Argument to -mdi option not found")
        mdi.MDI_Init(sys.argv[iarg+1],mpi_world)
        if use_mpi4py:
            mpi_world = mdi.MDI_Get_Intra_Code_MPI_Comm()
            world_rank = mpi_world.Get_rank()
        else:
            world_rank = 0
        has_mdi_arg = True
        iarg += 1
    elif arg == "-snap":
        # Get the location of the file that contains the snapshot
        if len(sys.argv) <= iarg+1:
            raise Exception("Argument to -snap option not found")
        snapshot_filename = sys.argv[iarg+1]
        has_snapshot_arg = True
        iarg += 1
    elif arg == "-probes":
        # Get the probes
        if len(sys.argv) <= iarg+1:
            raise Exception("Argument to -probes option not found")
        probes = sys.argv[iarg+1].strip('[]').split(',')
        probes = [ int(probes[i]) for i in range(len(probes)) ]
        has_probes_arg = True
        iarg += 1
    else:
        raise Exception("Unrecognized option")

    iarg += 1

# Confirm that the required command-line options were provided
if not has_mdi_arg:
    raise Exception("Did not receive the -mdi command-line option")
if not has_snapshot_arg:
    raise Exception("Did not receive the -snap command-line option")
if not has_probes_arg:
    raise Exception("Did not receive the -probes command-line option")

# Print the probe atoms
print("Probes: " + str(probes))

# Confirm that this code is being used as a driver
role = mdi.MDI_Get_Role()
if not role == mdi.MDI_DRIVER:
    raise Exception("Must run driver_py.py as a DRIVER")

# Connect to the engine
engine_comm = mdi.MDI_NULL_COMM
nengines = 1
for iengine in range(nengines):
    comm = mdi.MDI_Accept_Communicator()

    # Determine the name of the engine
    mdi.MDI_Send_Command("<NAME", comm)
    name = mdi.MDI_Recv(mdi.MDI_NAME_LENGTH, mdi.MDI_CHAR, comm)

    print(" Engine name: " + str(name))

    if name == "NO_EWALD":
        if engine_comm != mdi.MDI_NULL_COMM:
            raise Exception("Accepted a communicator from a second NO_EWALD engine.")
        engine_comm = comm
    else:
        raise Exception("Unrecognized engine name.")

# Read the file with the MD snapshots
snapshot_file = open(snapshot_filename, "r")
snapshot_linenum = 0
snapshots = []
angstrom_to_bohr = mdi.MDI_Conversion_Factor("angstrom","atomic_unit_of_length")
for unsplit_line in snapshot_file:
    line = unsplit_line.split()
    if snapshot_linenum == 0:
        # Read the number of atoms in the snapshot
        natoms = int(line[0])

        # Create a new NumPy array to contain the coordinate information
        snapshot = np.zeros((natoms,3))
        snapshots.append(snapshot)
    elif snapshot_linenum == 1:
        # This line has the cell dimensions
        pass
    else:
        # This line contains xyz coordinates
        iatom = snapshot_linenum - 2
        snapshot[iatom][0] = float(line[2]) * angstrom_to_bohr
        snapshot[iatom][1] = float(line[3]) * angstrom_to_bohr
        snapshot[iatom][2] = float(line[4]) * angstrom_to_bohr

    snapshot_linenum += 1
    if snapshot_linenum == natoms + 2:
        # This is a new snapshot
        snapshot_linenum = 0
        
# Get the number of atoms
mdi.MDI_Send_Command("<NATOMS", engine_comm)
natoms_engine = mdi.MDI_Recv(1, mdi.MDI_INT, engine_comm)
print("natoms: " + str(natoms_engine))
if natoms != natoms_engine:
    raise Exception("Snapshot file and engine have inconsistent number of atoms")

# Get the number of multipole centers
mdi.MDI_Send_Command("<NPOLES", engine_comm)
npoles = mdi.MDI_Recv(1, mdi.MDI_INT, engine_comm)
print("npoles: " + str(npoles))

# Inform Tinker of the probe atoms
mdi.MDI_Send_Command(">NPROBES", engine_comm)
mdi.MDI_Send(len(probes), 1, mdi.MDI_INT, engine_comm)
mdi.MDI_Send_Command(">PROBES", engine_comm)
mdi.MDI_Send(probes, len(probes), mdi.MDI_INT, engine_comm)

# Loop over all MD snapshots
for snapshot in snapshots:

    # Send the coordinates of this snapshot
    mdi.MDI_Send_Command(">COORDS", engine_comm)
    mdi.MDI_Send(snapshot, 3*natoms, mdi.MDI_DOUBLE, engine_comm)

    # Get the electric field information
    #mdi.MDI_Send_Command("<FIELD", engine_comm)
    #field = np.zeros(3 * npoles, dtype='float64')
    #mdi.MDI_Recv(3*npoles, mdi.MDI_DOUBLE, engine_comm, buf = field)
    #field = field.reshape(npoles,3)

    # Get the pairwise DFIELD
    dfield = np.zeros((len(probes),npoles,3))
    mdi.MDI_Send_Command("<DFIELD", engine_comm)
    mdi.MDI_Recv(3*npoles*len(probes), mdi.MDI_DOUBLE, engine_comm, buf = dfield)

    # Get the pairwise UFIELD
    ufield = np.zeros((len(probes),npoles,3))
    mdi.MDI_Send_Command("<UFIELD", engine_comm)
    mdi.MDI_Recv(3*npoles*len(probes), mdi.MDI_DOUBLE, engine_comm, buf = ufield)

    # Print the electric field information
    #print("Field: ")
    #for ipole in range(min(npoles,10)):
    #    print("   " + str(field[ipole]))

    # Print dfield for the first probe atom
    print("DFIELD; UFIELD: ")
    for ipole in range(min(npoles, 10)):
        print("   " + str(dfield[0][ipole]) + "; " + str(ufield[0][ipole]) )


# Send the "EXIT" command to the engine
mdi.MDI_Send_Command("EXIT", engine_comm)

# Ensure that all ranks have terminated
if use_mpi4py:
    MPI.COMM_WORLD.Barrier()
