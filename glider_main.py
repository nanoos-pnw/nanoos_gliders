# load packages
from erddapy import ERDDAP
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime
import matplotlib.dates as mdates
import pandas as pd
import json
from scipy.interpolate import griddata
import os
import xarray as xr

# run init_params.py to define all required parameters when new deployment added
# load init_params.json file
from init_params_NANOOS import init_params
gliderOps, outputpath = init_params()

# load the data, id the glider sections, and make the plots
for label in gliderOps:
    
    glider_active = label.active

    if glider_active:    
    
        for dataset in label.datasets:
            
            deployment_active = dataset.deployment_active
            dataset_id = dataset.dataset_id
            transect_id = dataset.transect_id
            glider_id = dataset.glider_id
            deployment_id = dataset.deployment_id
            deployment_label = dataset.deployment_label
            section_id = dataset.section_id
            section_label = dataset.section_label
            datetime_start = dataset.datetime_start
            datetime_end = dataset.datetime_end
            timelocdepth = dataset.dac_timelocdepth
            variables = dataset.dac_vars
            allvariables = timelocdepth+variables
            variables_label = dataset.vars_label
            variables_id = dataset.vars_id
            variables_units = dataset.vars_units
            variables_limits = dataset.vars_limits
            latlimmap = dataset.latlimmap
            lonlimmap = dataset.lonlimmap
            lonlimtransect = dataset.lonlimtransect
            depthlimtransect = dataset.depthlimtransect
            xLabel = dataset.x_label
            yLabel = dataset.y_label
            title = dataset.title
            fontSize = dataset.fontSize
            mycmap = dataset.mycmap
            tolerance = dataset.tolerance
            exppts = dataset.exppts
            num_interp_pts = dataset.num_interp_pts

            if not deployment_active:
                
                print('Glider deployment '+dataset_id+' is not active.')
                print('Proceeding to next glider deployment.')
                continue

            else:
                
                ###############################################
                # set params and load data from glider ERDDAP #
                ###############################################

                # "NOAA IOOS NGDAC (National Glider Data Assembly Center)", https://gliders.ioos.us/erddap
                e = ERDDAP(server='NGDAC')
                e.protocol = 'tabledap' # or 'griddap'
                e.response = 'csv' # or 'opendap'
                e.dataset_id = dataset_id

                # get metadata
                info_url = e.get_info_url() # dataset_id=e.dataset_id, response="csv")
                info = pd.read_csv(info_url)

                # define parameters from metadata
                transect_label = info[info['Variable Name'].str.match('NC_GLOBAL') & info['Attribute Name'].str.match('project')]['Value'].values[0]
                provider_name = info[info['Variable Name'].str.match('NC_GLOBAL') & info['Attribute Name'].str.contains('institution')]['Value'].values[0]
                provider_url = info[info['Variable Name'].str.match('NC_GLOBAL') & info['Attribute Name'].str.match('creator_url')]['Value'].values[0] #this is a bad link, needs http instead of https
                provider_contact_name = info[info['Variable Name'].str.match('NC_GLOBAL') & info['Attribute Name'].str.match('creator_name')]['Value'].values[0]
                provider_contact_email = info[info['Variable Name'].str.match('NC_GLOBAL') & info['Attribute Name'].str.match('creator_email')]['Value'].values[0]
                deployment_info_url_template = 'https://data.nanoos.org/wd/gliders/'+transect_id+'/{deployment_id}/deployment_info.json'
                section_info_url_template = 'https://data.nanoos.org/wd/gliders/'+transect_id+'/{deployment_id}/{section_id}/section_info.json'
                section_plots_url_template = 'https://data.nanoos.org/wd/gliders/'+transect_id+'/{deployment_id}/{section_id}/scientific/{variable_id}.png'
                glider_label = info[info['Variable Name'].str.match('NC_GLOBAL') & info['Attribute Name'].str.match('platform_type')]['Value'].values[0]
                if 'Slocum' in glider_label:
                    glider_type = 'slocum'
                else:
                    glider_type = 'seaglider'
                data_label = 'Glider DAC'
                data_url = 'https://gliders.ioos.us/erddap/tabledap/' + e.dataset_id
                
                datetime_latest = info[info['Variable Name'].str.match('NC_GLOBAL') & info['Attribute Name'].str.match('time_coverage_end')]['Value'].values[0]
                if datetime_end==None:
                    e.constraints = {'precise_time>=': datetime_start, 'precise_time<=': datetime_latest}
                else:
                    e.constraints = {'precise_time>=': datetime_start, 'precise_time<=': datetime_end}
                e.variables = allvariables

                # load data into a pandas dataframe, index by precise time
                print('Loading data from glider DAC')
                df = e.to_pandas(index_col='precise_time (UTC)', parse_dates=True)
                df.head()

                ################################################
                # save metadata glider_info.json files for NVS #
                ################################################
                from create_jsons import GliderJson

                # create folder/check if folder already exists for a given glider
                foldername = outputpath + transect_id
                try:
                    os.mkdir(foldername)
                except OSError:
                    print ('Directory %s already exists. Accessing directory.' % foldername)
                else:
                    print ('Successfully created the directory %s ' % foldername)                
                
                # check if glider_info.json already exists, if not create new, if so load
                print('Creating glider_info.json')
                info_json = foldername + '/glider_info.json'

                if not os.path.exists(info_json):
                
                    glider_obj = GliderJson(transect_id=transect_id, transect_label=transect_label, active=glider_active,
                        provider_name=provider_name, provider_url=provider_url, provider_contact_name=provider_contact_name,
                        provider_contact_email=provider_contact_email, deployment_info_url_template=deployment_info_url_template,
                        section_info_url_template=section_info_url_template, section_plots_url_template=section_plots_url_template)
                    
                    with open(info_json, "w") as write_file:
                        json.dump(glider_obj.__dict__, write_file) 
                
                else:
                    
                    with open(info_json) as g:
                        glider_dict = json.load(g)
                        glider_obj = GliderJson(json_obj=glider_dict)

                # check to see if deployment info already exists, if not: create new, if so: update end times
                with open(info_json) as g:
                    glider_dict = json.load(g)
                    glider_obj = GliderJson(json_obj=glider_dict)

                ids = []
                for depinfo in glider_obj.deployments:
                    ids.append(depinfo['id'])

                if deployment_id in ids:
                    glider_obj.update_deployment(deployment_id=deployment_id, deployment_end_time=datetime_latest)
                else:
                    glider_obj.add_deployment(deployment_id=deployment_id, deployment_label=deployment_label,
                        deployment_start_time=datetime_start, deployment_end_time=datetime_latest)

                # save updated glider_info.json
                with open(info_json, "w") as write_file:
                    json.dump(glider_obj.__dict__, write_file)  

                ##############################################
                # rename variables, convert to desired units #
                ##############################################
                print('Recasting variables')
                # dive number, depth
                divenum = df['profile_id'].values
                depth = df['depth (m)'].values # m

                # times
                ptime = df.index # precise time in UTC (PDT=UTC-7 hours)
                atime = df['time (UTC)'].values # average time per dive in UTC (PDT=UTC-7 hours)
                adatenum = [mdates.date2num(datetime.strptime(i, '%Y-%m-%dT%H:%M:%SZ')) for i in atime]

                # lats, lons
                plat = df['precise_lat (degrees_north)'].values # precise lat
                alat = df['latitude (degrees_north)'].values # average lat per dive
                plon = df['precise_lon (degrees_east)'].values # precise lon
                alon = df['longitude (degrees_east)'].values # average lon per dive
            
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

                #####################################
                # load bathymetry for GEBCO mapping #
                #####################################
                print('Loading and interpolating bathymetry')
                ds = xr.open_dataset('glider_bathy/GEBCO_2021/gebco_2021_n49.0_s39.0_w-130.0_e-123.0.nc')

                lats = ds['lat']
                lons = ds['lon']
                depths = ds['elevation']

                gliderlats = xr.DataArray(alat, dims='elevation')
                gliderlons = xr.DataArray(alon, dims='elevation')
                gliderdepths = depths.interp(lat=gliderlats,lon=gliderlons)

                ##############################################   
                # auto-detect turning points on glider track #
                ##############################################
                print('Detecting turn-around points')
                # determine turning points along the path
                from get_min_max import get_min_max
                inarr = plon
                endpts = get_min_max(inarr, tolerance, exppts)
                
                # save pairs of endpoints for each segment
                segments = list()
                for j in range(len(endpts)-1):
                    segments.append((endpts[j],endpts[j+1]))

                # plot endpoints connected by lines to see if path looks as expected
                fig,ax = plt.subplots(figsize=(9,9))
                plt.plot(plon[endpts],plat[endpts],'o-')
                ax.set_ylim(latlimmap)
                ax.set_xlim(lonlimmap)
                ax.set_ylabel('Latitude')
                ax.set_xlabel('Longitude')

                #######################
                # plot specifications #
                #######################

                plotVars = {name: None for name in variables_id}
                for iii, varid in enumerate(plotVars.keys()):
                    plotVars[varid] = {'data': datadict[varid], 'limits': variables_limits[iii],
                        'label': variables_label[iii], 'units': variables_units[iii], 'cmap': mycmap}
                
                #######################
                # plot depth profiles #
                #######################
                print('Plotting depth-longitude transects')
                k = 0
                for key2 in plotVars.keys():
                    var = plotVars[key2]['data']
                    varmin = plotVars[key2]['limits'][0]
                    varmax = plotVars[key2]['limits'][1]
                    varcmap = plotVars[key2]['cmap']
                    varname = plotVars[key2]['label'] + ' ' + plotVars[key2]['units']
                    
                    j = 0
                    for a,b in segments:
                        if k==0:
                            # create paths and folders
                            pathname = outputpath + transect_id
                            folderpath = [pathname]
                            folderpath.append(pathname + '/' + deployment_id)
                            folderpath.append(pathname + '/' + deployment_id + '/' + section_id[j])
                            folderpath.append(pathname + '/' + deployment_id + '/' + section_id[j] + '/scientific')
                            for folder in folderpath:
                                try:
                                    os.mkdir(folder)
                                except OSError:
                                    print ('Directory %s already exists' % folder)
                                else:
                                    print ('Successfully created the directory %s ' % folder)
                        
                        if j <= len(segments):
                            # make and save scientific plots
                            fig, ax = plt.subplots(figsize=(15, 6))
                            cs = ax.scatter(plon[a:b], depth[a:b], c=var[a:b],
                                s=30, marker='o', edgecolor='none',
                                vmin=varmin, vmax=varmax, cmap=varcmap
                            )
                            # add bathymetry
                            plt.plot(plon[a:b],-gliderdepths[a:b],'-k')
                        
                            # label time interval, make sure labels reflect glider direction of travel
                            if abs(plon[a]) > abs(plon[b]): # moving offshore to onshore
                                plt.text(lonlimtransect[0]+0.01, depthlimtransect[1]-5, ptime[a].strftime('%Y-%m-%d\n%H:%M:%S UTC'), fontsize=fontSize, fontdict=None, ma='left', ha='left')
                                plt.text(lonlimtransect[1]-0.01, depthlimtransect[1]-5, ptime[b].strftime('%Y-%m-%d\n%H:%M:%S UTC'), fontsize=fontSize, fontdict=None, ma='right', ha='right')
                            else: # moving onshore to offshore
                                plt.text(lonlimtransect[0]+0.01, depthlimtransect[1]-5, ptime[b].strftime('%Y-%m-%d\n%H:%M:%S UTC'), fontsize=fontSize, fontdict=None, ma='left', ha='left')
                                plt.text(lonlimtransect[1]-0.01, depthlimtransect[1]-5, ptime[a].strftime('%Y-%m-%d\n%H:%M:%S UTC'), fontsize=fontSize, fontdict=None, ma='right', ha='right')
                        
                            # labels, legends, colorbars
                            ax.set_xlim(lonlimtransect)
                            ax.set_ylim(depthlimtransect)
                            ax.set_xlabel(xLabel,fontsize=fontSize)
                            ax.tick_params(axis='x', labelsize=fontSize)
                            ax.invert_yaxis()
                            ax.set_ylabel(yLabel,fontsize=fontSize)
                            ax.tick_params(axis='y', labelsize=fontSize)
                            ax.set_title(title,fontsize=fontSize+2)
                            cbar = fig.colorbar(cs, orientation='vertical')#, extend="both")
                            cbar.ax.set_ylabel(varname,fontsize=fontSize)
                            cbar.ax.tick_params(labelsize=fontSize)
                            
                            # save plot into the "scientific" units folders
                            figpath = outputpath + transect_id + '/' + deployment_id + '/' + section_id[j] + '/scientific/' + variables_id[k]
                            plt.savefig(figpath)
                            plt.close(fig)

                        j += 1
                    k += 1     
                
                ####################################################
                # save metadata deployment_info.json files for NVS #
                ####################################################
                print('Creating deployment_info.json')
                from create_jsons import DeploymentJson

                deployment_route = np.array([plat[endpts].round(4).tolist(),plon[endpts].round(4).tolist()]).T
                
                section_datetime_start = [None] * len(segments)
                section_datetime_end = [None] * len(segments)
                for i,pair in enumerate(segments):    
                    section_datetime_start[i] = ptime[pair[0]].isoformat()[0:-6]+'Z'
                    section_datetime_end[i] = ptime[pair[1]].isoformat()[0:-6]+'Z'
                
                deployment_dict = DeploymentJson(deployment_id=deployment_id, deployment_label=deployment_label, data_url=data_url,
                    glider_id=glider_id, glider_label=glider_label, glider_type=glider_type,
                    datetime_start=datetime_start, datetime_end=datetime_end, deployment_route=deployment_route,
                    variable_id=variables_id, variable_label=variables_label, variable_units=variables_units,
                    section_id=section_id, section_label=section_label,
                    section_datetime_start=section_datetime_start, section_datetime_end=section_datetime_end,
                    data_label = data_label)

                # savepath for info.json files
                info_json = outputpath + transect_id + '/' + deployment_id + '/deployment_info.json'
                with open(info_json, "w") as write_file:
                    json.dump(deployment_dict.__dict__, write_file) 
                with open(info_json) as d:
                    d_dict = json.load(d)
                print(json.dumps(d_dict, indent = 4))    

                #################################################
                # save metadata section_info.json files for NVS #
                #################################################
                print('Creating section_info.json')
                from create_jsons import SectionJson

                for k,pair in enumerate(segments):
                        
                    section_datetime_start = ptime[pair[0]].isoformat()[0:-6]+'Z'
                    section_datetime_end = ptime[pair[1]].isoformat()[0:-6]+'Z'
                    
                    lons = [None] * (len(np.unique(divenum[pair[0]:pair[1]])))
                    lats = [None] * (len(np.unique(divenum[pair[0]:pair[1]])))
                    for j,dive in enumerate(np.unique(divenum[pair[0]:pair[1]])):
                        lons[j] = alon[divenum==dive].mean().round(4)
                        lats[j] = alat[divenum==dive].mean().round(4)
                    full_section_route = np.array([lons,lats]).T
                    
                    section_dict = SectionJson(deployment_id=deployment_id, glider_id=glider_id, section_id=section_id[k],
                        section_datetime_start=section_datetime_start, section_datetime_end=section_datetime_end, 
                        full_section_route=full_section_route)  
                    
                    # savepath for each section's json files
                    section_json = outputpath + transect_id + '/' + deployment_id + '/' + section_id[k] + '/section_info.json'
                    with open(section_json, "w") as write_file:
                        json.dump(section_dict.__dict__, write_file) 
                    with open(section_json) as s:
                        s_dict = json.load(s)
                    print(json.dumps(s_dict, indent = 4))  