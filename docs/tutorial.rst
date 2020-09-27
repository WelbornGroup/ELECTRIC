Tutorial
========

This tutorial will walk you through using ELECTRIC to analyze the electric field in a small protein. This tutorial assumes you have ELECTRIC and MDI-enabled Tinker installed. If you don't, navigate to the installation_ instructions.

.. note::
    This tutorial will assume the following:
        - You are able to run a molecular dynamics simulation using the Tinker software.
        - You are able to download or clone a directory from git.
        - You are familiar with bash scripts.


The pdb code for this protein is 1l2y_, and you can see the structure below.

.. moleculeView:: 
    
    data-pdb: 1l2y
    data-backgroundcolor: white
    width: 300px
    height: 300px
    data-style: cartoon
    data-style-color: spectrum

To follow along with this tutorial, you can clone the `tutorial repository`_. Included in this repository is folder called `data`. The `data` directory has all of the data you will need for this tutorial.

ELECTRIC is a post-processing analysis, meaning that you should first run your simulations using the AMOEBA forcefield and save the trajectory, and ELECTRIC performs analysis on that trajectory. We will be analyzing the included trajectory `1l2y_npt.arc`. This trajectory is a text file containing coordinates for a simulation snapshot we have run.

.. _1l2y: https://www.rcsb.org/structure/1l2y
.. _installation:
.. _`tutorial repository`: http://www.github.com/janash/ELECTRIC_tutorial