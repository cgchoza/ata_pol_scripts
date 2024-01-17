#!/usr/bin/env python3

#############################

# This script should be run using CASA 6.4.0.16 or higher

#############################

# Imports
import glob
import os, sys
import glob
import subprocess

# Fields for user to edit per-observation
bcal = '3c147'
pcal = '2343+538'
target = 'CasA'
ref_ant = '40'
pol_spw = '0'              # Measurement set should have only one spectral window, 
                                  # use to constrain bandpass used for polcal
obs_vis = 'CasA_polcal.ms'

use_3c286 = True
generate_plots = True
iterate_calibration = False

tab_name = obs_vis.split('.')[0]

polcal_table_dir = '/Users/cgchoza/Documents/pol_data/2023-10-30-15:11:08'

antennas = ['1b', '1c', '1e', '1g', '1h', '1k',
            '2b', '2d', '2e', '2f', '2h', '2j', '2k', '2l', '2m',
            '3d', '3l', '4e', '4j', '5e']
antenna_list = ','.join([f'"{a}"' for a in antennas])

#############################################

# Begin standard calibration

#############################################

# Flagging: script assumes pre-flagging using aoflagger.
## If manual flagging desired, uncomment the below and edit to suit
# flagdata(vis=vis, mode='manual', scan='28', flagbackup=False)

# Set flux model for flux calibrator 
setjy(vis=obs_vis, field=bcal, standard='Perley-Butler 2017', usescratch=True)

# Listobs
listobs(vis=obs_vis)

# Preliminary gaincal
# This discards XX vs. YY signal difference and will be thrown away after solving delay and bandpass
gaincal(vis=obs_vis, caltable=f'{tab_name}.G0', field=bcal, spw='0', refant=ref_ant, refantmode='strict', calmode='p', 
        solint='inf', parang=True)
gaincal(vis=obs_vis, caltable=f'{tab_name}.G1', field=bcal, spw='0', refant=ref_ant, refantmode='strict', calmode='a', 
        solint='100', preavg=1, minblperant=1, minsnr=0, gaintype='G', gaintable=[f'{tab_name}.G0'], parang=True)

if generate_plots:
        # Plot preliminary gain amplitudes
        plotms(vis=f'{tab_name}.G0', xaxis='antenna1', yaxis='gainphase',
        coloraxis='corr', antenna=antenna_list, spw='0',
        plotfile=f'G1_{tab_name}_phase.png', overwrite=True)
        # Plot preliminary gain phases
        plotms(vis=f'{tab_name}.G1', xaxis='antenna1', yaxis='gainamp',
        coloraxis='corr', antenna=antenna_list, spw='0',
        plotfile=f'G0_{tab_name}_amp.png', overwrite=True)

# Delay calibration
gaincal(vis=obs_vis, caltable=f'{tab_name}.K0', field=bcal, spw='0', refant=ref_ant, solint='inf', combine='scan', 
        preavg=1, minblperant=1, gaintype='K', gaintable=[f'{tab_name}.G0', f'{tab_name}.G1'], parang=True)

# Bandpass
# NOTE: low freq spectral windows so we'll use a small averaging window, may be appropriate to allow edit
bandpass(vis=obs_vis, caltable=f'{tab_name}.B0', field=bcal, spw='0', refant=ref_ant,
         bandtype='B', gaintable=[f'{tab_name}.G0', f'{tab_name}.G1', f'{tab_name}.K0'], parang=True)

if generate_plots:
        # Bandpass solutions, frequency vs amplitude and phase
        for ax in ['amp', 'phase']:
                plotms(vis=f'{tab_name}.B0', xaxis='freq', yaxis=f'gain{ax}',
                coloraxis='corr', iteraxis='antenna', gridrows=4, gridcols=5,
                yselfscale=True, antenna=antenna_list, spw='0',
                plotfile=f'B0_{tab_name}_{ax}.png', overwrite=True)

