import time
import numpy as np
import pandas as pd

from itertools import combinations

from util import process_pdb, index_fragments, create_parser

# Use local MDI build
import mdi.MDI_Library as mdi

from line_profiler import LineProfiler

lp = LineProfiler()


def connect_to_engines(nengines):
    """
    Accept connection(s) from the MDI engine(s) and perform basic validation of the connection.

    Parameters
    ---------
    nengines : int
        The number of MDI engines to connect to.

    Returns
    -------
    engine_comm : list
        a list of MDI_Comm values
    """
    # Confirm that this code is being used as a driver
    role = mdi.MDI_Get_Role()
    if not role == mdi.MDI_DRIVER:
        raise Exception("Must run driver_py.py as a DRIVER")

    # Connect to the engine
    engine_comm = []
    for iengine in range(nengines):
        print("Attempting to connect to engine " + str(iengine))
        comm = mdi.MDI_Accept_Communicator()
        engine_comm.append(comm)
        print("Connected!")

    # Verify the engine names
    for iengine in range(nengines):
        comm = engine_comm[iengine]

        # Determine the name of the engine
        mdi.MDI_Send_Command("<NAME", comm)
        name = mdi.MDI_Recv(mdi.MDI_NAME_LENGTH, mdi.MDI_CHAR, comm)
        print(f"Engine name: {name}")

        if name[:8] != "NO_EWALD":
            raise Exception("Unrecognized engine name", name)

    return engine_comm


@lp
def collect_task(
    comm, npoles, snapshot_coords, snap_num, atoms_pole_numbers, output, components
):
    """
    Receive all data associated with an engine's task.

    Parameters
    ---------
    comm : MDI_Comm
        The MDI communicator of the engine performing this task.

    npoles : int
        Number of poles involved in this calculation

    snapshot_coords : np.ndarray
        Nuclear coordinates at the snapshot associated with this task.

    snap_num : int
        The snapshot associated with this task.

    atoms_pole_numbers : list
        A multidimensional list where each element gives the pole indices in that fragment.

    output : pd.DataFrame
        The aggregated data from all tasks.

    Returns
    -------
    output : pd.DataFrame
        The aggregated data from all tasks, including the data collected by this function.
    """

    mdi.MDI_Recv(3 * npoles * len(probes), mdi.MDI_DOUBLE, comm, buf=dfield)

    # Get the pairwise UFIELD
    ufield = np.zeros((len(probes), npoles, 3))
    mdi.MDI_Send_Command("<UFIELD", comm)
    mdi.MDI_Recv(3 * npoles * len(probes), mdi.MDI_DOUBLE, comm, buf=ufield)

    # Sum the appropriate values
    fragment_labels = [
        f"{by_type} {x} {n} dimension" for x in from_fragment for n in ["x", "y", "z"]
    ]

    fields = [ufield, dfield]

    totfield = np.zeros((len(probes), len(atoms_pole_numbers), 3))

    # Loop over the fields and add the data to the dataframes
    for field in fields:
        field_at_fragment = np.array(
            [
                field[x, atoms_pole_numbers[i] - 1].sum(axis=0)
                for x in range(len(probes))
                for i in range(len(atoms_pole_numbers))
            ]
        )
        # reshape to keep as array for more calculations
        # for array calculations, we want x, y, z components for a fragment to
        # be together - add to totfield array.
        totfield += field_at_fragment.reshape(len(probes), len(from_fragment), 3)

    frame_data = pd.DataFrame(
        totfield.reshape(len(probes), -1),
        index=range(len(probes)),
        columns=fragment_labels,
    )

    frame_data = frame_data.T

    # Rename the columns to be the probe atom number and the snapshot number.
    frame_data.columns = [f"{probe} - frame {snap_num}" for probe in probes]

    # multiply by the conversion factor
    frame_data = frame_data * conversion_factor

    # Add the data to the output dataframe
    components = pd.concat([components, frame_data], axis=1)

    # Pairwise probe calculation - Get avg electric field
    # if user has specified that they want a projection.
    probe_coordinates = [snapshot_coords[probes[i] - 1] for i in range(len(probes))]

    if projection:
        # Get all combinations of probes
        labels = [
            f"{probes[i]} and {probes[j]} - frame {snap_num}"
            for i, j in combinations(range(len(probes)), 2)
        ]
        fragment_labels = [f"{by_type} {x}" for x in from_fragment]
        combos = [(i, j) for i, j in combinations(range(len(probes)), 2)]
        efield = np.zeros((len(combos), len(from_fragment)))

        for i, combo in enumerate(combos):
            avg_field = (totfield[combo[0]] + totfield[combo[1]]) / 2
            coord1 = probe_coordinates[combo[0]]
            coord2 = probe_coordinates[combo[1]]
            # Unit vector
            dir_vec = (coord2 - coord1) / np.linalg.norm(coord2 - coord1)
            efield_projection = np.dot(avg_field, dir_vec) * conversion_factor
            efield[i] = efield_projection

        # Add the data to the output dataframe
        output = pd.concat(
            [output, pd.DataFrame(efield.T, columns=labels, index=fragment_labels)],
            axis=1,
        )

    return output, components


