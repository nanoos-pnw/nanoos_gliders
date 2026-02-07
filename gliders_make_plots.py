#!/usr/bin/env python
# coding: utf-8
# %%

# %%


# load packages
from erddapy import ERDDAP
import numpy as np
import datetime
import pandas as pd
import json
import xarray as xr

import os
import sys
import getopt
import gc
import shutil

import matplotlib
from matplotlib import pyplot as plt
import matplotlib.dates as mdates

from importlib import reload

# import classes needed to build initial parameters objects
from classes import Dataset


import gliders_general_functions as gliders_gen

import create_jsons
from create_jsons import GliderJson
from create_jsons import Glider_Plotting_Json


import warnings
warnings.filterwarnings("ignore")


# %%


def make_oxy_colormap(vmin, vmax):
    
    # Define the number of colors to use
    ncolors = 256

    # Define the number of steps to use for just
    # the hypoxic colormap; which is
    # # also the start of the white color
    white_start = int(np.ceil((2/(vmax-vmin)) * ncolors))

    # Get the "rainbow" colormap
    colormap = matplotlib.colormaps['rainbow']

    # Use the upper 3/4 of the colormap, and split it into
    # a number of colors equal to the % of the variable range
    # above 2 mg/L
    colormap_colors = colormap(np.linspace(0.25,1,int(((vmax-2)/(vmax-vmin))*ncolors)))

    # To make the hypoxic range, we go range from a purple color to a 
    # white color, in a number of steps equal to the fraction of the total steps
    # which accounts for the 2mg/L threshold as a % of the colorbar range
    # (i.e., if the total range is from 0-8mg/L, the 2mg/L threshold is 25% of 
    #  the total range)
    hypoxic_range = np.ones((white_start,4))
    
    # The colormap for the selected purple color is (0.18, 0, 0.64)
    # The colormap for white is (1, 1, 1)
    # The hypoxic range is a linear interpolation of each color 
    # value range, over the number of steps determined above
    newrange = np.arange(0.18,1,(1-0.18)/white_start)
    if len(newrange) > white_start:
        hypoxic_range[:,0] = newrange[:-1]
    else:
        hypoxic_range[:,0] = newrange
        
    newrange = np.arange(0,1,(1-0)/white_start)
    if len(newrange) > white_start:
        hypoxic_range[:,1] = newrange[:-1]
    else:
        hypoxic_range[:,1] = newrange
        
    newrange = np.arange(0.64,1,(1-0.64)/white_start)
    if len(newrange) > white_start:
        hypoxic_range[:,2] = newrange[:-1]
    else:
        hypoxic_range[:,2] = newrange

    #
    if vmax - vmax < 10:
        colormap_start = 6
    else:
        colormap_start = 12

    if colormap_colors[colormap_start,0] < 1:
        colormap_colors[0:colormap_start,0] = np.arange(1, colormap_colors[colormap_start-1,0], 
                                                   -(1-colormap_colors[colormap_start-1,0])/colormap_start)
    if colormap_colors[colormap_start,1] < 1:
        colormap_colors[0:colormap_start,1] = np.arange(1, colormap_colors[colormap_start-1,1], 
                                                   -(1-colormap_colors[colormap_start-1,1])/colormap_start)
    if colormap_colors[colormap_start,2] < 1:
        colormap_colors[0:colormap_start,2] = np.arange(1, colormap_colors[colormap_start-1,2], 
                                                   -(1-colormap_colors[colormap_start-1,2])/colormap_start)

    # Append the modified rainbox colormap and the built hypoxic colormap together
    colormap_colors = np.append(hypoxic_range, colormap_colors,axis=0)

    # Create a new listed colormap for the new oxygen colormap
    colormap1 = colormap.copy()
    colormap1 = matplotlib.colors.ListedColormap(colormap_colors)
    
    return colormap1


# %%


def extract_position_variables(df, dep_plotinfo):
    
    ##############################################
    # rename variables, convert to desired units #
    ##############################################
    print('   Recasting variables: ' + datetime.datetime.now().strftime('%Y-%b-%d %H:%M:%S'))
    # dive number, depth
    divenum = df['profile_id'].values
    depth = df['depth'].values # m

    # times
    ptime = df.index # precise time in UTC (PDT=UTC-7 hours)
    atime = df['time'].values # average time per dive in UTC (PDT=UTC-7 hours)
    #adatenum = [mdates.date2num(datetime.datetime.strptime(i, '%Y-%m-%dT%H:%M:%SZ')) for i in atime]

    # lats, lons
    plat = df['precise_lat'].values # precise lat
    alat = df['latitude'].values # average lat per dive
    plon = df['precise_lon'].values # precise lon
    alon = df['longitude'].values # average lon per dive
    data_coords = {'divenum': divenum,
                   'depth': depth,
                   'plat': plat, 
                   'plon': plon,
                   'ptime': ptime,
                   'alat': alat, 
                   'alon': alon,
                   'atime': atime}
    
    
    #####################################
    # load bathymetry for GEBCO mapping #
    #####################################
    print('   Loading and interpolating bathymetry: ' + datetime.datetime.now().strftime('%Y-%b-%d %H:%M:%S'))
    ds = xr.load_dataset(os.path.join(os.getcwd(),
                                      'glider_bathy/GEBCO_2021/gebco_2021_n49.0_s39.0_w-130.0_e-123.0.nc'))

    lats = ds['lat']
    lons = ds['lon']
    depths = ds['elevation']

    gliderlats = xr.DataArray(alat, dims='elevation')
    gliderlons = xr.DataArray(alon, dims='elevation')
    gliderdepths = depths.interp(lat=gliderlats,lon=gliderlons)
    data_coords['gliderdepths'] = gliderdepths.to_numpy().flatten()
    
    ds.close()
    
    
    return data_coords


# %%


def extract_data_variables(df, dep_plotinfo):
    
    ##############################################
    # rename variables, convert to desired units #
    ##############################################

    # variables of interest
    datadict = {}
    temp_cols = [col for col in df.columns if 'temperature' in col]
    datadict['temp'] = [item for sublist in df[temp_cols].values.tolist() for item in sublist] # C
    sal_cols = [col for col in df.columns if 'salinity' in col]
    datadict['sal'] = [item for sublist in df[sal_cols].values.tolist() for item in sublist] # psu
    dens_cols = [col for col in df.columns if 'density' in col]
    datadict['dens'] = [item for sublist in df[dens_cols].values.tolist() for item in sublist] #kg m-3
    do_cols = [col for col in df.columns if 'oxygen' in col]
    datadict['do'] = [item*(31.9988/1000)*1.026 for sublist in df[do_cols].values.tolist() for item in sublist] #DO micromoles/kg * (31.9988 mg oxygen / 1000 micromoles) * (1.026 kg /l ) = DO mg/l
    chl_cols = [col for col in df.columns if 'chloro' in col or 'fluor' in col]
    datadict['chl'] = [item for sublist in df[chl_cols].values.tolist() for item in sublist] # ug l-1
    cdom_cols = [col for col in df.columns if 'CDOM' in col or 'cdom' in col]
    datadict['cdom'] = [item for sublist in df[cdom_cols].values.tolist() for item in sublist] # ppb
    bs_cols = [col for col in df.columns if 'backscatter' in col or 'opbs' in col]
    datadict['bs'] = [item for sublist in df[bs_cols].values.tolist() for item in sublist] # m-1
    
    
    return datadict


# %%


