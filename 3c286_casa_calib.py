#!/usr/bin/env python3

#############################

# This script should be run using CASA 6.4.0.16

#############################

# Imports
import glob

lo = 'b'
# Concatenate sample
vis_to_concat = glob.glob(f'*/*{lo}_averaged.ms')
concat(vis=vis_to_concat, concatvis=f'3C286_{lo}.ms')

# Fix scan numbers
execfile('fix_scans.py')

# Flagging for RFI and bandpass
# NOTE: FLAG SCAN 18! CHECK IF 3C286 WENT DOWN THEN
# NOTE: FLAG ANTENNA 4e
vis = f'3C286_{lo}.ms'
flagdata(vis=vis, field='0', mode='tfcrop', datacolumn='DATA')
flagdata(vis=vis, field='0', mode='rflag', datacolumn='DATA')
flagdata(vis=vis, field='1', mode='tfcrop', datacolumn='DATA')
flagdata(vis=vis, field='1', mode='rflag', datacolumn='DATA')
flagdata(vis=vis, antenna='31')
flagdata(vis=vis, scan='18')

# Set flux model for flux calibrator (in this case, field 0 is 3C286)
setjy(vis=vis, field='0', standard='Perley-Butler 2017', usescratch=True)

listobs(vis=vis)

# Initial gain calibration
# Note this discards XX vs. YY signal difference and will
# be thrown away after solving delay and bandpass
gaincal(vis=vis, caltable=f'3c286_{lo}.G0', field='0', refant='40', calmode='p', solint='inf')
gaincal(vis=vis, caltable=f'3c286_{lo}.G1', field='0', refant='40', calmode='a', solint='100', preavg=1, minblperant=1, minsnr=0, gaintype='G', gaintable=[f'3c286_{lo}.G0'])

# Delay calibration
gaincal(vis=vis, caltable=f'3c286_{lo}.K0', field='0', refant='40', solint='inf', combine='scan', preavg=1, minblperant=1, gaintype='K', gaintable=[f'3c286_{lo}.G0', f'3c286_{lo}.G1'])

# Write out a new measurement set here to check if everything looks alright
# before moving on to secondary gain cal
split(vis = f'3C286_{lo}.ms', outputvis = f'3C286_{lo}2.ms', datacolumn = 'data')
applycal(vis=f'3C286_{lo}2.ms', gaintable=[f'3c286_{lo}.G0', f'3c286_{lo}.G1', f'3c286_{lo}.K0'])
# Check as you go (weird bandpass response)
# check cross hand amps before and after kcross
# Phase/amp are the focus here

# Bandpass calibration
# Both low freq spectral windows so we'll use a small averaging window
bandpass(vis=vis, caltable=f'3c286_{lo}.B0', field='0', refant='40', solint='inf,2ch', combine='scan', bandtype='B', minblperant=1, minsnr=0, gaintable=[f'3c286_{lo}.G0', f'3c286_{lo}.G1', f'3c286_{lo}.K0'], append=False)

# Write out a new measurement set here to check if everything looks alright
# before moving on to secondary gain cal
split(vis = f'3C286_{lo}.ms', outputvis = f'3C286_{lo}3.ms', datacolumn = 'data')
applycal(vis=f'3C286_{lo}3.ms', gaintable=[f'3c286_{lo}.G0', f'3c286_{lo}.G1', f'3c286_{lo}.K0', f'3c286_{lo}.B0'])
# Check as you go (weird bandpass response)
# check cross hand amps before and after kcross
# Phase/amp are the focus here

# Secondary gain calibration after solving for delay and bandpass
# Phase and amplitude are solved independently
# For amplitude, we do a polarization-dependent calibration
# over all the scans to correct for the difference of
# gain in each channel and a polarization-independent
# calibration to compensate for gain changes with time
gaincal(vis=vis, caltable=f'3c286_{lo}.G2', field='0', refant='40', calmode='p', solint='10', preavg=1, minblperant=1, minsnr=0, gaintype='G', gaintable=[f'3c286_{lo}.K0', f'3c286_{lo}.B0'])
gaincal(vis=vis, caltable=f'3c286_{lo}.G3', field='0', refant='40', calmode='a', solint='inf', combine='scan', preavg=1, minblperant=1, minsnr=0, gaintype='G', gaintable=[f'3c286_{lo}.K0', f'3c286_{lo}.B0', f'3c286_{lo}.G2'])

split(vis = f'3C286_{lo}.ms', outputvis = f'3C286_{lo}4.ms', datacolumn = 'data')
applycal(vis=f'3C286_{lo}4.ms', gaintable=[f'3c286_{lo}.G2', f'3c286_{lo}.G3', f'3c286_{lo}.K0', f'3c286_{lo}.B0'])

# Polarization-independent solve gets one solution for both polarizations
# Catches tropospheric gain error
gaincal(vis=vis, caltable=f'3c286_{lo}.T0', field='0', refant='40', solint='10', preavg=1, minblperant=1, minsnr=0, gaintype='T', calmode='a', gaintable=[f'3c286_{lo}.K0', f'3c286_{lo}.B0', f'3c286_{lo}.G2', f'3c286_{lo}.G3'])

# Apply calibrations: delay, bandpass, post-bandpass amp and phase gain cal, tropospheric/pol independent cal
applycal(vis=vis, gaintable=[f'3c286_{lo}.K0', f'3c286_{lo}.B0', f'3c286_{lo}.G2', f'3c286_{lo}.G3', f'3c286_{lo}.T0'])

# Write out calibrated dataset
split(vis=vis, outputvis=f'3c286_{lo}_cal.ms', datacolumn='corrected')

# Normalize to unit flux--this may be important for polcal

gaincal(vis=f'3c286_{lo}_cal.ms', caltable=f'3c286_{lo}.T1', field='0', refant='40', solint='inf', combine='scan', smodel=[1,0,0,0], gaintype='T', calmode='a')

split(vis=f'3c286_{lo}_cal.ms', outputvis=f'3c286_{lo}_cal_copy.ms', datacolumn = 'data')
applycal(vis=f'3c286_{lo}_cal_copy.ms', gaintable=f'3c286_{lo}.T1')
split(vis=f'3c286_{lo}_cal_copy.ms', outputvis=f'3c286_{lo}_cal_norm.ms', datacolumn='corrected')

# Final gaincal for polfromgain calculation
gaincal(vis=f'3c286_{lo}_cal_norm.ms', caltable=f'3c286_{lo}_cal_norm.G0', solint='50', smodel=[1,0,0,0], gaintype='G', calmode='a', parang=True, field='0', preavg=10)

# Kcross normalization
gaincal(vis=f'3c286_{lo}_cal_norm.ms', caltable=f'3c286_{lo}_cal_norm.Kcross0', refant='40', solint='inf', gaintype='KCROSS', combine='scan', calmode='ap', minblperant=1, parang=True)

