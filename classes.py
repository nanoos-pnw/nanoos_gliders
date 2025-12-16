##########

# I tried my hand at defining and using classes to try to make things more efficient. 
# Not convinced I did everything right or more efficiently, but I'll explain...

# class Glider sets high level information for a given "line" (e.g., La Push, WA Shelf, Trinidad Head) 
# Glider class include label (machine-readable folder name associated with this line), active (True/False), and datasets (defined below)
# I did define some of the parameters of datasets (transect_id and title) with the Glider class beacuse these parameters do not change between deployments for that line
# dataset.transect_id = machine-readable folder name for each line
# dataset.title = human-readable name displayed on NVS for each line

##########

class Glider:
   
    def __init__(self, label, active, datasets):
        self.label = label
        self.active = active
        self.datasets = datasets


class WAShelfGlider(Glider):
      
    def __init__(self, datasets):
        super().__init__('washelf', True, datasets)
        
        for dataset in datasets:
            dataset.transect_id = 'washelf'
            dataset.title = 'WA Shelf Glider'


class TrinidadGlider(Glider):

    def __init__(self, datasets):
        super().__init__('OSU_Trinidad1', True, datasets)
        
        for dataset in datasets:
            dataset.transect_id = 'OSU_Trinidad1'
            dataset.title = 'Trinidad Head Glider'

class LaPushGlider(Glider):
    
    def __init__(self, datasets):
        super().__init__('LaPush', True, datasets)
        
        for dataset in datasets:
            dataset.transect_id = 'LaPush'
            dataset.title = 'La Push Glider'

##########

# Note regarding OOI, below:
# I'd suggest that you combine all OOI missions into one class (OOI), rather than trying to split them up (e.g., OOI Grays Harbor Shallow, OOI Newport Deep, etc.)
# There are more OOI missions than just the two classes listed here. I was just starting to try to tackle OOI when I stalled out.

##########

class OOIGraysHarborShallowGlider(Glider):
   
    def __init__(self, datasets):
        super().__init__('ooi_ghs', False, datasets)
        
        for dataset in datasets:
            dataset.transect_id = 'ooi_ghs'
            dataset.title = 'OOI Grays Habor Shallow Glider'


class OOINewportDeepGlider(Glider):
    
    def __init__(self, datasets):
        super().__init__('ooi_nd', False, datasets)
        
        for dataset in datasets:
            dataset.transect_id = 'ooi_nd'
            dataset.title = 'OOI Newport Deep Glider' 

##########

# class Dataset defines all the parameters that you need to pull and plot a deployment
# All of the parameters within a dataset are added in some way to the json files (using create_jsons.py) that Troy's code reads for display on NVS

