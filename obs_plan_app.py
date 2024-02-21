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
import matplotlib.pyplot as plt
from datetime import datetime
from pytz import timezone
import pytz

import argparse
import os,sys

import streamlit as st


# H5_PATH = "/datax/scratch/cgchoza/testpipes/TIC159107668"
# TEST_NODE_FILE = "/datag/pipeline/AGBT21A_996_49/blc03/blc03_guppi_59411_54700_UGCA127_0095.rawspec.0000.h5"

# @st.cache_data
# def load_file(path: str) -> Waterfall:
#     w = Waterfall(path)
#     w.blank_dc(1)
#     return stg.Frame(w)

# def select_file():
#     if st.checkbox("Use test file?"):
#         return TEST_NODE_FILE

#     st.subheader("File Selection")
#     st.write(f"Loading files from `{H5_PATH}`...")
#     files = os.listdir(H5_PATH)
#     st.write(f"Found `{len(files)}` files!")
#     files = [f for f in files if f.endswith("h5")]
#     st.write(f"Found `{len(files)}` h5 files!")
    
#     file = st.selectbox("Choose a file:", files)
#     path = Path(H5_PATH) / file

#     return path

# def display_metadata(f: stg.Frame):
#     w = f.get_waterfall()

#     col1, col2 = st.columns(2)
#     with col1:
#         st.subheader("File Metadata")
#         st.write(w.header)
#     with col2:
#         st.subheader("Computed Statistics")
#         time = Time(w.header["tstart"], format="mjd").to_datetime()
#         st.write(f"**Start time:** {time}")

def get_info() -> tuple:
    '''Grab all necessary information for plotting from user inputs and set up'''

    telescope_location = EarthLocation.from_geodetic(lat=40.8178*units.deg, lon=-121.4733*units.deg)

    # Soon: add multiple calibrators, see if ATATools has a valid list somewhere
    # number_calibrators: int = st.number_input("Number of Calibrators", min_value=1, max_value=5)
    st.write("Input time range:")
    begin: str = st.text_input("Start time (UTC)", placeholder='2024-1-24T20:30:00')
    end: str = st.text_input("End time (UTC)", placeholder='2024-1-24T20:30:00')

    if st.checkbox("Input custom calibrator coordinates?"):
        cal_ra: float = st.number_input("Calibrator ra (hours)", placeholder=None)
        cal_dec: float = st.number_input("Calibrator dec (degrees)", placeholder=None)
        cal_coords = ICRS(ra=cal_ra*units.hour,dec=cal_dec*units.deg)

        target = FixedTarget(coord=cal_coords)

    else:
        cal_name: str = st.text_input("Calibrator Name", placeholder='3c286')
        cal_dict = check.check_source(cal_name)
        cal_ra = cal_dict['ra']
        cal_dec = cal_dict['dec']
        cal_coords = ICRS(ra=cal_ra*units.hour, dec=cal_dec*units.deg)

        target = FixedTarget(name=cal_name, coord=cal_coords)

    ata = Observer(location=telescope_location, name="ATA", timezone="US/Pacific")
    
    start_time = Time(begin, scale='utc')
    end_time = Time(end, scale='utc')
    obs_times = start_time + (end_time - start_time) * np.linspace(0, 1, 200)

    return (ata, target, obs_times)



def plot_data(info: tuple):

    telescope_loc, targ_loc, obs_times = info
    cal_name = targ_loc.name

    col1, col2 = st.columns(2)
    with col1:
        fig1, ax1 = plt.subplots(nrows=1,ncols=1, figsize=(4,4))
        style_kwargs = {'lw':1.5, 'marker':'.', 'markersize':0.5}
        # Calculate altitudes at each obs time
        plots.time_dependent.plot_altitude(ax=ax1, targets=targ_loc, observer=telescope_loc, time=obs_times, style_kwargs=style_kwargs)
        ax1.grid(True, linestyle='-.')
        if cal_name is not None:
                ax1.set_title(f'{cal_name} Altitude')
        else:
                ax1.set_title('Calibrator Altitude')

        # st.write(ax1.get_xticklabels())
        # if st.checkbox("Use local time?"):  
        #     # date_format = '%m/%d/%Y %H:%M:%S %Z'
        #     # date_times = obs_times.to_datetime()
        #     # pacific_times = [stamp.astimezone(timezone('US/Pacific')) for stamp in date_times]
        #     labels = ax1.get_xticklabels()
        #     for i in range(8):
        #         ilabel = labels[str(i)]
        #         hours = ilabel.split("'")[1]
        #         hours_digit = 

        st.pyplot(fig1)
        
    with col2:
        fig2, ax2 = plt.subplots(nrows=1,ncols=1, figsize=(4,4))
        # Calculate parallactic angle at each obs time
        plots.time_dependent.plot_parallactic(ax=ax2, target=targ_loc, observer=telescope_loc, time=obs_times)
        ax2.grid(True, linestyle='-.')
        if cal_name is not None:
                ax2.set_title(f'{cal_name} Parallactic Angle')
        else:
                ax2.set_title('Calibrator Parallactic Angle')
        st.pyplot(fig2)

def main():
    st.title("ATAPol Planner")
    st.write("A tool for plotting calibrator rise times and parallactic angle coverage.")

    info = get_info()

    st.divider()

    plot_data(info)

if __name__ == "__main__":
    st.set_page_config(layout="wide")
    main()