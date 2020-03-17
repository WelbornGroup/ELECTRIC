# Sample Analysis

This directory contains a sample script to process the output of the driver. The driver will write a file called `proj_totfield.csv`. For an in depth explanation of this file, please see the `README.md` file in the top level of this repository.

The file `calculate_average.py` will calculate the time average projected field per fragment. This script should work to calculate the time average for any `proj_totfield.csv` output by the driver.

This script, will automatically look for a file called `proj_totfield.csv` in the current directory. To run it:

    python calculate_average.py

If you would like to change the file name, add the file name after the script name when you run.

    python calculate_average.py -filename FILENAME

The output will be a file for each pairwise probe interaction. The file gives the time average value of the projected field and the standard deviation.
