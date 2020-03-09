# MDI_EF_Analysis

## Overview

This repository contains a driver that uses the [MolSSI Driver Interface](https://github.com/MolSSI/MDI_Library) to perform electric field analysis of [Tinker](https://dasher.wustl.edu/tinker/) trajectories.

## Requirements:

This repository uses the NumPy [NumPy](https://numpy.org/) and [pandas](https://pandas.pydata.org/) Python packages.
We recommend installing these packages via Conda:

    conda install -c conda-forge numpy pandas

The repository includes a copy of the [MDI Library](https://github.com/MolSSI/MDI_Library), which is built using CMake, as described below.

## Installation

First clone the repository:

    git clone https://github.com/taylor-a-barnes/MDI_EF_Analysis.git

Then build it using CMake:

    cd MDI_EF_Analysis
    cmake .
    make

Running calculations with this driver will require an [MDI-enabled fork](https://github.com/taylor-a-barnes/Tinker) of Tinker.
This can be acquired using:

    git clone --branch mdi-ef https://github.com/taylor-a-barnes/Tinker.git

The above clone should be compiled before running calculations with the driver.
Only the `dynamic.x` Tinker executable is required by this driver.

## Testing

To test that the build is working, edit the file `MDI_EF_Analysis/test/locations/MDI_EF_Analysis` to provide the **full path** to the `MDI_EF_Analysis.py` Python script.
If you followed the installation instructions above, this file will be in `[...]/MDI_EF_Analysis/MDI_EF_Analysis/MDI_EF_Analysis.py`

Similarly, edit the file `MDI_EF_Analysis/test/locations/Tinker` to provide the **full path** to the `dynamic.x` executable you compiled from the Tinker distribution.

You can now run a quick test of the driver by changing directory to the `MDI_EF_Analysis/test/bench5` directory and running the `tcp.sh` script.
This script will run a short Tinker dynamics simulation that includes periodic boundary conditions:

    ${TINKER_LOC} bench5 -k bench5.key 10 1.0 0.001999 2 300.00 > Dynamics.log

It then launches an instance of Tinker as an MDI engine, which will request a connection to the driver and then listen for commands from the driver.

    ${TINKER_LOC} bench5 -k no_ewald.key -mdi "-role ENGINE -name NO_EWALD -method TCP -port 8022 -hostname localhost" 10 1.0 0.001999 2 300.00 > no_ewald.log &

It will then launch an instance of the driver in the background, which will listen for connections from an MDI engine:

    python ${DRIVER_LOC} -probes "1 40" -snap bench5.arc -mdi "-role DRIVER -name driver -method TCP -port 8022" --bymol &

The driver's output should match the reference output in the `ref` file.

## Usage

In general, running a calculation with the driver requires the following steps:

1. Run a dynamics simulation with Tinker.
This simulation should be run with periodic boundary conditions (if desired), and should print snapshots of its results to a single file (i.e., `coordinates.arc`).
If each snapshot was instead written to a different file (i.e., `coordinates.001`, `coordinates.002`, etc.) then you may concatenate them into a single file.

2. Create a new Tinker keyfile.
This keyfile should be identical to the one used in Step 1, except that it **must not** include periodic boundary conditions and **must not** use an Ewald summation.

3. Launch one (or more; see the `-nengines` option below) instance(s) of Tinker as an MDI engine, using the keyfile created in Step 2.
This is done simply by launching the `dynamic.x` executable with the `-mdi` command-line option.
The argument to this command-line option details how Tinker should connect to the driver; its possible arguments are described in the [MDI documentation](https://molssi.github.io/MDI_Library/html/library_page.html#library_launching_sec).
When in doubt, we recommend doing `-mdi "-role ENGINE -name NO_EWALD -method TCP -port 8021 -hostname localhost"`
When run as an engine, Tinker should be launched in the background; this is done by adding an ampersand (`&`) at the end of the launch line.

4. Launch the driver.
The driver accepts a variety of command-line options, which are described in detail below.
One possible launch command would be:

    `python ${DRIVER_LOC} -probes "1 2 10" -snap coordinates.arc -mdi "-role DRIVER -name driver -method TCP -port 8021" --byres ke15.pdb --equil 51 -nengines 15 &`

   where `DRIVER_LOC` is the path to MDI_EF_Analysis.py.
   The output will be written to `proj_totfield.py`.

It is useful to write a script that performs Steps 3 and 4, especially if the calculations are intended to be run on a shared cluster.
Such a script might look like:

    # location of required codes
    DRIVER_LOC=$(cat ../locations/MDI_EF_Analysis)
    TINKER_LOC=$(cat ../locations/Tinker)
    
    # number of instances of Tinker to run as an engine
    nengines=18

    # set the number of threads used by each code
    export OMP_NUM_THREADS=1
    
    # launch Tinker as an engine
    for i in $( eval echo {1..$nengines} )
    do
    ${TINKER_LOC} coordinates.in -k no_ewald.key -mdi "-role ENGINE -name NO_EWALD -method TCP -port 8021 -hostname localhost" 10 1.0 1.0 2 300 > no_ewald${i}.log &
    done
    
    # launch the driver
    python ${DRIVER_LOC} -probes "32 33 59 60" -snap coordinates.arc -mdi "-role DRIVER -name driver -method TCP -port 8021" --byres ke15.pdb --equil 51 -nengines ${nengines} &
    
    wait

## Command-Line Options

This driver accepts the following command-line options:

  * `-mdi` <br/>
    **required:** always <br/>
    **argument:** (string) containing MDI options, as described in the [MDI documentation](https://molssi.github.io/MDI_Library/html/library_page.html#library_launching_sec)
  * `-nengines` <br/>
    This option allows the driver to farm tasks out to multiple Tinker engines simultaneously, enabling parallelization of the electric field analysis computation.
    The argument to this option **must** be equal to the number of Tinker engines that are launched in Step 3 of the usage instructions above.
    <br/>
    **required:** only when running with multiple engines <br/>
    **argument:** (integer) number of engines to use <br/>
    **default:** 1