def calc_turning_points(data_coords, dep_plotinfo, prev_coords=None):
    
    ##############################################   
    # auto-detect turning points on glider track #
    ##############################################
    print('Detecting turn-around points')
    
    # Extract out the indices of the last point in each unique dive number
    divenum = data_coords['divenum'].copy()
    divenum_unique = np.unique(divenum)
    divenum_lastind = np.array([np.where(divenum == ii)[0][-1] 
                                for ii in divenum_unique])

    # Pull out the precise lat, lon, and time corresponding to
    # the last point in each unique dive
    plat = data_coords['plat'].copy()[divenum_lastind]
    plon = data_coords['plon'].copy()[divenum_lastind]
    ptime = data_coords['ptime'].copy()[divenum_lastind]
    
    # Ensure that all the points are sorted by time
    sortinds = np.argsort(ptime)
    divenum_lastind = divenum_lastind[sortinds]
    plat = plat[sortinds]
    plon = plon[sortinds]
    ptime = ptime[sortinds]
    
    # Null out any points for dives outside of the lat/lon limits
    badloc_inds = np.logical_or(np.logical_or(plat > np.max(dep_plotinfo['latlimmap']),
                                              plat < np.min(dep_plotinfo['latlimmap'])),
                                np.logical_or(plon > np.max(dep_plotinfo['lonlimmap']),
                                              plon < np.min(dep_plotinfo['lonlimmap'])))
    plat[badloc_inds] = np.nan
    plon[badloc_inds] = np.nan
    
    rdp_method = True
    bearing_method = True
    if rdp_method:
        bearing_method = False
        
    if rdp_method:
        # Using the RDP method to find segments
        segments = get_segments_by_rdp(data_coords, dep_plotinfo)
        if any(np.logical_not(np.logical_or(np.isnan(data_coords['plon']),
                                            np.isnan(data_coords['plat'])))):
            last_goodpt = np.where(np.logical_not(np.logical_or(np.isnan(data_coords['plon']),
                                                                np.isnan(data_coords['plat']))))[0][-1]
        else:
            last_goodpt = len(data_coords['plon'])-1
        endpts = np.append(segments, last_goodpt).astype(int)
        endpts = np.sort(endpts).astype(int)
        
    elif bearing_method:
        # Using the vessel bearing        
        [bearing_raw, bearing_smooth, bearing_smooth_wrapped,
         plon_smooth, plat_smooth] = calculate_glider_bearing(plat, plon, ptime)
        segments = get_segments_from_bearing(bearing_smooth, bearing_smooth_wrapped, 
                                             ptime, plon, plat)
        endpts = np.append(segments, len(bearing_raw)-1).astype(int)
        
        # Convert the "endpts" to indices corresponding to the
        # last point in each dive
        endpts = divenum_lastind[endpts].astype(int)
    else:
        # Determine turning points along the path
        # By finding the longitude min/max
        from get_min_max import get_min_max
        inarr = plon
        endpts = get_min_max(inarr, dep_plotinfo['tolerance'], dep_plotinfo['exppts'])
        
        # Convert the "endpts" to indices corresponding to the
        # last point in each dive
        endpts = divenum_lastind[endpts].astype(int)
        
        
    ############################################
    # If neeeded, merge the previous end points
    # with the newly calculated end points
    if prev_coords is not None:
        # If we are merging with previous end
        # points, use all of the previous end
        # points except for the last 3, and 
        # then merge in the new points as appropriate
        if len(prev_coords['endpts']) > 6:
            prev_endpts = prev_coords['endpts'][:-3]
        else:
            prev_endpts = prev_coords['endpts'][:-1]
            
        if len(prev_endpts) > 0:
            endpts_newstart = np.where(abs(endpts - prev_endpts[-1]) ==
                                       min(abs(endpts - prev_endpts[-1])))[0][0]
        elif len(prev_endpts) > 1:
            endpts_newstart = 0
        else:
            endpts_newstart = -1
        if len(endpts) > endpts_newstart+1:
            new_endpts = endpts[endpts_newstart+1:]
        else:
            new_endpts = []
        endpts = np.unique(np.append(prev_endpts, new_endpts)).astype(int)
        
    
    #########################################
    # Check that all segment/endpts are
    # within acceptable ranges
    plon_endpts = data_coords['plon'][endpts]
    plat_endpts = data_coords['plat'][endpts]
    keep_endpts = []
    for endpt in endpts:
        if not(np.logical_or(np.logical_or(data_coords['plat'][endpt] > np.max(dep_plotinfo['latlimmap']),
                                           data_coords['plat'][endpt] < np.min(dep_plotinfo['latlimmap'])),
                             np.logical_or(data_coords['plon'][endpt] > np.max(dep_plotinfo['lonlimmap']),
                                           data_coords['plon'][endpt] < np.min(dep_plotinfo['lonlimmap'])))):
               keep_endpts.append(endpt)
    if len(keep_endpts) > 0:
        endpts = np.array(keep_endpts).astype(int)
    else:
        endpts = np.array([]).astype(int)
    
    
    ################################
    # Assign section endpts, and build
    # remaining data coordinates
        
    data_coords['endpts'] = endpts.astype(int)

    # save pairs of endpoints for each segment
    segments = list()
    for j in range(len(endpts)-1):
        segments.append((endpts[j],endpts[j+1]))
    data_coords['segments'] = segments
    data_coords['section_id'] = ['section_' + chr(ord('@')+jj+1) 
                                 for jj in range(0,len(segments))]
    data_coords['section_label'] = [chr(ord('@')+jj+1) 
                                    for jj in range(0,len(segments))]
    
    # Determine the type of transect orientation
    [transect_heading, 
     _, _, _, _] = calculate_glider_bearing(np.array(data_coords['plat'][data_coords['endpts']].tolist()), 
                                            np.array(data_coords['plon'][data_coords['endpts']].tolist()), 
                                            np.array(data_coords['ptime'][data_coords['endpts']].tolist()))
    transect_type = []
    for ii in range(0,len(transect_heading)-1):

        # Heading is given in degrees from North 
        # (i.e, 0 is North, 90 is East, 180 south, -90 West)
        if ((transect_heading[ii] > 45 and transect_heading[ii] < 135)
            or
            (transect_heading[ii] > -135 and transect_heading[ii] < -45)):
            transect_type.append('latitudinal')
        else:
            transect_type.append('longitudinal')
    data_coords['orientation'] = transect_type
    
    return data_coords


# %%


def load_turning_points(outputpath, transect_id, deployment_id,
                        df, data_coords):
    
    # Get deployment section info from the deployment json
    transect_dir = os.path.join(outputpath,transect_id)
    deployment_dir = os.path.join(transect_dir, deployment_id)

    with open(os.path.join(deployment_dir, 'deployment_info.json')) as readfile:
        deployment_info = json.load(readfile)
        
        
    # Extract out the existing section IDs and labels
    section_ids = [ii['id'] for ii in deployment_info['sections']]
    section_labels = [ii['label'] for ii in deployment_info['sections']]

    # Extract out the dataframe precise time
    ptime = [(ii.to_pydatetime()).replace(tzinfo=None) 
             for ii in df.index.to_numpy()]

    # Extract our the existing section start and end times
    section_starttimes = [datetime.datetime.strptime(ii['datetime']['start'],
                                                     '%Y-%m-%dT%H:%M:%SZ')
                          for ii in deployment_info['sections']]
    section_endtimes = [datetime.datetime.strptime(ii['datetime']['end'],
                                                     '%Y-%m-%dT%H:%M:%SZ')
                          for ii in deployment_info['sections']]
    section_orientations = [ii['section_orientation'] 
                            for ii in deployment_info['sections']]

    # Find the indices in the dataframe precise time which
    # correspond with the section start and end times
    section_startinds = [np.where([ii == jj for ii in ptime])[0][0] 
                         for jj in section_starttimes]
    section_endinds = [np.where([ii == jj for ii in ptime])[0][0] 
                       for jj in section_endtimes]

    section_segments = [(section_startinds[ii], section_endinds[ii]) 
                        for ii in range(0,len(section_startinds))]
    section_endpts = np.unique(np.append(section_startinds, section_endinds)).astype(int)
    
    
    
    # Assign the data coordinates
    data_coords['endpts'] = section_endpts.astype(int)
    data_coords['segments'] = section_segments
    data_coords['section_id'] = section_ids
    data_coords['section_label'] = section_labels
    data_coords['orientation'] = section_orientations
    
        
        
    return data_coords


# %%


def great_circle_calc(lat, lon):
    
    lat_rad = np.radians(lat)
    lon_rad = np.radians(lon)
    
    R = 6370*1e3 # Radius of earth, in m
    
    dlon = lon_rad[1:] - lon_rad[:-1]
    
    fac1 = np.cos(lat_rad[1:]) * np.cos(lat_rad[:-1]) * np.cos(dlon)
    fac2 = np.sin(lat_rad[1:]) * np.sin(lat_rad[:-1])
    
    dist = R * np.arccos(fac1 + fac2)
    
    return dist


# %%


def get_segments_by_rdp(data_coords, dep_plotinfo, dist_tol=0.05, angle_tol=60):
    
    import rdp
    
    ###################################################
    # Extract out the "precise" lat/lon coordinates
    # for the start of each unique dive
    
    # Null out any points for dives outside of the lat/lon limits
    plon = data_coords['plon'].copy()
    plat = data_coords['plat'].copy()
    badloc_inds = np.logical_or(np.logical_or(plat > np.max(dep_plotinfo['latlimmap']),
                                              plat < np.min(dep_plotinfo['latlimmap'])),
                                np.logical_or(plon > np.max(dep_plotinfo['lonlimmap']),
                                              plon < np.min(dep_plotinfo['lonlimmap'])))
    if all(badloc_inds):
        print('   No points found in the lat/lon region')
        return []
    
    plat[badloc_inds] = np.nan
    plon[badloc_inds] = np.nan
    
    realcoords = np.where(np.logical_not(np.logical_or(np.logical_or(np.isnan(plon), np.isnan(plat)),
                                                       np.isnan(data_coords['ptime']))))[0]
    
    divenums, diveinds = np.unique(data_coords['divenum'][realcoords], return_index=True)
    diveinds = realcoords[diveinds]
    divelon = data_coords['plon'][diveinds]
    divelat = data_coords['plat'][diveinds]
    divetime = [pd.Timestamp(data_coords['ptime'][ind]).to_pydatetime()
                 for ind in diveinds]
    divetimeord = np.array([gliders_gen.datetime_toordinal_withseconds(ii)
                            for ii in divetime])

    
    #########################################
    # Use the Ramer-Douglas-Peucker algorithm
    # to simplify the path
    divecoords = list(map(list, zip(divelon,divelat,divetimeord)))
    
    rdp_coords = rdp.rdp(divecoords, epsilon=dist_tol)
    rdp_mask = rdp.rdp(divecoords, epsilon=dist_tol, return_mask=True)
    
    rdp_lon = np.array([rdp_coords[ii][0] 
                        for ii in range(0,len(rdp_coords))])
    rdp_lat = np.array([rdp_coords[ii][1] 
                        for ii in range(0,len(rdp_coords))])
    rdp_timeord = np.array([rdp_coords[ii][2] 
                            for ii in range(0,len(rdp_coords))])
    rdp_time = np.array([pd.Timestamp(divetime[ii]).to_pydatetime() 
                         for ii in range(0,len(divetime)) if rdp_mask[ii]])
    rdp_diveinds = np.array([diveinds[ii] for ii in range(0,len(divetime)) 
                             if rdp_mask[ii]])
    
    #########################################
    # Calculate the glider bearing 
    # (i.e., the direction the glider
    #        is heading) from the simplified path
    
    # Convert coordinates into radial coordinates
    lon_rad = np.radians(rdp_lon)
    lat_rad = np.radians(rdp_lat)

    # Calculate a turning angle for each segment
    # of the simplified path
    thet_ang = np.nan*np.zeros(len(lon_rad))
    for ii in range(0,len(thet_ang)-1):
        y = np.sin(lon_rad[ii+1] - lon_rad[ii]) * np.cos(lat_rad[ii+1])
        x = (np.cos(lat_rad[ii])*np.sin(lat_rad[ii+1]) - 
             np.sin(lat_rad[ii])*np.cos(lat_rad[ii+1])*np.cos(lon_rad[ii+1]-lon_rad[ii]))
        thet = np.arctan2(x, y)
        thet_ang[ii] = np.degrees(thet)

    # Ensure that thet_ang is on a 0-360 period
    thet_ang[thet_ang < 0] = 360 + thet_ang[thet_ang < 0]

    # Unwrap the bearing, and calculate the differnce
    # (i.e., the amount the glider turns) between
    # each segment
    thet_ang_unwrapped = np.unwrap(thet_ang, period=360)
    thet_ang_diff = np.diff(thet_ang_unwrapped)
    
    # Turns are found where the change in glider bearing
    # exceeds some threshold
    turninds = np.where(abs(thet_ang_diff)>angle_tol)[0]+1

    
    #################################
    # Extract out the segment indices
    
    # Each segment will start and end with the last point
    #
    # Additionally, the turns are found where the change in 
    # the bearing exceeds a threshold, but bearing is 
    # found by a change in vessel coordinate. 
    segments = np.unique(np.append(0, turninds)).astype(int)
    
    # Next, check the that there are no "short" segments,
    # and if so, to delete them out
    iterations = 0
    min_iters = 2
    while iterations < 2:
        segments = check_short_segments(rdp_lon, rdp_lat, rdp_time, 
                                        segments, iterations)
        iterations += 1
        
    # If we find that there are no "valid" segments,
    # be sure that the first point is still included
    # as the start of a segment, so that the only
    # valid segment runs the full length of the dataset
    if len(segments) == 0:
        segments = np.array([0])
        
    # Lastly, change the sigment index to make the dive index
    segments = np.unique(np.array([rdp_diveinds[ii] for ii in segments])).astype(int)
    
    return segments


