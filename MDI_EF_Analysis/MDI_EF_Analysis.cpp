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
  int natoms;
  MDI_Send_Command("<NATOMS", ewald_comm);
  MDI_Recv(&natoms, 1, MDI_INT, ewald_comm);
  cout << "natoms: " << natoms << endl;

  // Initialize a new MD simulation
  MDI_Send_Command("@INIT_MD", ewald_comm);

  // Go to the next force calculation
  int nsteps = 500;
  for (int istep=0; istep < nsteps; istep++) {
    MDI_Send_Command("@FORCES", ewald_comm);

    // Get the number of atoms
    MDI_Send_Command("<NATOMS", ewald_comm);
    MDI_Recv(&natoms, 1, MDI_INT, ewald_comm);
    cout << "natoms: " << natoms << endl;
  }

  // Send the "EXIT" command to each of the engines
  MDI_Send_Command("EXIT", ewald_comm);

  // Synchronize all MPI ranks
  MPI_Barrier(world_comm);

  return 0;
}
