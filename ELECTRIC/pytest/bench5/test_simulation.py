import os
import sys
import subprocess
import pytest
import pandas as pd
import numpy as np

error_tolerance = 0.000001
mypath = os.path.dirname(__file__)

def format_return(input_string):
    my_string = input_string.decode('utf-8')

    # remove any \r special characters, which sometimes are added on Windows
    my_string = my_string.replace('\r','')

    return my_string

def test_bench5():
    # get the name of the codes
    driver_path = os.path.join(mypath, "../../ELECTRIC.py")
    engine_path = os.path.join(mypath, "../../../modules/Tinker/build/tinker/source/dynamic.x")

    # run the calculation
    driver_proc = subprocess.Popen([sys.executable, driver_path, 
                                    "-probes", "1 40", "-snap", "bench5.arc", 
                                    "-mdi", "-role DRIVER -name driver -method TCP -port 8021"
                                    "--bymol"],
                                   stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=mypath)
    engine_proc = subprocess.Popen([engine_path, "bench5", "-k", "no_ewald.key", 
                                    "-mdi", "-role ENGINE -name NO_EWALD -method TCP -port 8021 -hostname localhost",
                                    "10", "1.0", "0.001999", "2", "300.00"],
                                    cwd=mypath)
    driver_tup = driver_proc.communicate()
    engine_tup = engine_proc.communicate()

    # convert the driver's output into a string
    driver_out = format_return(driver_tup[0])
    driver_err = format_return(driver_tup[1])

    # validate proj_totfield.csv against ref_totfield.csv
    ref_totfield_path = os.path.join(mypath, "ref_totfield.csv")
    proj_totfield_path = os.path.join(mypath, "proj_totfield.csv")
    ref_totfield = pd.read_csv(ref_totfield_path)
    proj_totfield = pd.read_csv(proj_totfield_path)

    pd.testing.assert_frame_equal(ref_totfield, proj_totfield)