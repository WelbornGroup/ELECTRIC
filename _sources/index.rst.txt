.. ELECTRIC documentation master file, created by
   sphinx-quickstart on Fri Sep 25 17:00:58 2020.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

ELECTRIC
====================================

ELECTRIC: Electric fields Leveraged from multipole Expansion Calculations in Tinker Rapid Interface Code.

ELECTRIC uses the `MolSSI Driver Interface <https://molssi.org/software/mdi-2/>`_ to perform electric field analysis of Tinker trajectories which use the AMOEBA forcefield. 
This currently works as a post-processing tool, meaning that you run simulations as normal using Tinker, then analyze the trajectories using MDI-enabled Tinker and this driver. 

ELECTRIC is written by Jessica A. Nash and Taylor A. Barnes from `The Molecular Sciences Software Institute <https://molssi.org/>`_, 
in collaboration with `Prof. Valerie Vassier Welborn <https://www.valeriewelborn.com/>`_.

Using this tool, you can calculate the electric field along a bond or between atoms due to molecules or residues in the system.

This method has been reported in the following publications:

- `Computational optimization of electric fields for better catalysis design <https://www.nature.com/articles/s41929-018-0109-2>`_, Nature Catalysis

- `Fluctuations of Electric Fields in the Active Site of the Enzyme Ketosteroid Isomerase <https://pubs.acs.org/doi/10.1021/jacs.9b05323>`_, Journal of the American Chemical Society

- `Computational Optimization of Electric Fields for Improving Catalysis of a Designed Kemp Eliminase <https://pubs.acs.org/doi/10.1021/acscatal.7b03151>`_, ACS Catalysis

You can read about the underlying principles of this analysis in 

- `Computational Design of Synthetic Enzymes <https://pubs.acs.org/doi/10.1021/acs.chemrev.8b00399>`_, Chemical Reviews

ELECTRIC is now available as an open source software package. To get started, head to the installation_ instructions, see the usage_, or try out the tutorial_.

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   installation
   usage
   tutorial


.. _installation: installation.html
.. _usage: usage.html
.. _tutorial: tutorial.html