# %%


def check_short_segments(plon, plat, ptime, segments_orig, iteration=0):
    
    segments = segments_orig.copy().astype(int)
    segments = np.append(segments, len(plon)-1).astype(int)
    dists = gliders_gen.great_circle_calc(plon, plat)
    
    nsegments = len(segments)
    if nsegments <= 0:
        print('   No segments found')
        return []
    seg_lengths = np.diff(ptime[segments])
    seg_dists = gliders_gen.great_circle_calc(plon[segments], plat[segments])
    cumdists = np.array([np.nansum(dists[int(segments[ii]):int(segments[ii+1])]) 
                         for ii in range(0,len(segments)-1)])
        
    
    # If there are any short segments
    # (i.e., less than 30 minutes, or less than 1000m traveled)
    # Find those distances, and delete them out
    if any(np.logical_or(seg_lengths < datetime.timedelta(minutes=30),
                         cumdists < 1000*(iteration+1))):
        min_segdist = np.min([1000*(iteration+1), 10000])
        short_segs = np.where(np.logical_or(seg_lengths < datetime.timedelta(minutes=30),
                                            cumdists < min_segdist))[0]
        if len(short_segs) > 0:
            segments = np.delete(segments, short_segs).astype(int)
            seg_lengths = np.delete(seg_lengths, short_segs)
            seg_dists = np.delete(seg_dists, short_segs)
            cumdists = np.delete(cumdists, short_segs)
        
        
    # Find the mean segment length;
    # perform the process iteratively to remove
    # the particularly short segments   
    seg_lengths = np.diff(ptime[segments])
    mean_segtime = np.nanmean(seg_lengths)
    mean_segdist = np.nanmean(seg_dists)
    long_segs = seg_lengths >= mean_segtime/4
    mean_count = 0
    while ((mean_segtime < np.nanmean(seg_lengths[long_segs]))
           and (mean_count < 5)):
        mean_segtime = np.nanmean(seg_lengths[long_segs])
        mean_segdist = np.nanmean(seg_dists[long_segs])
        long_segs = seg_lengths >= mean_segtime/4
        mean_count = mean_count + 1

        
    # Find the short segments
    short_segs = np.where(np.logical_or((seg_lengths < mean_segtime/4),
                                        (seg_lengths < datetime.timedelta(hours=6))))[0]


    # Check each segment, and check if the short segments
    # should be removed
    short_segs_to_remove = []
    goodinds = [True for ii in range(0,len(seg_dists))]
    for ii in range(0,len(short_segs)):
        if short_segs[ii] == 0:
            continue
        elif short_segs[ii] == len(seg_dists)-1:
            continue
        else:

            # Last good ind:
            lastgood_ind = np.where(goodinds[:short_segs[ii]])[0][-1]

            # Next good ind:
            nextgood_ind = short_segs[ii]+1+np.where(goodinds[short_segs[ii]+1:])[0][0]


            # If the duration of the segment is very short,
            # or the distance travelled is very short,
            # when compared to the average of all other segments
            # delete out that segment

            if (
                ((seg_lengths[short_segs[ii]] < 0.25*mean_segtime)
                 and
                 (seg_dists[short_segs[ii]] < 0.25*mean_segdist))
            ):

                # Update the segment number between the short segment to be the same as
                # the segment in the section before
                short_segs_to_remove.append(short_segs[ii])
                goodinds[lastgood_ind+1:nextgood_ind] = [False for ii in range(lastgood_ind+1,nextgood_ind)]
                
    # Remove the short segments
    segments = np.delete(segments, [ii for ii in short_segs_to_remove]).astype(int)
    
    return segments[:-1]


# %%


def calculate_glider_bearing(lat, lon, datatime):
    
    
    ###########################################
    # Smooth the latitude and longitude signals
    
    # Initialize copies
    lon_copy = lon.copy()
    lon_smooth = lon.copy()
    
    lat_copy = lat.copy()
    lat_smooth = lat.copy()
    
    outlier_threshold = 0.005
    
    # Perform an initial smooth
    lon_smooth = pd.Series(lon_smooth, index=datatime).rolling(window='5min', center=True).mean().to_numpy().squeeze()
    lon_outliers = np.where(abs(lon_copy[1:-1] - 
                                (lon_smooth[:-2]+lon_smooth[2:])/2) > outlier_threshold)[0]+1
    
    lat_smooth = pd.Series(lat_smooth, index=datatime).rolling(window='5min', center=True).mean().to_numpy().squeeze()
    lat_outliers = np.where(abs(lat_copy[1:-1] - 
                                (lat_smooth[:-2]+lat_smooth[2:])/2) > outlier_threshold)[0]+1

    # Null out the outliers, and smooth the data again
    if len(lon_outliers) > 0:
        lon_copy[lon_outliers] = np.nan
    if len(lat_outliers) > 0:
        lat_copy[lat_outliers] = np.nan
    
    lon_smooth = pd.Series(lon_smooth, index=datatime).rolling(window='5min', center=True).mean().to_numpy().squeeze()
    lon_outliers = np.where(abs(lon_copy[1:-1] - 
                                (lon_smooth[:-2]+lon_smooth[2:])/2) > outlier_threshold)[0]+1
    
    lat_smooth = pd.Series(lat_smooth, index=datatime).rolling(window='5min', center=True).mean().to_numpy().squeeze()
    lat_outliers = np.where(abs(lat_copy[1:-1] - 
                                (lat_smooth[:-2]+lat_smooth[2:])/2) > outlier_threshold)[0]+1

    # Null out the outliers, and smooth the data
    # one last time with a 30-minute window
    if len(lon_outliers) > 0:
        lon_copy[lon_outliers] = np.nan
    if len(lat_outliers) > 0:
        lat_copy[lat_outliers] = np.nan
    
    lon_smooth = pd.Series(lon_smooth, index=datatime).rolling(window='15min', center=True).mean().to_numpy().squeeze()
    lon_outliers = np.where(abs(lon_copy[1:-1] - 
                                (lon_smooth[:-2]+lon_smooth[2:])/2) > outlier_threshold)[0]+1
    
    lat_smooth = pd.Series(lat_smooth, index=datatime).rolling(window='15min', center=True).mean().to_numpy().squeeze()
    lat_outliers = np.where(abs(lat_copy[1:-1] - 
                                (lat_smooth[:-2]+lat_smooth[2:])/2) > outlier_threshold)[0]+1
    
    
    
    #########################################
    # Convert latitude and longitude from 
    # degrees to radians
    lon_rad = np.radians(lon_smooth)
    lat_rad = np.radians(lat_smooth)

    
    #########################################
    # Calculate the glider bearing 
    # (i.e., the direction the glider
    #        is heading)
    thet_ang = np.nan*np.zeros(len(lon_rad))
    for ii in range(0,len(thet_ang)-1):
        y = np.sin(lon_rad[ii+1] - lon_rad[ii]) * np.cos(lat_rad[ii+1])
        x = (np.cos(lat_rad[ii])*np.sin(lat_rad[ii+1]) - 
             np.sin(lat_rad[ii])*np.cos(lat_rad[ii+1])*np.cos(lon_rad[ii+1]-lon_rad[ii]))
        thet = np.arctan2(x, y)
        thet_ang[ii] = np.degrees(thet)

    # Ensure that thet_ang is on a 0-360 period
    thet_ang[thet_ang < 0] = 360 + thet_ang[thet_ang < 0]

        
    ##########################################
    # Smooth out any outliers in the direction
    
    # Make a copy of the original, calculated bearing,
    # and define the outlier threshold
    thet_ang_copy = thet_ang.copy()
    outlier_threshold = 40
    
    # Find individual spikes where there are single points that are significantly
    # further out than the two points around them
    thet_ang_diff = np.diff(np.unwrap(thet_ang,period=360))
    thet_ang_doubdiff = np.unwrap(thet_ang,period=360)[2:] - np.unwrap(thet_ang,period=360)[:-2]
    # Find spike inds, defined as where the change from one point to the next exceeds 45 degrees,
    # but the change from one point to two points later is less than 15 degrees
    # (this indicates a relatively large local jump)
    spikeinds = np.where(np.logical_and(abs(thet_ang_diff[:-1]) > 45,
                                        abs(thet_ang_doubdiff) < 15))[0]+1
    # NaN out the spike inds
    thet_ang_copy[spikeinds] = np.nan
    
    # Unwrap the angles
    thet_ang_unwrap = thet_ang_copy.copy()
    thet_ang_unwrap[~np.isnan(thet_ang_copy)] = np.unwrap(thet_ang_copy[~np.isnan(thet_ang_copy)], period=360)

    # Smooth the unwrapped angle with a 30-minute centered window
    thet_ang_lightsmooth = pd.Series(thet_ang_unwrap, index=datatime).rolling(window='0.5min', center=True).mean().to_numpy().squeeze()
    thet_ang_smooth = pd.Series(thet_ang_unwrap, index=datatime).rolling(window='15min', center=True).mean().to_numpy().squeeze()
    
    # Identify any outliers as where the smoothed angle deviates from
    # the raw angle by more than 10 degrees
    outliers = np.where(abs(thet_ang_unwrap[1:-1] - 
                            (thet_ang_smooth[:-2]+thet_ang_smooth[2:])/2) > outlier_threshold)[0]+1
    
    # Null out the outliers, re-unwrap the data, and
    # smooth the data again
    thet_ang_copy[outliers] = np.nan
    thet_ang_unwrap = thet_ang_copy.copy()
    thet_ang_unwrap[~np.isnan(thet_ang_copy)] = np.unwrap(thet_ang_copy[~np.isnan(thet_ang_copy)], period=360)
    thet_ang_smooth = pd.Series(thet_ang_unwrap, index=datatime).rolling(window='15min', center=True).mean().to_numpy().squeeze()
    
    # Identify any outliers as where the smoothed angle deviates from
    # the raw angle by more than 30 degrees
    outliers = np.where(abs(thet_ang_unwrap[1:-1] - 
                            (thet_ang_smooth[:-2]+thet_ang_smooth[2:])/2) > outlier_threshold)[0]+1
    
    # Null out the outliers, re-unwrap the data, and
    # smooth the data one last time
    thet_ang_copy[outliers] = np.nan
    thet_ang_unwrap = thet_ang_copy.copy()
    thet_ang_unwrap[~np.isnan(thet_ang_copy)] = np.unwrap(thet_ang_copy[~np.isnan(thet_ang_copy)], period=360)
    thet_ang_smooth = pd.Series(thet_ang_unwrap, index=datatime).rolling(window='30min', center=True).mean().to_numpy().squeeze()
    
    # Identify any outliers as where the smoothed angle deviates from
    # the raw angle by more than 30 degrees
    outliers = np.where(abs(thet_ang_unwrap[1:-1] - 
                            (thet_ang_smooth[:-2]+thet_ang_smooth[2:])/2) > 0.5*outlier_threshold)[0]+1
    thet_ang_smooth[outliers] = thet_ang_lightsmooth[outliers]
    
    # Re-wrap the data so that it is in a -180 to 180 degree range
    thet_ang = thet_ang % 360
    thet_ang[thet_ang > 180] = thet_ang[thet_ang > 180] - 360
    
    thet_ang_smooth_wrapped = thet_ang_smooth.copy()
    thet_ang_smooth = thet_ang_smooth % 360
    thet_ang_smooth[thet_ang_smooth > 180] = thet_ang_smooth[thet_ang_smooth > 180] - 360
    
    return thet_ang, thet_ang_smooth, thet_ang_smooth_wrapped, lon_smooth, lat_smooth


