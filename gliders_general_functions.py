#!/usr/bin/env python
# coding: utf-8

# In[ ]:


# load packages
from erddapy import ERDDAP

import numpy as np
import pandas as pd

import datetime

import json
import os
import shutil

# import classes needed to build initial parameters objects
from classes import Dataset

from importlib import reload
import time

# #

# In [ ]:

def get_pathdirs():

    basedir = os.path.dirname(__file__)
    infodir = os.path.join(basedir, 'info_jsons')
    with open(os.path.join(infodir, 'pathdirs.json'), "r") as pathfile:
        pathjson = json.load(pathfile)
    outputdir = pathjson['outputdir']
        
    return basedir, infodir, outputdir

# # General Calculations

# In[ ]:


def datetime_toordinal_withseconds(origdate):
    
    # Function: datetime_toordinal_withseconds
    # This function changes a datetime object
    # into an ordinal time (i.e., days since Jan-01-0000),
    # but includes resolution, to the second.
    
    import numpy as np
    import pandas as pd
    import datetime
    
    if pd.isna(origdate):
        return np.nan
    
    year = origdate.year
    month = origdate.month
    day = origdate.day
    hour = origdate.hour
    minute = origdate.minute
    second = origdate.second
    microsec = origdate.microsecond
    
    return (datetime.datetime.toordinal(datetime.datetime(year,month,day)) +
            (hour + (minute + (second + (microsec/1e6))/60)/60)/24)


# In[ ]:


def great_circle_calc(lat, lon):
    
    lat_rad = np.radians(lat)
    lon_rad = np.radians(lon)
    
    R = 6370*1e3 # Radius of earth, in m
    
    dlon = lon_rad[1:] - lon_rad[:-1]
    
    fac1 = np.cos(lat_rad[1:]) * np.cos(lat_rad[:-1]) * np.cos(dlon)
    fac2 = np.sin(lat_rad[1:]) * np.sin(lat_rad[:-1])
    
    dist = R * np.arccos(fac1 + fac2)
    
    return dist


# # File functions

# In[ ]:


def copyfile_func(src, dst):
    
    try:
        if os.path.isdir(src):
            shutil.copytree(src, dst)
        else:
            shutil.copy(src, dst)

    # If source and destination are same
    except shutil.SameFileError:
        print('Copy error for "' + src + '": Source and destination represents the same file.')

    # If there is any permission issue
    except PermissionError:
        print('Copy error for "' + src + '": Permission denied.')
        print("Permission denied.")

    # For other errors
    except Exception as e:
        print('Copy error for "' + src + '": Error occurred while copying file.')
        print('Error message: ' + str(e))


# In[ ]:


def get_outputpath():
    
    curpath = os.getcwd()

    knownpaths = ['/home/stravis',
                  'C:\\Users\\APLUser',
                  'C:\\Users\\stravis',
                  '/Users/rjcarini/']

    outputpaths = ['/home/stravis/gliders_web_directory/',
                   'C:\\Users\\APLUser\\NANOOS\\Gliders\\GliderOutput',
                   'C:\\Users\\stravis\\NANOOS\\Gliders\\GliderOutput',
                   '/Users/rjcarini/Documents/Python/gliders/GliderOutput']

    if any([ii in curpath for ii in knownpaths]):
        pathind = np.where([ii in curpath for ii in knownpaths])[0][0]
        outputpath = outputpaths[pathind]
    else:
        print('Unknown base directory. No working directory given.')
        outputpath = None
        
    return outputpath


# # ERDDAP Database Functions

# In[ ]:


def find_glider_datasets(glider_id, ooi_loc=None):
    
    ############################################
    # Connect to the ERDDAP server
    e = ERDDAP(server='NGDAC', protocol='tabledap')
    
    kw = {
        "cdm_data_type": "trajectoryprofile"
    }
    search_url  = e.get_search_url(response='csv', **kw)
    search_info = pd.read_csv(search_url)

    all_dataset_ids = search_info['Dataset ID'].to_numpy().squeeze()
    
    
    # Identify the dataset IDs which contain the glider ID
    glider_dataset_ids = []
    for dataset_id in all_dataset_ids:
        if glider_id in dataset_id:
            glider_dataset_ids.append(dataset_id)
            
            
    # Identify the products that are delayed
    delayed_ids = [False for ii in range(0,len(glider_dataset_ids))]
    for ii in range(0,len(glider_dataset_ids)):
        if 'delayed' in glider_dataset_ids[ii]:
            delayed_ids[ii] = True
            
    # Get the dataset date
    glider_dataset_dates = []
    for glider_dataset in glider_dataset_ids:
        if '-delayed' in glider_dataset:
            dataset_date = datetime.datetime.strptime(glider_dataset[len(glider_id)+1:glider_dataset.find('-delayed')],
                                                      '%Y%m%dT%H%M')
        else:
            dataset_date = datetime.datetime.strptime(glider_dataset[len(glider_id)+1:],
                                                      '%Y%m%dT%H%M')
        glider_dataset_dates.append(dataset_date)
    
    return glider_dataset_ids, glider_dataset_dates, delayed_ids


