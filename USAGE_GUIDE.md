# Usage Guide

This guide provides detailed examples and workflows for using the `nanoos_gliders` package.

## Table of Contents

1. [Basic Workflow](#basic-workflow)
2. [Processing Active Deployments](#processing-active-deployments)
3. [Adding New Deployments](#adding-new-deployments)
4. [Checking Deployment Status](#checking-deployment-status)
5. [Custom Plotting](#custom-plotting)
6. [JSON Metadata Management](#json-metadata-management)
7. [Advanced Usage](#advanced-usage)

## Basic Workflow

### Complete Processing Pipeline

The standard workflow processes all active glider deployments:

```python
# Run the main processing script
python gliders_main.py -t washelf --all
```

This script:
1. Loads deployment parameters from initialization file
2. Retrieves data from ERDDAP for each active deployment
3. Identifies transect sections using turning point detection
4. Generates scientific plots for all variables
5. Creates JSON metadata files
6. Saves outputs to configured directory

### Wrapper Script (gliders_main.py)

Use the wrapper to run checks and plots from a single command. It passes
arguments through to `gliders_check_transect_deployments.py` and
`gliders_make_plots.py`, and captures a combined log.

```bash
python gliders_main.py -t washelf --all
```

Common options:
- `--check`: only run deployment checks
- `--plots`: only run plotting
- `--all`: run checks, then plots
- `-d`: optional deployment name for plotting
- `--log-file`: write logs to a specific file
- `--log-dir`: directory for timestamped logs (default: logs)

If no flags are provided, the wrapper runs both checks and plots.

Examples:

```bash
python gliders_main.py -t washelf --check
python gliders_main.py -t washelf --plots
python gliders_main.py -t washelf --plots -d 2024_Jan_Ongoing
python gliders_main.py -t washelf --all --log-dir logs
```

### Manual Processing Steps

For more control, you can execute steps individually:

```python
from init_params_NANOOS import init_params
from erddapy import ERDDAP
import gliders_general_functions as gliders_gen
import gliders_make_plots as gliders_plot

# 1. Initialize parameters
gliderOps, outputpath = init_params()

# 2. Select specific glider and deployment
glider = gliderOps[0]  # First glider (e.g., WA Shelf)
dataset = glider.datasets[0]  # First deployment

# 3. Connect to ERDDAP
e = ERDDAP(server='NGDAC')
e.protocol = 'tabledap'
e.response = 'csv'
e.dataset_id = dataset.dataset_id

# 4. Set constraints and retrieve data
e.constraints = {
    'precise_time>=': dataset.datetime_start,
    'precise_time<=': dataset.datetime_end
}
e.variables = dataset.dac_timelocdepth + dataset.dac_vars
df = e.to_pandas()

# 5. Process and plot
# (See plotting section below)
```

## Processing Active Deployments

### Setting Deployment Status

Control which deployments are processed:

```python
from classes import Dataset, WAShelfGlider

# Create dataset with active flag
dataset = Dataset(
    dataset_id='washelf-20230101T0000',
    glider_id='washelf',
    deployment_id='2023_Jan_2023_Mar',
    deployment_label='2023 Jan - Mar',
    # ... other parameters ...
    deployment_active=True,  # Set to False to skip processing
)
```

### Processing Multiple Glider Lines

```python
from init_params_NANOOS import init_params

gliderOps, outputpath = init_params()

# Process only specific glider lines
for glider in gliderOps:
    if glider.label in ['washelf', 'LaPush']:
        if glider.active:
            print(f"Processing {glider.label}")
            # Process glider datasets
            for dataset in glider.datasets:
                if dataset.deployment_active:
                    # Process this deployment
                    pass
```

### Filtering by Date Range

Process only recent data:

```python
from datetime import datetime, timedelta

# Process last 30 days
end_date = datetime.now()
start_date = end_date - timedelta(days=30)

dataset.datetime_start = start_date.strftime('%Y-%m-%dT%H:%M:%SZ')
dataset.datetime_end = end_date.strftime('%Y-%m-%dT%H:%M:%SZ')
```

## Adding New Deployments

### Method 1: Using the Add Transect Script

```python
from gliders_add_transect_deployments import add_new_deployment

# Add a new deployment to existing transect
add_new_deployment(
    transect_id='washelf',
    glider_id='washelf_sg',
    dataset_id='washelf-20240101T0000',
    deployment_id='2024_Jan_Ongoing',
    deployment_label='2024 Jan - Ongoing',
    start_time='2024-01-01T00:00:00Z',
    end_time=None,  # Ongoing deployment
    deployment_active=True,
    plotting_active=True
)
```

### Method 2: Manual Configuration

Edit your initialization file to add new deployment:

```python
# In init_params_NANOOS.py

new_dataset = Dataset(
    dataset_id='washelf-20240101T0000',
    glider_id='washelf_sg',
    deployment_id='2024_Jan_Ongoing',
    deployment_label='2024 Jan - Ongoing',
    section_id=['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h'],
    section_label=['Section A', 'Section B', 'Section C', 'Section D', 
                   'Section E', 'Section F', 'Section G', 'Section H'],
    datetime_start='2024-01-01T00:00:00Z',
    datetime_end=None,  # Ongoing
    deployment_active=True,
    dac_timelocdepth=['precise_time', 'precise_lat', 'precise_lon', 'depth'],
    dac_variables=['temperature', 'salinity', 'density', 'chlorophyll_a', 'oxygen_concentration'],
    variables_label=['Temperature', 'Salinity', 'Density', 'Chlorophyll-a', 'Dissolved Oxygen'],
    variables_id=['temp', 'salt', 'dens', 'chla', 'oxygen'],
    variables_units=['°C', 'PSU', 'kg/m³', 'μg/L', 'mg/L'],
    variables_limits=[[4, 16], [31, 34], [1023, 1027], [0, 15], [0, 10]],
    latlimmap=[46.0, 48.5],
    lonlimmap=[-125.5, -124.0],
    lonlimtransect=[-125.5, -124.0],
    depthlimtransect=[0, 250],
    tolerance=0.15,
    exppts=16,
    num_interp_pts=150
)

# Add to glider
washelf_datasets.append(new_dataset)
```

### Determining Dataset Parameters

**Finding Dataset IDs on ERDDAP:**

```python
from erddapy import ERDDAP
import pandas as pd

e = ERDDAP(server='NGDAC')
# Search for datasets containing 'washelf'
search_url = e.get_search_url(search_for='washelf', response='csv')
datasets = pd.read_csv(search_url)
print(datasets[['Dataset ID', 'Title']])
```

**Getting Variable Names:**

```python
# Get metadata for specific dataset
e.dataset_id = 'your-dataset-id'
info_url = e.get_info_url()
info = pd.read_csv(info_url)

# List available variables
variables = info[info['Row Type'] == 'variable']['Variable Name'].values
print(variables)
```

## Checking Deployment Status

### Check All Deployments

```python
from gliders_check_transect_deployments import check_all_deployments

# Check status of all configured deployments
status_report = check_all_deployments(
    transect_id='washelf',
    check_erddap=True,  # Verify data availability
    days_threshold=7    # Flag if no data for 7 days
)

for dep in status_report:
    print(f"{dep['deployment_id']}: {dep['status']}")
    print(f"  Last data: {dep['last_data_time']}")
    print(f"  Active: {dep['deployment_active']}")
```

### Monitor Specific Deployment

```python
from gliders_check_transect_deployments import extract_latest_deployment

glider_id = 'washelf_sg'
latest_info = extract_latest_deployment(
    glider_id=glider_id,
    glider_info=glider_json,
    gliderplot_info=plot_json
)

print(f"Latest deployment: {latest_info['deployment_id']}")
print(f"Data through: {latest_info['end_time']}")
```

## Custom Plotting

### Generate Specific Variable Plots

```python
import gliders_make_plots as gliders_plot
import matplotlib.pyplot as plt

# Create temperature plot for specific section
gliders_plot.make_section_plot(
    data=section_data,
    variable='temperature',
    variable_label='Temperature',
    variable_units='°C',
    vmin=5,
    vmax=15,
    lon_limits=[-125.5, -124.0],
    depth_limits=[0, 200],
    colormap='rainbow',
    output_file='temp_section_a.png'
)
```

### Custom Oxygen Plot with Hypoxic Threshold

```python
# Create oxygen colormap highlighting hypoxic conditions
colormap = gliders_plot.make_oxy_colormap(vmin=0, vmax=10)

gliders_plot.make_section_plot(
    data=section_data,
    variable='oxygen_concentration',
    variable_label='Dissolved Oxygen',
    variable_units='mg/L',
    vmin=0,
    vmax=10,
    lon_limits=[-125.5, -124.0],
    depth_limits=[0, 200],
    colormap=colormap,
    output_file='oxygen_section_a.png'
)
```

### Create Map View

```python
# Plot glider track on map
gliders_plot.make_map_plot(
    latitude=data['latitude'],
    longitude=data['longitude'],
    lat_limits=[46.0, 48.5],
    lon_limits=[-125.5, -124.0],
    marker_color=data['temperature'],
    colormap='rainbow',
    output_file='glider_track_map.png'
)
```

### Custom Colormap

```python
import matplotlib.pyplot as plt
import numpy as np

# Load custom colormap from JSON
import json
with open('partial_rainbow.json', 'r') as f:
    cmap_data = json.load(f)

# Create colormap from specification
from matplotlib.colors import LinearSegmentedColormap
custom_cmap = LinearSegmentedColormap.from_list('custom', cmap_data)

# Use in plotting
plt.contourf(x, y, z, cmap=custom_cmap)
```

## JSON Metadata Management

### Create Glider Info JSON

```python
from create_jsons import GliderJson

# Initialize glider metadata
glider_json = GliderJson(
    transect_id='washelf',
    transect_label='WA Shelf Glider',
    active=True,
    display_map=True,
    provider_name='University of Washington',
    provider_url='https://www.ocean.washington.edu',
    provider_contact_name='Contact Name',
    provider_contact_email='contact@email.com',
    deployment_info_url_template='https://data.nanoos.org/wd/gliders/{transect_id}/{deployment_id}/deployment_info.json',
    section_info_url_template='https://data.nanoos.org/wd/gliders/{transect_id}/{deployment_id}/{section_id}/section_info.json',
    section_plots_url_template='https://data.nanoos.org/wd/gliders/{transect_id}/{deployment_id}/{section_id}/scientific/{variable_id}.png',
    section_data_url_template='https://data.nanoos.org/wd/gliders/{transect_id}/{deployment_id}/{section_id}/data.nc'
)

# Add deployment
glider_json.add_deployment(
    glider_id='washelf_sg',
    dataset_id='washelf-20240101T0000',
    deployment_id='2024_Jan_Ongoing',
    deployment_label='2024 Jan - Ongoing',
    deployment_active=True,
    plotting_active=True,
    deployment_start_time='2024-01-01T00:00:00Z',
    deployment_end_time=None
)

# Save to file
import json
with open('glider_info.json', 'w') as f:
    json.dump(glider_json.__dict__, f, indent=2)
```

### Update Existing Deployment

```python
# Update deployment end time and status
glider_json.update_deployment(
    deployment_id='2024_Jan_Ongoing',
    deployment_start_time='2024-01-01T00:00:00Z',
    deployment_end_time='2024-03-31T23:59:59Z',
    deployment_active=False,  # Mark as completed
    plotting_active=True,
    newdeployment_id='2024_Jan_2024_Mar',
    newdeployment_label='2024 Jan - Mar'
)
```

### Create Plotting JSON

```python
from create_jsons import Glider_Plotting_Json

plot_json = Glider_Plotting_Json(
    transect_id='washelf',
    deployment_id='2024_Jan_2024_Mar'
)

# Add section information
plot_json.add_section(
    section_id='a',
    section_label='Section A',
    start_time='2024-01-01T00:00:00Z',
    end_time='2024-01-05T12:00:00Z',
    variables=['temp', 'salt', 'dens', 'chla', 'oxygen']
)

# Save
plot_json.save('glider_plotting_info.json')
```

## Advanced Usage

### Section Detection Tuning

The section detection algorithm identifies turning points:

```python
from get_min_max import get_min_max

# Tune tolerance for your glider path
# Lower tolerance = more sections detected
# Higher tolerance = fewer sections detected

sections = get_min_max(
    inarr=longitude_data,
    Tolerance=0.15,  # Adjust based on glider behavior
    expPts=16        # Expected number of turning points
)

print(f"Found {len(sections)} sections")
```

**Tolerance Guidelines:**
- **0.1-0.15**: High-frequency sampling, short transects
- **0.15-0.25**: Standard transects
- **0.25-0.40**: Long transects, coarse turning points

### Custom Data Processing

```python
import gliders_general_functions as gliders_gen
import numpy as np
import pandas as pd

# Calculate along-track distance
def calculate_distance(lat, lon):
    """Calculate cumulative distance along glider track"""
    dist = gliders_gen.great_circle_calc(lat, lon)
    return np.cumsum(np.concatenate([[0], dist]))

# Convert datetime to ordinal with seconds
def process_time(df):
    """Process time column to ordinal with second resolution"""
    df['time_ordinal'] = df['time'].apply(
        gliders_gen.datetime_toordinal_withseconds
    )
    return df

# Apply to data
data['distance_km'] = calculate_distance(
    data['latitude'].values,
    data['longitude'].values
) / 1000

data = process_time(data)
```

### Batch Processing

Process multiple deployments in batch:

```python
import os
from init_params_NANOOS import init_params

gliderOps, outputpath = init_params()

# Create processing log
log_file = os.path.join(outputpath, 'processing_log.txt')

with open(log_file, 'w') as log:
    for glider in gliderOps:
        if not glider.active:
            continue
            
        log.write(f"\n{'='*50}\n")
        log.write(f"Processing glider: {glider.label}\n")
        log.write(f"{'='*50}\n")
        
        for dataset in glider.datasets:
            if not dataset.deployment_active:
                log.write(f"  Skipping {dataset.deployment_id} (inactive)\n")
                continue
                
            try:
                log.write(f"  Processing {dataset.deployment_id}...\n")
                # Process deployment
                # (main processing code here)
                log.write(f"  Success: {dataset.deployment_id}\n")
            except Exception as e:
                log.write(f"  ERROR: {dataset.deployment_id} - {str(e)}\n")

print(f"Processing complete. See log: {log_file}")
```

### Parallel Processing

Process multiple sections in parallel:

```python
from multiprocessing import Pool
import gliders_make_plots as gliders_plot

def process_section(section_data):
    """Process a single section"""
    section_id, data, params = section_data
    gliders_plot.make_all_plots(
        data=data,
        section_id=section_id,
        **params
    )
    return section_id

# Prepare section data
section_tasks = [
    (section_id, section_data, plot_params)
    for section_id, section_data in sections.items()
]

# Process in parallel
with Pool(processes=4) as pool:
    results = pool.map(process_section, section_tasks)

print(f"Processed {len(results)} sections")
```

### Error Handling

Robust error handling for production:

```python
import logging
from datetime import datetime

# Setup logging
logging.basicConfig(
    filename=f'glider_processing_{datetime.now():%Y%m%d}.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def safe_process_deployment(dataset):
    """Process deployment with comprehensive error handling"""
    try:
        logging.info(f"Starting {dataset.deployment_id}")
        
        # Data retrieval
        try:
            data = retrieve_erddap_data(dataset)
            logging.info(f"Retrieved {len(data)} records")
        except Exception as e:
            logging.error(f"Data retrieval failed: {e}")
            return None
        
        # Section detection
        try:
            sections = detect_sections(data, dataset.tolerance, dataset.exppts)
            logging.info(f"Detected {len(sections)} sections")
        except Exception as e:
            logging.error(f"Section detection failed: {e}")
            return None
        
        # Plotting
        try:
            for section_id, section_data in sections.items():
                make_plots(section_data, section_id, dataset)
            logging.info("Plotting complete")
        except Exception as e:
            logging.error(f"Plotting failed: {e}")
            return None
        
        logging.info(f"Successfully completed {dataset.deployment_id}")
        return True
        
    except Exception as e:
        logging.error(f"Unexpected error in {dataset.deployment_id}: {e}")
        return None
```

## Tips and Best Practices

### Performance Optimization

1. **Limit data retrieval**: Use tight time constraints
2. **Cache ERDDAP responses**: Save raw data locally
3. **Adjust interpolation points**: Balance quality vs. speed
4. **Use appropriate plot DPI**: 150 DPI sufficient for web

### Data Quality

1. **Check data availability** before processing
2. **Validate variable names** against ERDDAP metadata
3. **Review section detection** results manually first time
4. **Monitor data latency** from glider operators

### Workflow Automation

1. **Schedule processing**: Use cron (Linux) or Task Scheduler (Windows)
2. **Monitor logs**: Set up alerts for failures
3. **Version control**: Track configuration changes
4. **Backup outputs**: Archive processed data regularly

### Troubleshooting

**No sections detected:**
- Adjust `tolerance` parameter
- Check `exppts` matches expected transects
- Verify longitude data quality

**ERDDAP timeout:**
- Reduce time range
- Check server status
- Implement retry logic

**Memory issues:**
- Process sections separately
- Reduce `num_interp_pts`
- Clear memory between deployments

## Next Steps

- Review [API_REFERENCE.md](API_REFERENCE.md) for detailed function documentation
- Explore example scripts in package
- Customize for your specific glider lines
- Set up automated processing pipeline

## Support

For usage questions:
- Check error logs
- Review ERDDAP metadata
- Consult package README
- Contact package maintainers
