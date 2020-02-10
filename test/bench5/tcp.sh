#location of required codes
DRIVER_LOC=$(cat ../locations/MDI_EF_Analysis)
TINKER_LOC=$(cat ../locations/Tinker)

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
rm bench5.arc; ${TINKER_LOC} bench5 -k bench5.key 10 1.0 0.001999 2 300.00 > Dynamics.log

#launch Tinker using EWALD
${TINKER_LOC} bench5 -k no_ewald.key -mdi "-role ENGINE -name NO_EWALD -method TCP -port 8022 -hostname localhost" 10 1.0 0.001999 2 300.00 > no_ewald.log &

#launch driver
python ${DRIVER_LOC} -probes [1,2] -snap bench5.arc -mdi "-role DRIVER -name driver -method TCP -port 8022" &

wait
