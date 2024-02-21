#!/opt/mnt/miniconda3/bin/python

#############################################################################
# This script should be run using CASA 6.4.0.16 or higher
#############################################################################

# TODO: Reformat to run by-spectral-window to process an observation of the
# observe_3c286_pol format

# Add separate applycals for each field

# Imports
import glob
import os, sys
import glob
import subprocess
import numpy as np



#############################################################################
# Define necessary fields, load files, fix and separate scans
#############################################################################

# Targets
phase_calibrator = '1330+251'
primary_calibrator = '3c286'

# Visibility file
obs_vis = 'standard_polcal_set_6.3GHz.ms'

# Script choices
generate_plots = True
iterate_calibration = False

# CASA machinery
ref_ant = '40'
spw = '0'
pol_spw = '0'
tab_name = obs_vis.split('.')[0]

antennas = ['1b', '1c', '1e', '1g', '1h', '1k',
            '2b', '2d', '2e', '2f', '2h', '2j', '2k', '2l', '2m',
            '3d', '3l', '4e', '4j', '5e']
antenna_list = ','.join([f'"{a}"' for a in antennas])


#############################################################################
# Define useful functions
#############################################################################

# Borrowed from  MeerKAT pipeline for testing if a deliberate calculation is superior to polfromgain for known calibrator
def qu_polfield(polfield, visname):
    """
    Given the pol source name and the reference frequency, returns the fractional Q and U
    calculated from Perley & Butler 2013
    """

    msmd.open(visname)
    meanfreq = msmd.meanfreq(0, unit='MHz')
    msmd.done()

    if polfield in ["3c286", "1328+307", "1331+305", "J1331+3030"]:
        #f_coeff=[1.2515,-0.4605,-0.1715,0.0336]    # coefficients for model Stokes I spectrum from Perley and Butler 2013
        perley_frac = np.array([0.086,0.095,0.099])
        perley_f = np.array([1050,1450,1640])
        pa_polcal = np.array([33.0,33.0,33.0])
    elif polfield in ["3C138", "0518+165", "0521+166", "J0521+1638"]:
        #f_coeff=[1.0332,-0.5608,-0.1197,0.041]    # coefficients for model Stokes I spectrum from Perley and Butler 2013
        perley_frac = np.array([0.056,0.075,0.084,0.09,0.104,0.107,0.10])
        perley_f = np.array([1050,1450,1640,1950,2450,2950,3250])
        pa_polcal = np.array([-14.0,-11.0,-10.0,-10.0,-10.0,-10.0,-10.0])
    elif polfield in ["3C48", "0134+329", "0137+331", "J0137+3309"]:
        perley_frac = np.array([0.003, 0.005, 0.007])
        perley_f = np.array([1050,1450,1640])
        pa_polcal = np.array([25, 140, -5])
    elif polfield == "J1130-1449": #Manual model from Russ Taylor, taken from MeerKAT polarisation calibrator project
        perley_frac = np.array([0.038, 0.050, 0.056])
        perley_f = np.array([1050, 1450, 1640])
        pa_polcal = np.array([145, 66, 45])
    else:
        # This should never happen.
        raise ValueError("Invalid polarization field. Exiting.")

    p = np.polyfit(perley_f, perley_frac, deg=2)
    p = np.poly1d(p)

    pa = np.polyfit(perley_f, pa_polcal, deg=2)
    pa = np.poly1d(pa)

    #polpoly = np.poly1d(polcoeffs)
    #polval = polpoly(meanfreq)

    # BEWARE: Stokes I coeffs are in log-log space, so care must be taken while converting to linear.
    # They are in np.log10 space, not np.log space!
    # Coefficients are from Perley-Butler 2013 (An Accurate Flux Density Scale from 1 to 50 GHz)
    #stokesIpoly = np.poly1d(stokesIcoeffs)
    #stokesIval = stokesIpoly(np.log10(meanfreq))
    ## in Jy
    #stokesIval = np.power(10, stokesIval)

    q = p(meanfreq) * np.cos(2*np.deg2rad(pa(meanfreq)))
    u = p(meanfreq) * np.sin(2*np.deg2rad(pa(meanfreq)))

    return q, u

