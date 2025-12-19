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
import shutil

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
        last_deployment_ind = np.where([jj == max(dataset_dates) for jj in dataset_dates])[0][0]
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
    glplot_deploy = gliderplot_info['deployments']
    
    startimes = []
    for ii in range(0,len(gl_deploy)):
        startimes.append(datetime.datetime.strptime(gl_deploy[ii]['start_time'], '%Y-%m-%dT%H:%M:%SZ'))
    
    # Sort the start times, and rebuild the deployment order,
    # starting with the earliest
    sortinds = np.argsort(startimes)
    gl_deploy_sorted = []
    for ii in range(0,len(sortinds)):
        if (sortinds[ii] < len(sortinds)-1) and ('Ongoing' in gl_deploy[sortinds[ii]]['id']):
            
            print('Updating glider deployment labels for: ' + gl_deploy[sortinds[ii]]['id'])
            deployment_id, deployment_label = gliders_gen.set_dataset_id_label(gl_deploy[sortinds[ii]]['glider_id'], 
                                                                               gl_deploy[sortinds[ii]]['dataset_id'], 
                                                                               deployment_active=False)
            if os.path.exists(os.path.join(transect_dir,gl_deploy[sortinds[ii]]['id'])):
                # Rename the folder containing the data
                shutil.rmtree(os.path.join(transect_dir,gl_deploy[sortinds[ii]]['id']))
                
                # Re-write the json with the updated deployment labels
                deploy_json = 'deployment_info.json'
                with open(os.path.join(transect_dir, deployment_id, deploy_json), "r") as deploy_file:
                    deploy_info = json.load(deploy_file)
                deploy_info['id'] = deployment_id
                deploy_info['label'] = deployment_label
                with open(os.path.join(transect_dir, deployment_id, deploy_json), "w") as deploy_file:
                    json.dump(deploy_info, deploy_file)
                    
            # Update the glider info json with the correct deployment labels
            matchind = np.where([plot_dep['id'] == gl_deploy[sortinds[ii]]['id'] 
                                 for plot_dep in glplot_deploy])[0][0]
            
            gl_deploy[sortinds[ii]]['id'] = deployment_id
            gl_deploy[sortinds[ii]]['label'] = deployment_label
            
            glplot_deploy[matchind]['id'] = deployment_id
            glplot_deploy[matchind]['label'] = deployment_label
            
        gl_deploy_sorted.append(gl_deploy[sortinds[ii]])
        
    glider_info['deployments'] = gl_deploy_sorted
    
    # Re-write the json with the sorted deployments
    info_json = 'glider_info.json'
    with open(os.path.join(transect_dir,info_json), "w") as write_file:
        json.dump(glider_info, write_file)  
        
    
    #############################
    # Glider plotting info file
    
    # Extract the start time for each deployment
    startimes = []
    for ii in range(0,len(glplot_deploy)):
        startimes.append(datetime.datetime.strptime(glplot_deploy[ii]['start_time'], '%Y-%m-%dT%H:%M:%SZ'))
    
    # Sort the start times, and rebuild the deployment order,
    # starting with the earliest
    sortinds = np.argsort(startimes)
    gl_deploy_sorted = []
    for ii in range(0,len(sortinds)):            
        gl_deploy_sorted.append(glplot_deploy[sortinds[ii]])
        
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

    dataset_ids = [deployment_datasets[ii]['dataset_id'] 
                   for ii in range(0,len(deployment_datasets))]
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
                print('      Update existing non-delayed dataset with delayed product',
                      datasets_to_make[ii])

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


def update_glider_times_jsons(transect_id, glider_id, 
                              glider_obj, gliderplot_obj,
                              glider_datasets,
                              datasets_to_update):
    
    # Step through all of the datasets to make and/or update 
    # (i.e., add a new one or change an existing one to 
    #        a delayed-product)
    # for a given glider ID in a given transect
    for ii in range(0, len(datasets_to_update)):
        
        gliders_gen.load_erddap_glider_metadata(transect_id, datasets_to_update[ii])
        glider_dataset = glider_datasets[ii].copy()
        metadata = gliders_gen.load_erddap_glider_metadata(transect_id, datasets_to_update[ii])
        dataset_params = gliders_gen.set_deployment_dataset_parameters(glider_id, datasets_to_update[ii])
        
        glider_obj.update_deployment(deployment_id=glider_dataset['id'],
                                     deployment_start_time=dataset_params['datetime_start'],
                                     deployment_end_time=metadata['datetime_latest'],
                                     deployment_active=dataset_params['deployment_active'],
                                     plotting_active=True,
                                     newdeployment_id=dataset_params['deployment_id'],
                                     newdeployment_label=dataset_params['deployment_label'],
                                     dataset_id=datasets_to_update[ii])

        gliderplot_obj.update_deployment(deployment_id=glider_dataset['id'],
                                         deployment_start_time=dataset_params['datetime_start'],
                                         deployment_end_time=dataset_params['datetime_end'],
                                         newdeployment_id=dataset_params['deployment_id'],
                                         newdeployment_label=dataset_params['deployment_label'])  


