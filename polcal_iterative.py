#!/usr/bin/env python3

#############################################################################
# This script should be run using CASA 6.4.0.16 or higher
#############################################################################

# TODO:
# Add in provision for length of pol cal scans?
# Test iterative calibration and allow re-calibrated ms to be used for imaging
# Stokes maps
# Make a list of if_dosteps instead

# Add separate applycals for each field

# Imports
import glob
import os, sys
import glob
import subprocess
import numpy as np

#############################################################################
# Fields for user to edit per-observation
#############################################################################

# bandpass_calibrator = '3c147'
# phase_calibrator = '2343+538'
# target = 'CasA'
bandpass_calibrator = '3c286'
phase_calibrator = '1804+010'
# phase_calibrator = '3c286'
polarization_calibrator = '3c286'
target = '3c391'
# target = '3c286'
ref_ant = '40'
spw = '0'
pol_spw = '0:40~167'              # Measurement set should have only one spectral window, 
                                  # use to constrain bandpass used for polcal
# obs_vis = 'CasA_obs.ms'
obs_vis = '3c391_obs.ms'

use_3c286 = False
generate_plots = True
iterate_calibration = False
do_image = True

tab_name = obs_vis.split('.')[0]

polcal_table_dir = '/mnt/buf0/cchoza/pol_data/CasA_cal_imaging/CasA_cal_imaging'

antennas = ['1b', '1c', '1e', '1g', '1h', '1k',
            '2b', '2d', '2e', '2f', '2h', '2j', '2k', '2l', '2m',
            '3d', '3l', '4e', '4j', '5e']
antenna_list = ','.join([f'"{a}"' for a in antennas])


#############################################################################
# Define useful functions
#############################################################################

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
                plotfile=f'G2_{bandpass_calibrator}_{tab_name}_amp.png', overwrite=True)
        plotms(vis=f'{tab_name}.G2', xaxis='time', yaxis=f'gainphase',
                coloraxis='corr', iteraxis='antenna', gridrows=4, gridcols=5,
                yselfscale=True, antenna=antenna_list, spw='0',
                plotfile=f'G2_{bandpass_calibrator}_{tab_name}_phase.png', overwrite=True)

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
        
                # Plots of phase-frequency and real/imaginary leakage terms by antenna
                plotms(vis=f'{tab_name}_pol.Xfparang', xaxis='freq', yaxis='gainphase',
                                plotfile=f'{tab_name}_freq_vs_gainphase.png', overwrite=True)

                for ax in ['real', 'imag']:
                        plotms(vis=f'{tab_name}_pol.D0', xaxis='freq', yaxis=ax,
                                        coloraxis='corr', iteraxis='antenna', gridrows=4, gridcols=5,
                                        yselfscale=True, antenna=antenna_list,
                                        plotfile=f'D0_{tab_name}_pol_{ax}.png', overwrite=True)
                                
                for ax in ['real', 'imag']:
                                # Real and imaginary components versus parallactic angle for polarization calibrator
                        plotms(vis=f'{tab_name}_calibrated.ms', ydatacolumn='corrected', xaxis='parang', yaxis=ax,
                                coloraxis='corr', field=polarization_calibrator, avgchannel='168', spw='0',
                                plotfile=f'{tab_name}_parang_corrected_{ax}_vs_parang.png', overwrite=True)
                        # Real and imaginary components versus frequency for polarization calibrator
                        plotms(vis=f'{tab_name}_calibrated.ms', ydatacolumn='corrected', xaxis='freq', yaxis=ax,
                                coloraxis='corr', field=polarization_calibrator, avgtime='100000', avgscan=True, spw='0',
                                plotfile=f'{tab_name}_parang_corrected_{ax}_vs_freq.png', overwrite=True)
                        # Parallactic angle-corrected real vs imaginary components for polarization calibrator
                plotms(vis=f'{tab_name}_calibrated.ms', xdatacolumn='corrected', ydatacolumn='corrected',
                        xaxis='real', yaxis='imag', coloraxis='corr', field=polarization_calibrator,
                        avgtime='100000', avgscan=True, avgchannel='168', spw='0',
                        plotfile=f'{tab_name}_parang_corrected_reim.png')