def calibrator_diagnostics(calibrator: str = '', image_base: str = '', cell_size: float = 0):
        ia.open(f'{image_base}_clean_iter2.image.tt0')
        maj = ia.restoringbeam()['major']['value']
        min = ia.restoringbeam()['minor']['value']
        pos = ia.restoringbeam()['positionangle']['value']
        ia.close()


        fit_name = f'./IMAGES/{calibrator}/fitting_region.crtf'
        f = open(fit_name, 'w')
        f.write('#CRTF\n')
        f.write(f'circle[[1024pix, 1024pix],{cell_size * 8. * 5.}arcsec]')
        f.close()

        est_name = f'./IMAGES/{calibrator}/estimates.txt'
        f = open(est_name, 'w')
        f.write(f'1,1024,1024,{maj}arcsec,{min}arcsec,{pos}deg,abp')
        f.close()

        fit_results = imfit(imagename=f'{image_base}_clean_iter2.image.tt0', region=fit_name, estimates=est_name)
        flux_density = fit_results['deconvolved']['component0']['flux']['value'][0]
        error = fit_results['deconvolved']['component0']['flux']['error'][0]

        fit_result_name = f'./IMAGES/{calibrator}/fitting_results.txt'
        f = open(fit_result_name, 'w')
        f.write(str(flux_density) + ',' + str(error))
        f.close()

def generate_plots(use_3c286: bool = False):
        # Plot preliminary gain amplitudes
        plotms(vis=f'{tab_name}.G0', xaxis='antenna1', yaxis='gainphase',
        coloraxis='corr', antenna=antenna_list, spw='0',
        plotfile=f'G1_{tab_name}_phase.png', overwrite=True)
        # Plot preliminary gain phases
        plotms(vis=f'{tab_name}.G1', xaxis='antenna1', yaxis='gainamp',
        coloraxis='corr', antenna=antenna_list, spw='0',
        plotfile=f'G0_{tab_name}_amp.png', overwrite=True)

        # Bandpass solutions, frequency vs amplitude and phase
        for ax in ['amp', 'phase']:
                plotms(vis=f'{tab_name}.B0', xaxis='freq', yaxis=f'gain{ax}',
                coloraxis='corr', iteraxis='antenna', gridrows=4, gridcols=5,
                yselfscale=True, antenna=antenna_list, spw='0',
                plotfile=f'B0_{tab_name}_{ax}.png', overwrite=True)

        
        # For bandpass calibrator, gain amplitude and phase
        plotms(vis=f'{tab_name}.G2', xaxis='time', yaxis=f'gainamp',
                coloraxis='corr', iteraxis='antenna', gridrows=4, gridcols=5,
                yselfscale=True, antenna=antenna_list, spw='0',
                plotfile=f'G2_{primary_calibrator}_{tab_name}_amp.png', overwrite=True)
        plotms(vis=f'{tab_name}.G2', xaxis='time', yaxis=f'gainphase',
                coloraxis='corr', iteraxis='antenna', gridrows=4, gridcols=5,
                yselfscale=True, antenna=antenna_list, spw='0',
                plotfile=f'G2_{primary_calibrator}_{tab_name}_phase.png', overwrite=True)

        if not use_3c286:
                # For phase calibrator, gain amplitude and phase
                plotms(vis=f'{tab_name}_pol.G3', xaxis='time', yaxis=f'gainamp',
                        coloraxis='corr', iteraxis='antenna', gridrows=4, gridcols=5,
                        yselfscale=True, antenna=antenna_list, spw='0',
                        plotfile=f'G3_{tab_name}_pol_amp.png', overwrite=True)
                plotms(vis=f'{tab_name}_pol.G3', xaxis='time', yaxis=f'gainphase',
                        coloraxis='corr', iteraxis='antenna', gridrows=4, gridcols=5,
                        yselfscale=True, antenna=antenna_list, spw='0',
                        plotfile=f'G3_{phase_calibrator}_{tab_name}_pol_phase.png', overwrite=True)
                
                # Plot of Kcross solutions
                plotms(vis=f'{tab_name}_pol.Kcross0', yaxis='delay', spw='0',
                        antenna=ref_ant, coloraxis='corr',
                        plotfile=f'{tab_name}_Kcross0.png', overwrite=True)
                
                for ax in ['real', 'imag']:
                                # Real and imaginary components versus parallactic angle for polarization calibrator
                                plotms(vis=f'{tab_name}_calibrated.ms', ydatacolumn='corrected', xaxis='parang', yaxis=ax,
                                        coloraxis='corr', field=primary_calibrator, avgchannel='168', spw='0',
                                        plotfile=f'{tab_name}_parang_corrected_{ax}_vs_parang.png', overwrite=True)
                                # Real and imaginary components versus frequency for polarization calibrator
                                plotms(vis=f'{tab_name}_calibrated.ms', ydatacolumn='corrected', xaxis='freq', yaxis=ax,
                                        coloraxis='corr', field=primary_calibrator, avgtime='100000', avgscan=True, spw='0',
                                        plotfile=f'{tab_name}_parang_corrected_{ax}_vs_freq.png', overwrite=True)
                # Parallactic angle-corrected real vs imaginary components for polarization calibrator
                plotms(vis=f'{tab_name}_calibrated.ms', xdatacolumn='corrected', ydatacolumn='corrected',
                        xaxis='real', yaxis='imag', coloraxis='corr', field=primary_calibrator,
                        avgtime='100000', avgscan=True, avgchannel='168', spw='0',
                        plotfile=f'{tab_name}_parang_corrected_reim.png')

        
                # Plots of phase-frequency and real/imaginary leakage terms by antenna
                plotms(vis=f'{tab_name}_pol.Xfparang', xaxis='freq', yaxis='gainphase',
                                plotfile=f'{tab_name}_freq_vs_gainphase.png', overwrite=True)

                for ax in ['real', 'imag']:
                        plotms(vis=f'{tab_name}_pol.D0', xaxis='freq', yaxis=ax,
                                        coloraxis='corr', iteraxis='antenna', gridrows=4, gridcols=5,
                                        yselfscale=True, antenna=antenna_list,
                                        plotfile=f'D0_{tab_name}_pol_{ax}.png', overwrite=True)


