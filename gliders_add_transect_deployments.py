#!/usr/bin/env python
# coding: utf-8

# In[ ]:


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

# import classes needed to build initial parameters objects
from classes import Dataset

from importlib import reload

import gliders_general_functions as gliders_gen

import create_jsons
from create_jsons import GliderJson
from create_jsons import Glider_Plotting_Json


# # Working with transect jsons

# In[ ]:


def extract_latest_deployment(glider_id, glider_info, gliderplot_info, deployment_time=None):
    
    ########################################
    # Get latest deployment from glider info
    
    # Extract out the glider deployments for the given glider id
    glider_datasets = []
    for ii in range(0,len(glider_info['deployments'])):
        if glider_info['deployments'][ii]['glider_id'] == glider_id:
            glider_datasets.append(glider_info['deployments'][ii])
    if len(glider_datasets) == 0:
        glider_datasets.append(glider_info['deployments'][len(glider_info['deployments'])-1])
            
    dataset_ids = [glider_datasets[ii]['dataset_id'] for ii in range(0,len(glider_datasets))]
    dataset_dates = [datetime.datetime.strptime(glider_datasets[ii]['start_time'],
                                                '%Y-%m-%dT%H:%M:%SZ') 
                     for ii in range(0,len(glider_datasets))]
    
    
    
    # Get the latest deployment
    if deployment_time is not None:
        # Find the deployment which occurs closest to the deployment time
        time_since_deployment = [abs(deployment_time - jj) for jj in dataset_dates]
        last_deployment_ind = np.where([jj == min(time_since_deployment) for jj in time_since_deployment])[0][0]
    else:
        # Find the deployment with the maximum deployment time
        last_deployment_ind = np.where([jj == max(dataset_dates) for jj in dataset_dates])[0]
        if len(last_deployment_ind) > 0:
            last_deployment_ind = last_deployment_ind[0]
    last_deployment = glider_datasets[last_deployment_ind].copy()
    last_deployment_id = last_deployment['id']
    
    
    
    #################################################
    # Get latest deployment from glider plotting info
    
    # Extract out the glider plotting deployments for the given glider id
    gliderplot_datasets = []
    for ii in range(0,len(gliderplot_info['deployments'])):
        if gliderplot_info['deployments'][ii]['id'] == last_deployment_id:
            gliderplot_datasets.append(gliderplot_info['deployments'][ii])

    dataset_dates = [datetime.datetime.strptime(gliderplot_datasets[ii]['start_time'],
                                                '%Y-%m-%dT%H:%M:%SZ') 
                         for ii in range(0,len(gliderplot_datasets))]
    
    # Get the latest deployment
    last_deployment_ind = np.where([jj == max(dataset_dates) for jj in dataset_dates])[0][0]
    last_plotdeployment = gliderplot_datasets[last_deployment_ind].copy()
    
    
    return last_deployment, last_plotdeployment


# In[ ]:


def check_glider_deployment_order(transect_id):
    
    """
    This function is used to look at the json containing the relevant
    information for a given transect ID, and to then check that the 
    deployments for that transect ID are listed in chronological order,
    starting with the oldest
    
    Inputs: transect_id
    """
    
    __, __, transect_basedir = gliders_gen.get_pathdirs()
    transect_dir = os.path.join(transect_basedir,transect_id)
    
    # Load in the glider information
    glider_info, gliderplot_info = gliders_gen.load_glider_info_all(transect_id)
        
    
    #############################
    # Glider info file
    
    # Extract the start time for each deployment
    gl_deploy = glider_info['deployments']
    startimes = []
    for ii in range(0,len(gl_deploy)):
        startimes.append(datetime.datetime.strptime(gl_deploy[ii]['start_time'], '%Y-%m-%dT%H:%M:%SZ'))
    
    # Sort the start times, and rebuild the deployment order,
    # starting with the earliest
    sortinds = np.argsort(startimes)
    gl_deploy_sorted = []
    for ii in range(0,len(sortinds)):
        gl_deploy_sorted.append(gl_deploy[sortinds[ii]])
        
    glider_info['deployments'] = gl_deploy_sorted
    
    # Re-write the json with the sorted deployments
    info_json = 'glider_info.json'
    with open(os.path.join(transect_dir,info_json), "w") as write_file:
        json.dump(glider_info, write_file)  
        
    
    #############################
    # Glider plotting info file
    
    # Extract the start time for each deployment
    gl_deploy = gliderplot_info['deployments']
    startimes = []
    for ii in range(0,len(gl_deploy)):
        startimes.append(datetime.datetime.strptime(gl_deploy[ii]['start_time'], '%Y-%m-%dT%H:%M:%SZ'))
    
    # Sort the start times, and rebuild the deployment order,
    # starting with the earliest
    sortinds = np.argsort(startimes)
    gl_deploy_sorted = []
    for ii in range(0,len(sortinds)):
        gl_deploy_sorted.append(gl_deploy[sortinds[ii]])
        
    gliderplot_info['deployments'] = gl_deploy_sorted
    
    # Re-write the json with the sorted deployments
    info_json = 'glider_plottinginfo.json'
    with open(os.path.join(transect_dir,info_json), "w") as write_file:
        json.dump(gliderplot_info, write_file)  


