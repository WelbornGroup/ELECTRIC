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


cd modules/Tinker/dev
./full_build.sh
cd ../build/tinker/source
readlink_f dynamic.x > ../../../../../test/locations/Tinker_ELECTRIC
cd ../../../../../
cmake .
make
cd ELECTRIC
readlink_f ELECTRIC.py > ../test/locations/ELECTRIC
