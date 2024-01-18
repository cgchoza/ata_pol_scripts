#!/opt/mnt/miniconda3/bin/python

import pandas as pd
from astropy.coordinates import SkyCoord
from astropy import units
import numpy as np

import argparse
import os,sys

HELP=\
"""
The .dat file and parts of this script were given 
to me by Tessa Vernstrom

See this:
https://science.nrao.edu/facilities/vla/observing/callist

For calibration code quality, from the above website:

The key to the calibrator quality code, respectively determined in the 
A, B, C and D array configuration using a 50 MHz observing bandwidth, is:

- P : <3% amplitude closure errors expected. Great for calibration!
- S : 3-10% closure errors expected. Good for phase and gain (amplitude) calibration.
- W : 10-?% closure errors expected. Suitable for calibration of phases only.
- C : Confused source, probably not good to use for calibration.
- X : Do not use. Too much resolution or too weak but see CALIB restrictions note below!
- ? : Source structure unknown
"""

BANDS = ['X','P','W','S', 's', 'C', '?']
#C K L P Q U X
BANDS = ['X','P','W','S', 's', 'C', '?', 'K', 'L', 'Q', 'U']


def process_table(tab):
    """Process the secondary table into something manageable
    
    tab ({str}) -- ASCII table of a single secondary
    """
    lines = tab.split('\n')
    name = lines[0].split()[0]
    pos_j2000 = lines[0].split()[3:5]
    
    results = []
    for l in lines[5:]:
        bands = {}
        cols = l.split()
        if len(cols) <= 5:
            #print(f"{name} table has not calcodes?")
            continue
        if cols[5] not in BANDS:
            #print(f"{name} might be missing calcode?")
            continue
            
        bands['Band']    = cols[1]
        bands['Band_cm'] = cols[0]
        bands['A']       = cols[2]
        bands['B']       = cols[3] 
        bands['C']       = cols[4] 
        bands['D']       = cols[5] 
        try:
            bands['Flux']  = cols[6]
        except IndexError as e:
            bands['Flux']  = np.nan
        
        bands['Position'] = ' '.join(pos_j2000)
        bands['RA'] = pos_j2000[0]
        bands['Dec'] = pos_j2000[1]
        bands['Coord'] = SkyCoord(ra = bands['RA'],
                                  dec = bands['Dec'],
                                  frame='icrs')
        
        bands['Name'] = name
    
        results.append(bands)
        
    return results

def main():
    parser = argparse.ArgumentParser(description=
            'Find nearest VLA calibrator to a specific sky position')

    parser.add_argument(dest='ra', type=float,
            help="Right Ascension in decimal hours")
    parser.add_argument(dest='dec', type=float,
            help="Declination in decimal degrees")

    parser.add_argument('-hh', '--hheellpp', action='store_true',
            help='show more than this help message and exit')

    parser.add_argument('-b', '--band', dest='band', type=str,
            help="what band to use [default: X]",
            default='X')

    parser.add_argument('-d', '--dist', dest='dist', type=float,
            help="maximum distance from source [default: 10.0 deg]",
            default=10.0)

    if ('-hh' in sys.argv) or ('--hheellpp' in sys.argv):
        print(HELP)
        sys.exit(0)

    args = parser.parse_args()

    inp_ra       = args.ra #e.g. 17.04360
    inp_dec      = args.dec #e.g. 51.868083
    inp_band     = args.band # must be in C K L P Q U X
    max_distance = args.dist # degrees

    phdat = open(os.path.join(os.path.dirname(os.path.realpath(__file__)), 
        './VLA_Calibratorlist.dat')).read()
    results = []

    for i in phdat.split('\n \n'):
        tab_results =  process_table(i)
        results = results + tab_results

    # Get all the table
    df= pd.DataFrame(results)



    inp_coord = SkyCoord(ra = inp_ra*units.hour, 
                         dec = inp_dec*units.degree,
                         frame='icrs')


    # select based on band
    sel = df[df['Band'] == inp_band].copy()

    # select only the sources that have amplitude closure
    # of 0-10 % (AKA "P" and "S" according to the VLA website
    sel = sel[(sel['D'] == 'P') | (sel['D'] == 'S')].copy()

    # now get the coordinate difference
    diff = []
    for idx, d in sel.iterrows():
        t = np.sqrt((d['Coord'].ra - inp_coord.ra)**2 + 
                    (d['Coord'].dec - inp_coord.dec)**2)
        diff.append(t.value)

    sel['diff'] = diff

    # select only the ones within max_distance from source
    sel = sel[sel['diff'] < max_distance].copy()

    # sort in flux
    sel.sort_values('Flux', ascending=False, inplace=True)

    # now print
    print("="*79)
    print("Name | RA | Dec | Code | Flux [Jy] | Sep [deg]")
    for idx, ii in sel.iterrows():
        print(ii.Name, "|", ii.RA, "|", ii.Dec, "|", ii.D, 
                "|", ii.Flux, "|", ii['diff'])
    print("="*79)


if __name__ == "__main__":
    main()
