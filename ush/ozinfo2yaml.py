#!/usr/bin/env python
# ozinfo2yaml.py
# generate YAML from input ozinfo file
# for specified input GSI diag file(s)
import argparse
import yaml
import glob
import csv
import os
import numpy as np


def read_ozinfo(infofile):
    # read in ozinfo file
    sensor = []  # string used in the filename
    layer = []  # integer value of layer
    obuse = []  # use 1, monitor -1
    cv = open(infofile)
    rdcv = csv.reader(filter(lambda row: row[0] != '!', cv))
    for row in rdcv:
        try:
            rowsplit = row[0].split()
            sensor.append(rowsplit[0])
            layer.append(int(rowsplit[1]))
            obuse.append(int(rowsplit[2]))
        except IndexError:
            pass  # end of file
    cv.close()
    # loop through and set the last layer to 0, assuming total column
    # for sensors with multiple layers
    for i in range(len(layer)-1):
        if layer[i+1] <= layer[i]:
            layer[i] = 0  # indicates total column value
    return sensor, layer, obuse


def main(config):
    # call function to get lists from ozinfo file
    sensor, layer, obuse = read_ozinfo(config['ozinfo'])
    # get list of diagnostic files available
    diagpath = os.path.join(config['diagdir'], 'diag_*')
    diagfiles = glob.glob(diagpath)
    # compute suffix for files
    tmpsuffix = os.path.basename(diagfiles[0]).split('.')
    suffix = '.'.join((tmpsuffix[-2][10:], tmpsuffix[-1]))

    # initialize YAML dictionary for output
    if config['variable'] == 'obs':
        diagtype = 'observation'
    elif config['variable'] == 'hofx':
        diagtype = 'hofx'
    else:
        diagtype = 'oma' if config['loop'] == 'anl' else 'omf'

    unique_sensors = np.unique(sensor)

    for isensor in unique_sensors:
        yamlout = {'diagnostic': {}}

        sensorindx = np.where(np.array(sensor) == isensor)

        # first get filename and verify it exists
        diagfile = os.path.join(f"{config['diagdir']}",
                                (f"diag_{isensor}_{config['loop']}"
                                 f".{config['cycle']}{suffix}"))
        if diagfile not in diagfiles:
            continue  # skip if diag file is missing

        yamlout['diagnostic']['path'] = diagfile
        yamlout['diagnostic']['data type'] = diagtype
        yamlout['diagnostic']['ozone'] = []

        # loop through obtypes
        for iuse, ichan in zip(np.array(obuse)[sensorindx],
                               np.array(layer)[sensorindx]):

            if iuse != 1 and not config['monitor']:
                continue  # only process assimilated obs for now
            dictloop = {
                'layer': [int(ilayer)],
                'bias correction': [True]
            }

            yamlout['diagnostic']['ozone'].append(dictloop)

        filetype = os.path.basename(diagfile).split('.')[0]
        output_yamlfile = config['yaml'] + filetype + '.yaml'

        # write out the YAML
        with open(output_yamlfile, 'w') as file:
            yaml.dump(yamlout, file, default_flow_style=False)
        print('YAML written to ' + output_yamlfile)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=(
        'Given an input ozinfo ',
        'GSI file and path to ',
        'GSI diags, generate an output ',
        'YAML file for use by PyGSI'))
    parser.add_argument('-d', '--diagdir', type=str,
                        help='path to GSI netCDF diags', required=True)
    parser.add_argument('-c', '--cycle', type=str,
                        help='cycle YYYYMMDDHH', required=True)
    parser.add_argument('-i', '--ozinfo', type=str,
                        help='path to GSI ozinfo file', required=True)
    parser.add_argument('-y', '--yaml', type=str,
                        help='path to output YAML file', required=True)
    parser.add_argument('-l', '--loop', type=str,
                        help='guess or analysis?',
                        choices=['ges', 'anl'], default='ges',
                        required=False)
    parser.add_argument('-v', '--variable', type=str,
                        help='read departures, obs, or H(x)',
                        choices=['omf', 'obs', 'hofx'],
                        default='omf', required=False)
    parser.add_argument('-m', '--monitor', action='store_true',
                        help='include monitored obs?', required=False)
    args = parser.parse_args()

    config = vars(args)

    main(config)
