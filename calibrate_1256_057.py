#!/usr/bin/env python3

from distutils.dir_util import copy_tree, remove_tree
import pathlib

WORK_DIR = pathlib.Path('.').absolute()
print(WORK_DIR)
DATA_DIR = pathlib.Path('.').absolute()
print(DATA_DIR)
NSPW = 2  # number of spectral windows
REFANT = '40' # 5e

# # Copy ms files to a scratch directory to update the scan numbers
# scratch = WORK_DIR / 'scratch'
# scratch.mkdir()
# for scan, folder in enumerate(sorted(DATA_DIR.glob('uvh5*_measure_sets'))):
#     dest = scratch / folder.name
#     copy_tree(str(folder), str(dest))
#     for ms in dest.glob('*.ms'):
#         tb.open(str(ms), nomodify=False)
#         a = tb.getcol('SCAN_NUMBER')
#         a[:] = scan + 1  # CASA numbers the first scan as 1
#         tb.putcol('SCAN_NUMBER', a)
#         tb.close()

# # Concatenate everything
# ms_files = sorted([str(p) for p in scratch.glob('uvh5*_measure_sets/*.ms')])
vis = '3c286_obs.ms'
# concat(vis=ms_files, concatvis=vis)
# remove_tree(str(scratch))

# Flagging

# Scan 1 was the delay engine calibration scan
# Flag it to avoid confusion, since it uses different delay
# engine settings compared to the rest of the scans
flagdata(vis=vis, mode='manual', scan='1', flagbackup=False)

# The original ms files are already flagged
#
# To plot original flags:
#
# flagdata(vis=vis, mode='unflag', action='calculate', flagbackup=False, display='both')

# To reflag (arguably this produces worst results):
#
# flagdata(vis=vis, mode='unflag', flagbackup=False)
# for spw in range(nspw):
#     flagdata(vis=vis, spw=f'{spw}', mode='tfcrop', flagbackup=False)
#     flagdata(vis=vis, spw=f'{spw}', mode='rflag', flagbackup=False)

antennas = ['1b', '1c', '1e', '1g', '1h', '1k',
            '2b', '2d', '2e', '2f', '2h', '2j', '2k', '2l', '2m',
            '3d', '3l', '4e', '4j', '5e']
antenna_list = ','.join([f'"{a}"' for a in antennas])

# These plots take a very long time to generate
# for a0 in antennas:
#     for a1 in antennas:
#         plotms(vis=vis, ydatacolumn='data',
#                xaxis='freq', yaxis='phase',
#                avgtime='10000', coloraxis='corr', iteraxis='scan',
#                antenna=f'"{a0}"&"{a1}"', field='0',
#                gridcols=4, gridrows=4, spw='1',
#                plotfile=f'phase_vs_freq_{a0}_{a1}.png')

# Bandpass
#
# Simply use a scan of 3C286, which has more flux than the other source.
# In scan 2, the amplitudes in spw1 decrease in a strange way mid-scan, so
# we use scan 3 instead.

# The phase has already been calibrated by the delay engine and is stable enough
# over a 20 minute interval, so we don't need to calibrate it. Amplitudes are
# somewhat dissimilar over all the antennas, so we perform an amplitude
# calibration before the bandpass.

rmtables('uvh5_60247.G0')
gaincal(vis=vis, caltable='uvh5_60247.G0',
        refant=REFANT, refantmode='strict',
        scan='2', solint='inf', calmode='a')

# Get a gain calibration for the other source, for gain cal with Stokes later
gaincal(vis=vis, caltable='uvh5_60247_1256_057.G0',
        refant=REFANT, refantmode='strict',
        scan='3', solint='inf', calmode='a')

# This may fail--get bandpass solution with bright calibrator, pol with other
rmtables('uvh5_60247.B0')
bandpass(vis=vis, caltable='uvh5_60247.B0',
         refant=REFANT,
         scan='2', solint='inf',
         bandtype='B', gaintable=['uvh5_60247.G0'])

# Complex gain calibration for 1256_057
#
# This absorbs the polarization signature on the parallel-hands

