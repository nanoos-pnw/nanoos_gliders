# NANOOS Gliders Package

A comprehensive Python package for processing, analyzing, and visualizing autonomous underwater glider data from the NANOOS (Northwest Association of Networked Ocean Observing Systems) project.

## Overview

The `nanoos_gliders` package automates the processing of glider oceanographic data from the National Glider Data Assembly Center (NGDAC) ERDDAP server. It handles data retrieval, section identification, plot generation, and JSON metadata creation for integration with the NANOOS Visualization System (NVS).

### Key Features

- **Automated Data Retrieval**: Connects to IOOS NGDAC ERDDAP server to download glider deployment data
- **Section Detection**: Automatically identifies transect sections based on turning points
- **Scientific Visualizations**: Generates publication-ready plots for oceanographic variables
- **Multiple Glider Support**: Handles various glider types (Slocum, Seaglider) and transect lines
- **JSON Metadata Generation**: Creates structured metadata for web visualization systems
- **Deployment Management**: Tools for adding, checking, and updating glider deployments

### Supported Glider Lines

- **WA Shelf Glider**: Washington continental shelf monitoring
- **Trinidad Head Glider**: Off northern California coast
- **La Push Glider**: Washington coast transect
- **OOI Gliders**: Ocean Observatories Initiative deployments (Grays Harbor, Newport)

## Quick Start

```python
from init_params_NANOOS import init_params
import glider_main

# Initialize parameters and run processing
gliderOps, outputpath = init_params()

# Main processing loop handles all active deployments
# See glider_main.py for full workflow
```

## Project Structure

```
nanoos_gliders/
├── classes.py                              # Core data classes
├── glider_main.py                          # Main processing script
├── gliders_general_functions.py            # Utility functions
├── gliders_make_plots.py                   # Plotting functions
├── create_jsons.py                         # JSON metadata generation
├── gliders_add_transect_deployments.py     # Add new deployments
├── gliders_check_transect_deployments.py   # Check deployment status
├── get_min_max.py                          # Section detection algorithm
├── gliders_env.yml                         # Conda environment
├── info_jsons/                             # Configuration files
│   ├── pathdirs.json
│   ├── uav_list.json
│   ├── uav_transects.json
│   └── user_info.json
├── glider_bathy/                           # Bathymetry data
└── docs/                                   # Documentation
```

## Core Components

### Classes (`classes.py`)

- **Glider**: Base class for glider transect lines
  - `WAShelfGlider`, `TrinidadGlider`, `LaPushGlider`: Specific implementations
- **Dataset**: Encapsulates deployment parameters and metadata

### Main Processing (`glider_main.py`)

Orchestrates the complete data processing workflow:
1. Load deployment parameters
2. Connect to ERDDAP and retrieve data
3. Identify transect sections
4. Generate scientific plots
5. Create JSON metadata files

### Plotting (`gliders_make_plots.py`)

Comprehensive plotting capabilities:
- Vertical section plots for oceanographic variables
- Custom colormaps (including hypoxic oxygen colormap)
- Map views with glider tracks
- Automatic data interpolation and gridding

### JSON Generation (`create_jsons.py`)

Creates structured metadata for web visualization:
- `GliderJson`: Transect-level information
- `Glider_Plotting_Json`: Deployment and section metadata

## Installation

See [INSTALLATION.md](INSTALLATION.md) for detailed setup instructions.

### Quick Install

```bash
# Create conda environment
conda env create -f gliders_env.yml
conda activate gliders_env

# Configure paths in info_jsons/pathdirs.json
```

## Usage

See [USAGE_GUIDE.md](USAGE_GUIDE.md) for detailed examples and workflows.

### Basic Workflow

1. **Configure Deployment**: Define deployment parameters in initialization file
2. **Run Processing**: Execute `glider_main.py` to process active deployments
3. **Check Status**: Use `gliders_check_transect_deployments.py` to monitor
4. **Add Deployments**: Use `gliders_add_transect_deployments.py` for new data

## API Reference

See [API_REFERENCE.md](API_REFERENCE.md) for complete API documentation.

## Data Sources

- **Primary**: NOAA IOOS NGDAC (National Glider Data Assembly Center)
  - ERDDAP server: https://gliders.ioos.us/erddap
- **Bathymetry**: GEBCO 2021 (General Bathymetric Chart of the Oceans)

## Output Products

### Scientific Plots
- Temperature, Salinity, Density profiles
- Dissolved Oxygen (with hypoxic threshold highlighting)
- Chlorophyll-a fluorescence
- Other biogeochemical variables

### Metadata JSON Files
- `glider_info.json`: Transect and deployment information
- `deployment_info.json`: Deployment-specific metadata
- `section_info.json`: Individual section details
- `glider_plotting_info.json`: Visualization parameters

## Dependencies

Key packages:
- `erddapy`: ERDDAP data access
- `numpy`, `pandas`: Data manipulation
- `matplotlib`: Plotting
- `xarray`: NetCDF/multidimensional data
- `scipy`: Interpolation and scientific computing
- `geopandas`: Geospatial operations

See `gliders_env.yml` for complete dependency list.

## Contributing

To add new glider lines or deployments:
1. Create a new `Glider` subclass in `classes.py`
2. Define `Dataset` objects with deployment parameters
3. Update configuration JSONs in `info_jsons/`
4. Run processing scripts to generate outputs

## Known Limitations

- Manual intervention required for some deployment parameter settings
- Section detection algorithm may need tuning for complex glider paths
- Bathymetry interpolation occasionally produces artifacts

## Future Enhancements

- Automated detection of new deployments from ERDDAP
- Improved section detection algorithms
- Real-time processing capabilities
- Enhanced error handling and logging

## License

[Specify license information]

## Contact

For questions or issues:
- NANOOS: https://www.nanoos.org
- Provider contact information available in deployment metadata

## Acknowledgments

This package processes data from:
- NOAA Integrated Ocean Observing System (IOOS)
- National Glider Data Assembly Center (NGDAC)
- Various glider operators and institutions
- Ocean Observatories Initiative (OOI)

## Version History

See [CHANGELOG.md](CHANGELOG.md) for version history and updates.