# Secondary gaincal after solving for delay and bandpass
# Use both flux calibrator and phase/linear pol calibraton
gaincal(vis=obs_vis, caltable=f'{tab_name}.G2', field=bcal, spw='0', refant=ref_ant, calmode='ap', solint='300', 
        gaintable=[f'{tab_name}.K0', f'{tab_name}.B0'], parang=True)
if use_3c286:
        gaincal(vis=obs_vis, caltable=f'{tab_name}.G3', field='0', spw='0', refant=ref_ant, calmode='ap', solint='300', 
                gaintable=[f'{tab_name}.K0', f'{tab_name}.B0', f'{tab_name}.G2'], parang=True)

        if generate_plots:
                # For bandpass calibrator, gain amplitude and phase
                plotms(vis=f'{tab_name}.G2', xaxis='time', yaxis=f'gainamp',
                        coloraxis='corr', iteraxis='antenna', gridrows=4, gridcols=5,
                        yselfscale=True, antenna=antenna_list, spw='0',
                        plotfile=f'G2_{bcal}_{tab_name}_amp.png', overwrite=True)
                plotms(vis=f'{tab_name}.G2', xaxis='time', yaxis=f'gainphase',
                        coloraxis='corr', iteraxis='antenna', gridrows=4, gridcols=5,
                        yselfscale=True, antenna=antenna_list, spw='0',
                        plotfile=f'G2_{bcal}_{tab_name}_phase.png', overwrite=True)

                # For phase calibrator, gain amplitude and phase
                plotms(vis=f'{tab_name}.G3', xaxis='time', yaxis=f'gainamp',
                        coloraxis='corr', iteraxis='antenna', gridrows=4, gridcols=5,
                        yselfscale=True, antenna=antenna_list, spw='0',
                        plotfile=f'G3_{pcal}_{tab_name}_amp.png', overwrite=True)
                plotms(vis=f'{tab_name}.G3', xaxis='time', yaxis=f'gainphase',
                        coloraxis='corr', iteraxis='antenna', gridrows=4, gridcols=5,
                        yselfscale=True, antenna=antenna_list, spw='0',
                        plotfile=f'G3_{pcal}_{tab_name}_phase.png', overwrite=True)

                

else:
        # If using phase calibrator for polarization calibration, we allow the gains to absorb the parallactic angle 
        # variation so that we can use it to calculate the pcal Stokes model
        gaincal(vis=obs_vis, caltable=f'{tab_name}.G3', field=pcal, spw='0', refant=ref_ant, calmode='ap', solint='300', 
                gaintable=[f'{tab_name}.K0', f'{tab_name}.B0', f'{tab_name}.G2'])
        
        # Calculate Stokes model from gains
        qu_model = polfromgain(vis=obs_vis, tablein=f'{tab_name}.G3')

        # Redo gaincal with Stokes model; this does not absorb polarization signal
        gaincal(vis=obs_vis, caltable=f'{tab_name}_pol.G3', refant=ref_ant, refantmode='strict', solint='300', calmode='ap', 
                field=pcal, smodel=qu_model[pcal]['Spw0'], parang=True, gaintable=[f'{tab_name}.B0', f'{tab_name}.G2'])

        if generate_plots:
                # For bandpass calibrator, gain amplitude and phase
                plotms(vis=f'{tab_name}.G2', xaxis='time', yaxis=f'gainamp',
                        coloraxis='corr', iteraxis='antenna', gridrows=4, gridcols=5,
                        yselfscale=True, antenna=antenna_list, spw='0',
                        plotfile=f'G2_{bcal}_{tab_name}_amp.png', overwrite=True)
                plotms(vis=f'{tab_name}.G2', xaxis='time', yaxis=f'gainphase',
                        coloraxis='corr', iteraxis='antenna', gridrows=4, gridcols=5,
                        yselfscale=True, antenna=antenna_list, spw='0',
                        plotfile=f'G2_{bcal}_{tab_name}_phase.png', overwrite=True)

                # For phase calibrator, gain amplitude and phase
                plotms(vis=f'{tab_name}_pol.G3', xaxis='time', yaxis=f'gainamp',
                        coloraxis='corr', iteraxis='antenna', gridrows=4, gridcols=5,
                        yselfscale=True, antenna=antenna_list, spw='0',
                        plotfile=f'G3_{tab_name}_pol_amp.png', overwrite=True)
                plotms(vis=f'{tab_name}_pol.G3', xaxis='time', yaxis=f'gainphase',
                        coloraxis='corr', iteraxis='antenna', gridrows=4, gridcols=5,
                        yselfscale=True, antenna=antenna_list, spw='0',
                        plotfile=f'G3_{pcal}_{tab_name}_pol_phase.png', overwrite=True)

