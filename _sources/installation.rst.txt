Installation
============

Compiling MDI-Tinker and ELECTRIC
---------------------------------

.. note::
    The following instructions assume that you are using the `conda <https://docs.conda.io/en/latest/>`_ package manager and a Linux or Unix based operating system. 
    If you are not using :code:`conda`, you will need to install the dependencies manually.
    If you are using the Windows Operating System, we recommend the Windows Subsystem for Linux (WSL).

To install ELECTRIC and MDI-enabled Tinker, you should have :code:`cmake` and a Fortran compiler installed. 
If you are using the `conda` package manager, you can clone the repository and use the provided `environment.yaml` 
to create an environment with the required dependencies (including Python packages) using the following command.

.. code-block:: bash

    git clone --recurse-submodules https://github.com/WelbornGroup/ELECTRIC.git
    cd ELECTRIC
    conda create -f environment.yaml

After the environment is created and installed you should activate it:

.. code-block:: bash

    conda activate electric

After creating and activating your environment, you will have the necessary compilers and libraries required for compilating, installing, and running ELECTRIC.
Installation of ELECTRIC and MDI-enabled Tinker are bundled in one convenient build script. 
Execute the following command in the top level of your cloned repository to build ELECTRIC and MDI-enabled Tinker:

.. code-block:: bash

    ./build.sh


Upon successful building, you will have the ELECTRIC driver in :code:`ELECTRIC/ELECTRIC/ELECTRIC.py`, 
and the needed Tinker executable (:code:`dynamic.x`) in ELECTRIC/modules/Tinker/build/tinker/source/dynamic.x . 
The location of these files can be found in text files in :code:`ELECTRIC/test/locations/ELECTRIC` and :code:`ELECTRIC/test/locations/Tinker_ELECTRIC`.
You will need these for using ELECTRIC.

Testing Your Installation
--------------------------

To continue with testing your installation, make sure your `electric` `conda` environment is activated:

.. code-block:: bash

    conda activate electric

You can now run a quick test of the driver by changing directory to the :code:`ELECTRIC/test/bench5` directory and running the `tcp.sh` script:

.. code-block:: bash

    cd ELECTRIC/test/bench5
    ./tcp.sh

This script will run a short Tinker dynamics simulation that includes periodic boundary conditions. 
This command is on line 20 of the provided file. This is a standard Tinker call, as you would normally run a simulation. 
If you are performing post processing on a simulation, you will not use this line.

.. code-block:: bash

    ${TINKER_LOC} bench5 -k bench5.key 10 1.0 0.001999 2 300.00 > Dynamics.log

The script then launches an instance of Tinker as an MDI engine, 
which will request a connection to the driver and then listen for commands from the driver. 
This command is similar to running a simulation with Tinker, except that it uses a modified Tinker input file 
(more on this below), and adds an additional command line argument which passes information to MDI 
(`-mdi "role ENGINE -name NO_EWALD -method TCP -port 8022 -hostname localhost"`):

.. code-block:: bash

    ${TINKER_LOC} bench5 -k no_ewald.key -mdi "-role ENGINE -name NO_EWALD -method TCP -port 8022 -hostname localhost" 10 1.0 0.001999 2 300.00 > no_ewald.log &

The script will then launch an instance of the driver in the background, 
which will listen for connections from an MDI engine:

.. code-block:: bash

    python ${DRIVER_LOC} -probes "1 40" -snap bench5.arc -mdi "-role DRIVER -name driver -method TCP -port 8022" --bymol &

The driver's output should match the reference output file (`proj_totfield.csv`) in the `sample_analysis` directory.




