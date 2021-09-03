#!/bin/bash
#SBATCH --nodes=1
#SBATCH --time=0:30:00
#SBATCH --constraint=knl
#SBATCH --qos=debug
#SBATCH --account=dasrepo
#SBATCH --output=cori.out

module load python3

#location of required codes
DRIVER_LOC=$(cat ../locations/ELECTRIC)
TINKER_LOC=$(cat ../locations/Tinker_ELECTRIC)

#remove old files
if [ -d work ]; then
  rm -r work
fi

#create work directory
cp -r data work
cd work

#set the number of threads
export OMP_NUM_THREADS=1

# Run the tinker md simulation
# This will print out 5 frames to traj_out.arc
# A copy of traj_out.arc is included in data/, so it isn't necessary to re-run this
rm bench5.arc
srun -N 1 -n 1 ${TINKER_LOC} bench5 -k bench5.key 10 1.0 0.001999 2 300.00 > Dynamics.log

#launch driver
echo 0 python ${DRIVER_LOC} -probes \'1 40\' -snap bench5.arc -mdi \'-role DRIVER -name driver -method MPI -out driver.out\' --bymol > srun.conf

#launch Tinker using EWALD
echo 1 ${TINKER_LOC} bench5 -k no_ewald.key -mdi \'-role ENGINE -name NO_EWALD -method MPI -out no_ewald.log\' 10 1.0 0.001999 2 300.00 >> srun.conf

#launch the calculation
srun -n 2 --multi-prog srun.conf