# %%


def get_segments_from_bearing(bearing_smooth, bearing_wrapped, ptime, plon, plat):
    
    
    # Find initial jumps in the bearing
    goodinds = np.logical_not(np.isnan(bearing_smooth))
    bearing_unwrapped = bearing_smooth.copy()
    bearing_unwrapped[bearing_unwrapped < 0] = 360 + bearing_unwrapped[bearing_unwrapped < 0]
    bearing_unwrapped[goodinds] = np.unwrap(bearing_unwrapped[np.logical_not(np.isnan(bearing_unwrapped))],360)
    dbearing_smooth = bearing_unwrapped[10:]-bearing_unwrapped[:-10]
    
    if any(np.logical_and(np.logical_not(np.isnan(plon)),
                          np.logical_not(np.isnan(plat)))):
        last_goodpoint = np.where(np.logical_and(np.logical_not(np.isnan(plon)),
                                                 np.logical_not(np.isnan(plat))))[0][-1]-1
    else:
        last_goodpoint = len(plon)-1
    segments = np.where(abs(dbearing_smooth) > 45)[0]+10
    if any(np.diff(segments) == 1):
        segments = np.delete(segments, np.where(np.diff(segments)==1)[0]+1)
    segments = np.append(0,segments)
    segments = np.append(segments, last_goodpoint)
    
    dists = gliders_gen.great_circle_calc(plon, plat)
    
    
    
    
    # This is an iterative process; try stepping through it at least twice
    if len(segments) > 2:
        keep_iterating = True
    else:
        keep_iterating = False
    iterations = 0
    while keep_iterating:

        nsegments = len(segments)
        seg_lengths = np.diff(ptime[segments])
        seg_dists = gliders_gen.great_circle_calc(plon[segments], plat[segments])
        cumdists = np.array([np.nansum(dists[int(segments[ii]):int(segments[ii+1])]) 
                             for ii in range(0,len(segments)-1)])
        mean_bearing, _, _, _, _ = calculate_glider_bearing(plat[segments], plon[segments], ptime[segments])
        
        if any(np.logical_or(seg_lengths < datetime.timedelta(minutes=30),
                             cumdists < 1000)):
            min_segdist = np.min([1000*(iterations+1), 10000])
            short_segs = np.where(np.logical_or(seg_lengths < datetime.timedelta(minutes=30),
                                                cumdists < min_segdist))[0]
            if len(short_segs) > 0:
                segments = np.delete(segments, short_segs).astype(int)
                seg_lengths = np.delete(seg_lengths, short_segs)
                seg_dists = np.delete(seg_dists, short_segs)
                cumdists = np.delete(cumdists, short_segs)
                mean_bearing = np.delete(mean_bearing, short_segs)
        
        
        # Find the mean segment length;
        # perform the process iteratively to remove
        # the particularly short segments   
        seg_lengths = np.diff(ptime[segments])
        mean_segtime = np.nanmean(seg_lengths)
        mean_segdist = np.nanmean(seg_dists)
        long_segs = seg_lengths >= mean_segtime/4
        mean_count = 0
        while ((mean_segtime < np.nanmean(seg_lengths[long_segs]))
               and (mean_count < 5)):
            mean_segtime = np.nanmean(seg_lengths[long_segs])
            mean_segdist = np.nanmean(seg_dists[long_segs])
            long_segs = seg_lengths >= mean_segtime/4
            mean_count = mean_count + 1

            
        # Find the mean bearing for each segment
        mean_bearing = mean_bearing[:-1]
        std_bearing = []
        for ii in range(0,len(segments)-1):
            std_bearing.append(np.nanstd(bearing_smooth[int(segments[ii]):int(segments[ii+1])]))
        

        # Find the short segments
        short_segs = np.where(np.logical_or((seg_lengths < mean_segtime/4),
                                            (seg_lengths < datetime.timedelta(hours=6))))[0]
            

        # Check each segment, and check if the short segments
        # should be removed
        short_segs_to_remove = []
        goodinds = [True for ii in range(0,len(mean_bearing))]
        for ii in range(0,len(short_segs)):
            if short_segs[ii] == 0:
                continue
            elif short_segs[ii] == len(mean_bearing)-1:
                continue
            else:

                # Last good ind:
                lastgood_ind = np.where(goodinds[:short_segs[ii]])[0][-1]

                # Next good ind:
                nextgood_ind = short_segs[ii]+1+np.where(goodinds[short_segs[ii]+1:])[0][0]
                

                # If the angle between each segment before and after
                # the short segment is very small, assume
                # that the short segment is not a real segment
                if (
                    (abs(mean_bearing[lastgood_ind] - mean_bearing[nextgood_ind]) < 45)
                    or
                    (abs((mean_bearing[lastgood_ind]+360)%360 - 
                         (mean_bearing[nextgood_ind]+360)%360) < 45)
                    or (std_bearing[short_segs[ii]] > 45)
                ):                    

                    # Update the segment number between the short segment to be the same as
                    # the segment in the section before
                    #seg_num[segments[lastgood_ind]:segments[nextgood_ind]] = seg_num[segments[lastgood_ind]]
                    short_segs_to_remove.append(short_segs[ii])
                    goodinds[lastgood_ind+1:nextgood_ind] = [False for ii in range(lastgood_ind+1,nextgood_ind)]
                    
                    
                elif (
                    ((abs(mean_bearing[lastgood_ind] - mean_bearing[short_segs[ii]]) < 45)
                     or
                     (abs((mean_bearing[lastgood_ind]+360)%360 - 
                          (mean_bearing[short_segs[ii]]+360)%360) < 45))
                    and ((seg_lengths[short_segs[ii]] < 0.25*mean_segtime)
                         or
                         (seg_dists[short_segs[ii]] < 0.25*mean_segdist))
                ):

                    # Update the segment number between the short segment to be the same as
                    # the segment in the section before
                    #seg_num[segments[lastgood_ind]:segments[nextgood_ind]] = seg_num[segments[lastgood_ind]]
                    short_segs_to_remove.append(short_segs[ii])
                    goodinds[lastgood_ind+1:nextgood_ind] = [False for ii in range(lastgood_ind+1,nextgood_ind)]
                    
                    
                elif (
                    ((abs(mean_bearing[short_segs[ii]] - mean_bearing[nextgood_ind]) < 45)
                     or
                     (abs((mean_bearing[short_segs[ii]]+360)%360 - 
                          (mean_bearing[nextgood_ind]+360)%360) < 45))
                    and ((seg_lengths[short_segs[ii]] < 0.25*mean_segtime)
                         or
                         (seg_dists[short_segs[ii]] < 0.25*mean_segdist))
                ):

                    # Update the segment number between the short segment to be the same as
                    # the segment in the section before
                    #seg_num[segments[lastgood_ind]:segments[nextgood_ind]] = seg_num[segments[lastgood_ind]]
                    short_segs_to_remove.append(nextgood_ind)
                    goodinds[short_segs[ii]] = True
                    goodinds[nextgood_ind] = False



        # Remove the short segments
        mean_bearing = np.delete(mean_bearing, short_segs_to_remove)
        std_bearing = np.delete(std_bearing, short_segs_to_remove)
        segments = np.delete(segments, [ii for ii in short_segs_to_remove]).astype(int)
        seg_lengths = np.diff(ptime[segments])
        seg_dists = gliders_gen.great_circle_calc(plon[segments], plat[segments])
        cumdists = np.array([np.nansum(dists[int(segments[ii]):int(segments[ii+1])]) 
                             for ii in range(0,len(segments)-1)])
        
        if len(short_segs_to_remove) == 0:
            keep_iterating = False



        # Step through each segment, and if the mean bearing of the
        # segment is very close to the segment before,
        # or if the standard deviation of the segment is very large
        # for a relatively short segment (i.e., no distinct path), 
        # then remove the the second segment
        short_segs = []
        for ii in range(1,len(mean_bearing)):
            if (
                ((abs(mean_bearing[ii] - mean_bearing[ii-1]) < 45)
                 or
                 (abs((mean_bearing[ii]+360)%360 - (mean_bearing[ii-1]+360)%360) < 45))
                or
                ((std_bearing[ii] > 90) and (seg_lengths[ii] < mean_segtime/4) and (cumdists[ii] < 1.5*seg_dists[ii]))
            ):
                short_segs.append(ii)
        mean_bearing = np.delete(mean_bearing, short_segs)
        std_bearing = np.delete(std_bearing, short_segs)
        segments = np.delete(segments, [ii for ii in short_segs]).astype(int)
        seg_lengths = np.diff(ptime[segments])
        seg_dists = gliders_gen.great_circle_calc(plon[segments], plat[segments])
        cumdists = np.array([np.nansum(dists[int(segments[ii]):int(segments[ii+1])]) 
                             for ii in range(0,len(segments)-1)])
        
        
        
        # Step through each short segment, and if the time of the segment
        # is short, and the distance traveled since the end of the last segment
        # is short, remove the segment
        short_segs = []
        for ii in range(1,len(mean_bearing)):
            if (
                (seg_lengths[ii] < mean_segtime/10) and (seg_dists[ii] < 0.1*mean_segdist)
            ):
                short_segs.append(ii)
        mean_bearing = np.delete(mean_bearing, short_segs)
        std_bearing = np.delete(std_bearing, short_segs)
        segments = np.delete(segments, [ii for ii in short_segs]).astype(int)
        seg_lengths = np.diff(ptime[segments])
        seg_dists = gliders_gen.great_circle_calc(plon[segments], plat[segments])
        cumdists = np.array([np.nansum(dists[int(segments[ii]):int(segments[ii+1])]) 
                             for ii in range(0,len(segments)-1)])
        
        
        # Step through each segment, and check if any have been improperly
        # merged together. These are likely long segments with large
        # standard deviations in the bearings
        
        check_longsegs = False
        if check_longsegs:
            long_segs = []
            for ii in range(0,len(mean_bearing)-1):
                if (
                    (std_bearing[ii] > 60)
                    and
                    (seg_lengths[ii] > 1.5*mean_segtime)
                    and
                    (cumdists[ii] > 1.5*seg_dists[ii])
                ):
                    lonrange = (np.nanmax(plon[segments[ii:ii+1]]) -
                                np.nanmin(plon[segments[ii:ii+1]]))
                    latrange = (np.nanmax(plat[segments[ii:ii+1]]) -
                                np.nanmin(plat[segments[ii:ii+1]]))
                    if lonrange > latrange:
                        newind = segments[ii]                   
                    elif latrange > lonrange:
                        newind = segments[ii]
        
        
        # Increase the count of the number of iterations, and check
        # if the system should keep going
        
        iterations = iterations + 1
        if (iterations > 10) or (len(segments) == nsegments):
            keep_iterating = False
    
    if len(segments) > 1:
        segments = segments[:-1]
    
    return segments