if __name__ == "__main__":
    conversion_factor = 1440  # Conversion factor for Tinker units to Mv/cm.

    ###########################################################################
    #
    #   Handle user arguments
    #
    ###########################################################################

    start = time.time()
    print("ELECTRIC Calculation started.")

    parser = create_parser()
    args = parser.parse_args()
    nengines = args.nengines
    equil = args.equil
    stride = args.stride
    projection = not args.components_only

    # Process args for MDI
    mdi.MDI_Init(args.mdi)

    snapshot_filename = args.snap
    probes = [int(x) for x in args.probes.split()]

    # Compatibility check for arguments.
    if args.byres and args.bymol:
        parser.error(
            "--byres and --bymol cannot be used together. Please only use one."
        )

    if args.byres:
        residues = process_pdb(args.byres)[0]

    if not args.components_only and len(probes) < 2:
        parser.error(
            """At least two probes must be specified if calculating electric field projection. 
                     Use --components-only to calculate electric field components at specified probe."""
        )

    print("Connecting to engines...")
    engine_comm = connect_to_engines(nengines)
    # Print the probe atoms
    print(f"Probes: {probes}")

    elapsed = time.time() - start
    print(f"Setup:\t {elapsed}")

    ###########################################################################
    #
    #   Get Information from Tinker
    #
    ###########################################################################

    # Get the number of atoms
    mdi.MDI_Send_Command("<NATOMS", engine_comm[0])
    natoms_engine = mdi.MDI_Recv(1, mdi.MDI_INT, engine_comm[0])
    print(f"natoms: {natoms_engine}")

    # Get the number of multipole centers
    mdi.MDI_Send_Command("<NPOLES", engine_comm[0])
    npoles = mdi.MDI_Recv(1, mdi.MDI_INT, engine_comm[0])
    print("npoles: " + str(npoles))

    # Get the indices of the multipole centers per atom
    mdi.MDI_Send_Command("<IPOLES", engine_comm[0])
    ipoles = mdi.MDI_Recv(natoms_engine, mdi.MDI_INT, engine_comm[0])

    # Get the molecule information
    mdi.MDI_Send_Command("<MOLECULES", engine_comm[0])
    molecules = np.array(mdi.MDI_Recv(natoms_engine, mdi.MDI_INT, engine_comm[0]))

    # Get the residue information
    # Residue information comes from pdb.
    print(f"Initial Info to Tinker:\t {elapsed}")

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

    probe_pole_indices = [int(ipoles[atom_number - 1]) for atom_number in probes]

    # Get the atom and pole numbers for the molecules/residues of interest.
    atoms_pole_numbers = []
    if args.bymol:
        by_type = "molecule"
        fragment_list = molecules
    elif args.byres:
        by_type = "residue"
        fragment_list = residues
    else:
        by_type = "atom"
        # We are interested in all of the atoms.
        fragment_list = list(range(1, natoms_engine + 1))

    atoms_pole_numbers, from_fragment = index_fragments(fragment_list, ipoles)

    elapsed = time.time() - start
    print(f"Bookkeeping:\t {elapsed}")

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

    angstrom_to_bohr = mdi.MDI_Conversion_Factor("angstrom", "atomic_unit_of_length")
    elapsed - time.time() - start
    print(f"Sending info to Tinker:\t {elapsed}")

    ###########################################################################
    #
    #   Engine and Trajectory File Compatibility Check.
    #
    ###########################################################################

    # Check that engine and trajectory are compatible.
    # Process first two lines of snapshot to get information.
    with open(snapshot_filename, "r") as snapshot_file:
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
        raise Exception(
            f"Snapshot file and engine have inconsistent number of atoms \
                            Engine : {natoms_engine} \n Snapshot File : {natoms}"
        )

    ###########################################################################
    #
    #   Read Trajectory and do analysis.
    #
    ###########################################################################

    start = time.time()
    output = pd.DataFrame()
    components = pd.DataFrame()

    itask = 0
    itask_to_snap_num = {}
    snapshot_coords = [None for iengine in range(nengines)]

    # Read trajectory and do analysis
    for snap_num, snapshot in enumerate(
        pd.read_csv(
            snapshot_filename,
            chunksize=natoms + skip_line,
            header=None,
            delim_whitespace=True,
            names=range(15),
            skiprows=skip_line,
            index_col=None,
        ),
        1,
    ):
        if snap_num > equil:
            if (snap_num - equil) % stride == 0:
                icomm = itask % nengines
                itask_to_snap_num[itask] = snap_num
                itask += 1

                start_dfield = time.time()

                # Pull out just coords, convert to numeric and use conversion factor.
                # columns 2-4 of the pandas dataframe are the coordinates.
                # Must create a copy to send to MDI.
                snapshot_coords[icomm] = (
                    (
                        snapshot.iloc[:natoms, 2:5].apply(pd.to_numeric)
                        * angstrom_to_bohr
                    )
                    .to_numpy()
                    .copy()
                )

                mdi.MDI_Send_Command(">COORDS", engine_comm[icomm])
                mdi.MDI_Send(
                    snapshot_coords[icomm],
                    3 * natoms,
                    mdi.MDI_DOUBLE,
                    engine_comm[icomm],
                )

                # Get the pairwise DFIELD
                # Note: We only send the command here; we do NOT wait for Tinker to finish the calculation
                # This allows us to farm out tasks to each of the engines simultaneously
                dfield = np.zeros((len(probes), npoles, 3))
                mdi.MDI_Send_Command("<DFIELD", engine_comm[icomm])

                # After every engine has received a task, collect the data
                if (icomm % nengines) == (nengines - 1):
                    for jcomm in range(nengines):
                        output, components = collect_task(
                            engine_comm[jcomm],
                            npoles,
                            snapshot_coords[jcomm],
                            itask_to_snap_num[itask - nengines + jcomm],
                            atoms_pole_numbers,
                            output,
                            components,
                        )

                    elapsed_dfield = time.time() - start_dfield
                    print(f"DField Retrieval:\t {elapsed_dfield}")

    # Collect any tasks that have not yet been collected
    for icomm in range(itask % nengines):
        output, components = collect_task(
            engine_comm[icomm],
            npoles,
            snapshot_coords[icomm],
            itask_to_snap_num[itask - (itask % nengines) + icomm],
            atoms_pole_numbers,
            output,
            components,
        )

    if projection:
        output.to_csv("proj_totfield.csv")

    components.index.name = "Fragment and Dimension"
    components.to_csv("ef_components.csv")

    elapsed = time.time() - start
    print(f"Elapsed loop:{elapsed}")  #

    with open("profile_output.txt", "w") as f:
        lp.print_stats(stream=f)

    # Send the "EXIT" command to the engine
    for comm in engine_comm:
        mdi.MDI_Send_Command("EXIT", comm)
