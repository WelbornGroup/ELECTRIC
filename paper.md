---
title: 'ELECTRIC: Electric fields Leveraged from multipole Expansion Calculations in Tinker Rapid Interface Code'
tags:
  - Tinker
  - molecular dynamics
  - polarizable force fields
  - electric fields
authors:
  - name: Jessica Nash
    orcid: 0000-0003-1967-5094
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
date: July 1, 2020
bibliography: paper.bib
---


# Summary

Polarizable force fields have changed the landscape of biomolecular simulation, mostly by featuring improved electrostatic potential energy terms.[@doi:10.1146/annurev-biophys-070317-033349] These novel energy functions allow environment-driven changes in charge distribution, which yield simulations with improved geometries and molecular properties. In particular, the AMOEBA polarizable force field exhibits two fundamental changes compared to more traditional fixed charge force fields.[@doi:10.1021/ct4003702; @doi:10.1021/acs.jctc.7b01169] The first one relates to permanent electrostatics, expressed in AMOEBA in terms of atomic multipoles (truncated at quadrupoles) that account for anisotropy in the computed charge distributions. The second one represents polarizability through an induced dipole term that can respond to the chemical environment. These modified terms make the AMOEBA force field more physically grounded than other force fields and is the basis for more realistic simulations of biomolecular systems.

Improved electrostatics with AMOEBA give a unique opportunity to accurately compute electric fields, powerful metrics of catalytic activity in enzymes and other systems.[@doi:10.1021/jacs.6b12265; @doi:10.1021/acscatal.7b03151; @natcat] Electric fields projected onto specific bonds report on the effect of the surroundings (interacting via coulombic interactions, solvent effects, hydrogen bonding or other forces, all mostly electrostatic in nature) on the flow of electrons along these bonds. Therefore, projected electric fields are correlated to the probability of breaking these bonds, making them a useful probe of chemical reactivity.

`ELECTRIC` [@electric] is a MolSSI Driver Interface (MDI) [@mdi_repo; @barnes_taylor_arnold_2020_3659285] driver that utilizes Tinker [@doi:10.1021/acs.jctc.8b00529] to analyze specific components of electric fields that are modeled using the AMOEBA force field.  `ELECTRIC` parses Tinker trajectories and orchestrates additional Tinker calculations in order to project components of the electric fields onto user-defined bonds (specified by two atoms). It outputs the field in MV/cm, which is the sum of the direct field (from permanent electrostatics) and the induced field (from the induce dipole term), projected onto the bond unit vector (i.e. normalized by the bond length). `ELECTRIC` enables splitting of the total field into contributions from different components of the system, by molecules or by residues as specified in a reference PDB file. In summary, `ELECTRIC` was designed to improve quantitative system characterization via the computation of electric fields with user-friendly processing tools of Tinker-AMOEBA simulations.

# Mathematics
The electric field at atom $i$, $\vec{E}^i$, has components defined as:
\begin{equation}
E^i_x=\sum_jE^{j\to i}_x =\sum_j\left( E^{j\to i}_{x,\text{perm}} +E^{j\to i}_{x,\text{ind}} \right)
\end{equation}
where $E^i_x$ is the $x$-component of the electric field on atom $i$, $E^{j\to i}_x$ is the $x$-component of the electric field on atom $i$ due to atom $j$ and "perm" and "ind" refer to permanent and induced fields, respectively. 

Each atom $i$ is characterized by permanent atomic multipoles, including a monopole (charge) $q^i$, a dipole $\{\mu^i_x,\mu^i_y,\mu^i_z\}$ and a quadrupole $\{Q^i_{xx}, Q^i_{xx},Q^i_{xy},Q^i_{xz}...Q^i_{zz}\}$, such that
\begin{equation}
E^{j\to i}_{x,\text{perm}}=-T_xq^j+\sum_{m=y,z}T_{xm}\mu^j_m-\frac{1}{3}\sum_{m=y,z}\sum_{n=y,z}T_{xmn}Q^j_{mn},
\end{equation}
and
\begin{equation}
E^{j\to i}_{x,\text{ind}}=\sum_{m=y,z}=T_{xm}\mu^j_{\text{ind},m},
\end{equation}
where
\begin{equation}
T_{xy...}=\frac{1}{4\pi\epsilon_0}\nabla_x\nabla_y...\frac{1}{r_{ij}},
\end{equation}
as also defined in @doi:10.1021/jacs.6b12265.

Similar equations can be written for the $y$- and $z$-components of the field. 
The field projected onto a specific bond, say bond $ij$ between atoms $i$ and $j$, is then calculated as:  
\begin{equation}
E^{ij}_\text{proj}=\left( \frac{\vec{E}^i+\vec{E}^j}{2}\right).\vec{u}^{ij},
\end{equation}
where $E^{ij}_\text{proj}$ is the electric field projected onto bond $ij$ and $\vec{u}^{ij}$ the unitary vector defining bond $ij$.

# Acknowledgements

We would like to thank Yi Zheng for producing AMOEBA Tinker trajectories to test `ELECTRIC`.

# References
