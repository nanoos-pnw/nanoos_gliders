##########

#   Each of these jsons is created using a combination of manually entered info and ERDDAP-retrieved info. 
#   There is no new data pulling or parameter setting in this file. This code only reformats information so that Troy's code can find what it needs to plot the glider data.

#   GliderJson - class that creates json dictionary for each glider line
#   DeploymentJson - class that creates json dictionary for each deployment of a given glider line
#   SectionJson - class that creates json dictionary for each section of a given deployment

##########

# class GliderJson:
    
#    def __init__(self,transect_id,transect_label,active,provider_name,provider_url,provider_contact_name,provider_contact_email, \
#		deployment_info_url_template, section_info_url_template, section_plots_url_template):
#        self.transect = {'id':transect_id, 'label':transect_label}
#        self.active = active
#        self.provider = {'name':provider_name, 'url':provider_url, 'contact_name':provider_contact_name, \
#			'contact_email':provider_contact_email}
#        self.deployment_info_url_template = deployment_info_url_template
#        self.section_info_url_template = section_info_url_template
#        self.section_plots_url_template = section_plots_url_template
#        self.deployments = []
        
#    def add_deployment(self, deployment_id, deployment_label, deployment_start_time, deployment_end_time):
#        self.deployments.append({'id':deployment_id, 'label':deployment_label, \
#            'start_time': deployment_start_time, 'end_time': deployment_end_time})
    
#    def update_deployment(self, deployment_id, deployment_end_time):
#        for deps in range(len(self.deployments)):
#            if self.deployments[deps]['id']==deployment_id:
#                self.deployments[deps]['end_time']=deployment_end_time

##########

class GliderJson:
    
    def __init__(self, transect_id=None, transect_label=None, active=None, display_map=True, provider_name=None, provider_url=None,
                 provider_contact_name=None, provider_contact_email=None, deployment_info_url_template=None,
                 section_info_url_template=None, section_plots_url_template=None, json_obj=None):
        if json_obj is None:
            self.transect = {'id':transect_id, 'label':transect_label}
            self.active = active
            self.display_map = display_map
            self.provider = {'name':provider_name, 'url':provider_url, 'contact_name':provider_contact_name, \
                'contact_email':provider_contact_email}
            self.deployment_info_url_template = deployment_info_url_template
            self.section_info_url_template = section_info_url_template
            self.section_plots_url_template = section_plots_url_template
            self.deployments = []
        else:
            self.transect = json_obj['transect']
            self.active = json_obj['active']
            self.display_map = json_obj['display_map']
            self.provider = json_obj['provider']
            self.deployment_info_url_template = json_obj['deployment_info_url_template']
            self.section_info_url_template = json_obj['section_info_url_template']
            self.section_plots_url_template = json_obj['section_plots_url_template']
            self.deployments = json_obj['deployments']
        
    def add_deployment(self, glider_id, dataset_id, deployment_id, deployment_label, 
                       deployment_active, plotting_active,
                       deployment_start_time, deployment_end_time):
        
        for deps in range(len(self.deployments)):
            if self.deployments[deps]['id']==deployment_id:
                print('Deployment already exists. Do not add duplicate deployment.')
                return
        self.deployments.append({'glider_id': glider_id, 'dataset_id': dataset_id,
                                 'deployment_active': deployment_active,
                                 'plotting_active': plotting_active,
                                 'id':deployment_id, 'label':deployment_label, 
                                 'start_time': deployment_start_time, 'end_time': deployment_end_time})
    
    def update_deployment(self, deployment_id, 
                          deployment_start_time, deployment_end_time, 
                          deployment_active, plotting_active,
                          newdeployment_id=None, newdeployment_label=None, dataset_id=None):
        """
        This class function will update the parameters of a specific deployment in the glider_info json
        """
        for deps in range(len(self.deployments)):
            if self.deployments[deps]['id']==deployment_id:
                self.deployments[deps]['start_time']=deployment_start_time
                self.deployments[deps]['end_time']=deployment_end_time
                self.deployments[deps]['deployment_active']=deployment_active
                self.deployments[deps]['plotting_active']=plotting_active
                if newdeployment_id is not None:
                    self.deployments[deps]['id']=newdeployment_id
                if newdeployment_label is not None:
                    self.deployments[deps]['label']=newdeployment_label
                if dataset_id is not None:
                    self.deployments[deps]['dataset_id']=dataset_id

    #@property
    #def deployments(self):
    #    return self.json['deployments']
        
    #@deployments.setter
    #def deployments(self, deployments):
    #    self.json['deployments'] = deployments
    
    
