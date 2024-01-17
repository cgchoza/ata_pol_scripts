#!/usr/bin/env python3

#####################################################################
#
#  Polarimetric calibration of 3C286 observations
#  (using new calibrations commands)
#
#  This script was tested with CASA 6.6.0
#
#  The script can be run with '%run -i ./3c286_casa_new.py' in the CASA
#  IPython prompt
#
#####################################################################

import pathlib
lo = 'b'

vis = f'3c286_{lo}_cal_norm.ms'

# Extract XX and YY gain calibration for preliminary QU estimation
#
gaincal(vis=vis, caltable=f'3c286_{lo}_cal_norm.G0',
        solint='50', smodel=[1, 0, 0, 0],
        gaintype='G', calmode='a', minsnr=2,
        minblperant=1, parang=True,
        preavg=10)

# Calibrate cross-hand delay -- check where the tutorial applies this 
# (post first polcal?)
#
gaincal(vis=vis, caltable=f'3c286_{lo}_cal_norm.Kcross0',
        refant='0', gaintype='KCROSS',
        solint='inf', combine='scan', calmode='ap',
        minblperant=1, parang=True)

# A priori estimate of QU from difference in XX and YY gain calibration
qu = polfromgain(vis=vis, tablein=f'3c286_{lo}_cal_norm.G0')

print(qu)

# Determination of XY phase offset and source QU
# We want to try this first with a lower preavg, since the central 
# scans change so quickly in parallactic angle
# 
S = polcal(vis=vis, caltable=f'3c286_{lo}_cal_norm.Xfparang',
            solint='inf', combine='scan', field='0',
            preavg=50,
            smodel=qu['3c286']['Spw0'], poltype='Xfparang+QU',
            minblperant=1)

print(S)

# Gain calibration with source Stokes parameter model
gaincal(vis=vis, caltable=f'3c286_{lo}_cal_norm.G1',
        solint='50', smodel=S['3c286']['Spw0'],
        gaintype='G', calmode='a',
        minblperant=1, parang=True,
        preavg=10)

# D-term calibration
polcal(vis=vis, caltable=f'3c286_{lo}_cal_norm.D0',
        solint='inf', combine='scan',
        smodel=S['3c286']['Spw0'],
        preavg=50, poltype = 'Dlls',
        refant='',
        gaintable=[f'3c286_{lo}_cal_norm.G1',
                f'3c286_{lo}_cal_norm.Xfparang'])

# Apply calibrations
applycal(vis=vis,
        gaintable=[f'3c286_{lo}_cal_norm.G1',
                f'3c286_{lo}_cal_norm.D0',
                f'3c286_{lo}_cal_norm.Xfparang'],
                parang=True)
