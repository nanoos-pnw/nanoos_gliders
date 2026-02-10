# Quick Start Guide

Get started with the nanoos_gliders package in 15 minutes.

## Prerequisites

- Anaconda or Miniconda installed
- Basic Python knowledge
- Internet connection

## Installation (5 minutes)

### 1. Get the Package

```bash
cd /your/workspace
# Download or clone the nanoos_gliders package
cd nanoos_gliders
```

### 2. Create Environment

```bash
conda env create -f gliders_env.yml
conda activate gliders_env
```

### 3. Configure Paths

Edit `info_jsons/pathdirs.json`:

```json
{
    "outputdir": "C:/Users/YourName/glider_output"
}
```

Create the output directory:

```bash
mkdir -p C:/Users/YourName/glider_output
```

## First Time Setup (5 minutes)

### Create Initialization File

Create `init_params_NANOOS.py` in the package directory:

```python
from classes import WAShelfGlider, Dataset
import json
import os

def init_params():
    """Initialize glider deployment parameters"""
    
    # Get output path
    basedir = os.path.dirname(__file__)
    with open(os.path.join(basedir, 'info_jsons', 'pathdirs.json'), 'r') as f:
        paths = json.load(f)
    outputpath = paths['outputdir']
    
    # Define a test deployment
    test_dataset = Dataset(
        dataset_id='sp064-20210729T1913',  # Example public dataset
        glider_id='sp064',
        deployment_id='2021_Jul_2021_Sep',
        deployment_label='2021 Jul - Sep',
        section_id=['a', 'b', 'c', 'd', 'e'],
        section_label=['Section A', 'Section B', 'Section C', 'Section D', 'Section E'],
        datetime_start='2021-07-29T00:00:00Z',
        datetime_end='2021-08-15T23:59:59Z',  # Use shorter time range for testing
        deployment_active=True,
        dac_timelocdepth=['precise_time', 'precise_lat', 'precise_lon', 'depth'],
        dac_variables=['temperature', 'salinity', 'density'],
        variables_label=['Temperature', 'Salinity', 'Density'],
        variables_id=['temp', 'salt', 'dens'],
        variables_units=['°C', 'PSU', 'kg/m³'],
        variables_limits=[[4, 20], [30, 35], [1020, 1028]],
        latlimmap=[46.0, 49.0],
        lonlimmap=[-126.0, -123.0],
        lonlimtransect=[-126.0, -123.0],
        depthlimtransect=[0, 300],
        tolerance=0.2,
        exppts=10,
        num_interp_pts=100
    )
    
    # Create glider with dataset
    gliderOps = [
        WAShelfGlider([test_dataset])
    ]
    
    return gliderOps, outputpath
```

## Run First Test (5 minutes)

### Test ERDDAP Connection

```python
from erddapy import ERDDAP
import pandas as pd

# Connect to NGDAC
e = ERDDAP(server='NGDAC')
e.protocol = 'tabledap'
e.dataset_id = 'sp064-20210729T1913'

# Get dataset info
info_url = e.get_info_url()
info = pd.read_csv(info_url)
print("Dataset info retrieved successfully!")
print(f"Available variables: {len(info[info['Row Type'] == 'variable'])}")
```

Expected output:
```
Dataset info retrieved successfully!
Available variables: 45
```

### Run Processing

```bash
python glider_main.py
```

This will:
1. Load your parameters
2. Download data from ERDDAP
3. Detect transect sections
4. Generate plots
5. Create JSON metadata

**Processing time**: 2-10 minutes depending on data size and internet speed

### Check Results

```bash
ls C:/Users/YourName/glider_output/washelf/2021_Jul_2021_Sep/
```

You should see:
- Section folders (a/, b/, c/, etc.)
- Each section contains scientific/ folder with plots
- JSON metadata files

## Quick Examples

### Example 1: Check Available Datasets

```python
from erddapy import ERDDAP
import pandas as pd

# Search for glider datasets
e = ERDDAP(server='NGDAC')
search_url = e.get_search_url(search_for='washshelf', response='csv')
datasets = pd.read_csv(search_url)

print(f"Found {len(datasets)} datasets")
print(datasets[['Dataset ID', 'Title']].head())
```

### Example 2: Quick Plot

```python
from init_params_NANOOS import init_params
from erddapy import ERDDAP
import matplotlib.pyplot as plt
import pandas as pd

# Load parameters
gliderOps, outputpath = init_params()
dataset = gliderOps[0].datasets[0]

# Get data
e = ERDDAP(server='NGDAC')
e.protocol = 'tabledap'
e.response = 'csv'
e.dataset_id = dataset.dataset_id
e.constraints = {
    'precise_time>=': dataset.datetime_start,
    'precise_time<=': dataset.datetime_end
}
e.variables = ['precise_time', 'precise_lat', 'precise_lon', 
               'depth', 'temperature']
df = e.to_pandas()

# Quick scatter plot
plt.figure(figsize=(10, 4))

plt.subplot(1, 2, 1)
plt.plot(df['precise_lon'], df['precise_lat'], 'b-', alpha=0.5)
plt.xlabel('Longitude')
plt.ylabel('Latitude')
plt.title('Glider Track')
plt.grid(True)

plt.subplot(1, 2, 2)
plt.scatter(df['precise_lon'], df['depth'], 
            c=df['temperature'], cmap='rainbow', s=1)
plt.gca().invert_yaxis()
plt.xlabel('Longitude')
plt.ylabel('Depth (m)')
plt.colorbar(label='Temperature (°C)')
plt.title('Temperature Section')

plt.tight_layout()
plt.savefig('quick_plot.png', dpi=150)
print("Saved quick_plot.png")
```

