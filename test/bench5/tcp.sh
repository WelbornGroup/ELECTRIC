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

#launch Tinker without EWALD

#launch Tinker using EWALD
time ${TINKER_LOC} bench5 -mdi "-role ENGINE -name NO_EWALD -method TCP -port 8021 -hostname localhost" 1000 1.0 10.0 2 298.0 778.0 &

#launch driver
python ${DRIVER_LOC} -mdi "-role DRIVER -name driver -method TCP -port 8021" &

wait