#############################################################################
# Begin standard calibration
#############################################################################

print("Beginning standard calibration")
# If polarization_calibrator left as blank string, default pol cal to phase cal        
if polarization_calibrator == '':
                polarization_calibrator = phase_calibrator 
    
# If phase calibrator passed, include both as gain fields; otherwise, use only bandpass/primary
if phase_calibrator != bandpass_calibrator:
        gain_calibrators = f"{bandpass_calibrator},{phase_calibrator}"
else:
        gain_calibrators = f'{bandpass_calibrator}'

print(f"Gain calibrators: {gain_calibrators}")
# FLAGGING: script assumes pre-flagging using aoflagger.
## If manual flagging desired, uncomment the below and edit to suit
flagdata(vis=obs_vis, mode='manual', antenna="'1b'", flagbackup=False)
flagdata(vis=obs_vis, mode='manual', antenna="'1e'", flagbackup=False)
# flagdata(vis=obs_vis, mode='manual', antenna="'4e'", flagbackup=False)
flagdata(vis=obs_vis, field=target, mode='tfcrop', datacolumn='DATA')
flagdata(vis=obs_vis, field=target, mode='rflag', datacolumn='DATA')

# Set flux model for flux calibrator 
setjy(vis=obs_vis, field=bandpass_calibrator, standard='Perley-Butler 2017', usescratch=True)

# Listobs
listobs(vis=obs_vis)

print("Preliminary gaincal")
# Preliminary gaincal
# This will be thrown away after solving for delay and bandpass
gaincal(vis=obs_vis, caltable=f'{tab_name}.G0', field=bandpass_calibrator, spw=spw, refant=ref_ant, refantmode='strict', calmode='p', 
        solint='inf', parang=True)
gaincal(vis=obs_vis, caltable=f'{tab_name}.G1', field=bandpass_calibrator, spw=spw, refant=ref_ant, refantmode='strict', calmode='a', 
        solint='100', preavg=1, minblperant=1, minsnr=0, gaintype='G', gaintable=[f'{tab_name}.G0'], parang=True)

print("Delay calibration")
# Delay calibration
gaincal(vis=obs_vis, caltable=f'{tab_name}.K0', field=bandpass_calibrator, spw=spw, refant=ref_ant, solint='inf', combine='scan', 
        preavg=1, minblperant=1, gaintype='K', gaintable=[f'{tab_name}.G0', f'{tab_name}.G1'], parang=True)

print("Bandpass calibration")
# Bandpass
# NOTE: low freq spectral windows so we'll use a small averaging window, may be appropriate to allow edit
bandpass(vis=obs_vis, caltable=f'{tab_name}.B0', field=bandpass_calibrator, spw=spw, refant=ref_ant,
         bandtype='B', gaintable=[f'{tab_name}.G0', f'{tab_name}.G1', f'{tab_name}.K0'], parang=True)

# For fluxscale to work, we need a gain table with flux cal field and other gain calibrators both present
# Gaintype T to preserve the relative gains of XY feeds, needs testing
print("Second round gain calibration")
gaincal(vis=obs_vis, caltable=f'{tab_name}.G2', field=gain_calibrators, spw=spw, refant=ref_ant, calmode='ap', solint='300', 
        gaintype='G', minsnr=0, gaintable=[f'{tab_name}.K0', f'{tab_name}.B0'], parang=True)

# # Fluxscale if bootstrapping
# if len(gain_calibrators.split(',')) > 1:
#         fluxscale(vis=obs_vis, caltable=f"{tab_name}.G2", fluxtable=f'{tab_name}.fluxscale', reference=bandpass_calibrator, transfer=[phase_calibrator])

#############################################################################
# Polarization calibration
#############################################################################