# In[ ]:


def find_location_glider_ids(loc_text, ooi_loc=False):
    
    ############################################
    # Connect to the ERDDAP server
    e = ERDDAP(server='NGDAC', protocol='tabledap')
    
    kw = {
        "cdm_data_type": "trajectoryprofile"
    }
    search_for_text = loc_text
    search_url  = e.get_search_url(search_for=search_for_text, response='csv', **kw)
    search_info = pd.read_csv(search_url)

    all_dataset_ids = search_info['Dataset ID'].to_numpy().squeeze()
    
    # If the search text is an OOI glider hydrographic line, 
    # add an additional search to double check the meta-data
    # to ensure it is the correct hydrographic line
    if ooi_loc:
        all_dataset_info = search_info['Info'].to_numpy().squeeze()
        keeplines = [False for ii in range(0,len(all_dataset_info))]
        
        for ii in range(0,len(all_dataset_info)):
            dataset_info = pd.read_csv(all_dataset_info[ii])
            try:
                hydroline_ind = np.where(dataset_info['Attribute Name'] == 'hydrographic_line')[0][0]
                hydroline_name = dataset_info.iloc[hydroline_ind]['Value']

                if hydroline_name == search_for_text:
                    keeplines[ii] = True
            except:
                print('      No "hydrographic_line" available for:',all_dataset_ids[ii])
                
        if any(keeplines):
            all_dataset_ids = all_dataset_ids[np.where(keeplines)[0]]
                
    
    
    # Identify the dataset IDs which contain the glider ID
    glider_dataset_ids = []
    for dataset_id in all_dataset_ids:
        glider_dataset_ids.append(dataset_id)
            
            
    # Identify the products that are delayed
    delayed_ids = [False for ii in range(0,len(glider_dataset_ids))]
    for ii in range(0,len(glider_dataset_ids)):
        if 'delayed' in glider_dataset_ids[ii]:
            delayed_ids[ii] = True
            
    # Get the dataset date
    glider_dataset_dates = []
    for glider_dataset in glider_dataset_ids:
        if '-delayed' in glider_dataset:
            dataset_date = datetime.datetime.strptime(glider_dataset[glider_dataset.find('-')+1:glider_dataset.find('-delayed')],
                                                      '%Y%m%dT%H%M')
        else:
            dataset_date = datetime.datetime.strptime(glider_dataset[glider_dataset.find('-')+1:],
                                                      '%Y%m%dT%H%M')
        glider_dataset_dates.append(dataset_date)
        
    
    return glider_dataset_ids, glider_dataset_dates, delayed_ids


# In[ ]:


def load_erddap_glider_metadata(transect_id, dataset_id):
    
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
    transect_label = info[(info['Variable Name'].str.match('NC_GLOBAL') & 
                           info['Attribute Name'].str.match('project'))]['Value'].values[0]
    provider_name = info[(info['Variable Name'].str.match('NC_GLOBAL') & 
                          info['Attribute Name'].str.contains('institution'))]['Value'].values[0]
    # Note: ensure that python has up-to-date certificates
    # old note: this is a bad link, needs http instead of https
    provider_url = info[(info['Variable Name'].str.match('NC_GLOBAL') & 
                         info['Attribute Name'].str.match('creator_url'))]['Value'].values[0] 
    provider_contact_name = info[(info['Variable Name'].str.match('NC_GLOBAL') & 
                                  info['Attribute Name'].str.match('creator_name'))]['Value'].values[0]
    provider_contact_email = info[(info['Variable Name'].str.match('NC_GLOBAL') & 
                                   info['Attribute Name'].str.match('creator_email'))]['Value'].values[0]
    deployment_info_url_template = ('https://data.nanoos.org/wd/gliders/' + transect_id +
                                    '/{deployment_id}/deployment_info.json')
    section_info_url_template = ('https://data.nanoos.org/wd/gliders/' + transect_id +
                                 '/{deployment_id}/{section_id}/section_info.json')
    section_plots_url_template = ('https://data.nanoos.org/wd/gliders/' + transect_id + 
                                  '/{deployment_id}/{section_id}/scientific/{variable_id}.png')
    section_data_url_template = ('https://data.nanoos.org/wd/gliders/' + transect_id + 
                                '/{deployment_id}/{section_id}/scientific_data/{variable_id}_data.json')
    glider_label = info[(info['Variable Name'].str.match('NC_GLOBAL') & 
                         info['Attribute Name'].str.match('platform_type'))]['Value'].values[0]
    if 'Slocum' in glider_label:
        glider_type = 'slocum'
    else:
        glider_type = 'seaglider'
    data_label = 'Glider DAC'
    data_url = 'https://gliders.ioos.us/erddap/tabledap/' + e.dataset_id

    datetime_latest = info[(info['Variable Name'].str.match('NC_GLOBAL') & 
                            info['Attribute Name'].str.match('time_coverage_end'))]['Value'].values[0]
    
    # Create a dictionary of all of the metadata parameters
    metadata = {'transect_label': transect_label,
                'provider_name': provider_name,
                'provider_url': provider_url,
                'provider_contact_name': provider_contact_name,
                'provider_contact_email': provider_contact_email,
                'deployment_info_url_template': deployment_info_url_template,
                'section_info_url_template': section_info_url_template,
                'section_plots_url_template': section_plots_url_template,
                'section_data_url_template': section_data_url_template,
                'glider_label': glider_label,
                'glider_type': glider_type,
                'data_label': data_label,
                'data_url': data_url,
                'datetime_latest': datetime_latest}
    
    
    
    return metadata


