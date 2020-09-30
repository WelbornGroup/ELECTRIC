Usage
=====

Information Flow
----------------

ELECTRIC is a post-processing tool for simulations running with the AMOEBA polarizable force field using the Tinker software package.

.. image:: images/inputs_and_outputs.svg
   :width: 600

Procedure
---------

In general, running a calculation with the driver requires the following steps:

1. **Run a dynamics simulation with Tinker.**  
This simulation should be run with periodic boundary conditions (if desired), and should print snapshots of its results to a single file (i.e., :code:`coordinates.arc`).
If each snapshot was instead written to a different file (i.e., :code:`coordinates.001`, :code:`coordinates.002`, etc.) then you may concatenate them into a single file.

2. **Create a new Tinker keyfile.**   
This keyfile should be identical to the one used in Step 1, except that it **must not** include periodic boundary conditions and **must not** use an Ewald summation. This means that in the :code:`.key` file for running the driver, you should not have an :code:`a-axis` keyword, or keywords related to Ewald.

3. **Launch one (or more; see the `-nengines` option below) instance(s) of Tinker as an MDI engine, using the keyfile created in Step 2.**  
This is done in the same way you launch a normal Tinker simulation (by launching the :code:`dynamic.x` executable) except that the :code:`-mdi` command-line option is added. However, it is **very important** that the reference coordinates you use do not have periodic boundary information. So, if when you originally ran the simulation you started it with a snapshot from a previous simulation run, make sure to create a new snapshot to launch the simulation from which does not include box information on line 2.

The argument to the :code:`-mdi` command-line option details how Tinker should connect to the driver; its possible arguments are described in the `MDI documentation`_ .
When in doubt, we recommend doing :code:`-mdi "-role ENGINE -name NO_EWALD -method TCP -port 8021 -hostname localhost"`
When run as an engine, Tinker should be launched in the background; this is done by adding an ampersand (:code:`&`) at the end of the launch line.

4. **Launch the driver**
The driver accepts a variety of command-line options, which are described in detail below.
One possible launch command would be:

.. code-block:: bash

    `python ${DRIVER_LOC} -probes "1 2 10" -snap coordinates.arc -mdi "-role DRIVER -name driver -method TCP -port 8021" --byres ke15.pdb --equil 51 -nengines 15 &`

where `DRIVER_LOC` is the path to ELECTRIC.py which you set during the configuration step. See the section :ref:`electric settings` for a detailed explanation of command line arguments for ELECTRIC.

The output will be written to `proj_totfield.csv`.

It is useful to write a script that performs Steps 3 and 4, especially if the calculations are intended to be run on a shared cluster.
Such a script might look like:

.. _example:

Example Script
^^^^^^^^^^^^^^

.. code-block:: bash
    :linenos:

    # location of required codes
    DRIVER_LOC=$(cat ../locations/ELECTRIC)
    TINKER_LOC=$(cat ../locations/Tinker_ELECTRIC)

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

You can read more below, or you can try out the tutorial_ to run a calculation yourself.


.. _electric settings:

ELECTRIC Calculation Settings
-----------------------------

You can change the options for your electric calculation through command line arguments. 

.. argparse::
   :filename: ../ELECTRIC/util.py
   :func: create_parser
   :prog: python ELECTRIC.py


Output
------

The driver will output a file called :code:`proj_totfield.csv`. This is a CSV file which contains data on the projected electric field at the point between each probe atom due to each fragment , depending on input (`--byres` for by residue, `--bymol` for by molecule, or by atom if neither argument is given.). Each column will contain a header which indicates which probe atoms the measurement is between, followed by the frame number, while the rows will be the electric field at the mean location between the probe atoms due to a particular fragment

Consider the example (:code:`bench5`), which was run with the following command:

.. code-block:: bash

    python ${DRIVER_LOC} -probes "1 40" -snap bench5.arc -mdi "-role DRIVER -name driver -method TCP -port 8022" --bymol

Here, we have set the probe atoms to be atoms 1 and 40, and we have indicated we want the the electric field between the probe atoms based on contributions by molecule. Headers will be "`i and j - frame n`. Where `i` and `j` are the atom indices of the probes, and `n` is the frame number.

For the example, headers are:

.. code-block:: text

    "1 and 40 - frame 1"
    "1 and 40 - frame 2"
    "1 and 40 - frame 3"
    "1 and 40 - frame 4"
    "1 and 40 - frame 5"

Since this calculation was run using :code:`--bymol`, there are 216 rows, one for each molecule in the system.

The first entry, column :code:`1 and 40 - frame 1`, header :code:`molecule 1`, gives the projected total electric field at the midway point between :code:`atom 1` and :code:`atom 40` due to :code:`molecule 1`. The electric field has been projected along the vector which points from :code:`atom 1` to :code:`atom 40`. The projection will always be along the vector from atom 1 to atom 2. You can reverse the sign of the number if you would like the vector to point the opposite way.


Running ELECTRIC in Parallel
-----------------------------

.. note::

    You must have mpi4py installed to run ELECTRIC in parallel. You can install it from conda
    
    .. code-block:: bash

        conda install -c anaconda mpi4py

ELECTRIC is parallelized using MPI4Py. You can take advantage of this parallelization by making sure MPI4Py is installed and using more than one ELECTRIC engine using the :code:`-nengines` command. Note that if you are using the :code:`-nengines` argument with a number greater than one, you must launch the equivalent number of Tinker instances. In the :ref:`example`, this is acheived by setting a variable :code:`nengines` and using this number to launch Tinker instances in a loop (:code:`lines 12-15`) and inputting the same variable into the ELECTRIC launch on :code:`line 18`.

.. warning::

    Launching an unmatching number of MDI-Tinker and ELECTRIC instances will result in your calculation hanging. Make sure that you launch an equivalent number of MDI-Tinker instances to your :code:`-nengines` argument.

.. _tutorial: tutorial.html
.. _`MDI documentation`: https://molssi.github.io/MDI_Library/html/library_page.html#library_launching_sec
