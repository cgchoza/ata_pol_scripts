#!/opt/mnt/miniconda3/bin/python

import pandas as pd
from astropy.coordinates import SkyCoord
from astropy import units
from astropy.coordinates import EarthLocation, AltAz, ICRS, get_sun
import numpy as np
import astroplan
import astroplan.plots as plots
from astroplan import Observer
from astroplan import FixedTarget
from astropy.time import Time
import ATATools.ata_sources as check

import argparse
import os,sys

import tkinter as tk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
import matplotlib.pyplot as plt

class SideBySidePlotsApp:
    def __init__(self, root, cal_name, telescope_loc, obs_times, cal_loc):
        self.root = root
        self.root.title("Obs Plot GUI")

        # First plot: will be populated with astroplan altitude
        self.fig1, self.ax1 = plt.subplots(nrows=1,ncols=1, figsize=(5,5))
        self.create_plot(plot_type='alt', ax=self.ax1, cal_name=cal_name, telescope_loc=telescope_loc, obs_times=obs_times, targ_loc=cal_loc)
        self.canvas1 = FigureCanvasTkAgg(self.fig1, master=root)
        toolbar = NavigationToolbar2Tk(self.canvas1, self.root)
        toolbar.update()
        self.canvas_widget1 = self.canvas1.get_tk_widget()
        self.canvas_widget1.pack(side=tk.LEFT, fill=tk.BOTH, expand=1)

        # Second plot: will be populated with astroplan parallactic angle
        self.fig2, self.ax2 = plt.subplots(nrows=1, ncols=1, figsize=(5,5))
        self.ax2 = self.create_plot(plot_type='par', ax=self.ax2, cal_name=cal_name, telescope_loc=telescope_loc, obs_times=obs_times, targ_loc=cal_loc)
        self.canvas2 = FigureCanvasTkAgg(self.fig2, master=root)
        toolbar = NavigationToolbar2Tk(self.canvas2, self.root)
        toolbar.update()
        self.canvas_widget2 = self.canvas2.get_tk_widget()
        self.canvas_widget2.pack(side=tk.LEFT, fill=tk.BOTH, expand=1)

    def create_plot(self, ax, plot_type, cal_name, obs_times, targ_loc, telescope_loc):
        
        if plot_type == 'alt':
                # Calculate altitudes at each obs time
                plots.time_dependent.plot_altitude(ax=ax, targets=targ_loc, observer=telescope_loc, time=obs_times)
                plt.grid()
                if cal_name is not None:
                        plt.title(f'{cal_name} Altitude')
                else:
                        plt.title('Calibrator Altitude')

        if plot_type == 'par':
                # Calculate parallactic angle at each obs time
                plots.time_dependent.plot_parallactic(ax=ax, target=targ_loc, observer=telescope_loc, time=obs_times)
                plt.grid()
                if cal_name is not None:
                        plt.title(f'{cal_name} Parallactic Angle')
                else:
                        plt.title('Calibrator Parallactic Angle')
            

def main():
    parser = argparse.ArgumentParser(description=
            'Find nearest VLA calibrator to a specific sky position')
    
    parser.add_argument('-c', '--calibrator', dest='cal', type=str,
            help="The calibrator string name (VLA catalog)",
            default='X')

    parser.add_argument('-ra', '--rahours', dest='ra', type=float,
            help="Right Ascension in decimal hours")
    parser.add_argument('-dec', '--decdeg', dest='dec', type=float,
            help="Declination in decimal degrees")
    
    parser.add_argument('-b', '--beginobs', dest='begin', type=str,
            help="Time to begin observation plot")
    parser.add_argument('-e', '--endobs', dest='end', type=str,
            help="Time to end observation plot")

    parser.add_argument('-hh', '--hheellpp', action='store_true',
            help='show more than this help message and exit')

    if ('-hh' in sys.argv) or ('--hheellpp' in sys.argv):
        print(HELP)
        sys.exit(0)

    args = parser.parse_args()

    cal_name = args.cal
    begin = args.begin
    end = args.end
    telescope_location = EarthLocation.from_geodetic(lat=40.8178*units.deg, lon=-121.4733*units.deg)
    cal_ra = args.ra
    cal_dec = args.dec

    if cal_ra is None and cal_dec is None and cal_name is None:
          print("Must input either calibrator name or coordinates!")
          sys.exit()

    if cal_ra is not None and cal_dec is not None:
          cal_coords = ICRS(ra=cal_ra*units.deg,dec=cal_dec*units.deg)
    else:
          cal_dict = check.check_source(cal_name)
          cal_ra = cal_dict['ra']
          cal_dec = cal_dict['dec']
          cal_coords = ICRS(ra=cal_ra*units.hour, dec=cal_dec*units.deg)



    ata = Observer(location=telescope_location, name="ATA", timezone="US/Pacific")
    target = FixedTarget(name=cal_name, coord=cal_coords)
    print(cal_coords)

    start_time = Time(begin, scale='utc')
    end_time = Time(end, scale='utc')
    obs_times = start_time + (end_time - start_time) * np.linspace(0, 1, 500)
    print(obs_times)

    root = tk.Tk()
    app = SideBySidePlotsApp(root, cal_name=cal_name, telescope_loc=ata, cal_loc=target, obs_times=obs_times)
    root.mainloop()


if __name__ == "__main__":
    main()