# In[ ]:


def load_erddap_gliderdata(dataset_id, datetime_start, datetime_end, dac_vars):
    
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
    
    data_url = 'https://gliders.ioos.us/erddap/tabledap/' + e.dataset_id

    datetime_latest = info[(info['Variable Name'].str.match('NC_GLOBAL') & 
                            info['Attribute Name'].str.match('time_coverage_end'))]['Value'].values[0]
    
    
    
    e.constraints = {'precise_time>=': datetime_start, 'precise_time<=': datetime_end}
    e.variables = dac_vars
    # load data into a pandas dataframe, index by precise time
    print('      Loading data from glider DAC')
    loaddata_flag = True
    loaddata_count = 0
    while loaddata_flag:
        try:
            df = e.to_pandas(index_col='precise_time (UTC)', parse_dates=True)
            loaddata_flag = False
        except Exception as err:
            print('   ' + datetime.datetime.now().strftime('%H:%M:%S') 
                  + ': Download attempt #' + str(loaddata_count+1) 
                  + ' failed. Error in downloading data:')
            print('Error message: ' + str(err))
            loaddata_count = loaddata_count + 1
            if loaddata_count >= 5:
                print('   More than the maximum number of allowed attempts completed. End attempt.')
                loaddata_flag = False
                df = None
                return df
            else:
                print('   Wait 15 seconds and try again.')
                time.sleep(15)
        
    df.head()
    
    # Rename all of the dataframe columns, dropping any reference to the
    # units of the variables
    df_cols = df.columns
    df_newcols = []
    for jj in range(0,len(df_cols)):
        if ' ' in df_cols[jj]:
            df_newcols.append(df_cols[jj][:df_cols[jj].find(' ')])
        else:
            df_newcols.append(df_cols[jj])
    df_renamecols = {}
    for jj in range(0,len(df_cols)):
        df_renamecols[df_cols[jj]] = df_newcols[jj]
    df = df.rename(columns=df_renamecols)
    
    # Sort the data to ensure that it is in sequential order
    df = df.sort_index()
    
    return df


# In[ ]:


def set_dataset_id_label(glider_id, dataset_id, deployment_active=True):
    
    ############################################
    # Connect to the ERDDAP server
    e = ERDDAP(server='NGDAC')
    
    # Download the dataset information based on
    # the dataset id
    info = pd.read_csv(e.get_info_url(dataset_id=dataset_id, response="csv"))
    info = info[info['Variable Name'] == 'NC_GLOBAL'].reset_index(drop=True)

    dataset_info = {}
    for ii in range(0,len(info)):
        dataset_info[info.loc[ii,'Attribute Name']] = info.loc[ii,'Value']


    info = pd.read_csv(e.get_info_url(dataset_id=dataset_id, response="csv"))
    info = info[info['Row Type'] == 'variable'].reset_index(drop=True)

    variable_names = []
    for ii in range(0,len(info)):
        variable_names.append(info.loc[ii,'Variable Name'])
        
        
    ##################################
    # Initialize a dataset dictionary,
    # and start to populate the fields
    
    starttime = datetime.datetime.strptime(dataset_info['time_coverage_start'], '%Y-%m-%dT%H:%M:%SZ')
    endtime = datetime.datetime.strptime(dataset_info['time_coverage_end'], '%Y-%m-%dT%H:%M:%SZ')
    if ('delayed' not in dataset_id) and deployment_active:
        deployment_id = starttime.strftime('%Y_%B') + '_Ongoing'
        deployment_label = starttime.strftime('%Y %B') + ' - Ongoing'
    else:
        if (starttime.year == endtime.year) and (starttime.month == endtime.month):
            deployment_id = starttime.strftime('%Y_%B')
            deployment_label = starttime.strftime('%Y %B')
        else:
            deployment_id = starttime.strftime('%Y_%B') + '_' + endtime.strftime('%Y_%b')
            deployment_label = starttime.strftime('%Y %B') + ' - ' + endtime.strftime('%Y %B')
        
    return deployment_id, deployment_label


# In[ ]:


