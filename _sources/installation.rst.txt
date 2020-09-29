Installation
============

Compiling MDI-Tinker and ELECTRIC
----------------------------------

Installation of ELECTRIC and MDI-enabled Tinker are bundled in one convenient build script. 

To install ELECTRIC and MDI-enabled Tinker, you should have cmake and a fortran compiler installed. Then, you can download and build ELECTRIC and MDI-enabled Tinker using the following command in your terminal. Make sure you are in the directory where you want your ELECTRIC driver to be. You should note this location, because you will need to specify the path to some files built during this process in order to perform analysis.

.. code-block:: bash

    git clone --recurse-submodules https://github.com/WelbornGroup/ELECTRIC.git
    cd ELECTRIC
    ./build.sh

This will download and build ELECTRIC and MDI-enabled Tinker. 

Upon successful building, you will have the ELECTRIC driver in ELECTRIC/ELECTRIC/ELECTRIC.py, and the needed Tinker executable (dynamic.x) in ELECTRIC/modules/Tinker/build/tinker/source/dynamic.x . The location of these files can be found in text files in ELECTRIC/test/locations/ELECTRIC and ELECTRIC/test/locations/Tinker_ELECTRIC. You will need these for using ELECTRIC.

Python Dependencies
-------------------

In order to run ELECTRIC, you will need to be in a python environment which has numpy and pandas installed. If you want to run ELECTRIC with more than one engine, you should also install MPI4Py. We recommend installing these packages in a conda environment created for ELECTRIC analysis.

.. code-block:: bash   

    conda install -c anaconda mpi4py
    conda install -c conda-forge numpy pandas

Testing Your Installation
--------------------------

You can now run a quick test of the driver by changing directory to the `ELECTRIC/test/bench5` directory and running the `tcp.sh` script:

.. code-block:: bash

    ./tcp.sh

This script will run a short Tinker dynamics simulation that includes periodic boundary conditions. This command is on line 20 of the provided file. This is a standard Tinker call, as you would normally run a simulation. If you are performing post processing on a simulation, you will not use this line.

.. code-block:: bash

    ${TINKER_LOC} bench5 -k bench5.key 10 1.0 0.001999 2 300.00 > Dynamics.log

The script then launches an instance of Tinker as an MDI engine, which will request a connection to the driver and then listen for commands from the driver. This command is similar to running a simulation with Tinker, except that it uses a modified Tinker input file (more on this below), and adds an additional command line argument which passes information to MDI (`-mdi "role ENGINE -name NO_EWALD -method TCP -port 8022 -hostname localhost"`):

.. code-block:: bash

    ${TINKER_LOC} bench5 -k no_ewald.key -mdi "-role ENGINE -name NO_EWALD -method TCP -port 8022 -hostname localhost" 10 1.0 0.001999 2 300.00 > no_ewald.log &

The script will then launch an instance of the driver in the background, which will listen for connections from an MDI engine:

.. code-block:: bash

    python ${DRIVER_LOC} -probes "1 40" -snap bench5.arc -mdi "-role DRIVER -name driver -method TCP -port 8022" --bymol &

The driver's output should match the reference output file (`proj_totfield.csv`) in the `sample_analysis` directory.