class Glider_Plotting_Json:
    
    def __init__(self, 
                 transect_id=None, transect_label=None, active=None, 
                 json_obj=None):
        if json_obj is None:
            self.transect = {'id':transect_id, 'label':transect_label}
            self.active = active
            self.deployments = []
        else:
            self.transect = json_obj['transect']
            self.active = json_obj['active']
            self.deployments = json_obj['deployments']
            
        
    def add_deployment(self, deployment_id, deployment_label, 
                       deployment_start_time, deployment_end_time,
                       plot_params=None, verified=False):
        
        if plot_params is None:
            plot_params = {}
            plot_params['dac_timelocdepth']=['precise_time','time','precise_lat','latitude','precise_lon','longitude','profile_id','depth']
            plot_params['dac_variables']=['temperature','salinity','density','dissolved_oxygen','chlorophyll','CDOM','backscatter']
            plot_params['variables_label']=['Temperature','Salinity','Density','Dissolved Oxygen','Chlorophyll','CDOM','Backscatter']
            plot_params['variables_id']=['temp','sal','dens','do','chl','cdom','bs']
            plot_params['variables_units']=['\u00b0C','PSU','kg/m3','mg/l','ug/l','ppb','m-1']
            plot_params['variables_limits']=[[6.0,12.0],[29.0,34.0],[1023.0,1027.0],[0.0,11.0],[0.0,30.0],[0.0,3.0],[0.0,0.02]]
            plot_params['latlimmap']=[46.6,47.8]
            plot_params['lonlimmap']=[-125.2,-124.0]
            plot_params['lonlimtransect']=[-125.2,-124.0]
            plot_params['depthlimtransect']=[0,200]
            plot_params['tolerance']=0.13
            plot_params['exppts']=4
            plot_params['num_interp_pts']=250
        
        new_deployment = {}
        for param in plot_params:
            new_deployment[param] = plot_params[param]
        new_deployment['id'] = deployment_id
        new_deployment['label'] = deployment_label
        new_deployment['start_time'] = deployment_start_time
        new_deployment['end_time'] = deployment_end_time        
        new_deployment['verified'] = verified
        
        for deps in range(len(self.deployments)):
            if self.deployments[deps]['id']==deployment_id:
                print('Deployment already exists. Do not add duplicate deployment.')
                return
            
        self.deployments.append(new_deployment)    
    
    def update_deployment(self, deployment_id, 
                          deployment_start_time, deployment_end_time, 
                          newdeployment_id=None, newdeployment_label=None, 
                          verified=False):
        for deps in range(len(self.deployments)):
            if self.deployments[deps]['id']==deployment_id:
                self.deployments[deps]['start_time']=deployment_start_time
                self.deployments[deps]['end_time']=deployment_end_time
                self.deployments[deps]['verified']=verified
                if newdeployment_id is not None:
                    self.deployments[deps]['id']=newdeployment_id
                if newdeployment_label is not None:
                    self.deployments[deps]['label']=newdeployment_label
        



########        

class DeploymentJson:
	
    def __init__(self,deployment_id,deployment_label,data_url,glider_id,glider_label,glider_type, \
        datetime_start,datetime_end,deployment_route,variable_id,variable_label,variable_units,\
            section_id,section_label,section_datetime_start,section_datetime_end,\
                section_orientations, data_label):
        
        self.id = deployment_id
        self.label = deployment_label
        self.data = data_url
        self.glider = {'id':glider_id, 'label':glider_label, 'type':glider_type}
        self.datetime = {'start':datetime_start, 'end':datetime_end}
        
        self.route = []
        for [lat,lon] in deployment_route:
            self.route.append({'lat':lat,'lon':lon})
        
        self.variables =[]
        for i in range(len(variable_id)):
            self.variables.append({'id':variable_id[i], 'label':variable_label[i], 'units':variable_units[i]})
        
        self.sections = []
        for i in range(len(section_datetime_start)):
            self.sections.append({'id':section_id[i], 'label':section_label[i],
            'datetime':{'start':section_datetime_start[i], 'end':section_datetime_end[i]},
            'glider_id':glider_id, 'deployment_id':deployment_id,
            'section_orientation':section_orientations[i],
            'data':[{'label':data_label,'url':data_url}]})
        
##########

class SectionJson: 
    
    def __init__(self,deployment_id,glider_id,section_id,section_datetime_start,section_datetime_end,full_section_route):
        
        self.deployment_id = deployment_id
        self.glider_id= glider_id
        self.section_id = section_id
        self.datetime_start = section_datetime_start
        self.datetime_end = section_datetime_end
        self.route = []
        for [lon,lat] in full_section_route:
            self.route.append([lon,lat])
    