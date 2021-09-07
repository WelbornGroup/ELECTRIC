#!/bin/bash
#SBATCH --nodes=1
#SBATCH --time=0:30:00
#SBATCH --constraint=knl
#SBATCH --qos=debug
#SBATCH --account=dasrepo
#SBATCH --output=cori5.out

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

# number of instances of Tinker to run as an engine
nengines=5

#set the number of threads
export OMP_NUM_THREADS=1

# Run the tinker md simulation
# This will print out 5 frames to traj_out.arc
# A copy of traj_out.arc is included in data/, so it isn't necessary to re-run this
rm bench5.arc
srun -N 1 -n 1 ${TINKER_LOC} bench5 -k bench5.key 10 1.0 0.001999 2 300.00 > Dynamics.log

#launch driver
echo 0 python ${DRIVER_LOC} -probes \'1 40\' -snap bench5.arc -mdi \'-role DRIVER -name driver -method MPI -out driver.out\' --bymol --nengines ${nengines} > srun.conf

#launch Tinker using EWALD
for i in $( eval echo {1..$nengines} )
do
  echo "${i}" ${TINKER_LOC} bench5 -k no_ewald.key -mdi \'-role ENGINE -name NO_EWALD"${i}" -method MPI -out no_ewald"${i}".log\' 10 1.0 0.001999 2 300.00 >> srun.conf
done

#launch the calculation
srun -n "$((nengines+1))" --multi-prog srun.conf