## Use 3c286
if use_3c286:

       # Fetch and move the tables to this directory
        kcross_path = glob.glob(f'{polcal_table_dir}/*.Kcross0')[0]
        Xfparang_path = glob.glob(f'{polcal_table_dir}/*.Xfparang')[0]
        leakage_path = glob.glob(f'{polcal_table_dir}/*.D0')[0]

        print(kcross_path)
        print(Xfparang_path)
        print(leakage_path)

        test = subprocess.Popen(["cp", '-r', kcross_path, '.'])
        test2 = subprocess.Popen(["cp", '-r', Xfparang_path, '.'])
        test3 = subprocess.Popen(["cp", '-r', leakage_path, '.'])

        # Apply the tables
        kcross = kcross_path.split('/')[-1]
        Xfparang = Xfparang_path.split('/')[-1]
        leakage = leakage_path.split('/')[-1]

### Try on the fly with a strongly polarized calibrator
else:
        # Re-calibrate the polarization calibrator, allowing the gains to absorb the parallactic 
        # angle variation so that we can use it to calculate the polarization calibrator Stokes model'
        # Set flux model for flux calibrator 
        setjy(vis=obs_vis, field=polarization_calibrator, standard='Perley-Butler 2017', usescratch=True)

        print(f"polarization calibrator {polarization_calibrator}")
        # gaincal(vis=obs_vis, caltable=f'{tab_name}.G3', field=polarization_calibrator, spw=spw, refant=ref_ant, calmode='ap', solint='300', 
        #         gaintype='G', minsnr=0, gaintable=[f'{tab_name}.K0', f'{tab_name}.B0', f'{tab_name}.G2'])
        gaincal(vis=obs_vis, caltable=f'{tab_name}.G3', field=polarization_calibrator, spw=spw, refant=ref_ant, solint='300', 
                gaintype='G',gaintable=[f'{tab_name}.K0', f'{tab_name}.B0', f'{tab_name}.G2'])

        # Calculate Stokes model from gains
        qu_model = polfromgain(vis=obs_vis, tablein=f'{tab_name}.G3')
        print(f"Stokes model calculated from gains: {qu_model}")

        # Redo gaincal with Stokes model; this does not absorb polarization signal
        gaincal(vis=obs_vis, caltable=f'{tab_name}_pol.G3', refant=ref_ant, refantmode='strict', solint='300', calmode='ap', spw=spw,
                field=polarization_calibrator, smodel=qu_model[polarization_calibrator]['Spw0'], parang=True, gaintype='G',
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
               field=polarization_calibrator, gaintype='KCROSS', scan=str(best_scan), smodel=[1, 0, 1, 0], calmode='ap', 
               minblperant=1, refantmode='strict', parang=True)
               
        # Solve for the apparent cross-hand phase spectrum (channelized) fractional linear polarization, Q, U
        # Note that CASA calculates a Stokes model for the source in this step as well, but it will be incorrect!
        # The X-Y phase offset table generated here seems to be accurate
        S_model = polcal(vis=obs_vis, caltable=f'{tab_name}_pol.Xfparang',
                  field=polarization_calibrator, spw=pol_spw,
                  solint='inf', combine='scan', preavg=300,
                  smodel=qu_model[polarization_calibrator]['Spw0'], poltype='Xfparang+QU',
                  gaintable=[f'{tab_name}.B0', f'{tab_name}.G2', f'{tab_name}_pol.G3',
                             f'{tab_name}_pol.Kcross0'])
                             
        # Solve for leakage terms
        polcal(vis=obs_vis, caltable=f'{tab_name}_pol.D0', field='0', spw=pol_spw, solint='inf', combine='scan', preavg=300,
              smodel=qu_model[polarization_calibrator]['Spw0'], poltype='Dflls', refant='', 
              gaintable=[f'{tab_name}.B0', f'{tab_name}.G2', f'{tab_name}_pol.G3', f'{tab_name}_pol.Kcross0', 
                         f'{tab_name}_pol.Xfparang'])
        
        # Apply the tables
        kcross = f'{tab_name}_pol.Kcross0'
        Xfparang = f'{tab_name}_pol.Xfparang'
        leakage = f'{tab_name}_pol.D0'


#############################################################################
# Apply calibration
#############################################################################