# readme_template = Dataset(
#            dataset_id= Name of dataset in ERDDAP ('osu551-20230715T1729'), 
#            glider_id= Prefix of the dataset_id that stays the same for all deployments of a particular glider system ('osu_551'), 
#            NOTE: You could use a list of all the glider_ids that serve a glider line to search for 
#                  new deployments in the ERDDAP with that glider_id prefix on their dataset_id           
#            deployment_id= Machine-readable deployment name that describes the start and end year and month ('YYYY_Month_YYYY_Month'), 
#            deployment_label= Human-readable deployment name to be displayed on NVS ('YYYY Month - YYYY Month') 
#            NOTE: If deployment within a single year, drop the second YYYY ('YYYY Month - Month')
#            NOTE: If deployment ongoing, use 'YYYY Month - Ongoing'
#            section_id= Machine-readable list of folder names that will be used to id each 'section' (transect between turning points),
#            NOTE: I chose to use letters instead of numbers. Feel free to change that as you see fit.
#            NOTE: I manually list out how many (plus extra) that a deployment will need. 
#                  There has got to be an automated way to generate however many section folders as a 
#                  glider requires and to add them as it goes.  
#            section_label= Shorthand label matching the section_id... this gets added to a json file, 
#                           but I can't remember if it gets used for anything or if it is superfluous now, 
#            datetime_start= Start time for deployment format '0000-00-00T00:00:00Z', 
#            datetime_end= End time for deployment format '0000-00-00T00:00:00Z or can set to None if deployment ongoing, 
#            NOTE: If you use glider_id to search for and automatically find new deployments, the start time could be read from the ERDDAP
#            NOTE: Once the deployment ends (write code to calculate how many days since new data added to ERDDAP), 
#                  you could pull the end time from the ERDDAP
#            deployment_active= True/False I have been setting this parameter manually, 
#                               but you might find a way to do it automatically... 
#                               needed a way to make sure code doesn't re-run completed deployments, 
#            dac_timelocdepth= List of names of time, location, and depth parameters that I want to read from the DAC/ERDDAP, 
#            dac_variables= List of names of the variables that I want to read from the DAC/ERDDAP - 
#                           these must be exact matches to the ERDDAP syntax, 
#            variables_label= List of human-readable variable names for display on NVS,
#            variables_id= List of machine-readable variable names for processing and plotting code,
#            variables_units= List of units to be displayed on the plots for each variable,
#            variables_limits= List of pairs of colorbar axis limits for each variable,
#            NOTE: Order of variables/specfications listed in dac_variables, variables_label, variables_id, variables_units,
#                  variables_limits must be consistent because code loops through these to plot 
#                  (temperature data must all be in the same index location in each list)... 
#                  I'm sure there's a smarter way to do this with a dictionary, rather than a set of lists.
#            latlimmap= Min and max latitude for the map, 
#            lonlimmap= Min and max longitude for the map,
#            lonlimtransect= Min and max longitude for the plot, 
#            depthlimtransect= Min and max depth for the plot, 
#            tolerance= Parameter [value between 0 and 1, usually between 0.1 and 0.5] used in get_min_max.py code which 
#                       identified when the glider turned and started on a new section/transect, 
#            exppts= Expected number of turning points, 
#            num_interp_pts= Number of points to interpolate to for the bathymtry transect... 
#                            you can play around with this- plenty of times the bathy interpolation looks a bit wonky, 
#            transect_id= Set to None because, while we need it for each dataset, it stays the same, 
#                         so we set it as part of the Glider Class above, 
#            title= Set to None because, while we need it for each dataset, it stays the same, 
#                   so we set it as part of the Glider Class above
#        )

##########

class Dataset:

    def __init__(self, dataset_id, glider_id, deployment_id, deployment_label,
        section_id, section_label, datetime_start, datetime_end, deployment_active, 
        dac_timelocdepth, dac_variables, variables_label, variables_id, variables_units, variables_limits,
        latlimmap, lonlimmap, lonlimtransect, depthlimtransect,
        tolerance, exppts,num_interp_pts, transect_id=None, title=None):
        
        self.dataset_id = dataset_id
        self.transect_id = transect_id
        self.glider_id = glider_id
        self.deployment_id = deployment_id
        self.deployment_label = deployment_label 
        self.section_id = section_id
        self.section_label = section_label
        self.datetime_start = datetime_start
        self.datetime_end = datetime_end
        self.deployment_active = deployment_active
        self.dac_timelocdepth = dac_timelocdepth
        self.dac_vars = dac_variables 
        self.vars_label=variables_label
        self.vars_id=variables_id
        self.vars_units=variables_units
        self.vars_limits=variables_limits
        self.latlimmap = latlimmap
        self.lonlimmap = lonlimmap
        self.lonlimtransect = lonlimtransect
        self.depthlimtransect = depthlimtransect
        self.title = title
        self.x_label = 'Longitude'
        self.y_label = 'Depth (m)'
        self.fontSize = 14
        self.mycmap = 'rainbow'
        self.tolerance =  tolerance
        self.exppts = exppts
        self.num_interp_pts = num_interp_pts
