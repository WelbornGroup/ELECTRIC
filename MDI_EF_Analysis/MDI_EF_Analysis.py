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

# get the MPI communicator
if use_mpi4py:
    mpi_world = MPI.COMM_WORLD
else:
    mpi_world = None

# Initialize the MDI Library
mdi.MDI_Init(sys.argv[2],mpi_world)
if use_mpi4py:
    mpi_world = mdi.MDI_Get_Intra_Code_MPI_Comm()
    world_rank = mpi_world.Get_rank()
else:
    world_rank = 0

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

# Get the number of atoms
mdi.MDI_Send_Command("<NATOMS", engine_comm)
natoms = mdi.MDI_Recv(1, mdi.MDI_INT, engine_comm)
print("natoms: " + str(natoms))

# Get the number of multipole centers
mdi.MDI_Send_Command("<NPOLES", engine_comm)
npoles = mdi.MDI_Recv(1, mdi.MDI_INT, engine_comm)
print("npoles: " + str(npoles))

# Set the probe atoms
probes = [1, 2]

# Inform Tinker of the probe atoms
mdi.MDI_Send_Command(">NPROBES", engine_comm)
mdi.MDI_Send(len(probes), 1, mdi.MDI_INT, engine_comm)
mdi.MDI_Send_Command(">PROBES", engine_comm)
mdi.MDI_Send(probes, len(probes), mdi.MDI_INT, engine_comm)

# Get the electric field information
mdi.MDI_Send_Command("<FIELD", engine_comm)
field = np.zeros(3 * npoles, dtype='float64')
mdi.MDI_Recv(3*npoles, mdi.MDI_DOUBLE, engine_comm, buf = field)
field = field.reshape(npoles,3)

# Print the electric field information
print("Field: ")
for ipole in range(npoles):
    print("   " + str(field[ipole]))


# Send the "EXIT" command to the engine
mdi.MDI_Send_Command("EXIT", engine_comm)

# Ensure that all ranks have terminated
if use_mpi4py:
    MPI.COMM_WORLD.Barrier()