# What do we need to do here? 
if use_3c286:
        # applycal(vis=obs_vis, gaintable=[f'{tab_name}.K0', f'{tab_name}.B0', f'{tab_name}.G2', kcross, Xfparang, leakage], parang=True)

        print("Applying calibration: primary calibrator")
        applycal(vis=obs_vis, field=bandpass_calibrator,
                selectdata=False, calwt=False, gaintable=[f'{tab_name}.K0', f'{tab_name}.G2', f'{tab_name}.B0', kcross, Xfparang, leakage],
                gainfield=[bandpass_calibrator, bandpass_calibrator, bandpass_calibrator, '', '', ''],
                parang=True, interp='nearest,linearflag,nearest,nearest,nearest,nearest')
        
        print("Applying calibration: phase calibrator and target")
        fields = ','.join(set(i for i in [phase_calibrator, polarization_calibrator, target] if i != ''))
        applycal(vis=obs_vis, field=fields,
                selectdata=False, calwt=False, gaintable=[f'{tab_name}.K0', f'{tab_name}.G2', f'{tab_name}.B0', kcross, Xfparang, leakage],
                gainfield=[bandpass_calibrator, phase_calibrator, bandpass_calibrator, '', '', ''],
                parang=True, interp='nearest,linearflag,nearest,nearest,nearest,nearest')

        split(obs_vis, outputvis=f'{tab_name}_calibrated.ms', datacolumn='corrected')


else:
        # applycal(vis=obs_vis, gaintable=[f'{tab_name}.K0', f'{tab_name}.B0', f'{tab_name}.G2', kcross, Xfparang, leakage], parang=True)

        print("Applying calibration: primary calibrator")
        applycal(vis=obs_vis, field=bandpass_calibrator,
                selectdata=False, calwt=False, gaintable=[f'{tab_name}.K0', f'{tab_name}.G2', f'{tab_name}.B0', kcross, Xfparang, leakage],
                gainfield=[bandpass_calibrator, bandpass_calibrator, bandpass_calibrator, polarization_calibrator, polarization_calibrator, polarization_calibrator],
                parang=True, interp='nearest,linearflag,nearest,nearest,nearest,nearest')
        
        if polarization_calibrator != phase_calibrator:
                print("Applying calibration: polarization calibrator")
                applycal(vis=obs_vis, field=polarization_calibrator,
                        selectdata=False, calwt=False, gaintable=[f'{tab_name}.K0', f'{tab_name}.G2', f'{tab_name}_pol.G3', f'{tab_name}.B0', kcross, Xfparang, leakage],
                        gainfield=[bandpass_calibrator, polarization_calibrator, polarization_calibrator, bandpass_calibrator, polarization_calibrator, polarization_calibrator, polarization_calibrator],
                        parang=True, interp='nearest,linearflag,nearest,nearest,nearest,nearest,nearest')
                
        print("Applying calibration: phase calibrator and target")
        fields = ','.join(set(i for i in [phase_calibrator, target] if i != ''))
        applycal(vis=obs_vis, field=fields,
                selectdata=False, calwt=False, gaintable=[f'{tab_name}.K0', f'{tab_name}.G2', f'{tab_name}.B0', kcross, Xfparang, leakage],
                gainfield=[bandpass_calibrator, phase_calibrator, bandpass_calibrator, polarization_calibrator, polarization_calibrator, polarization_calibrator],
                parang=True, interp='nearest,linearflag,nearest,nearest,nearest,nearest')

        # Save out a calibrated measurement set
        split(vis=obs_vis, outputvis=f'{tab_name}_calibrated.ms', datacolumn='corrected')


generate_plots(use_3c286=use_3c286)

#############################################################################
# Iterate calibration
#############################################################################

