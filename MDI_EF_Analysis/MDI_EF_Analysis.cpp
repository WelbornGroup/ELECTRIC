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
  MDI_Comm engine_comm = MDI_NULL_COMM;
  int nengines = 1;
  for (int iengine=0; iengine < nengines; iengine++) {
    MDI_Comm comm;
    MDI_Accept_Communicator(&comm);
 
    // Determine the name of this engine
    char* engine_name = new char[MDI_NAME_LENGTH];
    MDI_Send_Command("<NAME", comm);
    MDI_Recv(engine_name, MDI_NAME_LENGTH, MDI_CHAR, comm);
 
    cout << "Engine name: " << engine_name << endl;
 
    if ( strcmp(engine_name, "NO_EWALD") == 0 ) {
      if ( engine_comm != MDI_NULL_COMM ) {
	throw runtime_error("Accepted a communicator from a second NO_EWALD engine.");
      }
      engine_comm = comm;
    }
    else {
      throw runtime_error("Unrecognized engine name.");
    }
 
    delete[] engine_name;
  }

  // Perform the simulation

  // Get the number of atoms
  int natoms;
  MDI_Send_Command("<NATOMS", engine_comm);
  MDI_Recv(&natoms, 1, MDI_INT, engine_comm);
  cout << "natoms: " << natoms << endl;

  // Get the number of multipole centers
  int npoles;
  MDI_Send_Command("<NPOLES", engine_comm);
  MDI_Recv(&npoles, 1, MDI_INT, engine_comm);
  cout << "npoles: " << npoles << endl;

  // Allocate arrays
  double coords[3*natoms];
  double charges[natoms];
  double rpoles[13*npoles];
  double field[3*npoles];
  double fid[3];

  // Set the probe atoms
  int nprobes = 2;
  int probes[nprobes];
  probes[0] = 1;
  probes[1] = 2;

  MDI_Send_Command(">NPROBES", engine_comm);
  MDI_Send(&nprobes, 1, MDI_INT, engine_comm);

  MDI_Send_Command(">PROBES", engine_comm);
  MDI_Send(&probes[0], nprobes, MDI_INT, engine_comm);

  MDI_Send_Command("<FIELD", engine_comm);
  MDI_Recv(&field[0], 3*npoles, MDI_DOUBLE, engine_comm);

  // Print the field
  cout << "Field: " << endl;
  for (int ipole=0; ipole < npoles; ipole++) {
    cout << "   " << ipole << ": " << field[3*ipole + 0] << " " << field[3*ipole + 1] << " " << field[3*ipole + 2] << endl;
  }

  // Send the "EXIT" command to each of the engines
  MDI_Send_Command("EXIT", engine_comm);

  // Synchronize all MPI ranks
  MPI_Barrier(world_comm);

  return 0;
}