#############################################################################
# Begin standard calibration
#############################################################################

print("Beginning standard calibration")

print(f"Gain calibrators: {primary_calibrator, phase_calibrator}")
# FLAGGING: script assumes pre-flagging using aoflagger.
## If manual flagging desired, uncomment the below and edit to suit
flagdata(vis=obs_vis, mode='manual', antenna="'1b'", flagbackup=False)
flagdata(vis=obs_vis, mode='manual', antenna="'1e'", flagbackup=False)
# flagdata(vis=obs_vis, mode='manual', antenna="'4e'", flagbackup=False)

# Set flux model for flux calibrator 
setjy(vis=obs_vis, field=primary_calibrator, standard='Perley-Butler 2017', usescratch=True)

# Listobs
listobs(vis=obs_vis)

print("Preliminary gaincal")
# Preliminary gaincal
# This will be thrown away after solving for delay and bandpass
gaincal(vis=obs_vis, caltable=f'{tab_name}.G0', field=primary_calibrator, spw=spw, refant=ref_ant, refantmode='strict', calmode='p', 
        solint='inf', parang=True, minsnr=0, minblperant=1)
gaincal(vis=obs_vis, caltable=f'{tab_name}.G1', field=primary_calibrator, spw=spw, refant=ref_ant, refantmode='strict', calmode='a', 
        solint='100', preavg=1, minblperant=1, minsnr=0, gaintype='G', gaintable=[f'{tab_name}.G0'], parang=True)

print("Delay calibration")
# Delay calibration
gaincal(vis=obs_vis, caltable=f'{tab_name}.K0', field=primary_calibrator, spw=spw, refant=ref_ant, solint='inf', combine='scan', 
        preavg=1, minsnr=0, minblperant=1, gaintype='K', gaintable=[f'{tab_name}.G0', f'{tab_name}.G1'], parang=True)

print("Bandpass calibration")
# Bandpass
# NOTE: low freq spectral windows so we'll use a small averaging window, may be appropriate to allow edit
bandpass(vis=obs_vis, caltable=f'{tab_name}.B0', field=primary_calibrator, spw=spw, refant=ref_ant,
         bandtype='B', gaintable=[f'{tab_name}.G0', f'{tab_name}.G1', f'{tab_name}.K0'], parang=True, minsnr=0, minblperant=1)

# For fluxscale to work, we need a gain table with flux cal field and other gain calibrators both present
# Gaintype T to preserve the relative gains of XY feeds, needs testing
print("Second round gain calibration")
gaincal(vis=obs_vis, caltable=f'{tab_name}.G2', field=f'{primary_calibrator},{phase_calibrator}', spw=spw, refant=ref_ant, calmode='ap', solint='300', 
        gaintype='G', minsnr=0, gaintable=[f'{tab_name}.K0', f'{tab_name}.B0', f'{tab_name}.G0', f'{tab_name}.G1'], parang=True, minblperant=1)

# # Fluxscale if bootstrapping
# if len(gain_calibrators.split(',')) > 1:
#         fluxscale(vis=obs_vis, caltable=f"{tab_name}.G2", fluxtable=f'{tab_name}.fluxscale', reference=bandpass_calibrator, transfer=[phase_calibrator])

#############################################################################
# Polarization calibration
#############################################################################

# Re-calibrate the polarization calibrator, allowing the gains to absorb the parallactic 
# angle variation so that we can use it to calculate the polarization calibrator Stokes model'
# Set flux model for flux calibrator 
setjy(vis=obs_vis, field=primary_calibrator, standard='Perley-Butler 2017', usescratch=True)

# print(f"polarization calibrator {primary_calibrator}")
gaincal(vis=obs_vis, caltable=f'{tab_name}.G3', field=primary_calibrator, spw=pol_spw, refant=ref_ant, solint='120', 
        gaintype='G',gaintable=[f'{tab_name}.K0', f'{tab_name}.B0', f'{tab_name}.G2'])