if iterate_calibration:
        # Could allow repeating multiple times
        if use_3c286:
                # If using 3c286, this could be done from the start; pass for now
                pass
        else:
                # Begin gain calibration again on the uncorrected bandpass calibrator, using previous info
                # Include best previous gain tables here?
                gaincal(vis=obs_vis, caltable=f'{tab_name}.G0i', field=bandpass_calibrator, spw='0', refant=ref_ant, refantmode='strict', calmode='p', 
                        solint='inf', gaintable=[leakage], parang=True)
                gaincal(vis=obs_vis, caltable=f'{tab_name}.G1i', field=bandpass_calibrator, spw='0', refant=ref_ant, refantmode='strict', calmode='a', 
                        solint='100', preavg=1, minblperant=1, minsnr=0, gaintype='G', gaintable=[f'{tab_name}.G0i', leakage], parang=True)

                # Redo delays
                gaincal(vis=obs_vis, caltable=f'{tab_name}.K0i', field=bandpass_calibrator, spw='0', refant=ref_ant, solint='inf', combine='scan', 
                        preavg=1, minblperant=1, gaintype='K', gaintable=[f'{tab_name}.G0i', f'{tab_name}.G1i', kcross], parang=True)

                # Redo bandpass with the new gain, delays, and leakage
                bandpass(vis=obs_vis, caltable=f'{tab_name}.B0i', field=bandpass_calibrator, spw='0', refant=ref_ant,
                        bandtype='B', gaintable=[f'{tab_name}.G0i', f'{tab_name}.G1i', f'{tab_name}.K0i', leakage], parang=True)

                # Redo gain with new preliminary gain, bandpass, delays, leakage
                gaincal(vis=obs_vis, caltable=f'{tab_name}.G2i', field=bandpass_calibrator, spw='0', refant=ref_ant, calmode='ap', solint='300', 
                        gaintable=[f'{tab_name}.K0i', f'{tab_name}.B0i', leakage, f'{tab_name}.G0i', f'{tab_name}.G1i', ], parang=True)
                
                # Redo phase calibrator gain absorbing parallactic angle contribution
                gaincal(vis=obs_vis, caltable=f'{tab_name}.G3i', field=phase_calibrator, spw='0', refant=ref_ant, calmode='ap', solint='300', 
                        gaintable=[f'{tab_name}.K0i', f'{tab_name}.B0i', f'{tab_name}.G2i', leakage, f'{tab_name}.G0i', f'{tab_name}.G1i'])

                # Redo Stokes model from gains
                qu_model_i = polfromgain(vis=obs_vis, tablein=f'{tab_name}.G3i')

                # Redo phase calibrator gain with new model and all previous tables
                gaincal(vis=obs_vis, caltable=f'{tab_name}_pol.G3i', refant=ref_ant, refantmode='strict', solint='300', calmode='ap', 
                        field=phase_calibrator, smodel=qu_model_i[phase_calibrator]['Spw0'], parang=True, gaintable=[f'{tab_name}.K0i', f'{tab_name}.B0i', f'{tab_name}.G2i', 
                        leakage, f'{tab_name}.G0i', f'{tab_name}.G1i'])

                # Redo X-Y phase offsets now that the full calibration has been repeated with an estimate of instrumental polarization
        
                # Kcross
                gaincal(vis=obs_vis, caltable=f'{tab_name}_pol.Kcross0i', spw='0', refant=ref_ant, solint='inf', 
                        field=phase_calibrator, gaintype='KCROSS', combine='scan', smodel=[1, 0, 1, 0], calmode='ap', 
                        minblperant=1, refantmode='strict', parang=True)

                # X-Y phase offsets
                S_model = polcal(vis=obs_vis, caltable=f'{tab_name}_pol.Xfparangi',
                        field=phase_calibrator, spw='0',
                        solint='inf', combine='scan', preavg=300,
                        smodel=qu_model[phase_calibrator]['Spw0'], poltype='Xfparang+QU',
                        gaintable=[f'{tab_name}.B0i', f'{tab_name}.G0i', f'{tab_name}.G1i', f'{tab_name}.G2i', f'{tab_name}_pol.G3i',
                                f'{tab_name}_pol.Kcross0i', leakage])

                # Redo leakage calibration with self-calibrated tables
                polcal(vis=obs_vis, caltable=f'{tab_name}_pol.D0i', field='0', spw='0', solint='inf', combine='scan', preavg=300,
                        smodel=qu_model[phase_calibrator]['Spw0'], poltype='Dflls', refant='', 
                        gaintable=[f'{tab_name}.B0i', f'{tab_name}.G0i', f'{tab_name}.G1i' f'{tab_name}.G2i', f'{tab_name}_pol.G3i',f'{tab_name}_pol.Kcross0i', 
                                f'{tab_name}_pol.Xfparangi'])

                # Apply new calculations
                kcross = f'{tab_name}_pol.Kcross0i'
                Xfparang = f'{tab_name}_pol.Xfparangi'
                leakage = f'{tab_name}_pol.D0i'

                applycal(vis=obs_vis, gaintable=[f'{tab_name}.K0', f'{tab_name}.B0', f'{tab_name}.G2', f'{tab_name}_pol.G3', 
                        kcross, Xfparang, leakage], parang=True)

                # Save out a calibrated measurement set
                split(vis=obs_vis, outputvis=f'{tab_name}_pol_cal_i.ms', datacolumn='corrected')


