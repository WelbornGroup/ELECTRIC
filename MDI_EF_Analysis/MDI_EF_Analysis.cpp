#include <iostream>
#include <mpi.h>
#include <stdexcept>
#include <string.h>
#include "mdi.h"

using namespace std;

int main(int argc, char **argv) {

  // Initialize the MPI environment
  MPI_Comm world_comm;
  MPI_Init(&argc, &argv);

  // Read through all the command line options
  int iarg = 1;
  bool initialized_mdi = false;
  while ( iarg < argc ) {

    if ( strcmp(argv[iarg],"-mdi") == 0 ) {

      // Ensure that the argument to the -mdi option was provided
      if ( argc-iarg < 2 ) {
	throw runtime_error("The -mdi argument was not provided.");
      }

      // Initialize the MDI Library
      world_comm = MPI_COMM_WORLD;
      int ret = MDI_Init(argv[iarg+1], &world_comm);
      if ( ret != 0 ) {
	throw runtime_error("The MDI library was not initialized correctly.");
      }
      initialized_mdi = true;
      iarg += 2;

    }
    else {
      throw runtime_error("Unrecognized option.");
    }

  }
  if ( not initialized_mdi ) {
    throw runtime_error("The -mdi command line option was not provided.");
  }

  // Connect to the engines
  MDI_Comm ewald_comm = MDI_NULL_COMM;
  MDI_Comm noewald_comm = MDI_NULL_COMM;
  int nengines = 1;
  for (int iengine=0; iengine < nengines; iengine++) {
    MDI_Comm comm;
    MDI_Accept_Communicator(&comm);
 
    // Determine the name of this engine
    char* engine_name = new char[MDI_NAME_LENGTH];
    MDI_Send_Command("<NAME", comm);
    MDI_Recv(engine_name, MDI_NAME_LENGTH, MDI_CHAR, comm);
 
    cout << "Engine name: " << engine_name << endl;
 
    if ( strcmp(engine_name, "EWALD") == 0 ) {
      if ( ewald_comm != MDI_NULL_COMM ) {
	throw runtime_error("Accepted a communicator from a second EWALD engine.");
      }
      ewald_comm = comm;
    }
    else if ( strcmp(engine_name, "NOEWALD") == 0 ) {
      if ( noewald_comm != MDI_NULL_COMM ) {
	throw runtime_error("Accepted a communicator from a second NOEWALD engine.");
      }
      noewald_comm = comm;
    }
    else {
      throw runtime_error("Unrecognized engine name.");
    }
 
    delete[] engine_name;
  }

  // Perform the simulation

  // Get the number of atoms
  int natoms;
  MDI_Send_Command("<NATOMS", ewald_comm);
  MDI_Recv(&natoms, 1, MDI_INT, ewald_comm);
  cout << "natoms: " << natoms << endl;

  // Get the number of multipole centers
  int npoles;
  MDI_Send_Command("<NPOLES", ewald_comm);
  MDI_Recv(&npoles, 1, MDI_INT, ewald_comm);
  cout << "npoles: " << npoles << endl;

  // Allocate arrays
  double coords[3*natoms];
  double charges[natoms];
  double poles[13*npoles];

  // Initialize a new MD simulation
  MDI_Send_Command("@INIT_MD", ewald_comm);

  // Go to the next force calculation
  int nsteps = 100;
  for (int istep=0; istep < nsteps; istep++) {
    //cout << "Iteration: " << istep << endl;

    MDI_Send_Command("@FORCES", ewald_comm);

    // Get the atomic coordinates
    MDI_Send_Command("<COORDS", ewald_comm);
    MDI_Recv(&coords[0], 3*natoms, MDI_DOUBLE, ewald_comm);

    // Get the charges
    MDI_Send_Command("<CHARGES", ewald_comm);
    MDI_Recv(&charges[0], natoms, MDI_DOUBLE, ewald_comm);

    // Get the poles
    MDI_Send_Command("<POLES", ewald_comm);
    MDI_Recv(&poles[0], 13*npoles, MDI_DOUBLE, ewald_comm);
  }

  // Print the coordinates
  /*
  cout << "Coords: " << endl;
  for (int iatom=0; iatom < natoms; iatom++) {
    cout << "   " << iatom << ": " << coords[3*iatom + 0] << " " << coords[3*iatom + 1] << " " << coords[3*iatom + 2] << endl;
  }
  */

  // Print the charges
  /*
  cout << "Charges: " << endl;
  for (int iatom=0; iatom < natoms; iatom++) {
    cout << "   " << iatom << ": " << charges[iatom] << endl;
  }
  */

  // Print the poles
  cout << "Monopoles: " << endl;
  for (int ipole=0; ipole < npoles; ipole++) {
    cout << "   " << ipole << ": " << poles[13*ipole + 0] << endl;
  }

  // Send the "EXIT" command to each of the engines
  MDI_Send_Command("EXIT", ewald_comm);

  // Synchronize all MPI ranks
  MPI_Barrier(world_comm);

  return 0;
}
