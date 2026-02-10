# API Reference

Complete API documentation for the `nanoos_gliders` package.

## Table of Contents

1. [Classes](#classes)
   - [Glider Classes](#glider-classes)
   - [Dataset Class](#dataset-class)
   - [JSON Classes](#json-classes)
2. [Main Modules](#main-modules)
   - [glider_main](#glider_main)
   - [gliders_general_functions](#gliders_general_functions)
   - [gliders_make_plots](#gliders_make_plots)
   - [create_jsons](#create_jsons)
3. [Utility Functions](#utility-functions)
4. [Configuration](#configuration)

---

## Classes

### Glider Classes

Base class and specific implementations for different glider transect lines.

#### `Glider`

Base class for glider transect lines.

```python
class Glider:
    def __init__(self, label, active, datasets)
```

**Parameters:**
- `label` (str): Machine-readable identifier for the glider line (e.g., 'washelf')
- `active` (bool): Whether this glider line is currently being processed
- `datasets` (list of Dataset): List of deployment datasets for this line

**Attributes:**
- `label` (str): Glider line identifier
- `active` (bool): Processing status
- `datasets` (list): Associated deployment datasets

---

#### `WAShelfGlider`

Washington Shelf glider implementation.

```python
class WAShelfGlider(Glider):
    def __init__(self, datasets)
```

**Parameters:**
- `datasets` (list of Dataset): Deployment datasets

**Auto-configured attributes:**
- `label`: 'washelf'
- `active`: True
- For each dataset:
  - `transect_id`: 'washelf'
  - `title`: 'WA Shelf Glider'

**Example:**
```python
from classes import WAShelfGlider, Dataset

datasets = [dataset1, dataset2]  # List of Dataset objects
wa_glider = WAShelfGlider(datasets)
```

---

#### `TrinidadGlider`

Trinidad Head glider implementation.

```python
class TrinidadGlider(Glider):
    def __init__(self, datasets)
```

**Parameters:**
- `datasets` (list of Dataset): Deployment datasets

**Auto-configured attributes:**
- `label`: 'OSU_Trinidad1'
- `active`: True
- For each dataset:
  - `transect_id`: 'OSU_Trinidad1'
  - `title`: 'Trinidad Head Glider'

---

#### `LaPushGlider`

La Push glider implementation.

```python
class LaPushGlider(Glider):
    def __init__(self, datasets)
```

**Parameters:**
- `datasets` (list of Dataset): Deployment datasets

**Auto-configured attributes:**
- `label`: 'LaPush'
- `active`: True
- For each dataset:
  - `transect_id`: 'LaPush'
  - `title`: 'La Push Glider'

---

#### `OOIGraysHarborShallowGlider`

OOI Grays Harbor Shallow glider implementation.

```python
class OOIGraysHarborShallowGlider(Glider):
    def __init__(self, datasets)
```

**Parameters:**
- `datasets` (list of Dataset): Deployment datasets

**Auto-configured attributes:**
- `label`: 'ooi_ghs'
- `active`: False (default)
- For each dataset:
  - `transect_id`: 'ooi_ghs'
  - `title`: 'OOI Grays Harbor Shallow Glider'

---

#### `OOINewportDeepGlider`

OOI Newport Deep glider implementation.

```python
class OOINewportDeepGlider(Glider):
    def __init__(self, datasets)
```

**Parameters:**
- `datasets` (list of Dataset): Deployment datasets

**Auto-configured attributes:**
- `label`: 'ooi_nd'
- `active`: False (default)
- For each dataset:
  - `transect_id`: 'ooi_nd'
  - `title`: 'OOI Newport Deep Glider'

---

### Dataset Class

Encapsulates all parameters for a glider deployment.

#### `Dataset`

```python
class Dataset:
    def __init__(self, dataset_id, glider_id, deployment_id, deployment_label,
                 section_id, section_label, datetime_start, datetime_end, 
                 deployment_active, dac_timelocdepth, dac_variables, 
                 variables_label, variables_id, variables_units, variables_limits,
                 latlimmap, lonlimmap, lonlimtransect, depthlimtransect,
                 tolerance, exppts, num_interp_pts, 
                 transect_id=None, title=None)
```

**Parameters:**

**Identification:**
- `dataset_id` (str): ERDDAP dataset identifier (e.g., 'washelf-20230101T0000')
- `glider_id` (str): Glider system identifier (e.g., 'washelf_sg')
- `deployment_id` (str): Deployment identifier (e.g., '2023_Jan_2023_Mar')
- `deployment_label` (str): Human-readable deployment name (e.g., '2023 Jan - Mar')
- `transect_id` (str, optional): Transect line identifier (auto-set by Glider class)
- `title` (str, optional): Display title (auto-set by Glider class)

**Sections:**
- `section_id` (list of str): Machine-readable section identifiers (e.g., ['a', 'b', 'c'])
- `section_label` (list of str): Human-readable section labels (e.g., ['Section A', 'Section B'])

**Time Range:**
- `datetime_start` (str): Start time in ISO format 'YYYY-MM-DDTHH:MM:SSZ'
- `datetime_end` (str or None): End time in ISO format, or None for ongoing deployments

**Status:**
- `deployment_active` (bool): Whether to process this deployment

**Data Variables:**
- `dac_timelocdepth` (list of str): Time/location/depth variable names from ERDDAP
  - Example: `['precise_time', 'precise_lat', 'precise_lon', 'depth']`
- `dac_variables` (list of str): Scientific variable names from ERDDAP
  - Example: `['temperature', 'salinity', 'density', 'chlorophyll_a']`
- `variables_label` (list of str): Human-readable variable names
  - Example: `['Temperature', 'Salinity', 'Density', 'Chlorophyll-a']`
- `variables_id` (list of str): Internal variable identifiers
  - Example: `['temp', 'salt', 'dens', 'chla']`
- `variables_units` (list of str): Units for each variable
  - Example: `['°C', 'PSU', 'kg/m³', 'μg/L']`
- `variables_limits` (list of [min, max]): Colorbar limits for each variable
  - Example: `[[5, 15], [32, 34], [1024, 1027], [0, 10]]`

**Plotting Parameters:**
- `latlimmap` (list of float): [min_lat, max_lat] for map view
- `lonlimmap` (list of float): [min_lon, max_lon] for map view
- `lonlimtransect` (list of float): [min_lon, max_lon] for transect plots
- `depthlimtransect` (list of float): [min_depth, max_depth] for transect plots

**Section Detection:**
- `tolerance` (float): Threshold for detecting turning points (typically 0.1-0.5)
- `exppts` (int): Expected number of turning points
- `num_interp_pts` (int): Number of points for bathymetry interpolation

**Auto-set Attributes:**
- `x_label`: 'Longitude'
- `y_label`: 'Depth (m)'
- `fontSize`: 14
- `mycmap`: 'rainbow'

**Example:**
```python
from classes import Dataset

dataset = Dataset(
    dataset_id='washelf-20230101T0000',
    glider_id='washelf_sg',
    deployment_id='2023_Jan_2023_Mar',
    deployment_label='2023 Jan - Mar',
    section_id=['a', 'b', 'c', 'd', 'e'],
    section_label=['Section A', 'Section B', 'Section C', 'Section D', 'Section E'],
    datetime_start='2023-01-01T00:00:00Z',
    datetime_end='2023-03-31T23:59:59Z',
    deployment_active=True,
    dac_timelocdepth=['precise_time', 'precise_lat', 'precise_lon', 'depth'],
    dac_variables=['temperature', 'salinity', 'density', 'chlorophyll_a'],
    variables_label=['Temperature', 'Salinity', 'Density', 'Chlorophyll-a'],
    variables_id=['temp', 'salt', 'dens', 'chla'],
    variables_units=['°C', 'PSU', 'kg/m³', 'μg/L'],
    variables_limits=[[5, 15], [32, 34], [1024, 1027], [0, 10]],
    latlimmap=[46.0, 48.5],
    lonlimmap=[-125.5, -124.0],
    lonlimtransect=[-125.5, -124.0],
    depthlimtransect=[0, 250],
    tolerance=0.2,
    exppts=10,
    num_interp_pts=100
)
```

---

### JSON Classes

Classes for creating metadata JSON files.

#### `GliderJson`

Creates glider transect metadata JSON.

```python
class GliderJson:
    def __init__(self, transect_id=None, transect_label=None, active=None, 
                 display_map=True, provider_name=None, provider_url=None,
                 provider_contact_name=None, provider_contact_email=None, 
                 deployment_info_url_template=None,
                 section_info_url_template=None, 
                 section_plots_url_template=None, 
                 section_data_url_template=None, 
                 json_obj=None)
```

**Parameters:**
- `transect_id` (str): Transect identifier
- `transect_label` (str): Human-readable transect name
- `active` (bool): Whether transect is active
- `display_map` (bool): Whether to display map view (default: True)
- `provider_name` (str): Data provider institution
- `provider_url` (str): Provider website URL
- `provider_contact_name` (str): Contact person name
- `provider_contact_email` (str): Contact email
- `deployment_info_url_template` (str): URL template for deployment info
- `section_info_url_template` (str): URL template for section info
- `section_plots_url_template` (str): URL template for plots
- `section_data_url_template` (str): URL template for data files
- `json_obj` (dict, optional): Initialize from existing JSON object

**Methods:**

##### `add_deployment`

```python
def add_deployment(self, glider_id, dataset_id, deployment_id, deployment_label, 
                   deployment_active, plotting_active,
                   deployment_start_time, deployment_end_time)
```

Add a deployment to the transect.

**Parameters:**
- `glider_id` (str): Glider system identifier
- `dataset_id` (str): ERDDAP dataset ID
- `deployment_id` (str): Deployment identifier
- `deployment_label` (str): Human-readable label
- `deployment_active` (bool): Whether deployment is active
- `plotting_active` (bool): Whether to generate plots
- `deployment_start_time` (str): Start time ISO format
- `deployment_end_time` (str or None): End time ISO format

**Example:**
```python
glider_json.add_deployment(
    glider_id='washelf_sg',
    dataset_id='washelf-20230101T0000',
    deployment_id='2023_Jan_2023_Mar',
    deployment_label='2023 Jan - Mar',
    deployment_active=False,
    plotting_active=True,
    deployment_start_time='2023-01-01T00:00:00Z',
    deployment_end_time='2023-03-31T23:59:59Z'
)
```

##### `update_deployment`

```python
def update_deployment(self, deployment_id, deployment_start_time, 
                     deployment_end_time, deployment_active, plotting_active,
                     newdeployment_id=None, newdeployment_label=None, 
                     dataset_id=None)
```

Update existing deployment information.

**Parameters:**
- `deployment_id` (str): Deployment to update
- `deployment_start_time` (str): Updated start time
- `deployment_end_time` (str): Updated end time
- `deployment_active` (bool): Updated active status
- `plotting_active` (bool): Updated plotting status
- `newdeployment_id` (str, optional): New deployment ID
- `newdeployment_label` (str, optional): New label
- `dataset_id` (str, optional): New dataset ID

**Example:**
```python
glider_json.update_deployment(
    deployment_id='2023_Jan_Ongoing',
    deployment_start_time='2023-01-01T00:00:00Z',
    deployment_end_time='2023-03-31T23:59:59Z',
    deployment_active=False,
    plotting_active=True,
    newdeployment_id='2023_Jan_2023_Mar',
    newdeployment_label='2023 Jan - Mar'
)
```

---

#### `Glider_Plotting_Json`

Creates plotting metadata JSON for deployments and sections.

```python
class Glider_Plotting_Json:
    def __init__(self, transect_id, deployment_id, json_obj=None)
```

**Parameters:**
- `transect_id` (str): Transect identifier
- `deployment_id` (str): Deployment identifier
- `json_obj` (dict, optional): Initialize from existing JSON

**Methods:**

##### `add_section`

```python
def add_section(self, section_id, section_label, start_time, end_time, variables)
```

Add section metadata.

**Parameters:**
- `section_id` (str): Section identifier
- `section_label` (str): Human-readable label
- `start_time` (str): Section start time
- `end_time` (str): Section end time
- `variables` (list of str): Variables plotted in this section

---

## Main Modules

### glider_main

Main processing script that orchestrates the complete workflow.

**Script Flow:**
1. Load initialization parameters
2. Iterate through active glider lines
3. For each active deployment:
   - Connect to ERDDAP
   - Retrieve metadata and data
   - Detect transect sections
   - Generate plots
   - Create JSON metadata

**Usage:**
```bash
python glider_main.py
```

**Key Variables:**
- `gliderOps` (list): List of Glider objects
- `outputpath` (str): Output directory path

---

### gliders_general_functions

General utility functions for glider data processing.

#### File Operations

##### `get_pathdirs()`

```python
def get_pathdirs()
```

Get configured directory paths.

**Returns:**
- `basedir` (str): Package base directory
- `infodir` (str): Info JSONs directory
- `outputdir` (str): Output directory

**Example:**
```python
import gliders_general_functions as gliders_gen

basedir, infodir, outputdir = gliders_gen.get_pathdirs()
print(f"Output will be saved to: {outputdir}")
```

##### `copyfile_func(src, dst)`

```python
def copyfile_func(src, dst)
```

Copy file or directory with error handling.

**Parameters:**
- `src` (str): Source path
- `dst` (str): Destination path

**Returns:**
- `bool`: True if successful, False otherwise

---

#### Time Calculations

##### `datetime_toordinal_withseconds(origdate)`

```python
def datetime_toordinal_withseconds(origdate)
```

Convert datetime to ordinal time with second resolution.

**Parameters:**
- `origdate` (datetime): Input datetime object

**Returns:**
- `float`: Ordinal time (days since Jan 1, 0000) including fractional seconds

**Example:**
```python
from datetime import datetime
import gliders_general_functions as gliders_gen

dt = datetime(2023, 1, 1, 12, 30, 45)
ordinal = gliders_gen.datetime_toordinal_withseconds(dt)
print(f"Ordinal time: {ordinal}")
```

---

#### Distance Calculations

##### `great_circle_calc(lat, lon)`

```python
def great_circle_calc(lat, lon)
```

Calculate great circle distance between consecutive points.

**Parameters:**
- `lat` (numpy.ndarray): Latitude array in degrees
- `lon` (numpy.ndarray): Longitude array in degrees

**Returns:**
- `numpy.ndarray`: Distance array in meters (length = len(lat) - 1)

**Example:**
```python
import numpy as np
import gliders_general_functions as gliders_gen

lat = np.array([47.0, 47.1, 47.2])
lon = np.array([-125.0, -124.9, -124.8])
distances = gliders_gen.great_circle_calc(lat, lon)
print(f"Segment distances (m): {distances}")
print(f"Total distance (km): {distances.sum() / 1000:.2f}")
```

---

### gliders_make_plots

Comprehensive plotting functions for glider data visualization.

#### Colormap Functions

##### `make_oxy_colormap(vmin, vmax)`

```python
def make_oxy_colormap(vmin, vmax)
```

Create custom colormap for dissolved oxygen highlighting hypoxic conditions.

**Parameters:**
- `vmin` (float): Minimum oxygen value (mg/L)
- `vmax` (float): Maximum oxygen value (mg/L)

**Returns:**
- `ListedColormap`: Custom colormap object

**Description:**
Creates a colormap where:
- Values < 2 mg/L (hypoxic): Purple to white gradient
- Values >= 2 mg/L: Rainbow colormap

**Example:**
```python
import gliders_make_plots as gliders_plot
import matplotlib.pyplot as plt

oxy_cmap = gliders_plot.make_oxy_colormap(vmin=0, vmax=10)

# Use in plotting
plt.contourf(x, y, oxygen_data, cmap=oxy_cmap, levels=20)
plt.colorbar(label='Dissolved Oxygen (mg/L)')
```

---

#### Section Plotting

##### `make_section_plot(...)`

```python
def make_section_plot(data, variable, variable_label, variable_units,
                     vmin, vmax, lon_limits, depth_limits,
                     colormap='rainbow', output_file=None, **kwargs)
```

Create vertical section plot for oceanographic variable.

**Parameters:**
- `data` (DataFrame): Section data with longitude, depth, and variable columns
- `variable` (str): Column name of variable to plot
- `variable_label` (str): Label for colorbar
- `variable_units` (str): Units string
- `vmin` (float): Colorbar minimum
- `vmax` (float): Colorbar maximum
- `lon_limits` (list): [min_lon, max_lon]
- `depth_limits` (list): [min_depth, max_depth]
- `colormap` (str or Colormap): Colormap to use
- `output_file` (str, optional): Output filename
- `**kwargs`: Additional matplotlib parameters

**Returns:**
- `matplotlib.figure.Figure`: Figure object

**Example:**
```python
import gliders_make_plots as gliders_plot
import pandas as pd

# Assuming section_data is a DataFrame with columns: longitude, depth, temperature

fig = gliders_plot.make_section_plot(
    data=section_data,
    variable='temperature',
    variable_label='Temperature',
    variable_units='°C',
    vmin=5,
    vmax=15,
    lon_limits=[-125.5, -124.0],
    depth_limits=[0, 200],
    colormap='rainbow',
    output_file='temperature_section_a.png'
)
```

---

#### Map Plotting

##### `make_map_plot(...)`

```python
def make_map_plot(latitude, longitude, lat_limits, lon_limits,
                 marker_color=None, colormap='viridis',
                 output_file=None, **kwargs)
```

Create map view of glider track.

**Parameters:**
- `latitude` (array): Latitude coordinates
- `longitude` (array): Longitude coordinates
- `lat_limits` (list): [min_lat, max_lat]
- `lon_limits` (list): [min_lon, max_lon]
- `marker_color` (array, optional): Values for color-coding track
- `colormap` (str): Colormap for track coloring
- `output_file` (str, optional): Output filename
- `**kwargs`: Additional plotting parameters

**Returns:**
- `matplotlib.figure.Figure`: Figure object

**Example:**
```python
fig = gliders_plot.make_map_plot(
    latitude=data['latitude'],
    longitude=data['longitude'],
    lat_limits=[46.0, 48.5],
    lon_limits=[-125.5, -124.0],
    marker_color=data['temperature'],
    colormap='rainbow',
    output_file='glider_track_map.png'
)
```

---

### create_jsons

Functions for creating and managing JSON metadata files.

See [JSON Classes](#json-classes) section above for `GliderJson` and `Glider_Plotting_Json` classes.

---

## Utility Functions

### get_min_max

Section detection algorithm for identifying glider turning points.

##### `get_min_max(inarr, Tolerance, expPts)`

```python
def get_min_max(inarr, Tolerance, expPts)
```

Find start and end points for each segment of the glider path.

**Parameters:**
- `inarr` (numpy.ndarray): Input array (typically longitude), NO NaNs allowed
- `Tolerance` (float): Threshold determining when new segment starts (typically 0.1-0.5)
- `expPts` (int): Expected number of endpoints for full glider path

**Returns:**
- `ind_min_max` (list of int): Array indices denoting sequential endpoints

**Algorithm:**
1. Start at first point
2. Track whether glider is moving toward maximum or minimum
3. When movement reverses by more than `Tolerance`, mark as turning point
4. Continue until all points processed

**Example:**
```python
from get_min_max import get_min_max
import numpy as np

# Glider longitude data
longitude = np.array([-125.5, -125.4, -125.2, -125.0, -124.8,  # Moving east
                      -124.9, -125.1, -125.3, -125.5])          # Turning, moving west

# Detect sections (tolerance = 0.2 degrees, expect ~4 endpoints)
endpoints = get_min_max(longitude, Tolerance=0.2, expPts=4)
print(f"Section endpoints at indices: {endpoints}")
# Output might be: [0, 4, 8]  (start, turn, end)

# Split into sections
for i in range(len(endpoints) - 1):
    section_start = endpoints[i]
    section_end = endpoints[i + 1]
    print(f"Section {i}: indices {section_start} to {section_end}")
```

**Tolerance Guidelines:**
- **Too small** (< 0.1): Detects spurious turning points from glider wandering
- **Too large** (> 0.5): Misses actual turning points
- **Typical values**: 0.15-0.25 for most glider transects

---

## Configuration

### Configuration Files

#### `info_jsons/pathdirs.json`

Directory path configuration.

**Format:**
```json
{
    "outputdir": "/path/to/output/directory"
}
```

#### `info_jsons/user_info.json`

User and institution information.

**Format:**
```json
{
    "user_name": "Your Name",
    "user_email": "email@example.com",
    "institution": "Institution Name"
}
```

#### `info_jsons/uav_list.json`

List of UAVs (gliders) to process.

**Format:**
```json
{
    "gliders": [
        {
            "glider_id": "washelf_sg",
            "glider_type": "seaglider",
            "active": true
        },
        {
            "glider_id": "trinidad_sg",
            "glider_type": "seaglider",
            "active": true
        }
    ]
}
```

#### `info_jsons/uav_transects.json`

Transect definitions.

**Format:**
```json
{
    "transects": [
        {
            "transect_id": "washelf",
            "transect_label": "WA Shelf Glider",
            "lat_range": [46.0, 48.5],
            "lon_range": [-125.5, -124.0]
        }
    ]
}
```

#### `do_colormap.json`

Dissolved oxygen colormap specification.

**Format:**
```json
{
    "colormap": "custom_oxygen",
    "hypoxic_threshold": 2.0,
    "below_threshold": "purple_to_white",
    "above_threshold": "rainbow"
}
```

#### `partial_rainbow.json`

Partial rainbow colormap specification for other variables.

**Format:**
```json
{
    "colors": [[0.25, [0.0, 0.0, 1.0]], 
               [0.50, [0.0, 1.0, 1.0]],
               [0.75, [1.0, 1.0, 0.0]],
               [1.00, [1.0, 0.0, 0.0]]]
}
```

---

## Environment Configuration

### Conda Environment (`gliders_env.yml`)

Key dependencies specifications:
- Python 3.7+
- erddapy >= 1.1.0
- numpy >= 1.20
- pandas >= 1.3
- matplotlib >= 3.4
- xarray >= 0.19
- scipy >= 1.7
- geopandas >= 0.6
- gdal >= 2.3

See [INSTALLATION.md](INSTALLATION.md) for complete setup.

---

## Data Structures

### Expected DataFrame Structure

Data retrieved from ERDDAP should have these columns:

**Required Columns:**
- `precise_time` (datetime or str): Timestamp
- `precise_lat` (float): Latitude in degrees
- `precise_lon` (float): Longitude in degrees
- `depth` (float): Depth in meters (positive down)

**Variable Columns (examples):**
- `temperature` (float): Water temperature in °C
- `salinity` (float): Practical salinity (PSU)
- `density` (float): Water density in kg/m³
- `chlorophyll_a` (float): Chlorophyll-a concentration
- `oxygen_concentration` (float): Dissolved oxygen in mg/L

### Section Data Structure

After section detection, data organized as:

```python
sections = {
    'a': DataFrame with section A data,
    'b': DataFrame with section B data,
    # ... etc
}
```

Each section DataFrame contains subset of full deployment data between turning points.

---

## Error Handling

### Common Exceptions

**ERDDAPError:**
- Raised when ERDDAP server unreachable
- Raised when dataset_id not found
- Raised when variable names invalid

**Processing Errors:**
- `ValueError`: Invalid parameters (e.g., negative tolerance)
- `KeyError`: Missing required data columns
- `IndexError`: Section detection failed (adjust tolerance or exppts)

### Error Recovery Patterns

```python
import logging

try:
    # ERDDAP data retrieval
    data = e.to_pandas()
except Exception as e:
    logging.error(f"ERDDAP retrieval failed: {e}")
    # Implement retry logic or skip deployment

try:
    # Section detection
    sections = get_min_max(lon_data, tolerance, exppts)
except Exception as e:
    logging.error(f"Section detection failed: {e}")
    # Adjust parameters and retry

try:
    # Plotting
    make_section_plot(...)
except Exception as e:
    logging.error(f"Plotting failed: {e}")
    # Continue with next section
```

---

## Performance Considerations

### Optimization Tips

1. **Data Retrieval:**
   - Use tight time constraints
   - Request only needed variables
   - Cache ERDDAP responses locally

2. **Section Detection:**
   - Tune tolerance to avoid excessive sections
   - Use appropriate exppts estimate

3. **Plotting:**
   - Adjust num_interp_pts based on data density
   - Use appropriate DPI (150 for web, 300 for print)
   - Close figures after saving to free memory

4. **Memory Management:**
   ```python
   import gc
   
   # Process each section
   for section in sections:
       process_section(section)
       gc.collect()  # Force garbage collection
   ```

---

## Version Compatibility

**Python:** 3.7, 3.8, 3.9, 3.10

**Key Package Versions:**
- erddapy: 1.1.0+
- numpy: 1.20+
- pandas: 1.3+
- matplotlib: 3.4+

---

## Complete Example

Full workflow example combining all components:

```python
# Import required modules
from init_params_NANOOS import init_params
from erddapy import ERDDAP
import gliders_general_functions as gliders_gen
import gliders_make_plots as gliders_plot
from get_min_max import get_min_max
from create_jsons import GliderJson
import pandas as pd
import numpy as np
import json
import os

# 1. Initialize
gliderOps, outputpath = init_params()

# 2. Select deployment
glider = gliderOps[0]  # WA Shelf
dataset = glider.datasets[0]  # First deployment

# 3. Connect to ERDDAP
e = ERDDAP(server='NGDAC')
e.protocol = 'tabledap'
e.response = 'csv'
e.dataset_id = dataset.dataset_id

# 4. Set constraints and retrieve
e.constraints = {
    'precise_time>=': dataset.datetime_start,
    'precise_time<=': dataset.datetime_end
}
e.variables = dataset.dac_timelocdepth + dataset.dac_vars
df = e.to_pandas()

# 5. Clean data
df = df.dropna(subset=['precise_lon', 'depth'])

# 6. Detect sections
lon_data = df['precise_lon'].values
sections_idx = get_min_max(lon_data, dataset.tolerance, dataset.exppts)

# 7. Split into sections
sections = {}
for i in range(len(sections_idx) - 1):
    section_id = dataset.section_id[i]
    start_idx = sections_idx[i]
    end_idx = sections_idx[i + 1]
    sections[section_id] = df.iloc[start_idx:end_idx].copy()

# 8. Plot each section
for section_id, section_data in sections.items():
    section_dir = os.path.join(outputpath, dataset.transect_id, 
                               dataset.deployment_id, section_id, 'scientific')
    os.makedirs(section_dir, exist_ok=True)
    
    # Plot each variable
    for var, label, units, limits in zip(dataset.vars_id, 
                                         dataset.vars_label,
                                         dataset.vars_units,
                                         dataset.vars_limits):
        output_file = os.path.join(section_dir, f"{var}.png")
        
        gliders_plot.make_section_plot(
            data=section_data,
            variable=var,
            variable_label=label,
            variable_units=units,
            vmin=limits[0],
            vmax=limits[1],
            lon_limits=dataset.lonlimtransect,
            depth_limits=dataset.depthlimtransect,
            output_file=output_file
        )

# 9. Create JSON metadata
glider_json = GliderJson(
    transect_id=dataset.transect_id,
    transect_label=dataset.title,
    active=True,
    display_map=True,
    provider_name='Example Provider',
    provider_url='https://example.com',
    provider_contact_name='Contact Name',
    provider_contact_email='contact@example.com',
    deployment_info_url_template='https://data.example.com/{transect_id}/{deployment_id}/deployment_info.json',
    section_info_url_template='https://data.example.com/{transect_id}/{deployment_id}/{section_id}/section_info.json',
    section_plots_url_template='https://data.example.com/{transect_id}/{deployment_id}/{section_id}/scientific/{variable_id}.png',
    section_data_url_template='https://data.example.com/{transect_id}/{deployment_id}/{section_id}/data.nc'
)

glider_json.add_deployment(
    glider_id=dataset.glider_id,
    dataset_id=dataset.dataset_id,
    deployment_id=dataset.deployment_id,
    deployment_label=dataset.deployment_label,
    deployment_active=dataset.deployment_active,
    plotting_active=True,
    deployment_start_time=dataset.datetime_start,
    deployment_end_time=dataset.datetime_end
)

# Save JSON
json_file = os.path.join(outputpath, dataset.transect_id, 'glider_info.json')
with open(json_file, 'w') as f:
    json.dump(glider_json.__dict__, f, indent=2)

print(f"Processing complete! Output saved to: {outputpath}")
```

---

## Additional Resources

- **ERDDAP Documentation**: https://coastwatch.pfeg.noaa.gov/erddap/index.html
- **IOOS NGDAC**: https://gliders.ioos.us/
- **NANOOS**: https://www.nanoos.org/

---

## Support and Contributing

For API questions or bug reports:
1. Check this documentation
2. Review example code
3. Examine error messages and logs
4. Contact package maintainers

When reporting issues, include:
- Python version
- Package version
- Full error traceback
- Minimal reproducible example

---