# %%


def make_output_folders(outputpath, transect_id, deploy_id, sections):
    
    # Build a list of folders that are needed for output
    pathname = os.path.join(outputpath, transect_id)
    folderpath = [pathname]
    folderpath.append(os.path.join(pathname, deploy_id))
    for ii in range(0,len(sections)):
        folderpath.append(os.path.join(pathname, deploy_id, sections[ii]))
        folderpath.append(os.path.join(pathname, deploy_id, sections[ii], 'scientific'))
    
    # Step through the list of needed folders, and if they do not 
    # yet exist, make the folder
    for folder in folderpath:
        if not(os.path.exists(folder)):
            try:
                os.mkdir(folder)
            except OSError:
                print ('Directory %s already exists' % folder)
            else:
                print ('Successfully created the directory %s ' % folder)


# %%


def make_transect_path_plot(outputpath, transect_id, 
                            dep_plotinfo, data_coords):
        
    
    #############################################################
    # plot endpoints connected by lines to see if path looks as expected
    plat = data_coords['plat']
    plon = data_coords['plon']
    ptime = data_coords['ptime'].to_pydatetime()
    ptime = [ii.replace(tzinfo=None) for ii in ptime]
    ptime = [(ii-ptime[0]).total_seconds() for ii in ptime]

    minlon = np.min([dep_plotinfo['lonlimmap'][0],
                     np.floor(10*np.nanmin(plon))/10])
    maxlon = np.max([dep_plotinfo['lonlimmap'][0],
                     np.ceil(10*np.nanmax(plon))/10])
    minlat = np.min([dep_plotinfo['latlimmap'][0],
                     np.floor(10*np.nanmin(plat))/10])
    maxlat = np.max([dep_plotinfo['lonlimmap'][0],
                     np.ceil(10*np.nanmax(plat))/10])


    fig,ax = plt.subplots(nrows=2, figsize=(9,9))
    ax[0].plot(data_coords['plon'][data_coords['endpts']],
               data_coords['plat'][data_coords['endpts']],'ro-')
    ax[0].scatter(plon, plat, s=2, c=ptime, alpha=0.5)
    ax[0].plot([dep_plotinfo['lonlimmap'][0], dep_plotinfo['lonlimmap'][0], 
                dep_plotinfo['lonlimmap'][1], dep_plotinfo['lonlimmap'][1],
                dep_plotinfo['lonlimmap'][0]],
               [dep_plotinfo['latlimmap'][0], 
                dep_plotinfo['latlimmap'][1], dep_plotinfo['latlimmap'][1], 
                dep_plotinfo['latlimmap'][0], dep_plotinfo['latlimmap'][0]], 
               '--k', alpha=0.25, label='Original Limits')
    for ii in range(0,len(data_coords['section_label'])):
        ax[0].annotate(data_coords['section_label'][ii],
                       (data_coords['plon'][data_coords['endpts'][ii]], 
                        data_coords['plat'][data_coords['endpts'][ii]]))
    ax[0].set_ylim([minlat, maxlat])
    ax[0].set_xlim([minlon, maxlon])
    ax[0].set_ylabel('Latitude')
    ax[0].set_xlabel('Longitude')
    ax[0].legend(loc='lower left')
    ax[0].set_position([0.1, 0.425, 0.85, 0.525])

    ax[1].plot(data_coords['ptime'][data_coords['endpts']], 
               data_coords['plon'][data_coords['endpts']], '--*')
    for ii in range(0,len(data_coords['section_label'])):
        ax[1].annotate(data_coords['section_label'][ii],
                       (data_coords['ptime'][data_coords['endpts'][ii]], 
                        data_coords['plon'][data_coords['endpts'][ii]]))
    ax[1].set_position([0.1, 0.075, 0.85, 0.275])
    
    figpath = os.path.join(outputpath, transect_id, dep_plotinfo['id'], 'transect_path')
    plt.savefig(figpath)
    plt.close(fig)
    
    return


# %%