rmtables('uvh5_60247_1256_057.field0.G1')
gaincal(vis=vis, caltable='uvh5_60247_1256_057.field1.G1',
        refant=REFANT, refantmode='strict', solint='300',
        calmode='ap', field='1',
        gaintable=['uvh5_60247.B0', 'uvh5_60247_1256_057.G0'])

# Estimate of QU from parallel-hands amplitude (contained in the cal table)

qu_field1 = polfromgain(vis=vis, tablein='uvh5_60247_1256_057.field1.G1')

# New complex gain calibration for 1256-057 using Stokes parameters estimated from
# gain amplitudes. This does not absorb the polarization signature.

rmtables('uvh5_60247_1256_057.field1.G2')
gaincal(vis=vis, caltable='uvh5_60247_1256_057.field1.G2',
        refant=REFANT, refantmode='strict', solint='300',
        calmode='ap', field='1', smodel=qu_field1['1256-057']['Spw1'],
        parang=True,
        gaintable=['uvh5_60247.B0', 'uvh5_60247_1256_057.G0'])

# By looking at the XX and YY amplitudes once B0, G0, G2 are applied, we see
# that in scan 11 the XX and YY amplitudes cross, which means that at that point
# the polarized signal in the cross-hands is maximum. That is the best scan
# to examine the cross-hands and calibrate Kcross.

# Spectral window 0 is too tricky to calibrate because there is a lot of RFI

# Spectral window 1 also has some problems. If we do
#
# applycal(vis=vis, gaintable=['uvh5_60247.B0', 'uvh5_60247.G0', 'uvh5_60247.field0.G2'],
#          field='0')
# plotms(vis=vis, ydatacolumn='corrected', xdatacolumn='corrected',
#        xaxis='channel', yaxis='phase', avgtime='10000', coloraxis='corr',
#        iteraxis='scan', avgbaseline=True, field='0', gridcols=4, gridrows=3, spw='1')
#
# we see that the lower channels' cross-hands phase is all over the place.
# For some unknown reason. We ignore the channels below 50 in polarization
# calibration.

polcal_spw = '1:50~167'

# Cross-hand delay calibration
#
# It turns out that the cross-hand delay is on the order of 10 ns, so it needs
# to be calibrated. (Why is it so large?)
rmtables('uvh5_60247.Kcross0')
gaincal(vis=vis, caltable='uvh5_60247_1256_057.Kcross0',
        scan='10', spw=polcal_spw,
        gaintype='KCROSS', solint='inf',
        refant=REFANT, refantmode='strict',
        smodel=[1,0,1,0],
        gaintable=['uvh5_60247.B0', 'uvh5_60247_1256_057.G0', 'uvh5_60247_1256_057.field1.G2'],
        interp=['nearest','nearest', 'nearest'])

# Determination of XY phase offset and source QU
#
# Use Stokes parameters from spw1 because it has much less RFI than Spw0
# (although the two Stokes parameters are very close)
#
# Note: the Stokes parameters returned by this are not very good, but
# the Xparang table looks somewhat reasonable.

rmtables('uvh5_60247.Xfparang')
S_field1 = polcal(vis=vis, caltable='uvh5_60247_1256_057.Xfparang',
                  field='1', spw=polcal_spw,
                  solint='inf', combine='scan', preavg=300,
                  smodel=qu_field1['1256-057']['Spw1'], poltype='Xfparang+QU',
                  gaintable=['uvh5_60247.B0', 'uvh5_60247_1256_057.G0', 'uvh5_60247_1256_057.field1.G2',
                             'uvh5_60247_1256_057.Kcross0'])

# Determination of leakage terms
#
# Note: The Stokes parameters coming from polcal() are not good enough to do this.
# If we use them, the leakage solution gets heavily contaminated by the polarization
# signature. Instead we use the Stokes parameters from polfromgain().

rmtables('uvh5_60247.D0')
polcal(vis=vis, caltable='uvh5_60247_1256_057.D0',
       field='1', spw=polcal_spw,
       solint='inf', combine='scan', preavg=300,
       smodel=qu_field1['1256-057']['Spw1'], poltype='Dflls',
       refant='',
       gaintable=['uvh5_60247.B0', 'uvh5_60247_1256_057.G0', 'uvh5_60247_1256_057.field1.G2',
                  'uvh5_60247_1256_057.Kcross0', 'uvh5_60247_1256_057.Xfparang'])