# In[ ]:


def update_inactive_gliders_jsons(transect_id, glider_id, 
                                      glider_obj, gliderplot_obj,
                                      glider_datasets,
                                      datasets_to_update):
    
    # Step through all of the datasets to make and/or update 
    # (i.e., add a new one or change an existing one to 
    #        a delayed-product)
    # for a given glider ID in a given transect
    for ii in range(0, len(datasets_to_update)):
        
        gliders_gen.load_erddap_glider_metadata(transect_id, datasets_to_update[ii])
        glider_dataset = glider_datasets[ii].copy()
        metadata = gliders_gen.load_erddap_glider_metadata(transect_id, datasets_to_update[ii])
        dataset_params = gliders_gen.set_deployment_dataset_parameters(glider_id, datasets_to_update[ii])
        
        glider_obj.update_deployment(deployment_id=glider_dataset['id'],
                                     deployment_start_time=glider_dataset['start_time'],
                                     deployment_end_time=glider_dataset['end_time'],
                                     deployment_active=False,
                                     plotting_active=True,
                                     newdeployment_id=glider_dataset['id'],
                                     newdeployment_label=glider_dataset['label'],
                                     dataset_id=datasets_to_update[ii])

        gliderplot_obj.update_deployment(deployment_id=glider_dataset['id'],
                                         deployment_start_time=glider_dataset['start_time'],
                                         deployment_end_time=glider_dataset['end_time'],
                                         newdeployment_id=glider_dataset['id'],
                                         newdeployment_label=glider_dataset['label'])  


# In[ ]:


def get_ooi_deploymentname(transect_id):
    
    if transect_id == 'ooi_ghs':
        location_txt = "Grays Harbor Shallow"
    elif transect_id == 'ooi_ghd':
        location_txt = "Grays Harbor Deep"
    elif transect_id == 'ooi_ns':
        location_txt = "Newport Hydrographic Shallow"
    elif transect_id == 'ooi_nd':
        location_txt = "Newport Hydrographic Deep"
    elif transect_id == 'ooi_coosbay':
        location_txt = "Coos Bay"
        
    else:
        print('Valid transects include: ')
        print('"ooi_ghs" - OOI shallow glider at Grays Harbor, Washington')
        print('"ooi_ghd" - OOI deep glider at Grays Harbor, Washington')
        print('"ooi_ns" - OOI shallow glider at Newport, Oregon')
        print('"ooi_nd" - OOI deep glider at Newport, Oregon')
        print('"ooi_coosbay" - OOI deep glider at Coos Bay, Oregon')
        location_txt = None
        
    return location_txt


# In[ ]:


