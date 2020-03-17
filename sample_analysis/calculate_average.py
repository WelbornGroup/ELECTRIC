"""
Calculates time average for probe pairs.
"""

import pandas as pd
import numpy as np

import argparse

import matplotlib.pyplot as plt

parser = argparse.ArgumentParser()

parser.add_argument('-filename', help='The projected electric field file to calculate the average for',
        required=False, default='proj_totfield.csv')

args = parser.parse_args()

fn = args.filename
current = pd.read_csv(fn)

fragment_type = current.iloc[0].values[0].split()[0]

probes = [x.split('-')[0].strip() for x in current.columns[1:]]
probes = np.unique(probes)

n_probe = len(probes)

for probe_pair in probes:
    cols = [x for x in current.columns if probe_pair in x]
    bond_values = current[cols]
    means = bond_values.mean(axis=1)
    std = bond_values.std(axis=1)
    means.name = probe_pair
    means.index.name = fragment_type
    means.index += 1

    std.name = "standard deviation"
    std.index.name = fragment_type
    std.index += 1

    concat = pd.concat([means, std], axis=1)

    file_name = probe_pair.replace(" ", "_")
    file_name = file_name + '.csv'
    concat.to_csv(file_name, header=True)