def set_deployment_dataset_parameters(glider_id, dataset_id, 
                                      last_dataset_json=None):
    
    ############################################
    # Connect to the ERDDAP server
    e = ERDDAP(server='NGDAC')
    
    # Download the dataset information based on
    # the dataset id
    info = pd.read_csv(e.get_info_url(dataset_id=dataset_id, response="csv"))
    info = info[info['Variable Name'] == 'NC_GLOBAL'].reset_index(drop=True)

    dataset_info = {}
    for ii in range(0,len(info)):
        dataset_info[info.loc[ii,'Attribute Name']] = info.loc[ii,'Value']


    info = pd.read_csv(e.get_info_url(dataset_id=dataset_id, response="csv"))
    info = info[info['Row Type'] == 'variable'].reset_index(drop=True)

    variable_names = []
    for ii in range(0,len(info)):
        variable_names.append(info.loc[ii,'Variable Name'])
        
        
        
    ##################################
    # Initialize a dataset dictionary,
    # and start to populate the fields
    
    deployment_dataset = {}
    deployment_dataset['dataset_id'] = dataset_id
    deployment_dataset['glider_id'] = glider_id

    deployment_dataset['datetime_start'] = dataset_info['time_coverage_start']
    starttime = datetime.datetime.strptime(dataset_info['time_coverage_start'], '%Y-%m-%dT%H:%M:%SZ')
    endtime = datetime.datetime.strptime(dataset_info['time_coverage_end'], '%Y-%m-%dT%H:%M:%SZ')
    if 'delayed' not in dataset_id:
        deployment_dataset['deployment_id'] = starttime.strftime('%Y_%b') + '_Ongoing'
        deployment_dataset['deployment_label'] = starttime.strftime('%Y %B') + ' - Ongoing'
        deployment_dataset['datetime_end'] = None
        deployment_dataset['deployment_active'] = True
    else:
        if (starttime.year == endtime.year) and (starttime.month == endtime.month):
            deployment_dataset['deployment_id'] = starttime.strftime('%Y_%b')
            deployment_dataset['deployment_label'] = starttime.strftime('%Y %B')
        else:
            deployment_dataset['deployment_id']= starttime.strftime('%Y_%b') + '_' + endtime.strftime('%Y_%b')
            deployment_dataset['deployment_label']=starttime.strftime('%Y %B') + ' - ' + endtime.strftime('%Y %B')
        deployment_dataset['datetime_end'] = dataset_info['time_coverage_end']
        deployment_dataset['deployment_active'] = False


    deployment_dataset['latlimmap'] = [np.floor(10*(float(dataset_info['geospatial_lat_min']) - 0.25))/10,
                                       np.ceil(10*(float(dataset_info['geospatial_lat_max']) + 0.25))/10]
    deployment_dataset['lonlimmap'] = [np.floor(10*(float(dataset_info['geospatial_lon_min']) - 0.25))/10,
                                       np.ceil(10*(float(dataset_info['geospatial_lon_max']) + 0.25))/10]
    deployment_dataset['lonlimtransect'] = deployment_dataset['lonlimmap']
    deployment_dataset['depthlimtransect']=[0,
                                            np.ceil(0.1*(float(dataset_info['geospatial_lon_max']) + 5))/0.1]


    defaultdac_axisvars = ['precise_time','time',
                           'precise_lat','latitude',
                           'precise_lon','longitude',
                           'profile_id','depth']
    dac_axisvars = []
    for var in defaultdac_axisvars:
        if any([var == ii for ii in variable_names]):
            dac_axisvars.append(var)

    [dac_variables, 
     dac_varlabel, 
     dac_varid,
     dac_varunits] = check_default_variable_names(variable_names)

    deployment_dataset['dac_timelocdepth'] = dac_axisvars
    deployment_dataset['dac_variables'] = dac_variables
    deployment_dataset['variables_label'] = dac_varlabel
    deployment_dataset['variables_id'] = dac_varid
    deployment_dataset['variables_units'] = dac_varunits
    deployment_dataset['variables_limits'] = [[6.0,12.0],[29.0,34.0],[1023.0,1027.0],
                                              [0.0,11.0],[0.0,30.0],[0.0,3.0],[0.0,0.02]]

    
    # 
    deployment_dataset = set_default_dataset_parameters(deployment_dataset)
    deployment_dataset['manual_reviewed'] = False
    
    
    #############################################
    # If a prior glider ID json exists, load
    # in that json, and set some of the fields
    # which are generally supposed to be user-defined
    # to match the prior json.
    
    if last_dataset_json is not None:
        last_dataset = load_dataset_info(last_dataset_json)
        
        # Check the lat/lon ranges;
        # If the lat/lon range is significantly different
        # than the last dataset, so not update
        # to match the else range
        
        if ((abs(last_dataset.latlimmap[0] - deployment_dataset['latlimmap'][0]) > 10)
            or
            (abs(last_dataset.latlimmap[1] - deployment_dataset['latlimmap'][1]) > 10)
            or
            (abs(last_dataset.lonlimmap[0] - deployment_dataset['lonlimmap'][0]) > 10)
            or
            (abs(last_dataset.lonlimmap[1] - deployment_dataset['lonlimmap'][1]) > 10)):
            
            print('Prior dataset is in a significantly different range.')
            print('Prior dataset range:   ' + 
                  str(last_dataset.latlimmap[0]) + '-' + str(last_dataset.latlimmap[1]) + 'N,' +
                  str(last_dataset.lonlimmap[0]) + '-' + str(last_dataset.lonlimmap[1]) + 'E')
            print('Current dataset range: ' + 
                  str(deployment_dataset['latlimmap'][0]) + '-' + str(deployment_dataset['latlimmap'][1]) + 'N,' +
                  str(deployment_dataset['lonlimmap'][0]) + '-' + str(deployment_dataset['lonlimmap'][1]) + 'E')
            print('Do not update current deployment dataset bounds')
            
        else:
        
            # Set the variable limits to match the prior deployment
            deployment_dataset['variables_limits'] = last_dataset.vars_limits

            # Set the plotting parameters to match
            deployment_dataset['exppts'] = last_dataset.exppts
            deployment_dataset['num_interp_pts'] = last_dataset.num_interp_pts
    
    
    return deployment_dataset