# # Calculate Stokes model from gains
qu_model = polfromgain(vis=obs_vis, tablein=f'{tab_name}.G3')
print(f"Stokes model calculated from gains: {qu_model}")

# NOTE: TESTING MEERKAT METHOD OF DIRECLTY CALCULATING QU MODEL. WILL THIS DO BETTER?
polqu = qu_polfield(primary_calibrator, visname=obs_vis)
print(polqu)

# Redo gaincal with Stokes model; this does not absorb polarization signal
gaincal(vis=obs_vis, caltable=f'{tab_name}_pol.G3', refant=ref_ant, refantmode='strict', solint='120', calmode='ap', spw=spw,
        field=primary_calibrator, smodel=qu_model[primary_calibrator]['Spw0'], parang=True, gaintype='G',
        gaintable=[f'{tab_name}.K0', f'{tab_name}.B0', f'{tab_name}.G2'])

# Redo Stokes model to check for residual gains; should be close to zero
qu_model_calibrated = polfromgain(vis=obs_vis, tablein=f'{tab_name}_pol.G3')
print(f"Stokes model calculated from gains corrected for Stokes model: {qu_model_calibrated}")

# Best scan to calibrate cross-hands will be where the polarization signal is 
# minimum in XX and YY (i.e., maximum in XY and YX); find the scan using the
# gain calibration for the phase/polarization calibrator
# This code taken from ALMA pipeline
tb.open(f'{tab_name}.G3')
scans = tb.getcol('SCAN_NUMBER')
gains = np.squeeze(tb.getcol('CPARAM'))
tb.close()
scan_list = np.array(list(set(scans)))
ratios = np.zeros(len(scan_list))
for si, s in enumerate(scan_list):
        filt = scans == s
        ratio = np.sqrt(np.average(np.power(np.abs(gains[0,filt])/np.abs(gains[1,filt])-1.0,2.)))
        ratios[si] = ratio

best_scan_index = np.argmin(ratios)
best_scan = scan_list[best_scan_index]
print(f"Scan with highest expected X-Y signal: {best_scan}")

# Kcross calibration
gaincal(vis=obs_vis, caltable=f'{tab_name}_pol.Kcross0', spw=pol_spw, refant=ref_ant, solint='inf', 
        field=primary_calibrator, gaintype='KCROSS', scan=str(best_scan), smodel=[1, 0, 1, 0], calmode='ap', 
        minblperant=1, refantmode='strict', parang=True)
        
# Solve for the apparent cross-hand phase spectrum (channelized) fractional linear polarization, Q, U
# Note that CASA calculates a Stokes model for the source in this step as well, but it will be incorrect!
# The X-Y phase offset table generated here seems to be accurate
S_model = polcal(vis=obs_vis, caltable=f'{tab_name}_pol.Xfparang',
                field=primary_calibrator, spw=pol_spw,
                solint='inf', combine='scan', preavg=120,
                smodel=qu_model[primary_calibrator]['Spw0'], poltype='Xfparang+QU',
                gaintable=[f'{tab_name}.B0', f'{tab_name}.G2', f'{tab_name}_pol.G3',
                        f'{tab_name}_pol.Kcross0'], 
                gainfield=[primary_calibrator, primary_calibrator, primary_calibrator, 
                           primary_calibrator])

print(f'Stokes parameters from Xfparang: {S_model}')
# Solve for leakage terms
polcal(vis=obs_vis, caltable=f'{tab_name}_pol.D0', field=primary_calibrator, spw=pol_spw, solint='inf', combine='scan', preavg=120,
        smodel=qu_model[primary_calibrator]['Spw0'], poltype='Dflls', refant='', 
        gaintable=[f'{tab_name}.B0', f'{tab_name}.G2', f'{tab_name}_pol.G3', f'{tab_name}_pol.Kcross0', 
                        f'{tab_name}_pol.Xfparang'])

# Apply the tables
kcross = f'{tab_name}_pol.Kcross0'
Xfparang = f'{tab_name}_pol.Xfparang'
leakage = f'{tab_name}_pol.D0'


#############################################################################
# Apply calibration
#############################################################################


applycal(vis=obs_vis, field=primary_calibrator,
                selectdata=False, calwt=False, gaintable=[f'{tab_name}.K0', f'{tab_name}.G2',f'{tab_name}_pol.G3', f'{tab_name}.B0', kcross, Xfparang, leakage],
                gainfield=[primary_calibrator, '', primary_calibrator, primary_calibrator, primary_calibrator, primary_calibrator, primary_calibrator],
                parang=True, interp='nearest,linearflag,nearest,nearest,nearest,nearest,nearest')

# Save out a calibrated measurement set
split(vis=obs_vis, outputvis=f'{tab_name}_calibrated.ms', datacolumn='corrected')


generate_plots(use_3c286=False)