def make_section_plots(outputpath, transect_id, transect_label, dep_plotinfo, 
                       metadata, datadict, data_coords, 
                       section_start, section_end, section_id, section_orientation):
    
    
    #######################
    # plot specifications #
    #######################

    plotVars = {name: None for name in dep_plotinfo['variables_id']}
    for iii, varid in enumerate(plotVars.keys()):
        plotVars[varid] = {'data': datadict[varid], 'limits': dep_plotinfo['variables_limits'][iii],
            'label': dep_plotinfo['variables_label'][iii], 'units': dep_plotinfo['variables_units'][iii], 
            'cmap': 'rainbow'}

    #######################
    # plot depth profiles #
    #######################
    print('      ' + datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S') + ' - Plotting depth-longitude transects for section '+section_id+'...')
    for key2 in plotVars.keys():
        var = plotVars[key2]['data']
        varmin = plotVars[key2]['limits'][0]
        varmax = plotVars[key2]['limits'][1]
        varcmap = plotVars[key2]['cmap']
        varname = plotVars[key2]['label'] + ' ' + plotVars[key2]['units']

        if 'Ongoing' not in dep_plotinfo['id']:
            markersize=15
        else:
            markersize=30
                    
        if 'oxygen' in varname.lower():
            varcmap = make_oxy_colormap(varmin, varmax)
            
        
        depthlims = dep_plotinfo['depthlimtransect']
        
        upperzlims = [ii for ii in depthlims[:-1]]
        lowerzlims = [ii for ii in depthlims[1:]]
        
        if section_orientation == 'longitudinal':
            xvar = data_coords['plon'][section_start:section_end+1]
        elif section_orientation == 'latitudinal':
            xvar = data_coords['plat'][section_start:section_end+1]
        else:
            print('Invalid section orientation. Check value, and replot.')
            return
        zvar = data_coords['depth'][section_start:section_end+1]
        
            
        # make and save scientific plots
        fig, axes = plt.subplots(nrows=len(upperzlims), ncols=1, figsize=(15, 6))
        for zz in range(0,len(upperzlims)):
            if len(upperzlims) == 1:
                ax = axes
            else:
                ax = axes[zz]
            upperzlim = upperzlims[zz]
            lowerzlim = lowerzlims[zz]
            cs = ax.scatter(xvar, zvar, 
                            c=var, s=markersize, marker='o', edgecolor='none',
                            vmin=varmin, vmax=varmax, cmap=varcmap
            )

            ax.set_facecolor('lightgrey')

            # add bathymetry
            shade_bathy = True
            if shade_bathy:
                ax.plot(xvar,
                        -data_coords['gliderdepths'][section_start:section_end+1],
                        linestyle='-', color='darkgrey')
                ax.fill_between(xvar,
                                -data_coords['gliderdepths'][section_start:section_end+1],
                                dep_plotinfo['depthlimtransect'][-1]*np.ones(len(xvar))+1,
                                alpha=0.5, color='dimgrey')
                ax.fill_between(xvar,
                                -data_coords['gliderdepths'][section_start:section_end+1],
                                dep_plotinfo['depthlimtransect'][-1]*np.ones(len(xvar))+1,
                                alpha=0.75, hatch='\\\//', color='none', 
                                edgecolor='silver', linewidth=0.5, linestyle='--')
            else:            
                ax.plot(xvar,
                         -data_coords['gliderdepths'][section_start:section_end+1],
                         linestyle='-', color='black')

            # label time interval, make sure labels reflect glider direction of travel
            plot_fontSize=14
            if zz == len(upperzlims)-1:
                if section_orientation == 'longitudinal':
                    if abs(data_coords['plon'][section_start]) > abs(data_coords['plon'][section_end]): 
                        # moving offshore to onshore
                        ax.text(dep_plotinfo['lonlimtransect'][0]+0.01, 
                                lowerzlim-5, 
                                data_coords['ptime'][section_start].strftime('%Y-%m-%d\n%H:%M:%S UTC'), 
                                fontsize=plot_fontSize, fontdict=None, ma='left', ha='left')
                        ax.text(dep_plotinfo['lonlimtransect'][1]-0.01, 
                                lowerzlim-5, 
                                data_coords['ptime'][section_end].strftime('%Y-%m-%d\n%H:%M:%S UTC'), 
                                fontsize=plot_fontSize, fontdict=None, ma='right', ha='right')

                    else: 
                        # moving onshore to offshore
                        ax.text(dep_plotinfo['lonlimtransect'][0]+0.01, 
                                lowerzlim-5, 
                                data_coords['ptime'][section_end].strftime('%Y-%m-%d\n%H:%M:%S UTC'), 
                                fontsize=plot_fontSize, fontdict=None, ma='left', ha='left')
                        ax.text(dep_plotinfo['lonlimtransect'][1]-0.01, 
                                lowerzlim-5, 
                                data_coords['ptime'][section_start].strftime('%Y-%m-%d\n%H:%M:%S UTC'), 
                                fontsize=plot_fontSize, fontdict=None, ma='right', ha='right')
                else:
                    if abs(data_coords['plat'][section_start]) < abs(data_coords['plat'][section_end]): 
                        # moving offshore to onshore
                        ax.text(dep_plotinfo['latlimtransect'][0]+0.01, 
                                lowerzlim-5, 
                                data_coords['ptime'][section_start].strftime('%Y-%m-%d\n%H:%M:%S UTC'), 
                                fontsize=plot_fontSize, fontdict=None, ma='left', ha='left')
                        ax.text(dep_plotinfo['latlimtransect'][1]-0.01, 
                                lowerzlim-5, 
                                data_coords['ptime'][section_end].strftime('%Y-%m-%d\n%H:%M:%S UTC'), 
                                fontsize=plot_fontSize, fontdict=None, ma='right', ha='right')

                    else: 
                        # moving onshore to offshore
                        ax.text(dep_plotinfo['latlimtransect'][0]+0.01, 
                                lowerzlim-5, 
                                data_coords['ptime'][section_end].strftime('%Y-%m-%d\n%H:%M:%S UTC'), 
                                fontsize=plot_fontSize, fontdict=None, ma='left', ha='left')
                        ax.text(dep_plotinfo['latlimtransect'][1]-0.01, 
                                lowerzlim-5, 
                                data_coords['ptime'][section_start].strftime('%Y-%m-%d\n%H:%M:%S UTC'), 
                                fontsize=plot_fontSize, fontdict=None, ma='right', ha='right')

            # labels, legends, colorbars
            if section_orientation == 'longitudinal':
                xlab = 'Longitude'
                ax.set_xlim(dep_plotinfo['lonlimtransect'])
            else:
                xlab = 'Latitude'
                ax.set_xlim(dep_plotinfo['latlimtransect'])
            
            ylab = 'Depth (m)'
            ax.set_ylim([upperzlim,lowerzlim])
            ax.invert_yaxis()
            ax.set_ylabel(ylab,fontsize=plot_fontSize)
            ax.tick_params(axis='y', labelsize=plot_fontSize)
            
            if zz == len(upperzlims)-1:
                ax.set_xlabel(xlab,fontsize=plot_fontSize)
                ax.tick_params(axis='x', labelsize=plot_fontSize)
            else:
                ax.set_title(transect_label,fontsize=plot_fontSize+2)
                ax.tick_params(axis='x', which='major', 
                               labelbottom=False, bottom=False)
                
            if len(upperzlims) > 1:
                if zz == 0:
                    ax.spines['bottom'].set_linestyle((0, (10, 5)))        
                    #ax.spines['bottom'].set_linewidth(0.5)
                    yticks = ax.get_yticks()
                    yticklabels = ax.get_yticklabels()
                    yticklabels[-1] = ''
                    ax.set_yticks(yticks)
                    ax.set_yticklabels(yticklabels)
                else:
                    ax.spines['top'].set_linestyle((0, (10, 5)))
                    #ax.spines['top'].set_linewidth(0.5)
            
        
        cbar = fig.colorbar(cs, orientation='vertical')#, extend="both")
        cbar.ax.set_ylabel(varname,fontsize=plot_fontSize)
        cbar.ax.tick_params(labelsize=plot_fontSize)
        
        set_figsize = True
        if set_figsize:
            if len(upperzlims) == 1:
                ax.set_position([0.075, 0.1125, 0.8, 0.8])
            else:
                yoffset = 0.01
                topheight = 0.4*(0.8-yoffset)
                botheight = 0.6*(0.8-yoffset)
                axes[0].set_position([0.075, 0.1125+botheight+yoffset, 0.8, topheight])
                axes[1].set_position([0.075, 0.1125, 0.8, botheight])
            cbar.ax.set_position([0.9, 0.1125, 0.05, 0.8])
        
        
        
        
        

        # save plot into the "scientific" units folders
        figdir = os.path.join(outputpath, transect_id, dep_plotinfo['id'],
                               section_id, 'scientific')
        try:
            os.makedirs(figdir, exist_ok=True)
        except Exception:
            pass
        figpath = os.path.join(figdir, key2)
        plt.savefig(figpath)
        
        fig.clf()
        plt.close(fig)
        gc.collect()
        
    return

def make_section_data_json(outputpath, transect_id, dep_plotinfo,
                           datadict, data_coords, varid, section_ind, depth_step=10):
    
    # Extract the data for the section
    datavar = np.array(datadict[varid])
    section_start = data_coords['endpts'][section_ind]
    section_end = data_coords['endpts'][section_ind+1]
    xvar = data_coords['plon'][section_start:section_end+1]
    yvar = data_coords['plat'][section_start:section_end+1]
    zvar = data_coords['depth'][section_start:section_end+1]
    section_time = data_coords['atime'][section_start:section_end+1]
    bathyvar = data_coords['gliderdepths'][section_start:section_end+1]
    divenums = data_coords['divenum'][section_start:section_end+1]
    orientation = data_coords['orientation'][section_ind]

    if len(datavar) == 0:
        print('\t\tNo data present for variable ' + varid + ' in section ' +
                  data_coords['section_id'][section_ind] + '; skipping JSON creation.')
        return
        #datavar = np.nan*np.zeros(len(xvar))
    
    # Remove any NaN values from the data
    if any(np.isnan(datavar)):
        valid_inds = np.where(np.logical_and(np.logical_and(~np.isnan(datavar),
                                                            ~np.isnan(zvar)),
                                             np.logical_and(~np.isnan(xvar),
                                                            ~np.isnan(yvar))))[0]
        if len(valid_inds) == 0:
            print('\t\tNo valid data for variable ' + varid + ' in section ' +
                  data_coords['section_id'][section_ind] + '; skipping JSON creation.')
            return
        xvar = xvar[valid_inds]
        yvar = yvar[valid_inds]
        zvar = zvar[valid_inds]
        datavar = datavar[valid_inds]
        section_time = section_time[valid_inds]
        bathyvar = bathyvar[valid_inds]
        divenums = divenums[valid_inds]

    # Build the section data dictionary
    section_id = data_coords['section_id'][section_ind]

    # Identify the unique dives for the section
    unique_dives = np.unique(divenums)
    ref_time = datetime.datetime(1970,1,1)
    
    sorting_spatial = True
    if sorting_spatial:
        # Sort the dives by their position along the transect

        # If the dominant orientation of the section is along the longitude, sort
        # by longitude; if along the latitude, sort by latitude
        dive_pos = []
        for dd in range(0,len(unique_dives)):
            dive = unique_dives[dd]
            dive_inds = np.where(divenums == dive)[0]
            if orientation == 'longitudinal':
                dive_pos.append(xvar[dive_inds[0]])
            elif orientation == 'latitudinal':
                dive_pos.append(yvar[dive_inds[0]])
        sortinds = np.argsort(dive_pos)
        unique_dives = unique_dives[sortinds]

    else:
        # Check that the starting time for each unique dive is in chronological order
        dive_start_times = []
        for dd in range(0,len(unique_dives)):
            dive = unique_dives[dd]
            dive_inds = np.where(divenums == dive)[0]
            dive_start_times.append(datetime.datetime.strptime(section_time[dive_inds[0]],
                                                            '%Y-%m-%dT%H:%M:%SZ'))
        sorted_inds = np.argsort(dive_start_times)
        unique_dives = unique_dives[sorted_inds]


    # Extract the transect position for the first dive
    first_divelon = np.round(xvar[np.where(divenums == unique_dives[0])[0][0]],6)
    first_divelat = np.round(yvar[np.where(divenums == unique_dives[0])[0][0]],6)

    # Extract the transect position for the last dive
    last_divelon = np.round(xvar[np.where(divenums == unique_dives[-1])[0][0]],6)
    last_divelat = np.round(yvar[np.where(divenums == unique_dives[-1])[0][0]],6)

    # Get some limits, based on the deployment info
    depthlims = dep_plotinfo['depthlimtransect']

    # Variable min/max values
    if len(datavar) > 0 and sum(np.logical_not(np.isnan(datavar))) > 0:
        varmin = np.floor(10*np.nanmin(datavar))/10
        varmax = np.ceil(10*np.nanmax(datavar))/10
    else:
        varmin = np.nan
        varmax = np.nan

    plotVars = {name: None for name in dep_plotinfo['variables_id']}
    for iii, plotVarid in enumerate(plotVars.keys()):
        plotVars[plotVarid] = {'data': datadict[plotVarid], 'limits': dep_plotinfo['variables_limits'][iii],
            'label': dep_plotinfo['variables_label'][iii], 'units': dep_plotinfo['variables_units'][iii], 
            'cmap': 'rainbow'}
    plotVar = plotVars[varid]
    plotVarmin = plotVar['limits'][0]
    plotVarmax = plotVar['limits'][1]



    # Begin to build the section data json dictionary,
    # with the data and bathymetry to be added later
    section_data = {
        "transect_id": transect_id,
        "deployment_id": dep_plotinfo['id'],
        "section_id": section_id,
        "variable_id": varid,
        "properties": {
            "depth": {"top": 0, "bottom": depthlims[-1]},
            "value": {"min": plotVarmin, "max": plotVarmax},
            "units": plotVar['units'],
            "transect": [
                {"lat": first_divelat, "lon": first_divelon},
                {"lat": last_divelat, "lon": last_divelon}
            ]
        },
        "data": [],
        "bathymetry": []
    }
    # Add a transition point for oxygen
    if varid.lower() == 'do':
        section_data['properties']['value']['transition'] = 2.0

    # Step through each unique dive in the section
    # and add bathymetry position and depth
    for dd in range(0,len(unique_dives)):
        dive = unique_dives[dd]
        dive_inds = np.where(divenums == dive)[0]
        # Add the bathymetry data for each dive
        section_data["bathymetry"].append({
            "lat": np.round(yvar[dive_inds[0]],6),
            "lon": np.round(xvar[dive_inds[0]],6),
            'depth': -np.round(bathyvar[dive_inds[0]],2)          
            }
        )

        # Initialize the new dive dictionary for the current dive
        newdive = {
            "lat": np.round(yvar[dive_inds[0]],6),
            "lon": np.round(xvar[dive_inds[0]],6),
            "timestamp": int((datetime.datetime.strptime(section_time[dive_inds[0]],'%Y-%m-%dT%H:%M:%SZ')-ref_time).total_seconds()),
            "dive_number": int(dive),
            "values": []
        }

        # Define the data target depths in the current dive
        target_depths = np.arange(np.floor(depth_step*np.nanmin(zvar[dive_inds]))/depth_step, 
                                  np.ceil(depth_step*np.nanmax(zvar[dive_inds]))/depth_step, depth_step)
                
        # Get the depths and values nearest to each target depth
        nearest_indices = [np.argmin(np.abs(zvar[dive_inds] - td)) for td in target_depths]
        nearest_depths = zvar[dive_inds][nearest_indices]
        nearest_values = datavar[dive_inds][nearest_indices]
        if len(nearest_indices) == 0:
            continue

        # Step through each point in the dive, and add the depth and value to the json
        for point in range(0,len(nearest_depths)):
            newdive["values"].append({
                "depth": np.round(nearest_depths[point],2),
                "value": nearest_values[point]
            })
        section_data["data"].append(newdive)

    # Create a function to make sure all data is json serializable
    def json_safe(obj):
        if obj is None:
            return None
        if isinstance(obj, float):
            return None if np.isnan(obj) or np.isinf(obj) else obj
        if isinstance(obj, (np.floating,)):
            v = float(obj)
            return None if np.isnan(v) or np.isinf(v) else v
        if isinstance(obj, (np.integer,)):
            return int(obj)
        if isinstance(obj, (np.ndarray,)):
            return [json_safe(x) for x in obj.tolist()]
        if isinstance(obj, dict):
            return {k: json_safe(v) for k, v in obj.items()}
        if isinstance(obj, (list, tuple)):
            return [json_safe(x) for x in obj]
        return obj
        

    # Save the section data json
    json_dir = os.path.join(outputpath, transect_id, dep_plotinfo['id'],
                            section_id, 'scientific_data')
    try:
        os.makedirs(json_dir, exist_ok=True)
    except Exception:
        print('Directory %s already exists' % json_dir)
        pass
    jsonpath = os.path.join(json_dir, f"{varid}_data.json")
    # Write out the section data dictionary to a json file,
    # while also ensuring that all the data is json serializable
    with open(jsonpath, 'w') as outfile:
        json.dump(json_safe(section_data), outfile)


# %%


def make_plots_for_transect(transect_id, deployment_id=None):
    
    # run init_params.py to define all required parameters when new deployment added
    # load init_params.json file
    __, __, outputpath = gliders_gen.get_pathdirs()
    
    transect_basedir = outputpath
    transect_dir = os.path.join(transect_basedir,transect_id)
    
    [glider_info, gliderplot_info] = gliders_gen.load_glider_info_all(transect_id)
    
    successFlag = True
    
    ###############################
    make_plots_flag = True
    update_jsons_flag = True

    # load the data, id the glider sections, and make the plots
    if deployment_id is not None:
        if deployment_id.lower() == 'all':
            dep_inds = range(0,len(glider_info['deployments']))
            for dep_ind in dep_inds:
                glider_info['deployments'][dep_ind]['plotting_active'] = True
        else:
            dep_inds = [ii for ii in range(0,len(glider_info['deployments'])) 
                        if glider_info['deployments'][ii]['id'] == deployment_id]
            if len(dep_inds) == 0:
                print('   NOTE: Deployment ID "' + deployment_id + '" not found for transect ' + transect_id)
                return
    else:
        dep_inds = range(0,len(glider_info['deployments']))


    ###################################
    # Step through the indices for each deployment,
    # and attempt to make the plots
    ###################################
    for dep_ind in dep_inds:
        deployment = glider_info['deployments'][dep_ind].copy()

        matchind = np.where([ii['id'] == deployment['id'] 
                             for ii in gliderplot_info['deployments']])[0][0]
        deployment_plotinfo = gliderplot_info['deployments'][matchind]

        if (deployment['plotting_active']) or (deployment_id is not None):
            
            print('\n' + datetime.datetime.now().strftime('%Y-%b-%d %H:%M:%S') + 
                  ' - Working on dataset ' + deployment['dataset_id'] + 
                  ': ' + deployment_plotinfo['label'])

            
            ####################################
            # Load in general data from ERDDAP
            ####################################
            metadata = gliders_gen.load_erddap_glider_metadata(glider_info['transect']['id'],
                                                               deployment['dataset_id'])
            
            
            ####################################
            # Load in positional data from ERDDAP
            ####################################
            vars_to_get = deployment_plotinfo['dac_timelocdepth']
            df_pos = gliders_gen.load_erddap_gliderdata(deployment['dataset_id'], 
                                                        deployment['start_time'], 
                                                        deployment['end_time'],
                                                        vars_to_get)
            
            
            ####################################
            # Load/calculate the turning points,
            # which will define the section
            # end points
            ####################################
            data_coords = extract_position_variables(df_pos, deployment_plotinfo)
            if (os.path.exists(os.path.join(outputpath, 
                                            glider_info['transect']['id'], 
                                            deployment_plotinfo['id']))
                and
                not(deployment['deployment_active'])):
                # If the folder for the deployment,
                # contain the deployment json with path information,
                # already exists, load in the data from that json
                print('   Load in previously existing turning points')
                data_coords = load_turning_points(outputpath, 
                                                  glider_info['transect']['id'], 
                                                  deployment_plotinfo['id'],
                                                  df_pos, data_coords)
                # Update the make_jsons_flag to indicate that a new
                # json DOES NOT need to be made
                make_jsons_flag = True # Keep it true for now
            
            else:
                
                # If the deployment folder does not exist, or the
                # deployment is active, then section coordinate 
                # need to be calculated first.
                # 
                # This can be partially done to update existing
                # coordinates, or fully done if needed

                if (os.path.exists(os.path.join(outputpath, 
                                                glider_info['transect']['id'], 
                                                deployment_plotinfo['id']))
                    and
                    deployment_plotinfo['verified']
                   ):
                    print('   Load in previously existing turning points')
                    # Load in previously calculated data coordinates
                    # if they exist, and if they have been verified
                    prev_datacoords = load_turning_points(outputpath, 
                                                          glider_info['transect']['id'], 
                                                          deployment_plotinfo['id'],
                                                          df_pos, data_coords)
                else:
                    prev_datacoords = None


                data_coords = calc_turning_points(data_coords, deployment_plotinfo,
                                                  prev_datacoords)
                
                # Update the make_jsons_flag to indicate that a new
                # json DOES need to be made
                make_jsons_flag = True
                
            # Make the transect path plot
            print(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S') + '   Begin making transect path plot' )
            make_output_folders(outputpath, transect_id, deployment_plotinfo['id'], data_coords['section_id'])
            make_transect_path_plot(outputpath, transect_id, 
                                    deployment_plotinfo, data_coords)
                
                
            
            ##############################################
            # Make the figures
            ##############################################
            
            
            
            if make_plots_flag:
                print(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S') + '   Begin making section plots')
                
                
                # Make a copy of the existing folders to use as a backup
                deployment_folder = os.path.join(outputpath, transect_id, 
                                                 deployment_plotinfo['id'])
                existing_folders = [ii for ii in os.listdir(deployment_folder) 
                                    if os.path.isdir(os.path.join(deployment_folder,ii))]
                existing_folders = sorted(existing_folders)
                for folder in existing_folders:
                    src = os.path.join(deployment_folder, folder)
                    dst = os.path.join(deployment_folder, folder+'_backup')
                    gliders_gen.copyfile_func(src, dst)
                    del src, dst
                    
                
                # Step through each of the segments and
                # make the section plots
                for ii in range(0,len(data_coords['segments'])):                                

                    # Extract the starting and ending coordinates of the segments
                    startind = data_coords['segments'][ii][0]
                    endind = data_coords['segments'][ii][1]

                    # Download the sensor data for the section, and 
                    # extract it to a dictionary
                    vars_to_get = np.unique((deployment_plotinfo['dac_variables'] + 
                                             deployment_plotinfo['dac_timelocdepth'])).tolist()
                    df = gliders_gen.load_erddap_gliderdata(deployment['dataset_id'], 
                                                            data_coords['ptime'][startind].strftime('%Y-%m-%dT%H:%M:%SZ'), 
                                                            (data_coords['ptime'][endind]+datetime.timedelta(seconds=1)).strftime('%Y-%m-%dT%H:%M:%SZ'),
                                                            vars_to_get)
                    df = df.reset_index()
                    df = df[df['precise_time (UTC)'] <= data_coords['ptime'][endind]]
                    # Double-check that we have the right number of points
                    # Note that this error usual occurs because of 
                    # duplicate time stamps
                    if len(df) != (endind+1-startind):
                        if endind+1-startind > len(df):
                            print('Not enough points')
                            endind = endind - (endind+1-startind > len(df))
                        if endind+1-startind < len(df):
                            print('Too many points. Look for duplicates.')
                            maxind = np.where(df['precise_time (UTC)'] == data_coords['ptime'][endind])[0][0]
                            df = df.copy().iloc[:maxind+1,:]
                    
                    datadict = extract_data_variables(df, deployment_plotinfo)
                                        
                        

                    # Make the section plots for each variable
                    try:
                        make_section_plots(outputpath, transect_id, gliderplot_info['transect']['label'], 
                                           deployment_plotinfo, metadata, datadict, data_coords, 
                                           startind, endind, data_coords['section_id'][ii], 
                                           data_coords['orientation'][ii])
                        # Create section data JSON for each variable in the deployment plotinfo
                        for varid in deployment_plotinfo.get('variables_id', []):
                            try:
                                make_section_data_json(outputpath, transect_id, deployment_plotinfo,
                                                       datadict, data_coords, varid, ii)
                            except Exception as e:
                                print(f'An error occurred while making section data json for section {ii} var {varid}')
                                print(e)
                                successFlag = False
                    except Exception as e:
                        
                        print('An error occurred while making section plots for section ' + str(ii))
                        print(e)
                        
                        # If the sections were not successfully created, and a temp backup
                        # of the previously existing plots exists, then restore the
                        # plots using the temp backups
                        if os.path.exists(os.path.join(outputpath, transect_id, 
                                                       deployment_plotinfo['id'],
                                                       data_coords['section_id'][ii]+'_tempbackup')):
                            dst = os.path.join(outputpath, transect_id, 
                                               deployment_plotinfo['id'],
                                               data_coords['section_id'][ii])
                            src = os.path.join(outputpath, transect_id, 
                                               deployment_plotinfo['id'],
                                               data_coords['section_id'][ii]+'_tempbackup')
                            shutil.copytree(src, dst)
                            del src
                            del dst

                        successFlag = False
                            
                    
                    del df
                    del datadict
                    gc.collect()
                    
                
                # Remove all of the backup folders, and then
                # ensure that the correct number of folders exist
                for folder in existing_folders:
                    if os.path.exists(os.path.join(deployment_folder, folder+'_backup')):
                        shutil.rmtree(os.path.join(deployment_folder, folder+'_backup'))
                        
                if len(existing_folders) > len(data_coords['segments']):
                    for folder in existing_folders:
                        if not(any([folder == ii for ii in data_coords['section_id']])):
                            if os.path.exists(os.path.join(deployment_folder, folder)):
                                shutil.rmtree(os.path.join(deployment_folder, folder))                            


            ####################################################
            # save metadata deployment_info.json 
            # and section_info json files for NVS #
            ####################################################
            if make_jsons_flag:
                gliders_gen.save_deployment_info_jsons(outputpath, glider_info['transect']['id'],
                                                       deployment, deployment_plotinfo,
                                                       metadata, data_coords) 
                
                gliders_gen.save_section_info_jsons(outputpath, glider_info['transect']['id'],
                                                    deployment, deployment_plotinfo,
                                                    metadata, data_coords)
                    
                del data_coords
                gc.collect()



            # Check if the deployment is active;
            # if the deployment is not active, then
            # this round of plotting should be the last
            # time that the figures are made, and the glider info
            # json should be updated to indicate that this deployment
            # does not need to be plotted anymore
            if not deployment['deployment_active']:

                print('Glider deployment ' + deployment['dataset_id'] + ' is not active.')
                print('This is the final plotting update for this deployment.')
                print('Update the jsons to account for this.')

                # Set the update_jsons_flag to true to indicate that
                # the glider_info json should be updated
                update_jsons_flag = True
                glider_info['deployments'][dep_ind]['plotting_active'] = False
                
                print('Updating jsons for this transect')
                glider_obj = GliderJson(json_obj=glider_info)
                gliderplot_obj = Glider_Plotting_Json(json_obj=gliderplot_info)
                gliders_gen.save_glider_info_all(glider_info['transect']['id'], 
                                                 glider_obj, gliderplot_obj)
            
            



    # If any deployments are no longer active, and do not need to be
    # plotted, the update_jsons_flag should be true. If so,
    # then write out the updated json file.
    if update_jsons_flag:
        print('Updating jsons for this transect')
        glider_obj = GliderJson(json_obj=glider_info)
        gliderplot_obj = Glider_Plotting_Json(json_obj=gliderplot_info)
        gliders_gen.save_glider_info_all(glider_info['transect']['id'], 
                                         glider_obj, gliderplot_obj)
        
    return successFlag


# def set_alldeployments_toplot():
#     
#     with open('C:/Users/APLUser/NANOOS/Gliders/GliderOutput/washelf/glider_info.json', 'r') as open_json:
#         glider_info = json.load(open_json)
# 
#     for ii in range(0,len(glider_info['deployments'])):
#         deployment = glider_info['deployments'][ii]
#         deployment['plotting_active'] = True
#         glider_info['deployments'][ii] = deployment
# 
#     with open('C:/Users/APLUser/NANOOS/Gliders/GliderOutput/washelf/glider_info.json', 'w') as open_json:
#         json.dump(glider_info, open_json)

# %%


def main():
    
    try:
        opts, args = getopt.getopt(sys.argv[1:], "hu:t:d:", ["help", "transect", "deployment"])
    except Exception as inst:
        # print help information and exit:
        print('Error in getting options: ' + str(inst)) # will print something like "option -a not recognized"
        sys.exit(2)
        
    
    # step through command-line options and their arguments
    processFlag = False
    transectFlag = False
    deploymentFlag = False
    
    # For all the command-line arguments, update a flag to indicate if the option was given,
    # and extract the value of the command-line argument
    for o, a in opts:
        if o == "-v":
            bVerbose = True
            # but currently verbose run is not implemented!
        elif o in ("-h", "--help"):
            sys.exit()
        elif o in ("-t", "--transect"):
            transectFlag = True
            transectName = a
        elif o in ("-d", "--deployment"):
            deploymentFlag = True
            deploymentName = a
        else:
            assert False, "unhandled option"
    
        
        
    # If the transect name was given, ensure that the transect name is in lowercase,
    # and that it matches one of the valid transect names
    valid_transects = ['lapush', 'osu_trinidad1', 'washelf', 
                       'ooi_ghs', 'ooi_ghd', 'ooi_nd', 'ooi_ns', 'ooi_coosbay']    
    def list_valid_transects():
        print('Valid transects include: ')
        print('"lapush" - NANOOS glider off of LaPush, Washington')
        print('"osu_trinidad1" - NANOOS glider at Trinidad Head, Oregon')
        print('"washelf" - NANOOS glider along the Washington Shelf')
        print('"ooi_ghs" - OOI shallow glider at Grays Harbor, Washington')
        print('"ooi_ghd" - OOI deep glider at Grays Harbor, Washington')
        print('"ooi_ns" - OOI shallow glider at Newport, Oregon')
        print('"ooi_nd" - OOI deep glider at Newport, Oregon')
        print('"ooi_coosbay" - OOI glider at Coos Bay, Oregon')
        
        return        
    
    if transectFlag:
        if transectName.lower() in valid_transects:
            print('\n\n' + datetime.datetime.now().strftime('%Y-%b-%d %H:%M:%S') 
                  + ' - Process will be performed for the transect: ' + transectName)
        else:
            print('Invalid transect name. Check name, and retry.')
            list_valid_transects()
            sys.exit(2)
    else:
        print('No transect name is given. Try again with options: "-t *transect*"')
        list_valid_transects()
        sys.exit(2)


    if deploymentFlag:
        print('Process will be performed for deployment: ' + deploymentName)
        print('Note that if the deployment is still active, plots will be made for the current data.')
    else:
        deploymentName = None
        
   

    #######################################
    # Make the plots for a defined transect
    try:
        successFlag = make_plots_for_transect(transectName, deploymentName)
        print(datetime.datetime.now().strftime('%Y-%b-%d %H:%M:%S') 
                  + ' - Processing for transect "' + transectName + '" complete.\n\n\n')
    except Exception as e:
        print('An error occured while making plots for transect ' + transectName)
        print('Error message:')
        print(e)

        error_msg = "An error occured while making plots for transect " + transectName + ".\n\n" + "Error message:\n" + str(e)
        error_sbj = "NVS Gliders Plotting Error for Transect " + transectName
        __, infodir, __ = gliders_gen.get_pathdirs()
        with open(os.path.join(infodir, 'user_info.json'), 'r') as infofile:
            user_info = json.load(infofile)
        gliders_gen.send_emailreport(msgtxt=error_msg, subj=error_sbj,
                                     fromaddr=user_info['email_fromaddr'], toaddr="setht1@uw.edu",
                                     login=user_info['email_login'],
                                     passwd=user_info['email_passwd'])
        sys.exit(2)
        
    if not(successFlag):
        error_msg = "An error occured while making plots for transect " + transectName + ".\n\n" + "Please check the log for details."
        error_sbj = "NVS Gliders Plotting Error for Transect " + transectName
        __, infodir, __ = gliders_gen.get_pathdirs()
        with open(os.path.join(infodir, 'user_info.json'), 'r') as infofile:
            user_info = json.load(infofile)
        gliders_gen.send_emailreport(msgtxt=error_msg, subj=error_sbj,
                                     fromaddr=user_info['email_fromaddr'], toaddr="setht1@uw.edu",
                                     login=user_info['email_login'],
                                     passwd=user_info['email_passwd'])
        
    sys.exit(0)


# %%


if __name__ == "__main__":
    main()

