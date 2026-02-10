# Installation Guide

This guide provides detailed instructions for installing and configuring the `nanoos_gliders` package.

## Prerequisites

- **Anaconda or Miniconda**: Python distribution with conda package manager
- **Operating System**: Windows, macOS, or Linux
- **Python Version**: 3.7 or higher (specified in environment)
- **Disk Space**: ~2GB for environment and dependencies
- **Internet Connection**: Required for ERDDAP data access

## Installation Steps

### 1. Clone or Download Repository

```bash
cd /path/to/your/workspace
git clone [repository-url] nanoos_gliders
cd nanoos_gliders
```

Or download and extract the package to your desired location.

### 2. Create Conda Environment

The package includes a complete environment specification file:

```bash
conda env create -f gliders_env.yml
```

This creates an environment named `gliders_env` with all required dependencies.

### 3. Activate Environment

```bash
conda activate gliders_env
```

On Windows PowerShell:
```powershell
conda activate gliders_env
```

### 4. Verify Installation

Test that key packages are available:

```python
python -c "import erddapy; import numpy; import matplotlib; print('Installation successful!')"
```

## Configuration

### Path Configuration

Create or edit `info_jsons/pathdirs.json`:

```json
{
    "outputdir": "/path/to/output/directory"
}
```

This directory will store:
- Generated plots
- JSON metadata files
- Processed data outputs

### User Information

Edit `info_jsons/user_info.json` (if needed):

```json
{
    "user_name": "Your Name",
    "user_email": "your.email@example.com",
    "institution": "Your Institution"
}
```

### Glider Configuration

1. **UAV List** (`info_jsons/uav_list.json`):
   - List of unmanned autonomous vehicles (gliders) to process
   
2. **UAV Transects** (`info_jsons/uav_transects.json`):
   - Transect definitions and parameters

3. **Colormaps** (`do_colormap.json`, `partial_rainbow.json`):
   - Custom colormap specifications for oxygen and other variables

## Bathymetry Data Setup

### Download GEBCO Data

1. Visit [GEBCO Grid Download](https://www.gebco.net/data_and_products/gridded_bathymetry_data/)
2. Select region covering your glider transects
3. Download NetCDF format
4. Place in `glider_bathy/GEBCO_2021/` directory

The package expects a file like:
```
glider_bathy/GEBCO_2021/gebco_2021_n49.0_s39.0_w-130.0_e-123.0.nc
```

Adjust file paths in plotting functions if using different bathymetry data.

## Creating Initialization Parameters

You need to create an initialization file (not included in repository):

**Create `init_params_NANOOS.py`:**

```python
from classes import (WAShelfGlider, TrinidadGlider, LaPushGlider,
                     Dataset)
import json
import os

def init_params():
    """
    Initialize glider deployment parameters
    
    Returns:
        gliderOps: List of Glider objects with deployments
        outputpath: Path to output directory
    """
    
    # Load output path
    basedir = os.path.dirname(__file__)
    with open(os.path.join(basedir, 'info_jsons', 'pathdirs.json'), 'r') as f:
        paths = json.load(f)
    outputpath = paths['outputdir']
    
    # Define datasets for each glider line
    washelf_datasets = [
        Dataset(
            dataset_id='your-dataset-id',
            glider_id='your-glider-id',
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
            latlimmap=[44.0, 48.0],
            lonlimmap=[-127.0, -124.0],
            lonlimtransect=[-126.5, -124.5],
            depthlimtransect=[0, 200],
            tolerance=0.2,
            exppts=10,
            num_interp_pts=100
        )
    ]
    
    # Create glider objects
    gliderOps = [
        WAShelfGlider(washelf_datasets),
        # Add other gliders as needed
    ]
    
    return gliderOps, outputpath
```

## Environment Variables (Optional)

For automated deployments, you can set:

```bash
export NANOOS_GLIDERS_OUTPUT=/path/to/output
export NANOOS_GLIDERS_DATA=/path/to/data
```

## Testing Installation

### Test 1: Import Modules

```python
from classes import Dataset, WAShelfGlider
from create_jsons import GliderJson
import gliders_general_functions as gliders_gen
print("All modules imported successfully!")
```

### Test 2: ERDDAP Connection

```python
from erddapy import ERDDAP

e = ERDDAP(server='NGDAC')
e.protocol = 'tabledap'
print(f"Connected to ERDDAP server: {e.server}")
```

### Test 3: Path Configuration

```python
import gliders_general_functions as gliders_gen

basedir, infodir, outputdir = gliders_gen.get_pathdirs()
print(f"Base directory: {basedir}")
print(f"Info directory: {infodir}")
print(f"Output directory: {outputdir}")
```

## Troubleshooting

### Common Issues

**1. Conda environment creation fails**
```bash
# Update conda first
conda update -n base conda
# Try creating environment again
conda env create -f gliders_env.yml
```

**2. ERDDAP connection timeout**
- Check internet connection
- Verify firewall settings
- Try accessing https://gliders.ioos.us/erddap in browser

**3. Missing init_params_NANOOS.py**
- This file must be created manually (see above)
- Contains deployment-specific parameters

**4. Output directory errors**
```bash
# Ensure directory exists and is writable
mkdir -p /path/to/output
chmod 755 /path/to/output
```

**5. Import errors**
```bash
# Verify environment is activated
conda activate gliders_env
# Check if in correct directory
pwd  # Should be nanoos_gliders directory
```

### Package-Specific Issues

**GDAL Installation**
If GDAL fails to install:
```bash
conda install -c conda-forge gdal=3.3.0
```

**Matplotlib Backend**
If plotting fails:
```python
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import matplotlib.pyplot as plt
```

## Updating

To update the environment:

```bash
conda activate gliders_env
conda env update -f gliders_env.yml --prune
```

To update individual packages:

```bash
conda update package-name
```

## Uninstallation

Remove the conda environment:

```bash
conda deactivate
conda env remove -n gliders_env
```

Delete the package directory:

```bash
rm -rf /path/to/nanoos_gliders
```

## Next Steps

After installation:

1. Read [USAGE_GUIDE.md](USAGE_GUIDE.md) for usage examples
2. Review [API_REFERENCE.md](API_REFERENCE.md) for detailed API documentation
3. Configure your glider deployments in initialization file
4. Run test processing on a single deployment

## Support

For installation issues:
- Check package README.md
- Review error messages carefully
- Ensure all prerequisites are met
- Verify configuration files are correctly formatted

## System Requirements

### Minimum Requirements
- CPU: 2+ cores
- RAM: 4GB
- Storage: 10GB free space
- Internet: Broadband connection

### Recommended Requirements
- CPU: 4+ cores
- RAM: 8GB+
- Storage: 50GB+ free space (for multiple deployments)
- Internet: High-speed connection

## Dependencies Explanation

### Core Scientific Computing
- **numpy** (1.20+): Array operations and numerical computing
- **pandas** (1.3+): Data manipulation and analysis
- **scipy** (1.7+): Scientific computing and interpolation

### Data Access
- **erddapy** (1.1+): ERDDAP server communication
- **xarray** (0.19+): Multi-dimensional data handling
- **netCDF4**: NetCDF file I/O

### Visualization
- **matplotlib** (3.4+): Plotting and visualization
- **cartopy** or **basemap**: Map projections (optional)

### Geospatial
- **geopandas** (0.6+): Geospatial data operations
- **gdal** (2.3+): Geospatial data abstraction

### Utilities
- **requests**: HTTP requests
- **json**: JSON file handling
- **datetime**: Time handling

All dependencies are automatically installed via `gliders_env.yml`.