def check_transect_deployments(transect_id):
    
    __, __, transect_basedir = gliders_gen.get_pathdirs()
    successFlag = True

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

    # Extract out the glider IDs, and find the unique glider IDs
    if 'ooi' in transect_id:
        glider_ids = [get_ooi_deploymentname(transect_id)]
        
    else:
        glider_ids = []
        for ii in range(0,len(glider_info['deployments'])):
            glider_ids.append(glider_info['deployments'][ii]['glider_id'])

        glider_ids = np.unique(glider_ids)

    
    #############################################
    # Step through each glider ID, and find any
    # gliders that need to have a new deployment
    # added, or an existing deployment updated
    # to a delayed product
    update_jsonflag = False
    for ind in range(0,len(glider_ids)):
        glider_id = glider_ids[ind]
        print('   Checking deployments to add/update status for glider:',glider_id)

        # Get a list of all datasets for a given
        # glider on the Glider ERDDAP
        if 'ooi' in transect_id:
            print('      OOI Transect: Look for gliders by transect label.')
            [glider_alldatasets,
             glider_alldataset_times,
             glider_alldataset_delayed] = gliders_gen.find_location_glider_ids(glider_id, ooi_loc=True)
        else:
            [glider_alldatasets,
             glider_alldataset_times,
             glider_alldataset_delayed] = gliders_gen.find_glider_datasets(glider_id)
        
        # Extract out the datasets to exclude for the glider
        excluded_datasets = []
        if glider_exclusions is not None:
            for ii in range(0,len(glider_exclusions['excluded_deployments'])):
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


        # Update the glider datasets 
        # (i.e., add new one, or change an existing one to
        #        a delayed-product)
        print('      # of datasets to make new/update to delayed-product:',len(datasets_to_make))
        if len(datasets_to_make) > 0:
            update_jsonflag = True
            update_glider_dataset_jsons(transect_id, glider_id, 
                                        glider_info, gliderplot_info, 
                                        glider_obj, gliderplot_obj,
                                        glider_datasets, dataset_dates, dataset_ids,
                                        datasets_to_make, 
                                        datasets_to_make_times, 
                                        datasets_to_make_delayed)
            
    
    #################################################
    # Check all gliders for a transect to ensure that
    # the ending date of the transect matches the
    # ending date of the data
    for glider_id in glider_ids:
        print('   Checking deployments to update latest time for glider:',glider_id)
        
        ## Get a list of all datasets for a given
        ## glider on the Glider ERDDAP
        #if 'ooi' in transect_id:
        #    [glider_alldatasets,
        #     glider_alldataset_times,
        #     glider_alldataset_delayed] = gliders_gen.find_location_glider_ids(glider_id)
        #else:
        #    [glider_alldatasets,
        #     glider_alldataset_times,
        #     glider_alldataset_delayed] = gliders_gen.find_glider_datasets(glider_id)

        # Extract out the existing dataset IDs and start dates
        glider_datasets = []
        for ii in range(0,len(glider_info['deployments'])):
            
            # Look through each deployment for a given glider,
            # and if the deployment is active, append it to a list
            # to check, as well as the start and end dates of the deploymnet
            if ((glider_info['deployments'][ii]['glider_id'] == glider_id)
                and
                glider_info['deployments'][ii]['deployment_active']):                
                glider_datasets.append(glider_info['deployments'][ii])
                
            # Extract our the relevant field from the identified glider datasets
            dataset_ids = [glider_datasets[ii]['dataset_id'] 
                           for ii in range(0,len(glider_datasets))]
            dataset_startdates = [datetime.datetime.strptime(glider_datasets[ii]['start_time'],
                                                             '%Y-%m-%dT%H:%M:%SZ') 
                                  for ii in range(0,len(glider_datasets))]
            dataset_enddates = [datetime.datetime.strptime(glider_datasets[ii]['end_time'],
                                                           '%Y-%m-%dT%H:%M:%SZ') 
                                for ii in range(0,len(glider_datasets))]

        # After a list of active deployments has been made, compare the glider info
        # end date to the erddap metadata end date, and if their metadata end date
        # is later, there is new data, and the glider info should be updated
        glider_datasets_to_update = []
        datasets_to_update = []
        for ii in range(0,len(dataset_ids)):
            glider_metadata = gliders_gen.load_erddap_glider_metadata(transect_id, 
                                                                      dataset_ids[ii])
            if (datetime.datetime.strptime(glider_metadata['datetime_latest'],
                                           '%Y-%m-%dT%H:%M:%SZ') > dataset_enddates[ii]):
                glider_datasets_to_update.append(glider_datasets[ii])
                datasets_to_update.append(dataset_ids[ii])
        
        print('      # of datasets to make update latest time:',len(datasets_to_update))
        if len(datasets_to_update) > 0:
            update_jsonflag = True
            update_glider_times_jsons(transect_id, glider_id, 
                                      glider_obj, gliderplot_obj,
                                      glider_datasets_to_update,
                                      datasets_to_update)
            
            
    #########################################
    # OOI Gliders use multiple gliders on the
    # same line. Therefore, we also need to
    # check deployments to see if there are
    # any additional deployments that exist
    # for a given glider after the dataset.
    
    if 'ooi' in transect_id:  
        print('   Checking OOI deployments to ensure no later glider deployments')      
        glider_active_datasets = []
        glider_active_dataset_ids = []
        glider_active_inds = []
        glider_active_enddates = []
        for ii in range(0,len(glider_info['deployments'])):
            if glider_info['deployments'][ii]['deployment_active']:
                glider_active_datasets.append(glider_info['deployments'][ii])
                glider_active_dataset_ids.append(glider_info['deployments'][ii]['dataset_id'])
                glider_active_inds.append(ii)
                glider_active_enddates.append(datetime.datetime.strptime(glider_info['deployments'][ii]['end_time'],
                                                                   '%Y-%m-%dT%H:%M:%SZ'))
        glider_active_ids = [ii[:ii.find('-')] for ii in glider_active_dataset_ids]


        # After a list of active deployments has been made, 
        # compare the glider info
        # end date to the erddap metadata end date, and if there metadata end date
        # is later, there is new data, and the glider info should be updated
        glider_datasets_to_update = []
        datasets_to_update = []        
        for ind in range(0,len(glider_active_inds)):

            glider_id = glider_active_ids[ind]

            # Get a list of all datasets for a given
            # glider on the Glider ERDDAP
            [glider_alldatasets,
             glider_alldataset_times,
             glider_alldataset_delayed] = gliders_gen.find_glider_datasets(glider_id)

            if any([starttime > glider_active_enddates[ind]
                    for starttime in glider_alldataset_times]):                
                glider_datasets_to_update.append(glider_active_datasets[ind])
                datasets_to_update.append(glider_active_dataset_ids[ind])

        print('      # of OOI datasets to update as inactive:',len(datasets_to_update))
        if len(datasets_to_update) > 0:
            update_jsonflag = True
            update_inactive_gliders_jsons(transect_id, glider_id, 
                                              glider_obj, gliderplot_obj,
                                              glider_datasets_to_update,
                                              datasets_to_update)
        
        
        
    
    #########################################
    # OLD Datasets: Check if there are any
    # datasets that are particularly old;
    # (i.e., more than 6 months old)
    # Assume that if the last data is more
    # than 6 months old, then that dataset
    # is unlikely to be updated again.
    
    print('   Checking "active" deployments to look for old datasets')      
    glider_active_datasets = []
    glider_active_dataset_ids = []
    glider_active_inds = []
    glider_active_enddates = []
    for ii in range(0,len(glider_info['deployments'])):
        if glider_info['deployments'][ii]['deployment_active']:
            glider_active_datasets.append(glider_info['deployments'][ii])
            glider_active_dataset_ids.append(glider_info['deployments'][ii]['dataset_id'])
            glider_active_inds.append(ii)
            glider_active_enddates.append(datetime.datetime.strptime(glider_info['deployments'][ii]['end_time'],
                                                               '%Y-%m-%dT%H:%M:%SZ'))
    glider_active_ids = [ii[:ii.find('-')] for ii in glider_active_dataset_ids]


    # After a list of active deployments has been made, 
    # compare the glider info
    # end date to the erddap metadata end date, and if there metadata end date
    # is later, there is new data, and the glider info should be updated
    glider_datasets_to_update = []
    datasets_to_update = []     
    olddate_cutoff = (datetime.datetime.now().replace(hour=0,minute=0,second=0,microsecond=0)
                      - datetime.timedelta(days=180))
    for ind in range(0,len(glider_active_inds)):

        glider_id = glider_active_ids[ind]

        glider_metadata = gliders_gen.load_erddap_glider_metadata(transect_id, 
                                                                  glider_active_dataset_ids[ind])
        if (datetime.datetime.strptime(glider_metadata['datetime_latest'],
                                       '%Y-%m-%dT%H:%M:%SZ') < olddate_cutoff):
            glider_datasets_to_update.append(glider_active_datasets[ind])
            datasets_to_update.append(glider_active_dataset_ids[ind])

    print('      # of "old" datasets to update as inactive:',len(datasets_to_update))
    if len(datasets_to_update) > 0:
        update_jsonflag = True
        update_inactive_gliders_jsons(transect_id, glider_id, 
                                      glider_obj, gliderplot_obj,
                                      glider_datasets_to_update,
                                      datasets_to_update)
        
        
        
            
        
    ##########################################
    # After all gliders have been checked and updated,
    # save the glider objects into the jsons
    if update_jsonflag:
        print('All gliders checked. Saving the results...')
        if not(os.path.exists(os.path.join(transect_basedir, transect_id, 'json_archive'))):
            try:
                foldername = os.path.join(transect_basedir, transect_id, 'json_archive')
                os.mkdir(foldername)
            except OSError:
                print ('Directory %s already exists. Accessing directory.' % foldername)
            else:
                print ('Successfully created the directory %s ' % foldername)   


        if os.path.exists(os.path.join(transect_basedir, transect_id, 'json_archive','glider_info.json')):
            print('Need to make an later archived copy')
        if os.path.exists(os.path.join(transect_basedir, transect_id, 'json_archive','glider_plottinginfo.json')):
            print('Need to make an later archived copy 2')
            
        src = os.path.join(transect_basedir, transect_id, 'glider_info.json')
        dst = os.path.join(transect_basedir, transect_id, 'json_archive','glider_info.json')
        gliders_gen.copyfile_func(src, dst)
        del src, dst
        
        src = os.path.join(transect_basedir, transect_id, 'glider_plottinginfo.json')
        dst = os.path.join(transect_basedir, transect_id, 'json_archive','glider_plottinginfo.json')
        gliders_gen.copyfile_func(src, dst)
        del src, dst
        gliders_gen.save_glider_info_all(transect_id, glider_obj, gliderplot_obj)
    else:
        print('All gliders checked. No changes found. Glider jsons not changed.')
    
    
    #################################################
    # Ensure that all deployments are in the right order for the transect
    #check_glider_deployment_order(transect_id)
    
    return successFlag


