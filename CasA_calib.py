#!/usr/bin/env python3

#############################

# This script should be run using CASA 6.4.0.16 or 

#############################

# Imports
import glob

# lo = 'b'
# # Concatenate sample
# vis_to_concat = glob.glob(f'*/*{lo}_averaged.ms')
# concat(vis=vis_to_concat, concatvis=f'CasA_polcal.ms')

# # Fix scan numbers
# execfile('fix_scans.py')

# bcal = '2350+646'       # gain, bandpass, and pol angle
bcal = '3c147'
pcal = '2343+538'    # unknown pol leakage calibrator, also phase calibrator
polcalb = '3c48'     # low-frequency unpolarized leakage cal (should be usable as pol angle standard)
polcalc = '2355+498' # bright unpolarized calibrator
target = 'CasA'

# Flagging for RFI and bandpass
# NOTE: FLAG SCAN 28
# May need to flag first scan of Cas A
vis = 'CasA_polcal.ms'
flagdata(vis=vis, mode='manual', scan='28', flagbackup=False)

# Set flux model for flux calibrator (in this case, field 0 is 3C286)
setjy(vis=vis, field='', standard='Perley-Butler 2017', usescratch=True)

listobs(vis=vis)

spw='0'

# Initial gain calibration
# Note this discards XX vs. YY signal difference and will
# be thrown away after solving delay and bandpass
gaincal(vis=vis, caltable='CasA_polcal.G0', field=bcal, spw=spw, refant='40', calmode='p', solint='inf')
gaincal(vis=vis, caltable='CasA_polcal.G1', field=bcal, spw=spw, refant='40', calmode='a', solint='100', preavg=1, minblperant=1, minsnr=0, gaintype='G', gaintable=[f'CasA_polcal.G0'])

# Delay calibration
gaincal(vis=vis, caltable='CasA_polcal.K0', field=bcal, spw=spw, refant='40', solint='inf', combine='scan', preavg=1, minblperant=1, gaintype='K', gaintable=[f'CasA_polcal.G0', f'CasA_polcal.G1'])

# Write out a new measurement set here to check if everything looks alright
# before moving on to secondary gain cal
split(vis = f'CasA_polcal.ms', outputvis = 'CasA_polcal2.ms', datacolumn = 'data')
applycal(vis=f'CasA_polcal2.ms', gaintable=['CasA_polcal.G0', 'CasA_polcal.G1', 'CasA_polcal.K0'])
# Check as you go (weird bandpass response)
# check cross hand amps before and after kcross
# Phase/amp are the focus here

# Bandpass calibration
# Both low freq spectral windows so we'll use a small averaging window
bandpass(vis=vis, caltable=f'CasA_polcal.B0', field=bcal, spw=spw, refant='40', solint='inf,2ch', combine='scan', bandtype='B', minblperant=1, minsnr=0, gaintable=[f'CasA_polcal.G0', f'CasA_polcal.G1', f'CasA_polcal.K0'], append=False)

# Write out a new measurement set here to check if everything looks alright
# before moving on to secondary gain cal
split(vis = 'CasA_polcal.ms', outputvis = 'CasA_polcal3.ms', datacolumn = 'data')
applycal(vis='CasA_polcal3.ms', gaintable=['CasA_polcal.G0', 'CasA_polcal.G1', 'CasA_polcal.K0', 'CasA_polcal.B0'])
# Check as you go (weird bandpass response)
# check cross hand amps before and after kcross
# Phase/amp are the focus here

# Secondary gain calibration after solving for delay and bandpass
# Phase and amplitude are solved independently
# For amplitude, we do a polarization-dependent calibration
# over all the scans to correct for the difference of
# gain in each channel and a polarization-independent
# calibration to compensate for gain changes with time
gaincal(vis=vis, caltable=f'CasA_polcal.G2', field=bcal, spw=spw, refant='40', calmode='ap', solint='10', gaintable=[f'CasA_polcal.K0', f'CasA_polcal.B0'])
gaincal(vis=vis, caltable=f'CasA_polcal.G3', field=pcal, spw=spw, refant='40', calmode='ap', solint='inf', gaintable=[f'CasA_polcal.K0', f'CasA_polcal.B0', f'CasA_polcal.G2'], append=True)

split(vis = 'CasA_polcal.ms', outputvis = 'CasA_polcal4.ms', datacolumn = 'data')
applycal(vis='CasA_polcal4.ms', gaintable=['CasA_polcal.G2', 'CasA_polcal.G3', f'CasA_polcal.K0', f'CasA_polcal.B0'])

# # Kcross normalization
# gaincal(vis=f'CasA_polcal_cal.ms', caltable=f'CasA_polcal_cal_norm.Kcross0', spw=spw, refant='40', solint='inf', gaintype='KCROSS', combine='scan', calmode='ap', minblperant=1, parang=True)

try_new = False

if try_new:
    # Try to observe parallactic angle behavior for that linear one and use the scan where X and Y amps cross
    gaincal(vis=f'CasA_polcal_cal.ms', caltable=f'CasA_polcal_cal_norm.Kcross0', spw=spw, refant='40', solint='inf', field='4', gaintype='KCROSS', combine='scan', calmode='ap', minblperant=1, parang=True)

    # qufromgain on polcalib_b

    qu_field0 = polfromgain(vis=vis, tablein='uvh5_60247.field0.G1')



# Apply calibrations: delay, bandpass, post-bandpass amp and phase gain cal
applycal(vis=vis, gaintable=['CasA_polcal.K0', 'CasA_polcal.B0', 'CasA_polcal.G2', 'CasA_polcal.G3'])
# Write out calibrated dataset
split(vis=vis, outputvis=f'CasA_polcal_cal.ms', datacolumn='corrected')