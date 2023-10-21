Tutorial
========

This tutorial will walk you through using ELECTRIC to analyze the electric field in a small protein. 
This tutorial assumes you have ELECTRIC and MDI-enabled Tinker installed. 
If you don't, navigate to the installation_ instructions.

.. note::
    This tutorial will assume the following:
        - You are able to run a molecular dynamics simulation using the Tinker software, or are familiar enough with molecular dynamics to follow along.
        - You have installed ELECTRIC and MDI-enabled Tinker. If you have not, see the installation_ instructions.
        - You are able to download or clone a directory from git.
        - You are familiar with bash scripts.

To begin the tutorial, first make sure you have your `electric` environment activated:

.. code-block:: bash

    conda activate electric


The pdb code for this protein is 1l2y_, and you can see the structure below. 
We have chosen a small protein for demonstrative purposes. 
The image below shows only the protein, but our simulation is solvated.

.. moleculeView:: 
    
    data-pdb: 1l2y
    data-backgroundcolor: white
    width: 300px
    height: 300px
    data-style: cartoon:color=spectrum

Running an ELECTRIC calculation
###############################

Preparing Files
----------------
To follow along with this tutorial, clone the `tutorial repository`_. 
Included in this repository is folder called :code:`data`. The :code:`data` directory has all of the data you will need for this tutorial.

ELECTRIC is a post-processing analysis, meaning that you should first run your simulations using the AMOEBA forcefield and save the trajectory. 
After you have a trajectory from Tinker simulation, use ELECTRIC to perform electric field analysis on that trajectory. 
We will be analyzing the trajectory included in the tutorial repository, :code:`1l2y_npt.arc`. 
This trajectory is a text file containing coordinates for a simulation that has already been run.

To get started with ELECTRIC, we will need to prepare our input files. We will need:
    - a molecular dynamics trajectory
    - a Tinker input file (usually called a key file) which does not have settings for periodic boundaries or Ewald summation
    - the forcefield parameter file
    - a bash script file 

We already have the molecular dynamics trajectory, so let's look at each of these additional files.

Simulation Parameter File
^^^^^^^^^^^^^^^^^^^^^^^^^
This file contains the force field parameters for the simulation you have run. If you are using this software for analysis, use the same force field you used to run the molecular dynamics simulation. 
For this tutorial, the parameter file is :code:`amoebabio18.prm`. We will need this for our Tinker input file (next section).

Tinker input file
^^^^^^^^^^^^^^^^^
Next, we must prepare an input file which tells Tinker settings for our calculation. 
This input file should be a modified version of the one which you used to run your initial simulation. 
Consider the input file, :code:`tinker.key` used to obtain this trajectory. 
The parameter file in the previous step is given on :code:`line 1`.

.. code-block:: text
    :linenos:

    parameters amoebabio18.prm 
    openmp-threads 16

    a-axis 50.00 
    b-axis 50.00
    c-axis 50.00

    polar-eps 0.000010
    polar-predict
    polarization mutual


    cutoff 10.0
    ewald
    neighbor-list
    integrator beeman

    thermostat nose-hoover
    barostat nose-hoover

    maxiter 8000
    printout 1000


The input file used for this simulation uses periodic boundaries and an Ewald summation for electrostatics. 
During a Tinker simulation using AMOEBA, electric fields are evaluated in order to calculate the induced dipoles at each step. 
In order to get electric field contributions from specific residues, we must calculate the electric field using the real space interactions only (no periodic boundaries or Ewald). 

Remove settings related to cutoffs (:code:`cutoff` keyword), periodic boundaries (:code:`a-axis`, :code:`b-axis`,:code:`c-axis`) and Ewald summation (:code:`ewald`). 
You can also remove settings having to do with neighbor lists (:code:`neighbor-list`), as they are not needed and can cause an error for this calculation if included.

The modifed input file for ELECTRIC is given below. 
This file is saved in the data directory with the name :code:`noewald.key`.

.. code-block:: text

    parameters amoebabio18.prm
    openmp-threads 16

    polar-eps 0.000010
    polar-predict
    polarization mutual

    integrator beeman

    thermostat nose-hoover
    barostat nose-hoover

    maxiter 8000
    printout 100


Bash script - run_analysis.sh
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
When you run analysis uisng ELECTRIC, ELECTRIC parses your given trajectory sends snapshots to Tinker for electric field calculation. 
The MDI-enabled version of Tinker then calculates the electric field information for that snapshot. 

