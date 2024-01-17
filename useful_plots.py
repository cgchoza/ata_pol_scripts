# Evalution plots

vis = 'CasA_polcal.ms'

polcal_spw = '1:50~167'

antennas = ['1b', '1c', '1e', '1g', '1h', '1k',
            '2b', '2d', '2e', '2f', '2h', '2j', '2k', '2l', '2m',
            '3d', '3l', '4e', '4j', '5e']
antenna_list = ','.join([f'"{a}"' for a in antennas])
REFANT='5e'

plot_calibration_tables = True
plot_calibrated_data = True
plot_pol_cal_tables = True

for ax in ['real', 'imag']:
    plotms(vis=vis, ydatacolumn='corrected', xaxis='parang', yaxis=ax,
           coloraxis='corr', field='0', avgchannel='168', spw=polcal_spw,
           plotfile=f'{vis}_parang_corrected_{ax}_vs_parang.png', overwrite=True)

    plotms(vis=vis, ydatacolumn='corrected', xaxis='freq', yaxis=ax,
           coloraxis='corr', field='0', avgtime='100000', avgscan=True, spw='0',
           plotfile=f'{vis}_parang_corrected_{ax}_vs_freq.png', overwrite=True)

plotms(vis=vis, xdatacolumn='corrected', ydatacolumn='corrected',
       xaxis='real', yaxis='imag', coloraxis='corr', field='0',
       avgtime='100000', avgscan=True, avgchannel='168', spw=polcal_spw,
       plotfile=f'{vis}_parang_corrected_reim.png')

# Calibration table plots

if plot_calibration_tables:
    for ax in ['amp', 'phase']:
        plotms(vis=f'{vis}.B0', xaxis='freq', yaxis=f'gain{ax}',
            coloraxis='corr', iteraxis='antenna', gridrows=4, gridcols=5,
            yselfscale=True, antenna=antenna_list, spw='0',
            plotfile=f'B0_{ax}.png', overwrite=True)

    plotms(vis=f'{vis}.G0', xaxis='antenna1', yaxis='gainamp',
        coloraxis='corr', antenna=antenna_list, spw='0',
        plotfile='G0_amp.png', overwrite=True)

    for j in [1, 2]:
        for ax in ['amp', 'phase']:
            plotms(vis=f'{vis}.field0.G{j}', xaxis='time', yaxis=f'gain{ax}',
                coloraxis='corr', iteraxis='antenna', gridrows=4, gridcols=5,
                yselfscale=True, antenna=antenna_list, spw='0',
                plotfile=f'G{j}_field0_{ax}.png', overwrite=True)

    plotms(vis=f'uvh5_60247.Kcross0', yaxis='delay', spw='0',
        antenna=REFANT, coloraxis='corr',
        plotfile=f'Kcross0.png', overwrite=True)

if plot_pol_cal_tables:
    for xf in ['Xfparang']:
        plotms(vis=f'uvh5_60247.{xf}', xaxis='freq', yaxis='gainphase',
            plotfile=f'{xf}.png', overwrite=True)

    for ax in ['real', 'imag']:
        plotms(vis='uvh5_60247.D0', xaxis='freq', yaxis=ax,
            coloraxis='corr', iteraxis='antenna', gridrows=4, gridcols=5,
            yselfscale=True, antenna=antenna_list,
            plotfile=f'D0_{ax}.png', overwrite=True)