# In[ ]:


def main():
    
    try:
        opts, args = getopt.getopt(sys.argv[1:], "hu:t:", ["help", "transect="])
    except Exception as inst:
        # print help information and exit:
        print('Error in getting options: ' + str(inst)) # will print something like "option -a not recognized"
        sys.exit(2)
        
    # step through command-line options and their arguments
    transectFlag = False
    
    
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
            transectId = a
        else:
            assert False, "unhandled option"
    
       
    # If the buoy designation was given, ensure that the buoy designation is in uppercase,
    # and that it matches one of the valid buoy designations
    valid_transects = ['washelf', 'LaPush', 'OSU_Trinidad1', 
                       'ooi_ns', 'ooi_nd', 'ooi_ghs', 'ooi_ghd', 'ooi_coosbay']
    check_transects = ['washelf', 'lapush', 'osu_trinidad1', 
                       'ooi_ns', 'ooi_nd', 'ooi_ghs', 'ooi_ghd', 'ooi_coosbay']
    if transectFlag:
        transectId = transectId.lower()
        if transectId in check_transects:
            transect_ind = np.where([ii == transectId for ii in check_transects])[0][0]
            transectId = valid_transects[transect_ind]
            print('Check deployments for transect "' + transectId + '"')
        else:
            print('Invalid transect ID. Check name, and retry.')
            sys.exit(2)
    else:
        print('No transect ID given. Try again with options: "-t *transect ID*"')
        sys.exit(2)
        
        
    
    ###################################################################
    ## Process the hex files for a given buoy designation
    try:
        successFlag = check_transect_deployments(transectId)
    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        print('Error in processing:')
        print(e)
        print('Error occurs on line ' + str(exc_tb.tb_lineno))

        error_msg = "An error occured while updating deployments for transect " + transectId + ".\n\n" + "Error message:\n" + str(e)
        error_sbj = "NVS Gliders Checking Deployment Error for Transect " + transectId
        __, infodir, __ = gliders_gen.get_pathdirs()
        with open(os.path.join(infodir, 'user_info.json'), 'r') as infofile:
            user_info = json.load(infofile)
        gliders_gen.send_emailreport(msgtxt=error_msg, subj=error_sbj,
                                     fromaddr=user_info['email_fromaddr'], toaddr="setht1@uw.edu",
                                     login=user_info['email_login'],
                                     passwd=user_info['email_passwd'])
        
        sys.exit(2)

    if not(successFlag):
        error_msg = "An error occured while updating deployments for transect " + transectName + ".\n\nCheck the processing log for details."
        error_sbj = "NVS Gliders Checking Deployment Error for Transect " + transectName
        __, infodir, __ = gliders_gen.get_pathdirs()
        with open(os.path.join(infodir, 'user_info.json'), 'r') as infofile:
            user_info = json.load(infofile)
        gliders_gen.send_emailreport(msgtxt=error_msg, subj=error_sbj,
                                     fromaddr=user_info['email_fromaddr'], toaddr="setht1@uw.edu",
                                     login=user_info['email_login'],
                                     passwd=user_info['email_passwd'])
        sys.exit(2)

        
    sys.exit(0)


# In[ ]:


if __name__ == "__main__":
    main()