#############################################################################
# Imaging
#############################################################################

if do_image:
        # Pick calibrated ms to use
        if iterate_calibration:
                calibrated_vis = f'{tab_name}_calibrated_i.ms'
        else:
                calibrated_vis = f'{tab_name}_calibrated.ms'
        
        # Split out bandpass_calibrator, phase_calibrator, target
        mstransform(vis=calibrated_vis, outputvis=f"{bandpass_calibrator}_calibrated.ms", antenna='!*&&&', field=bandpass_calibrator, datacolumn='DATA')
        mstransform(vis=calibrated_vis, outputvis=f"{phase_calibrator}_calibrated.ms", antenna='!*&&&', field=phase_calibrator, datacolumn='DATA')
        mstransform(vis=calibrated_vis, outputvis=f"{target}_calibrated.ms", antenna='!*&&&', field=target, datacolumn='DATA')

        # Get maximum baseline
        tb.open(obs_vis)
        B_max = np.max(np.sqrt(tb.getcol('UVW')[0]**2 + tb.getcol('UVW')[1]**2 + tb.getcol('UVW')[2]**2))
        tb.close()

        # Get maximum frequency
        tb.open(f"{obs_vis}/SPECTRAL_WINDOW/")
        nu_max = np.max(tb.getcol('REF_FREQUENCY'))
        tb.close()

        # Calculate cell size
        cell = ((3.e8 / nu_max) / B_max) * (180. / np.pi) * 3600. / 8.

        # Image bandpass calibrator
        obs_vis = f"{bandpass_calibrator}_calibrated.ms"
        os.makedirs(f"./IMAGES/{bandpass_calibrator}/")

        image_base = f'IMAGES/{bandpass_calibrator}/{bandpass_calibrator}_briggs0_{round(cell, 2)}arcsec'

        tclean(vis=obs_vis, weighting='briggs', robust=0, imagename=f"{image_base}_dirty", 
        cell=f"{cell}arcsec", imsize=[2048,2048], pblimit=-1, deconvolver='mtmfs')
        dirty_rms = imstat(f"{image_base}_dirty.image.tt0")['rms'][0]
        tclean(vis=obs_vis, weighting='briggs', robust=0, imagename=f"{image_base}_clean_iter1", cell=f"{cell}arcsec", 
        imsize=[2048,2048], niter=1000, threshold = f"{dirty_rms*5.}Jy", pblimit=-1, deconvolver='mtmfs')
        clean_rms = imstat(f"{image_base}_clean_iter1.residual.tt0")['rms'][0]
        tclean(vis=obs_vis, weighting='briggs', robust=0, imagename=f"{image_base}_clean_iter2", 
        cell=f"{cell}arcsec", imsize=[2048,2048], niter=1000, threshold = f"{clean_rms*5.}Jy", pblimit=-1,deconvolver='mtmfs')

        calibrator_diagnostics(image_base=image_base, cell_size=cell, calibrator=bandpass_calibrator)

        if len(gain_calibrators.split(',')) > 1:
                # Image phase calibrator
                obs_vis = f"{phase_calibrator}_calibrated.ms"
                os.makedirs(f"./IMAGES/{phase_calibrator}/")
                image_base = f'IMAGES/{phase_calibrator}/{phase_calibrator}_briggs0_{round(cell, 2)}arcsec'

                tclean(vis=obs_vis, weighting='briggs', robust=0, imagename=f"{image_base}_dirty", 
                cell=f"{cell}arcsec", imsize=[2048,2048], pblimit=-1, deconvolver='mtmfs')
                dirty_rms = imstat(f"{image_base}_dirty.image.tt0")['rms'][0]
                tclean(vis=obs_vis, weighting='briggs', robust=0, imagename=f"{image_base}_clean_iter1", cell=f"{cell}arcsec", 
                imsize=[2048,2048], niter=1000, threshold = f"{dirty_rms*5.}Jy", pblimit=-1, deconvolver='mtmfs')
                clean_rms = imstat(f"{image_base}_clean_iter1.residual.tt0")['rms'][0]
                tclean(vis=obs_vis, weighting='briggs', robust=0, imagename=f"{image_base}_clean_iter2", 
                cell=f"{cell}arcsec", imsize=[2048,2048], niter=1000, threshold = f"{clean_rms*5.}Jy", pblimit=-1,deconvolver='mtmfs')

                calibrator_diagnostics(image_base=image_base, cell_size=cell, calibrator=phase_calibrator)

        # Image target
        obs_vis = f"{target}_calibrated.ms"
        os.makedirs(f"./IMAGES/{target}/")
        image_base = f'IMAGES/{target}/{target}_briggs0_{round(cell, 2)}arcsec'

        print("Stokes I Image")
        tclean(vis=f'{target}_calibrated.ms', imagename=f"{image_base}_dirty", spw='0', specmode='mfs', deconvolver='mtmfs', 
                gridder='standard', imsize=[2048,2048], cell=f"{cell}arcsec", weighting='briggs', niter=100)
        tclean(vis=f'{target}_calibrated.ms', imagename=f'{image_base}_clean_iter_1000', spw='0', specmode='mfs', deconvolver='mtmfs', 
        gridder='standard', imsize=[2048,2048], cell=f"{cell}arcsec", weighting='briggs', niter=1000)

        print("Stokes Q Image")
        tclean(vis=f'{target}_calibrated.ms', imagename=f"{image_base}_Q_dirty", spw='0', specmode='mfs', deconvolver='mtmfs', 
                gridder='standard', imsize=[2048,2048], cell=f"{cell}arcsec", weighting='briggs', niter=100, stokes='Q')
        tclean(vis=f'{target}_calibrated.ms', imagename=f'{image_base}_Q_clean_iter_1000', spw='0', specmode='mfs', deconvolver='mtmfs', 
        gridder='standard', imsize=[2048,2048], cell=f"{cell}arcsec", weighting='briggs', niter=1000, stokes='Q')

        print("Stokes U Image")
        tclean(vis=f'{target}_calibrated.ms', imagename=f"{image_base}_U_dirty", spw='0', specmode='mfs', deconvolver='mtmfs', 
                gridder='standard', imsize=[2048,2048], cell=f"{cell}arcsec", weighting='briggs', niter=100, stokes='U')
        tclean(vis=f'{target}_calibrated.ms', imagename=f'{image_base}_U_clean_iter_1000', spw='0', specmode='mfs', deconvolver='mtmfs', 
        gridder='standard', imsize=[2048,2048], cell=f"{cell}arcsec", weighting='briggs', niter=1000, stokes='U')

        print("Stokes V Image")
        tclean(vis=f'{target}_calibrated.ms', imagename=f"{image_base}_V_dirty", spw='0', specmode='mfs', deconvolver='mtmfs', 
                gridder='standard', imsize=[2048,2048], cell=f"{cell}arcsec", weighting='briggs', niter=100, stokes='V')
        tclean(vis=f'{target}_calibrated.ms', imagename=f'{image_base}_V_clean_iter_1000', spw='0', specmode='mfs', deconvolver='mtmfs', 
        gridder='standard', imsize=[2048,2048], cell=f"{cell}arcsec", weighting='briggs', niter=1000, stokes='V')