# Try to obtain Stokes parameters from cross-hands again,
# now with D-terms removed.
#
# Note: the results look quite similar to the previous attempt. The
# returned Stokes parameters are still bad.

rmtables('uvh5_60247.Xfparang1')
S_field1 = polcal(vis=vis, caltable='uvh5_60247_1256_057.Xfparang1',
                  field='1', spw=polcal_spw,
                  solint='inf', combine='scan', preavg=300,
                  smodel=qu_field1['1256-057']['Spw1'], poltype='Xfparang+QU',
                  gaintable=['uvh5_60247.B0', 'uvh5_60247_1256_057.G0', 'uvh5_60247_1256_057.field1.G2',
                             'uvh5_60247_1256_057.Kcross0', 'uvh5_60247_1256_057.D0'])

# Apply calibrations for evaluation

applycal(vis=vis,
         gaintable=['uvh5_60247.B0', 'uvh5_60247_1256_057.G0', 'uvh5_60247_1256_057.field1.G2',
                    'uvh5_60247_1256_057.Kcross0', 'uvh5_60247_1256_057.Xfparang1', 'uvh5_60247_1256_057.D0'],
         field='1', parang=True)

# Evalution plots

for ax in ['real', 'imag']:
    plotms(vis=vis, ydatacolumn='corrected', xaxis='parang', yaxis=ax,
           coloraxis='corr', field='1', avgchannel='168', spw=polcal_spw,
           plotfile=f'1256-057_parang_corrected_{ax}_vs_parang.png', overwrite=True)

    plotms(vis=vis, ydatacolumn='corrected', xaxis='freq', yaxis=ax,
           coloraxis='corr', field='1', avgtime='100000', avgscan=True, spw='1',
           plotfile=f'1256-057_parang_corrected_{ax}_vs_freq.png', overwrite=True)

plotms(vis=vis, xdatacolumn='corrected', ydatacolumn='corrected',
       xaxis='real', yaxis='imag', coloraxis='corr', field='1',
       avgtime='100000', avgscan=True, avgchannel='168', spw=polcal_spw,
       plotfile='1256-057_parang_corrected_reim.png')

# Calibration table plots

for ax in ['amp', 'phase']:
    plotms(vis=f'uvh5_60247_1256_057.B0', xaxis='freq', yaxis=f'gain{ax}',
           coloraxis='corr', iteraxis='antenna', gridrows=4, gridcols=5,
           yselfscale=True, antenna=antenna_list, spw='1',
           plotfile=f'B0_{ax}.png', overwrite=True)

plotms(vis='uvh5_60247_1256_057.G0', xaxis='antenna1', yaxis='gainamp',
       coloraxis='corr', antenna=antenna_list, spw='1',
       plotfile='G0_amp.png', overwrite=True)

for j in [1, 2]:
    for ax in ['amp', 'phase']:
        plotms(vis=f'uvh5_60247_1256_057.field1.G{j}', xaxis='time', yaxis=f'gain{ax}',
               coloraxis='corr', iteraxis='antenna', gridrows=4, gridcols=5,
               yselfscale=True, antenna=antenna_list, spw='1',
               plotfile=f'G{j}_field1_{ax}.png', overwrite=True)

plotms(vis='uvh5_60247_1256_057.Kcross0', yaxis='delay', spw='1',
       antenna=REFANT, coloraxis='corr',
       plotfile=f'Kcross0.png', overwrite=True)

for xf in ['Xfparang', 'Xfparang1']:
    plotms(vis=f'uvh5_60247_1256_057.{xf}', xaxis='freq', yaxis='gainphase',
           plotfile=f'{xf}.png', overwrite=True)

for ax in ['real', 'imag']:
    plotms(vis='uvh5_60247_1256_057.D0', xaxis='freq', yaxis=ax,
           coloraxis='corr', iteraxis='antenna', gridrows=4, gridcols=5,
           yselfscale=True, antenna=antenna_list,
           plotfile=f'D0_{ax}.png', overwrite=True)