# In[ ]:


def find_datasets_to_make(glider_id, glider_info, 
                          glider_alldatasets, glider_alldataset_times, 
                          glider_alldataset_delayed, excluded_datasets):
    
    # Extract all of the datasets for a given glider from the
    # glider transect info
    deployment_datasets = []
    for ii in range(0,len(glider_info['deployments'])):
        if glider_info['deployments'][ii]['glider_id'] == glider_id:
            deployment_datasets.append(glider_info['deployments'][ii])

    dataset_ids = [deployment_datasets[ii]['dataset_id'] for ii in range(0,len(deployment_datasets))]
    dataset_dates = [datetime.datetime.strptime(deployment_datasets[ii]['start_time'],
                                                '%Y-%m-%dT%H:%M:%SZ') 
                     for ii in range(0,len(deployment_datasets))]
    
    
    
    # Based upon the existing jsons and the list of datasets 
    # on ERDDAP, make a list of jsons that still need to
    # be created
    datasets_to_make = []
    datasets_to_make_times = []
    datasets_to_make_delayed = []
    for ii in range(0,len(glider_alldatasets)):
        close_datasets = [abs(jj - glider_alldataset_times[ii]) < datetime.timedelta(days=7) 
                          for jj in glider_alldataset_times]
        close_datasets[ii] = False
        if glider_alldatasets[ii] in dataset_ids:
            # If the ERDDAPglider dataset already exists in the list
            # of saved glider datasets, continue on without
            # adding to the list of datasets to make
            continue
            
            #print('Check 1: Dataset already exists:', glider_alldatasets[ii])
            
        elif glider_alldatasets[ii] in excluded_datasets:
            # If the ERDDAPglider dataset is in the list of
            # datasets to excluded, continue on without 
            # adding to the list of datasets to make
            continue

        elif any(close_datasets):
            # If there are any datasets that do not current exist, 
            # and the start time of the dataset is close to the start time
            # of one of the existing datasets (i.e., within +/- 7 days),
            # then check closer to see if the dataset should be added
            # to the list of datasets to make

            
            close_dataset_inds = np.where(close_datasets)[0]
            #print('Check 2a: Close datasets exist:',glider_alldatasets[ii])
            #print('   Close dataset(s) is(are):',[glider_alldatasets[jj] for jj in close_dataset_inds])


            if (any(['delayed' in glider_alldatasets[close_dataset_inds[jj]] 
                     for jj in range(0,len(close_dataset_inds))]) 
                and not(glider_alldataset_delayed[ii])):
                # If the close dataset is a delayed product, the dataset being checked
                # is not a delayed product, then continue on without
                # adding the dataset to the list of datasets to make
                #print('Check 2a: Dataset being checked is not delayed, and a close one exists:', glider_alldatasets[ii])
                continue
            else:
                # If any of the above are not true, then add the dataset to
                # the list of datasets to make
                #print('Check 2b: Dataset being checked is fine:', glider_alldatasets[ii])
                datasets_to_make.append(glider_alldatasets[ii])
                datasets_to_make_times.append(glider_alldataset_times[ii])
                datasets_to_make_delayed.append(glider_alldataset_delayed[ii])
        else:
            # If the dataset does not already exist in the list of existing datasets
            # and the start time of the dataset is not close to that of another dataset,
            # then add the dataset to the list of datasets to make
            #print('Check 3: Dataset looks good:',glider_alldatasets[ii])
            datasets_to_make.append(glider_alldatasets[ii])
            datasets_to_make_times.append(glider_alldataset_times[ii])
            datasets_to_make_delayed.append(glider_alldataset_delayed[ii])
        
    datasets_to_make = sorted(datasets_to_make)
    
    
    return datasets_to_make, datasets_to_make_times, datasets_to_make_delayed


# In[ ]:


def update_glider_dataset_jsons(transect_id, glider_id, 
                                glider_info, gliderplot_info,
                                glider_obj, gliderplot_obj,
                                existing_glider_datasets,
                                existing_dataset_dates,
                                existing_dataset_ids,
                                datasets_to_make, 
                                datasets_to_make_times, 
                                datasets_to_make_delayed):
    
    # Step through all of the datasets to make and/or update 
    # (i.e., add a new one or change an existing one to 
    #        a delayed-product)
    # for a given glider ID in a given transect
    for ii in range(0, len(datasets_to_make)):

        gliders_gen.load_erddap_glider_metadata(transect_id, datasets_to_make[ii])

        if any([abs(jj - datasets_to_make_times[ii]) < datetime.timedelta(days=7) 
                for jj in existing_dataset_dates]):
            # If there are any datasets that do not current exist, 
            # and the start time of the dataset is close to the start time
            # of one of the existing datasets (i.e., within +/- 7 days),
            # then check closer to see if the dataset should be added
            # to the list of datasets to make

            close_datasets = [abs(jj - datasets_to_make_times[ii]) < datetime.timedelta(days=7) 
                              for jj in existing_dataset_dates]
            close_datasets = np.where(close_datasets)[0]
            if (not(any(['delayed' in existing_dataset_ids[close_datasets[jj]] 
                         for jj in range(0,len(close_datasets))])) 
                and datasets_to_make_delayed[ii]):
                print('      Update existing non-delayed dataset with delayed product',datasets_to_make[ii])

                closest_id = close_datasets[0]
                glider_dataset = existing_glider_datasets[closest_id].copy()

                metadata = gliders_gen.load_erddap_glider_metadata(transect_id, datasets_to_make[ii])
                dataset_params = gliders_gen.set_deployment_dataset_parameters(glider_id, datasets_to_make[ii])
                

                glider_obj.update_deployment(deployment_id=glider_dataset['id'],
                                             deployment_start_time=dataset_params['datetime_start'],
                                             deployment_end_time=dataset_params['datetime_end'],
                                             deployment_active=dataset_params['deployment_active'],
                                             plotting_active=True,
                                             newdeployment_id=dataset_params['deployment_id'],
                                             newdeployment_label=dataset_params['deployment_label'],
                                             dataset_id=datasets_to_make[ii])
                
                gliderplot_obj.update_deployment(deployment_id=glider_dataset['id'],
                                                 deployment_start_time=dataset_params['datetime_start'],
                                                 deployment_end_time=dataset_params['datetime_end'],
                                                 newdeployment_id=dataset_params['deployment_id'],
                                                 newdeployment_label=dataset_params['deployment_label'])

        else:
            print('      Add new dataset:',datasets_to_make[ii])

            [last_deployment, 
             last_plotdeployment] = extract_latest_deployment(glider_id, glider_info, gliderplot_info)

            metadata = gliders_gen.load_erddap_glider_metadata(transect_id, datasets_to_make[ii])
            dataset_params = gliders_gen.set_deployment_dataset_parameters(glider_id, datasets_to_make[ii])
            

            glider_obj.add_deployment(glider_id=glider_id,
                                      dataset_id=datasets_to_make[ii],
                                      deployment_id=dataset_params['deployment_id'], 
                                      deployment_label=dataset_params['deployment_label'],
                                      deployment_start_time=dataset_params['datetime_start'], 
                                      deployment_end_time=metadata['datetime_latest'],
                                      deployment_active=dataset_params['deployment_active'],
                                      plotting_active=True)

            gliderplot_obj.add_deployment(deployment_id=dataset_params['deployment_id'],
                                          deployment_label=dataset_params['deployment_label'],
                                          deployment_start_time=dataset_params['datetime_start'],
                                          deployment_end_time=metadata['datetime_latest'],
                                          plot_params=last_plotdeployment,
                                          verified=False)


# In[ ]:


def add_transect_deployments(transect_id, glider_id, location_txt=None):
    
    __, __, transect_basedir = gliders_gen.get_pathdirs()

    #################################################
    # Ensure that all deployments are in the right order for the transect
    check_glider_deployment_order(transect_id)

    
    #################################################
    # Load in all the glider info, and ensure that it is set
    # up in dataset objects
    glider_info, gliderplot_info = gliders_gen.load_glider_info_all(transect_id)
    glider_obj = GliderJson(json_obj=glider_info)
    gliderplot_obj = Glider_Plotting_Json(json_obj=gliderplot_info)
    
    glider_exclusions = gliders_gen.load_glider_exclusions(transect_id)

    
    
    # Get a list of all datasets for a given
    # glider on the Glider ERDDAP
    if ('ooi' in transect_id) and (location_txt is not None):
        [glider_alldatasets,
         glider_alldataset_times,
         glider_alldataset_delayed] = gliders_gen.find_location_glider_ids(location_txt)
    else:
        [glider_alldatasets,
         glider_alldataset_times,
         glider_alldataset_delayed] = gliders_gen.find_glider_datasets(glider_id)
    
    
    ###################################
    # Step through each glider ID, and update the
    print('   Checking deployments for glider:',glider_id)



    # Extract out the datasets to exclude for the glider
    excluded_datasets = []
    if glider_exclusions is not None:
        for ii in range(0,len(glider_exclusions)):
            if glider_exclusions['excluded_deployments'][ii]['glider_id'] == glider_id:
                excluded_datasets.append(glider_exclusions['excluded_deployments'][ii]['dataset_id'])

    # Extract out the existing dataset IDs and start dates
    glider_datasets = []
    for ii in range(0,len(glider_info['deployments'])):
        if glider_info['deployments'][ii]['glider_id'] == glider_id:
            glider_datasets.append(glider_info['deployments'][ii])

    dataset_ids = [glider_datasets[ii]['dataset_id'] for ii in range(0,len(glider_datasets))]
    dataset_dates = [datetime.datetime.strptime(glider_datasets[ii]['start_time'],
                                                '%Y-%m-%dT%H:%M:%SZ') 
                     for ii in range(0,len(glider_datasets))]


    # Determine all of the datasets to make for a given glider ID
    # from the list of all available datasets
    [datasets_to_make, 
     datasets_to_make_times, 
     datasets_to_make_delayed] = find_datasets_to_make(glider_id, glider_info, 
                                                       glider_alldatasets, 
                                                       glider_alldataset_times, 
                                                       glider_alldataset_delayed,
                                                       excluded_datasets)

    print('      # of datasets to make/update:',len(datasets_to_make))


    # Update the glider datasets 
    # (i.e., add new one, or change an existing one to
    #        a delayed-product)
    update_glider_dataset_jsons(transect_id, glider_id, 
                                glider_info, gliderplot_info, 
                                glider_obj, gliderplot_obj,
                                glider_datasets, dataset_dates, dataset_ids,
                                datasets_to_make, 
                                datasets_to_make_times, 
                                datasets_to_make_delayed)
        
    
    ##########################################
    # After all gliders have been checked and updated,
    # save the glider objects into the jsons
    print('All gliders checked. Saving the results...')
    gliders_gen.save_glider_info_all(transect_id, glider_obj, gliderplot_obj)
    
    
    #################################################
    # Ensure that all deployments are in the right order for the transect
    check_glider_deployment_order(transect_id)
    
    return


# In[ ]:


def main():
    
    try:
        opts, args = getopt.getopt(sys.argv[1:], "hu:t:g:", ["help", "transect", "glider"])
    except Exception as inst:
        # print help information and exit:
        print('Error in getting options: ' + str(inst)) # will print something like "option -a not recognized"
        sys.exit(2)
        
    
    # step through command-line options and their arguments
    processFlag = False
    transectFlag = False
    gliderFlag = False
    
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
        elif o in ("-g", "--glider"):
            gliderFlag = True
            gliderName = a
        else:
            assert False, "unhandled option"
    
        
        
    # If the transect name was given, ensure that the transect name is in lowercase,
    # and that it matches one of the valid transect names
    valid_transects = ['lapush', 'osu_trinidad1', 'washelf', 
                       'ooi_ghs', 'ooi_ghd', 'ooi_ns', 'ooi_nd', 'ooi_coosbay']    
    def list_valid_transects():
        print('Valid transects include: ')
        print('"lapush" - NANOOS glider off of LaPush, Washington')
        print('"osu_trinidad1" - NANOOS glider at Trinidad Head, Oregon')
        print('"washelf" - NANOOS glider along the Washington Shelf')
        print('"ooi_ghs" - OOI shallow glider at Grays Harbor, Washington')
        print('"ooi_ghd" - OOI deep glider at Grays Harbor, Washington')
        print('"ooi_ns" - OOI shallow glider at Newport, Oregon')
        print('"ooi_nd" - OOI deep glider at Newport, Oregon')
        print('"ooi_coosbay" - OOI deep glider at Coos Bay, Oregon')
        return        
    
    if transectFlag:
        if transectName.lower() in valid_transects:
            print(datetime.datetime.now().strftime('%Y-%b-%d %H:%M:%S') 
                  + ' - Process will be performed for the transect:' + transectName)
            print('   Process: adding new datasets')
        else:
            print('Invalid transect name. Check name, and retry.')
            list_valid_transects()
            sys.exit(2)
    else:
        print('No transect name is given. Try again with options: "-t *transect*"')
        list_valid_transects()
        sys.exit(2)
        
   

    #######################################
    # Make the plots for a defined transect
    try:
        if transectFlag and gliderFlag:
            add_transect_deployments(transectName, gliderName)
        else:
            if not(transectFlag):
                print('No transect given. Give a transect name, and try again')
                list_valid_transects()
            if not(gliderFlag):
                print('No glider ID given. Give a glider name, and try again')
                
    except Exception as e:
        print('An error occured while making plots for transect ' + transectName)
        print('Error message:')
        print(e)
        
    sys.exit(2)


# In[ ]:


if __name__ == "__main__":
    main()