###########################################
        
# Polarization calibration

###########################################


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

        applycal(vis=obs_vis, gaintable=[f'{tab_name}.K0', f'{tab_name}.B0', f'{tab_name}.G2', f'{tab_name}.G3', kcross, Xfparang, leakage], parang=True)
        # applycal(vis=obs_vis, gaintable=[kcross, Xfparang, leakage], parang=True)

        # Save out a calibrated measurement set

        split(obs_vis, outputvis=f'{tab_name}_pol_cal.ms', datacolumn='corrected')

        if generate_plots:
                for ax in ['real', 'imag']:
                        # Real and imaginary components versus parallactic angle for polarization calibrator
                        plotms(vis=f'{tab_name}_pol_cal.ms', ydatacolumn='corrected', xaxis='parang', yaxis=ax,
                                coloraxis='corr', field=pcal, avgchannel='168', spw=spw,
                                plotfile=f'{tab_name}_parang_corrected_{ax}_vs_parang.png', overwrite=True)
                        # Real and imaginary components versus frequency for polarization calibrator
                        plotms(vis=f'{tab_name}_pol_cal.ms', ydatacolumn='corrected', xaxis='freq', yaxis=ax,
                                coloraxis='corr', field=pcal, avgtime='100000', avgscan=True, spw='0',
                                plotfile=f'{tab_name}_parang_corrected_{ax}_vs_freq.png', overwrite=True)
                # Parallactic angle-corrected real vs imaginary components for polarization calibrator
                plotms(vis=f'{tab_name}_pol_cal.ms', xdatacolumn='corrected', ydatacolumn='corrected',
                        xaxis='real', yaxis='imag', coloraxis='corr', field=pcal,
                        avgtime='100000', avgscan=True, avgchannel='168', spw=spw,
                        plotfile=f'{tab_name}_pol_cal_parang_corrected_reim.png')


### Try on the fly with a strongly polarized calibrator