You use ELECTRIC from the command line. 
Consider the following bash script provided for analysis, :code:`run_analysis.sh`. 
We will explain this script in detail.

.. code-block:: bash
    :linenos:

    #location of required codes
    DRIVER_LOC=LOCATION/TO/ELECTRIC/ELECTRIC.py
    TINKER_LOC=LOCATION/TO/DYNAMIC/dynamic.x

    #remove old files
    if [ -d work ]; then
    rm -r work
    fi

    #create work directory
    cp -r data work
    cd work

    #set the number of threads
    export OMP_NUM_THREADS=2

    #launch MDI enabled Tinker
    ${TINKER_LOC} 1l2y -k no_ewald.key -mdi "-role ENGINE -name NO_EWALD -method TCP -port 8022 -hostname localhost"  10 1.0 0.002 2 300.00 > no_ewald.log &

    #launch driver
    python ${DRIVER_LOC} -snap 1l2y_npt.arc -probes "93 94" -mdi "-role DRIVER -name driver -method TCP -port 8022" --byres 1l2y_solvated.pdb  --equil 120 --stride 2 &

    wait

.. note:: 

    For this tutorial, we use the approach of having all data needed for analysis in a directory called `data`. During analysis, we copy everything from :code:`data` into a folder :code:`work`. This part of the tutorial is stylistic. The authors prefer this method to keep files separated, and original files unaltered.

In lines :code:`2` and :code:`3`, you should change the location to your installed ELECTRIC.py file and MDI-enabled :code:`dynamic.x`. 
Recall from the installation instructions that you can find these in the ELECTRIC directory in the files :code:`ELECTRIC/test/locations/ELECTRIC` and :code:`ELECTRIC/test/locations/Tinker_ELECTRIC`. 

The next section removes the folder called :code:`work` if it exists. 
This bash script is written to put all analysis files into a folder called :code:`work` to keep our original files clean. 

MDI-enabled Tinker is launched on :code:`line 18` with the command

.. code-block:: bash

    ${TINKER_LOC} 1l2y -k no_ewald.key -mdi "-role ENGINE -name NO_EWALD -method TCP -port 8022 -hostname localhost"  10 1.0 0.002 2 300.00 > no_ewald.log &

The first thing on this line, :code:`${TINKER_LOC}` fills in the location for :code:`dynamic.x` which you put in line 2. 
Next, `1l2y` is the file name (without an extension) of the xyz file for this calculation (provided vile :code:`12ly.xyz`). 
You should have this from your original simulation. 
However, make sure that there is no box information on line two of this :code:`xyz` file, as this could cause Tinker to use periodic boundaries. 
Next, we give the input file (key file) we have prepared in the previous step using :code:`-k noewald.key`. 
Then, we give our MDI options. 
The given options should work for most analysis. After the MDI options are some Tinker input options. 
For our analysis, it will not really matter what we put here since we are running calculations on one snapshot at a time. 
However, you must have these present for Tinker to run. Very importantly, note the ampersand (:code:`&`) at the end of this line. This will launch Tinker in the background, where it will be waiting for commands from ELECTRIC.

.. warning::
    
    Make sure that there is no box information on line two of the :code:`xyz` file used to launch MDI-enabled Tinker. This could cause Tinker to use periodic boundaries.

In the next command (:code:`line 21`), we launch ELECTRIC.

.. code-block:: bash   

    python ${DRIVER_LOC} -snap 1l2y_npt.arc -probes "78 93 94"  -mdi "-role DRIVER -name driver -method TCP -port 8022" --byres 1l2y_solvated.pdb  --equil 120 --stride 2 &

Here, we first give the location of our ELECTRIC driver. 
We indicate our trajectory file using the `-snap` argument with the filename to analyze, followed by MDI options.

Probe Atoms 
++++++++++++

To run an ELECTRIC calculation, you must give the indices of your probe atoms. 
The probe atoms are the atoms which are used as 'probes' for the electric field. ELECTRIC reports the projected total electric field at the midpoint between all probe atom pairs. 
This allows you to calculate electric fields along bonds `as reported in literature <https://pubs.acs.org/doi/10.1021/jacs.9b05323>`_.

You should obtain the number of the probe atoms from the :code:`xyz` file you use to launch MDI-enabled Tinker. Note that the index you use here should match the number given in the first column of your xyz file. The projection of the electric field at the midpoint of these two atoms will be reported for each analyzed frame. If you indicate more than two probes, all pairwise fields will be reported (ie, if using "78 93 94", you will get "78 and 93", "78 and 94" and "93 and 94"). You can see the atoms we have chosen as probes highlighted below:

.. moleculeView:: 
    
    data-pdb: 1l2y
    data-backgroundcolor: 0xffffff
    width: 300px
    height: 300px
    data-style: cartoon:color=spectrum
    data-select1: serial:78,93,94
    data-style1: sphere

The argument `--byres` gives information to ELECTRIC about how we would like the electric field reported. When we use the :code:`--byres` argument, it should be followed by a pdb which contains residue information for the system you are studying. When using this argument, electric field contributions from each residue will be reported. Other options are :code:`--byatom` top report electric field contributions from each atom, and :code:`--bymol` to report electric field contributions from each molecule. 

When using :code:`--byres`, solvent should be at the end of the pdb and xyz files. Solvent (ions and water) will be grouped together into a single residue.

.. warning::

    When using the :code:`byres` option, you should verify that the residues in your pdb file match what you expect for your xyz file. You can do this with the utility function :code:`residue_report.py`. ELECTRIC will check that the :code:`xyz` and :code:`pdb` have the same number of atoms. However, all residue information will come from the PDB, so make sure the residue information in your provided PDB is as you expect.

.. note::

    The utility script :code:`residue_report.py` is provided in the same directory as :code:`ELECTRIC.py`. To use it,

    .. code-block:: bash

        python residue_report.py PDB_FILENAME

    This will output a report which gives the residue number, the atom index on which the residue starts and the residue name. When using :code:`--byres`, you should first verify that your pdb file has residues defined as you want and matches your xyz file and trajectory. ELECTRIC only checks that the pdb and xyz file have the same number of atoms, it does not check atom identity or order. For this tutorial, our output is

    .. code-block:: text

        Found 12199 atoms and 21 residues.
        Residue Number       Starting atom        Residue Name        
                1                    1                   ASN         
                2                    17                  LEU         
                3                    36                  TYR         
                4                    57                  ILE         
                5                    76                  GLN         
                6                    93                  TRP         
                7                   117                  LEU         
                8                   136                  LYS         
                9                   158                  ASP         
                10                  170                  GLY         
                11                  177                  GLY         
                12                  184                  PRO         
                13                  198                  SER         
                14                  209                  SER         
                15                  220                  GLY         
                16                  227                  ARG         
                17                  251                  PRO         
                18                  265                  PRO         
                19                  279                  PRO         
                20                  293                  SER         
                21                  305                solvent       


Finally, we give arguments which gives information about the frame we want to analyze. Using `--equil 120` tells ELECTRIC to skip the first 120 frames for analysis, and :code:`--stride 2` tells ELECTRIC to analyze every other frame after 120.

Running the calculation
-----------------------

After you have prepared your files, you can run analysis using the command

.. code-block:: bash

    ./run_analysis.sh > analysis.out &

This will launch ELECTRIC. Again, using the ampersand :code:`&` will run this in the background. Now, you just have to wait for your analysis to finish running.

Analyzing Results from ELECTRIC
###############################

ELECTRIC will output a csv file with the electric field information :code:`proj_totfield.csv` in the :code:`work` folder. Below, we show results (numbers rounded for clarity) for probes 78 and 93 from :code:`proj_totfield.csv`. When these numbers are reported, they are the electric field in Mv/cm projected along the vector pointing from atom 1 to atom 2 due to each residue.

.. datatable::

    csv_file: data/proj_totfield.csv


You are free to analyze this as you like, but we recommend using `pandas`_ to process the csv file. A script to perform averaging of probe pairs across frames is provided in :code:`ELECTRIC/sample_analysis/calculate_average.py`. For example, you can run this script

.. code-block :: bash

    python PATH/TO/calculate_average.py -filename work/proj_totfield.csv

This will output a file with the average projected field for each residue pair. In our case, three files should be output: :code:`78 _and_93.csv`, :code:`78_and_94.csv`, and :code:`93_and_94.csv`. The output for the :code:`78_and_93.csv` is shown in the table below:

.. datatable::

    csv_file: data/78_and_93.csv

.. _1l2y: https://www.rcsb.org/structure/1l2y
.. _installation: installation.html
.. _`tutorial repository`: http://www.github.com/janash/ELECTRIC_tutorial
.. _pandas: https://pandas.pydata.org/
