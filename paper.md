---
title: 'ELECTRIC: Electric fields Leveraged from multipole Expansion Calculations in Tinker Rapid Interface Code'
tags:
  - Tinker
  - molecular dynamics
  - polarizable force fields
  - electric fields
authors:
  - name: Jessica Nash
    orcid: 0000-0000-0000-0000
    affiliation: "1, 2" 
  - name: Taylor Barnes
    orcid: 0000-0001-9396-1094
    affiliation: "1, 2" 
  - name: Valerie Vaissier Welborn
    orcid: 0000-0003-0834-4441
    affiliation: 2 
affiliations:
 - name: The Molecular Sciences Software Institute
   index: 1
 - name: Department of Chemistry, Virginia Tech
   index: 2
date: 30 June 2020
bibliography: paper.bib


# Summary

Polarizable force fields have changed the landscape of biomolecular simulation, mostly by featuring improved electrostatic potential energy terms.[@doi:10.1146/annurev-biophys-070317-033349] These novel energy functions allow environment-driven changes in charge distribution, which yield simulations with improved geometries and molecular properties. In particular, the AMOEBA polarizable force field exhibits two fundamental changes compared to more traditional fixed charge force fields.[@doi:10.1021/ct4003702; @doi:10.1021/acs.jctc.7b01169] The first one relates to permanent electrostatics, expressed in AMOEBA in terms of atomic multipoles (truncated at quadrupoles) that account for anisotropy in the computed charge distributions. The second one represents polarizability through an induced dipole term that can respond to the chemical environment. These modified terms make the AMOEBA force field more physically grounded than other force fields and is the basis for more realistic simulations of biomolecular systems.

Improved electrostatics with AMOEBA give a unique opportunity to accurately compute electric fields, powerful metrics of catalytic activity in enzymes and other systems.[@doi:10.1021/jacs.6b12265; @doi:10.1021/acscatal.7b03151; @natcat] Electric fields projected onto specific bonds report on the combined effects of the surroundings (interacting via coulombic interactions, solvent effects, hydrogen bonding, etc., which are mostly electrostatic in nature) on the flow of electrons along these bonds. Therefore, projected electric fields are correlated to the probablitly of breaking these bonds, making them a useful probe of chemical reactivity.

`ELECTRIC` [@electric] is a MolSSI Driver Interface (MDI) [@mdi_library; @barnes_taylor_arnold_2020_3659285] driver that utilizes Tinker to analyze specific components of electric fields that are modeled using the AMOEBA force field.  `ELECTRIC` parses Tinker trajectories and orchestrates additional Tinker calculations in order to project components of the electric fields onto user-defined bonds (specified by two atoms). It outputs the field in MV/cm, which is the sum of the direct field (from permanent electrostatics) and the induced field (from the induce dipole term), projected onto the bond unit vector (i.e. normalized by the bond length). `ELECTRIC` enables splitting of the total field into contributions from different components, by molecules or by residues as specified in a reference PDB file for the system. In summary, `ELECTRIC` was designed to improve quantitative system characterization via the computation of electric fields with user-friendly processing tools of Tinker-AMOEBA simulations.


# Acknowledgements

We would like to thank Yi Zheng for producing AMOEBA Tinker trajectories to test `ELECTRIC`.

# References
