#!/bin/bash

# Reproduce the behavior of "readlink -f", in a manner compatible with MacOS
readlink_f() {
  filename=$1

  cd `dirname $filename`
  filename=`basename $filename`

  while [ -L "$filename" ]
  do
      cd `dirname $filename`
      filename=`basename $filename`
  done

  real_path=`pwd -P`
  echo $real_path/$filename
}

# Enable building shared libraries on Cray systems
export CRAYPE_LINK_TYPE=dynamic

# If the C compiler has been set, ensure that its value propagates to any other scripts
[[ ! -z "${CC}" ]] && export CC=${CC}

# If the Fortran compiler has been set, ensure that its value propagates to any other scripts
[[ ! -z "${FC}" ]] && export FC=${FC}

# Compile the Tinker submodule
cd modules/Tinker/dev
./full_build.sh
cd ../build/tinker/source
readlink_f dynamic.x > ../../../../../test/locations/Tinker_ELECTRIC
cd ../../../../../

# Compile ELECTRIC
cmake .
make
cd ELECTRIC
readlink_f ELECTRIC.py > ../test/locations/ELECTRIC