else:
        # Set flux model for phase calibrator
        setjy(vis=obs_vis, field=pcal, standard='Perley-Butler 2017', usescratch=True)
        
        # Kcross
        gaincal(vis=obs_vis, caltable=f'{tab_name}_pol.Kcross0', spw=spw, refant=ref_ant, solint='inf', 
               field=pcal, gaintype='KCROSS', combine='scan', smodel=[1, 0, 1, 0], calmode='ap', 
               minblperant=1, refantmode='strict', parang=True)

        if generate_plots:
                # Plot of Kcross solutions
                plotms(vis=f'{tab_name}_pol.Kcross0', yaxis='delay', spw='0',
                        antenna=ref_ant, coloraxis='corr',
                        plotfile=f'{tab_name}_Kcross0.png', overwrite=True)
               
        # Solve for the apparent cross-hand phase spectrum (channelized) fractional linear polarization, Q, U
        # Note that CASA calculates a Stokes model for the source in this step as well, but it will be incorrect!
        # The X-Y phase offset table generated here seems to be accurate
        S_model = polcal(vis=obs_vis, caltable=f'{tab_name}_pol.Xfparang',
                  field=pcal, spw=spw,
                  solint='inf', combine='scan', preavg=300,
                  smodel=qu_model[pcal]['Spw0'], poltype='Xfparang+QU',
                  gaintable=[f'{tab_name}.B0', f'{tab_name}.G0', f'{tab_name}.G2', f'{tab_name}_pol.G3',
                             f'{tab_name}_pol.Kcross0'])
                             
        # Solve for leakage terms
        polcal(vis=obs_vis, caltable=f'{tab_name}_pol.D0', field='0', spw=spw, solint='inf', combine='scan', preavg=300,
              smodel=qu_model[pcal]['Spw0'], poltype='Dflls', refant='', 
              gaintable=[f'{tab_name}.B0', f'{tab_name}.G0', f'{tab_name}.G2', f'{tab_name}_pol.G3',f'{tab_name}_pol.Kcross0', 
                         f'{tab_name}_pol.Xfparang'])

        if generate_plots:
                # Plots of phase-frequency and real/imaginary leakage terms by antenna
                plotms(vis=f'{tab_name}_pol.Xfparang', xaxis='freq', yaxis='gainphase',
                        plotfile=f'{tab_name}_freq_vs_gainphase.png', overwrite=True)

                for ax in ['real', 'imag']:
                        plotms(vis=f'{tab_name}_pol.D0', xaxis='freq', yaxis=ax,
                                coloraxis='corr', iteraxis='antenna', gridrows=4, gridcols=5,
                                yselfscale=True, antenna=antenna_list,
                                plotfile=f'D0_{tab_name}_pol_{ax}.png', overwrite=True)
        
        # Apply the tables
        kcross = f'{tab_name}_pol.Kcross0'
        Xfparang = f'{tab_name}_pol.Xfparang'
        leakage = f'{tab_name}_pol.D0'

        applycal(vis=obs_vis, gaintable=[f'{tab_name}.K0', f'{tab_name}.B0', f'{tab_name}.G2', f'{tab_name}_pol.G3', 
                kcross, Xfparang, leakage], parang=True)

        # Save out a calibrated measurement set
        split(vis=obs_vis, outputvis=f'{tab_name}_pol_cal.ms', datacolumn='corrected')

        if generate_plots:
                for ax in ['real', 'imag']:
                        # Real and imaginary components versus parallactic angle for polarization calibrator
                        plotms(vis=f'{tab_name}_pol_cal.ms', ydatacolumn='corrected', xaxis='parang', yaxis=ax,
                                coloraxis='corr', field=pcal, avgchannel='168', spw='0',
                                plotfile=f'{tab_name}_parang_corrected_{ax}_vs_parang.png', overwrite=True)
                        # Real and imaginary components versus frequency for polarization calibrator
                        plotms(vis=f'{tab_name}_pol_cal.ms', ydatacolumn='corrected', xaxis='freq', yaxis=ax,
                                coloraxis='corr', field=pcal, avgtime='100000', avgscan=True, spw='0',
                                plotfile=f'{tab_name}_parang_corrected_{ax}_vs_freq.png', overwrite=True)
                # Parallactic angle-corrected real vs imaginary components for polarization calibrator
                plotms(vis=f'{tab_name}_pol_cal.ms', xdatacolumn='corrected', ydatacolumn='corrected',
                        xaxis='real', yaxis='imag', coloraxis='corr', field=pcal,
                        avgtime='100000', avgscan=True, avgchannel='168', spw=spw,
                        plotfile=f'{tab_name}_pol_cal_parang_corrected_reim.png')

### Try on the fly with unpolarized cal

    # VERDICT: this is not possible with current CASA
    # It would involve using 'Dflls' or 'Df' followed by 'Xf'; it states about 'Dflls'
    # (Had we used an unpolarized calibrator, we would not have a valid xy-phase solution, 
    # nor would we have had access to the absolute instrumental polarization solution 
    # demonstrated here.). The alternative options strictly state they cannot be used
    # for the linear basis and will give bad solutions.

# Iterate calibration with D-term solution and save out another calibrated ms

# Cleaning?

##############################################################################################################