# # Dataset info parameters

# In[ ]:


def set_default_dataset_parameters(dataset):
    
    dataset['tolerance'] = 0.1
    dataset['exppts'] = 10
    dataset['num_interp_pts'] = 250
    dataset['transect_id'] = None
    dataset['title'] = None

    dataset['section_id'] = None
    dataset['section_label'] = None
    
    return dataset


# In[ ]:


def load_glider_info_all(transect_id):
    
    """
    This function takes a given transect ID, and loads in all the 
    data (both glider info & plotting info)
    
    Input: transect_id
    """
    
    __, __, transect_basedir = get_pathdirs()
    transect_dir = os.path.join(transect_basedir,transect_id)
    
    # Load in the glider information
    info_json = 'glider_info.json'
    with open(os.path.join(transect_dir, info_json), "r") as read_file:
        glider_info = json.load(read_file)

    info_json = 'glider_plottinginfo.json'
    with open(os.path.join(transect_dir, info_json), "r") as read_file:
        gliderplot_info = json.load(read_file)
        
    return glider_info, gliderplot_info


# In[ ]:


def load_glider_exclusions(transect_id):
    
    """
    This function takes a given transect ID, and loads in 
    the list of excluded datasets
    
    Input: transect_id
    """
    
    __, __, transect_basedir = get_pathdirs()
    transect_dir = os.path.join(transect_basedir, transect_id)
    
    # Load in the glider information
    info_json = 'glider_exclusions.json'
    if os.path.exists(os.path.join(transect_dir, info_json)):
        with open(os.path.join(transect_dir, info_json), "r") as read_file:
            glider_exclusions = json.load(read_file)
    else:
        glider_exclusions = None
        
    return glider_exclusions


# In[ ]:


def save_glider_info_all(transect_id, glider_obj, gliderplot_obj):
    
    """
    This function takes a given transect ID and dataset objects, 
    # and saves all the data (both glider info & plotting info)
    
    Input: transect_id    - determines save location
           glider_obj     - dataset object holding glider deployment info
           gliderplot_obj - dataset object holding glider deployment plotting info
    """
    
    __, __, transect_basedir = get_pathdirs()
    transect_dir = os.path.join(transect_basedir, transect_id)
    
    
    # Save updated glider_info.json
    info_json = 'glider_info.json'
    with open(os.path.join(transect_dir, info_json), "w") as write_file:
        if isinstance(glider_obj, dict):
            json.dump(glider_obj, write_file) 
        else:
            json.dump(glider_obj.__dict__, write_file)  
        
    
    # Save updated glider_plottinginfo.json    
    info_json = 'glider_plottinginfo.json'
    with open(os.path.join(transect_dir, info_json), "w") as write_file:
        if isinstance(gliderplot_obj, dict):
            json.dump(gliderplot_obj, write_file)  
        else:
            json.dump(gliderplot_obj.__dict__, write_file)  
        
    return


# In[ ]:


def check_default_variable_names(variable_names):
    
    vars_to_get = []
    varlabel = []
    varid = []
    varunits = []
    
    
    for var in variable_names:
        
        if var.lower() in ['chlorophyll','fluorescence']:
            vars_to_get.append(var)
            varlabel.append('Chlorophyll')
            varid.append('chl')
            varunits.append('ug/l')
            
        elif var.lower() in ['backscatter']:
            vars_to_get.append(var)
            varlabel.append('Backscatter')
            varid.append('bs')
            varunits.append('m-1')
            
        elif var.lower() in ['cdom', 'colored_dissolved_organic_matter']:
            vars_to_get.append(var)
            varlabel.append('CDOM')
            varid.append('cdom')
            varunits.append('ppb')
            
        elif var.lower() in ['dissolved_oxygen']:
            vars_to_get.append(var)
            varlabel.append('Dissolved Oxygen')
            varid.append('do')
            varunits.append('mg/l')
            
        elif var.lower() in ['temperature']:
            vars_to_get.append(var)
            varlabel.append('Temperature')
            varid.append('temp')
            varunits.append('\u00b0C')
            
        elif var.lower() in ['salinity']:
            vars_to_get.append(var)
            varlabel.append('Salinity')
            varid.append('sal')
            varunits.append('PSU')
            
        elif var.lower() in ['density']:
            vars_to_get.append(var)
            varlabel.append('Density')
            varid.append('dens')
            varunits.append('kg/m3')
        
    return vars_to_get, varlabel, varid, varunits


# # Functions to save jsons

# In[ ]:


def save_deployment_info_jsons(outputpath, transect_id,
                               deployment_info, plotting_info, metadata, data_coords):
    
    ####################################################
    # save metadata deployment_info.json files for NVS #
    ####################################################
    print('Creating deployment_info.json')
    from create_jsons import DeploymentJson

    deployment_route = np.array([data_coords['plat'][data_coords['endpts']].round(4).tolist(),
                                 data_coords['plon'][data_coords['endpts']].round(4).tolist()]).T

    section_datetime_start = [None] * len(data_coords['segments'])
    section_datetime_end = [None] * len(data_coords['segments'])
    section_orientations = [None] * len(data_coords['segments'])
    for i,pair in enumerate(data_coords['segments']):    
        section_datetime_start[i] = data_coords['ptime'][pair[0]].isoformat()[0:-6]+'Z'
        section_datetime_end[i] = data_coords['ptime'][pair[1]].isoformat()[0:-6]+'Z'
        section_orientations[i] = data_coords['orientation'][i]

    deployment_dict = DeploymentJson(
        deployment_id=deployment_info['id'], 
        deployment_label=deployment_info['label'], 
        data_url=metadata['data_url'], 
        glider_id=deployment_info['glider_id'], 
        glider_label=metadata['glider_label'], 
        glider_type=metadata['glider_type'], 
        datetime_start=deployment_info['start_time'], 
        datetime_end=deployment_info['end_time'], 
        deployment_route=deployment_route,
        variable_id=plotting_info['variables_id'], 
        variable_label=plotting_info['variables_label'], 
        variable_units=plotting_info['variables_units'],
        section_id=data_coords['section_id'], 
        section_label=data_coords['section_label'],
        section_datetime_start=section_datetime_start, 
        section_datetime_end=section_datetime_end,
        section_orientations=section_orientations,
        data_label = metadata['data_label']
    )

    # savepath for info.json files
    info_json = os.path.join(outputpath, transect_id, plotting_info['id'], 'deployment_info.json')
    with open(info_json, "w") as write_file:
        json.dump(deployment_dict.__dict__, write_file) 

    return  


# In[ ]:


def save_section_info_jsons(outputpath, transect_id,
                            deployment_info, plotting_info, 
                            metadata, data_coords):
    
    #################################################
    # save metadata section_info.json files for NVS #
    #################################################
    print('Creating section_info.json')
    from create_jsons import SectionJson

    for k,pair in enumerate(data_coords['segments']):

        section_datetime_start = data_coords['ptime'][pair[0]].isoformat()[0:-6]+'Z'
        section_datetime_end = data_coords['ptime'][pair[1]].isoformat()[0:-6]+'Z'

        unique_divenums = np.unique(data_coords['divenum'][pair[0]:pair[1]])
        lons = [None] * (len(unique_divenums))
        lats = [None] * (len(unique_divenums))
        for j,dive in enumerate(unique_divenums):
            lons[j] = np.nanmean(data_coords['plon'][data_coords['divenum']==dive]).round(4)
            lats[j] = np.nanmean(data_coords['plat'][data_coords['divenum']==dive]).round(4)
        full_section_route = np.array([lons,lats]).T

        section_dict = SectionJson(deployment_id=deployment_info['id'], glider_id=deployment_info['glider_id'], 
            section_id=data_coords['section_id'][k], section_datetime_start=section_datetime_start, 
            section_datetime_end=section_datetime_end, 
            full_section_route=full_section_route)  

        # savepath for each section's json files
        section_json = os.path.join(outputpath, transect_id, deployment_info['id'],
                                    data_coords['section_id'][k], 'section_info.json')
        with open(section_json, "w") as write_file:
            json.dump(section_dict.__dict__, write_file) 
        
    return


# # Legacy functions

# These functions help to transition from some of the original
# glider set-up to the new system. In particular, the dataset
# information found in the "init_params_NANOOS.py" and 
# "init_params_OOI.py" scripts are able to be converted into
# jsons which are compatible with the new setup.

# In[ ]:


def make_base_transects_info_from_orig_datasets():
    
    ###################################################
    # Create an inital list of the existing (if exists)
    # transect info file
    
    transects_file = 'uav_transects.json'
    if os.path.exists(transects_file):
        with open('uav_transects.json', "r") as read_file:
            transects = json.load(read_file)

        existing_transect_ids = [ii['transect_id'] for ii in transects]
    else:
        transects = []
        existing_transect_ids = []
    
    
    #########################################
    # Load the init params for NANOOS gliders
    # and add them to the transects
    
    # load init_params.json file
    from init_params_NANOOS import init_params
    gliderOps, outputpath = init_params()
    
    # Step through all the gliders, and add the transects to
    # the list
    for label in gliderOps:
        cur_transect = {}
        cur_transect['transect_id'] = label.datasets[0].transect_id
        cur_transect['Title'] = label.datasets[0].title
        cur_transect['active'] = label.active
        cur_transect['data_source'] = 'https://gliders.ioos.us/erddap/'
        cur_transect['transect_directory_template'] = 'https://data.nanoos.org/wd/gliders/{transect_id}'
        
        if cur_transect['transect_id'] in existing_transect_ids:
            print('Transect ID already exists:',cur_transect['transect_id'])
            continue
        else:
            transects.append(cur_transect)
                        
    # Step through all the gliders, get the requisite 
    # metadata for that file, and 
    for label in gliderOps:
        for dataset in label.datasets:                
            print('Transect: ' + dataset.transect_id + ', Dataset: ' + dataset.dataset_id)                
            metadata = load_erddap_glider_metadata(dataset.transect_id, dataset.dataset_id)
            save_dataset_as_glider_info_jsons(outputpath, dataset, metadata)
            save_dataset_as_glider_plottinginfo_jsons(outputpath, dataset, metadata)
            
            
            
    #########################################
    # Load the init params for OOI gliders
    # and add them to the transects
    
    # load init_params.json file
    from init_params_OOI import init_params
    gliderOps, outputpath = init_params()
    
    # Step through all the gliders, and add the transects to
    # the list
    for label in gliderOps:
        cur_transect = {}
        cur_transect['transect_id'] = label.datasets[0].transect_id
        cur_transect['Title'] = label.datasets[0].title
        cur_transect['active'] = label.active
        cur_transect['data_source'] = 'https://gliders.ioos.us/erddap/'
        cur_transect['transect_directory_template'] = 'https://data.nanoos.org/wd/gliders/{transect_id}'

        if cur_transect['transect_id'] in existing_transect_ids:
            print('Transect ID already exists:',cur_transect['transect_id'])
            continue
        else:
            transects.append(cur_transect)
                        
    # Step through all the gliders, get the requisite 
    # metadata for that file, and 
    for label in gliderOps:
        for dataset in label.datasets:                
            print('Transect: ' + dataset.transect_id + ', Dataset: ' + dataset.dataset_id)
            metadata = load_erddap_glider_metadata(dataset.transect_id, dataset.dataset_id)
            save_dataset_as_glider_info_jsons(outputpath, dataset, metadata)
            save_dataset_as_glider_plottinginfo_jsons(outputpath, dataset, metadata)

            
            
    #############################################
    # Write out all of the transect info into the
    # UAV transects json
    with open('uav_transects.json', "w") as write_file:
        json.dump(transects, write_file)
        
        
    return


# In[ ]:


def get_dataset_plotparams(dataset):
    
    plot_params = {}
    plot_params['dac_timelocdepth']=dataset.dac_timelocdepth
    plot_params['dac_variables']=dataset.dac_vars
    plot_params['variables_label']=dataset.vars_label
    plot_params['variables_id']=dataset.vars_id
    plot_params['variables_units']=dataset.vars_units
    plot_params['variables_limits']=dataset.vars_limits
    plot_params['latlimmap']=dataset.latlimmap
    plot_params['lonlimmap']=dataset.lonlimmap
    plot_params['lonlimtransect']=dataset.lonlimtransect
    plot_params['depthlimtransect']=dataset.depthlimtransect
    plot_params['tolerance']=dataset.tolerance
    plot_params['exppts']=dataset.exppts
    plot_params['num_interp_pts']=dataset.num_interp_pts
    
    return plot_params


# In[ ]:


def save_dataset_as_glider_info_jsons(outputpath, dataset, metadata):
    
    ################################################
    # save metadata glider_info.json files for NVS #
    ################################################
    from create_jsons import GliderJson

    # create folder/check if folder already exists for a given glider
    foldername = outputpath + dataset.transect_id
    if not(os.path.exists(foldername)):
        try:
            os.mkdir(foldername)
        except OSError:
            print ('Directory %s already exists. Accessing directory.' % foldername)
        else:
            print ('Successfully created the directory %s ' % foldername)                

    # check if glider_info.json already exists, if not create new, if so load
    print('   ...creating glider_info.json for')
    info_json = os.path.join(foldername, 'glider_info.json')

    if not os.path.exists(info_json):

        glider_obj = GliderJson(transect_id=dataset.transect_id, transect_label=metadata['transect_label'], 
                                active=dataset.deployment_active,
                                provider_name=metadata['provider_name'], provider_url=metadata['provider_url'], 
                                provider_contact_name=metadata['provider_contact_name'],
                                provider_contact_email=metadata['provider_contact_email'], 
                                deployment_info_url_template=metadata['deployment_info_url_template'],
                                section_info_url_template=metadata['section_info_url_template'], 
                                section_plots_url_template=metadata['section_plots_url_template'],
                                section_data_url_template=metadata['section_data_url_template'])

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

    if dataset.deployment_id in ids:
        glider_obj.update_deployment(deployment_id=dataset.deployment_id, 
                                     deployment_start_time=dataset.datetime_start,
                                     deployment_end_time=metadata['datetime_latest'],
                                     deployment_active=dataset.deployment_active,
                                     plotting_active=True)
    else:
        glider_obj.add_deployment(glider_id=dataset.glider_id,
                                  dataset_id=dataset.dataset_id,
                                  deployment_id=dataset.deployment_id, 
                                  deployment_label=dataset.deployment_label,
                                  deployment_active=dataset.deployment_active,
                                  plotting_active=True,
                                  deployment_start_time=dataset.datetime_start, 
                                  deployment_end_time=metadata['datetime_latest'])

    # save updated glider_info.json
    with open(info_json, "w") as write_file:
        json.dump(glider_obj.__dict__, write_file)  
        
    return


# In[ ]:


def save_dataset_as_glider_plottinginfo_jsons(outputpath, dataset, metadata):
    
    ################################################
    # save metadata glider_info.json files for NVS #
    ################################################
    from create_jsons import Glider_Plotting_Json

    # create folder/check if folder already exists for a given glider
    foldername = outputpath + dataset.transect_id
    if not(os.path.exists(foldername)):
        try:
            os.mkdir(foldername)
        except OSError:
            print ('Directory %s already exists. Accessing directory.' % foldername)
        else:
            print ('Successfully created the directory %s ' % foldername)                

    # check if glider_info.json already exists, if not create new, if so load
    print('   ...creating glider_plottinginfo.json')
    info_json = os.path.join(foldername, 'glider_plottinginfo.json')

    if not os.path.exists(info_json):
        gliderplot_obj = Glider_Plotting_Json(transect_id=dataset.transect_id, 
                                              transect_label=metadata['transect_label'])
        with open(info_json, "w") as write_file:
            json.dump(gliderplot_obj.__dict__, write_file) 

    else:
        with open(info_json) as g:
            glider_dict = json.load(g)
            gliderplot_obj = Glider_Plotting_Json(json_obj=glider_dict)
            
            

    # check to see if deployment info already exists, if not: create new, if so: update end times
    with open(info_json) as g:
        glider_dict = json.load(g)
        gliderplot_obj = Glider_Plotting_Json(json_obj=glider_dict)

    ids = []
    for depinfo in gliderplot_obj.deployments:
        ids.append(depinfo['id'])

    if dataset.deployment_id in ids:
        gliderplot_obj.update_deployment(deployment_id=dataset.deployment_id, 
                                         deployment_start_time=dataset.datetime_start,
                                         deployment_end_time=metadata['datetime_latest'])
    else:
        plot_params = get_dataset_plotparams(dataset)        
        gliderplot_obj.add_deployment(deployment_id=dataset.deployment_id, 
                                      deployment_label=dataset.deployment_label,
                                      deployment_start_time=dataset.datetime_start, 
                                      deployment_end_time=metadata['datetime_latest'],
                                      plot_params=plot_params, verified=True)

    # save updated glider_info.json
    with open(info_json, "w") as write_file:
        json.dump(gliderplot_obj.__dict__, write_file)  
        
    return

# In[ ]:

def send_emailreport(msgtxt, subj,
                     fromaddr='nwemdata@uw.edu', toaddr='nwemdata@uw.edu',
                     login='nwemdata@gamail.uw.edu', passwd='bu0yWhi$perer', 
                     smtpserver='smtp.uw.edu:587', htmlflag=False):
    
    # Function: send_emailreport
    # This function is used to send automatic emails to the data manager
    
    import smtplib
    from email.message import EmailMessage
        
    
    # Create the email message
    msg = EmailMessage()
    msg['Subject'] = subj
    msg['From'] = fromaddr
    msg['To'] = toaddr
    if htmlflag:
        msg.set_content(msgtxt, subtype='html')
    else:
        msg.set_content(msgtxt)
    
    # Login to the email server
    server = smtplib.SMTP(smtpserver)
    server.ehlo()
    server.starttls()
    server.ehlo()
    server.login(login, passwd)
    
    
    # Send the message
    problems = server.send_message(msg)
    
    # Logout of the email server
    server.quit()
    
    return