### Example 3: Section Detection

```python
import numpy as np
from get_min_max import get_min_max

# Simulate glider path
lon = np.concatenate([
    np.linspace(-125.5, -124.5, 50),  # East
    np.linspace(-124.5, -125.5, 50),  # West
    np.linspace(-125.5, -124.5, 50),  # East again
])

# Detect sections
sections = get_min_max(lon, Tolerance=0.2, expPts=6)
print(f"Detected {len(sections)} section boundaries at indices: {sections}")

# Visualize
import matplotlib.pyplot as plt

plt.figure(figsize=(12, 4))
plt.plot(lon, 'b-', alpha=0.5, label='Glider path')
for i, idx in enumerate(sections):
    plt.axvline(idx, color='r', linestyle='--', alpha=0.7)
    plt.text(idx, lon[idx], f'Section {i}', rotation=90)
plt.xlabel('Data point')
plt.ylabel('Longitude')
plt.title('Section Detection')
plt.legend()
plt.grid(True)
plt.savefig('section_detection.png', dpi=150)
print("Saved section_detection.png")
```

## Common Commands Cheat Sheet

### Activate Environment
```bash
conda activate gliders_env
```

### Run Main Processing
```bash
python glider_main.py
```

### Check Deployment Status
```python
from gliders_check_transect_deployments import check_all_deployments

status = check_all_deployments('washelf')
for dep in status:
    print(f"{dep['deployment_id']}: {dep['status']}")
```

### Add New Deployment
```python
from gliders_add_transect_deployments import add_new_deployment

add_new_deployment(
    transect_id='washelf',
    glider_id='washelf_sg',
    dataset_id='new-dataset-id',
    deployment_id='2024_Jan_Ongoing',
    deployment_label='2024 Jan - Ongoing',
    start_time='2024-01-01T00:00:00Z',
    end_time=None,
    deployment_active=True,
    plotting_active=True
)
```

### Update Paths
```bash
# Edit configuration
notepad info_jsons/pathdirs.json  # Windows
nano info_jsons/pathdirs.json     # Linux/Mac
```

### View Available Variables
```python
from erddapy import ERDDAP
import pandas as pd

e = ERDDAP(server='NGDAC')
e.dataset_id = 'your-dataset-id'
info = pd.read_csv(e.get_info_url())
vars = info[info['Row Type'] == 'variable']['Variable Name'].values
print(vars)
```

## Troubleshooting Quick Fixes

### "Module not found" error
```bash
# Make sure environment is activated
conda activate gliders_env

# Reinstall dependencies
conda env update -f gliders_env.yml
```

### "Cannot connect to ERDDAP"
```python
# Test connection
from erddapy import ERDDAP
e = ERDDAP(server='NGDAC')
print(e.server)  # Should print server URL

# Check your internet connection
# Try accessing https://gliders.ioos.us/erddap in browser
```

### "No sections detected"
```python
# Adjust tolerance parameter
dataset.tolerance = 0.3  # Try different values (0.1 to 0.5)

# Increase expected points
dataset.exppts = 20  # Allow more sections
```

### "Output directory not found"
```bash
# Create the directory
mkdir -p /path/to/output

# Or update the path in pathdirs.json
```

### "Dataset ID not found"
```python
# Search for available datasets
from erddapy import ERDDAP
import pandas as pd

e = ERDDAP(server='NGDAC')
url = e.get_search_url(search_for='keyword', response='csv')
datasets = pd.read_csv(url)
print(datasets['Dataset ID'])
```

## Next Steps

### Learn More
1. Read [USAGE_GUIDE.md](USAGE_GUIDE.md) for detailed examples
2. Review [API_REFERENCE.md](API_REFERENCE.md) for complete API docs
3. Check [INSTALLATION.md](INSTALLATION.md) for advanced setup

### Customize Your Setup
1. Add your own glider deployments
2. Customize plotting parameters
3. Set up automated processing
4. Integrate with your workflow

### Get Help
- Check documentation files
- Review example code
- Look at error messages carefully
- Contact package maintainers

## Quick Reference Card

### File Structure
```
nanoos_gliders/
├── glider_main.py              # Main script
├── init_params_NANOOS.py       # Your config (create this)
├── classes.py                  # Core classes
├── gliders_make_plots.py       # Plotting
├── info_jsons/
│   ├── pathdirs.json          # Configure this
│   └── ...
└── docs/                       # Documentation
```

### Key Concepts
- **Deployment**: Single glider mission with start/end dates
- **Section**: One transect between turning points
- **Dataset**: ERDDAP dataset containing glider data
- **Tolerance**: Sensitivity for detecting turning points
- **ERDDAP**: Server providing glider data access

### Important Parameters
- `dataset_id`: NGDAC dataset identifier
- `datetime_start/end`: Time range to process
- `deployment_active`: Enable/disable processing
- `tolerance`: Section detection sensitivity (0.1-0.5)
- `variables_limits`: Colorbar ranges for plots

### Workflow
1. Configure → 2. Run → 3. Review → 4. Iterate

### Time Estimates
- Initial setup: 15 minutes
- Process one deployment: 5-15 minutes
- Add new deployment: 5 minutes
- Troubleshooting: 5-30 minutes

---

**Ready to go?** Start with the test deployment above, then customize for your gliders!

For detailed information, see the full documentation in the [README.md](README.md).
