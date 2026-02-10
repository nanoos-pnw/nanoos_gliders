# Changelog

All notable changes to the nanoos_gliders package will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Added gliders_main wrapper script to run checks and plots with logging.

### Planned Features
- Automated detection of new deployments from ERDDAP
- Real-time processing capabilities
- Enhanced error handling and logging framework
- Improved section detection algorithms
- Support for additional glider types
- Web dashboard for monitoring processing status
- Automated testing suite
- Docker containerization

## [1.0.0] - Current

### Added
- Initial release of nanoos_gliders package
- Core glider processing workflow
- Support for multiple glider lines:
  - WA Shelf Glider
  - Trinidad Head Glider
  - La Push Glider
  - OOI Gliders (Grays Harbor, Newport)
- ERDDAP data retrieval integration
- Automated section detection using turning point algorithm
- Scientific visualization capabilities:
  - Temperature, salinity, density plots
  - Dissolved oxygen with hypoxic highlighting
  - Chlorophyll-a fluorescence
  - Map views with glider tracks
- JSON metadata generation for NVS integration
- Custom colormap support:
  - Oxygen colormap with hypoxic threshold
  - Partial rainbow colormap
- Bathymetry integration (GEBCO 2021)
- Deployment management tools:
  - Add new deployments
  - Check deployment status
  - Update deployment information
- Configuration system via JSON files
- Comprehensive documentation:
  - README with overview
  - Installation guide
  - Usage guide with examples
  - Complete API reference

### Core Modules
- `classes.py`: Glider and Dataset classes
- `gliders_main.py`: Wrapper for checks and plotting
- `gliders_general_functions.py`: Utility functions
- `gliders_make_plots.py`: Plotting functions
- `create_jsons.py`: JSON metadata creation
- `gliders_add_transect_deployments.py`: Deployment addition
- `gliders_check_transect_deployments.py`: Deployment monitoring
- `get_min_max.py`: Section detection algorithm

### Configuration Files
- `gliders_env.yml`: Conda environment specification
- `info_jsons/pathdirs.json`: Directory configuration
- `info_jsons/user_info.json`: User information
- `info_jsons/uav_list.json`: Glider list
- `info_jsons/uav_transects.json`: Transect definitions
- `do_colormap.json`: Oxygen colormap specification
- `partial_rainbow.json`: Rainbow colormap specification

### Dependencies
- erddapy 1.1.0+: ERDDAP data access
- numpy: Numerical computing
- pandas: Data manipulation
- matplotlib: Visualization
- xarray: Multi-dimensional data
- scipy: Scientific computing
- geopandas: Geospatial operations
- gdal: Geospatial data abstraction

### Known Issues
- Section detection may need manual tuning for complex glider paths
- Bathymetry interpolation occasionally produces visual artifacts
- Manual intervention required for some deployment parameters
- Limited error recovery in ERDDAP connection failures

## Development History

### Pre-release Development

#### Phase 3 - Documentation and Refinement
- Created comprehensive documentation suite
- Added usage examples and tutorials
- Documented all API functions and classes
- Improved code comments

#### Phase 2 - Feature Enhancement
- Added deployment management tools
- Implemented JSON metadata generation
- Created custom colormap functionality
- Integrated bathymetry visualization
- Added support for multiple glider types

#### Phase 1 - Core Implementation
- Implemented basic data retrieval from ERDDAP
- Created section detection algorithm
- Built initial plotting capabilities
- Designed class structure for gliders and datasets
- Established configuration system

#### Phase 0 - Initial Design
- Researched ERDDAP API and glider data formats
- Designed package architecture
- Identified key requirements from NANOOS
- Created initial prototype scripts

## Version History Details

### [1.0.0] - 2024-02-06

**Initial Release**

This is the first documented version of the nanoos_gliders package. It represents the culmination of development work to create an automated glider data processing system for the NANOOS program.

**Key Capabilities:**
- Processes glider oceanographic data from IOOS NGDAC
- Generates publication-quality scientific visualizations
- Creates structured metadata for web visualization systems
- Supports multiple concurrent glider deployments
- Handles both Slocum and Seaglider platforms

**Target Users:**
- Ocean observing system operators
- Marine scientists analyzing glider data
- Data managers maintaining glider data products
- Web developers integrating glider visualizations

**System Requirements:**
- Python 3.7+
- Conda package manager
- Internet connection for ERDDAP access
- ~2GB disk space for environment

**Documentation:**
- Complete user guide
- API reference
- Installation instructions
- Code examples

## Migration Guide

### From Pre-1.0 Scripts to 1.0 Package

If you were using earlier prototype scripts:

1. **Update imports:**
   ```python
   # Old
   import glider_processing_script
   
   # New
   from init_params_NANOOS import init_params
   import gliders_general_functions as gliders_gen
   ```

2. **Use new class structure:**
   ```python
   # Old
   dataset_params = {...}
   
   # New
   from classes import Dataset, WAShelfGlider
   dataset = Dataset(...)
   ```

3. **Update configuration:**
   - Move hardcoded paths to `pathdirs.json`
   - Migrate deployment parameters to Dataset objects
   - Update colormap specifications to JSON format

4. **Adopt new workflow:**
   - Use `gliders_main.py` for standard processing
   - Use deployment management scripts for updates
   - Follow documented API patterns

## Future Roadmap

### Version 1.1.0 (Planned)
- Enhanced error handling and recovery
- Improved logging with configurable levels
- Performance optimizations for large deployments
- Extended test coverage
- Additional colormap options

### Version 1.2.0 (Planned)
- Automated deployment detection from ERDDAP
- Real-time data processing mode
- Email notifications for processing completion/errors
- Web-based monitoring dashboard
- Database backend for deployment tracking

### Version 2.0.0 (Future)
- Complete API redesign for extensibility
- Plugin architecture for custom processing
- Machine learning integration for quality control
- Multi-glider coordinated mission support
- Cloud deployment support (AWS, Azure, GCP)

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines on:
- Reporting bugs
- Suggesting features
- Submitting code changes
- Documentation improvements

## Release Process

### For Maintainers

1. **Update version numbers** in:
   - `setup.py` (if applicable)
   - Documentation files
   - This CHANGELOG

2. **Update CHANGELOG**:
   - Move [Unreleased] items to new version section
   - Add release date
   - Document breaking changes

3. **Test thoroughly**:
   - Run test suite
   - Verify example code
   - Check documentation accuracy

4. **Create release**:
   - Tag version in git
   - Build distribution packages
   - Update published documentation

5. **Announce release**:
   - Update README
   - Notify users
   - Post to relevant channels

## Versioning Policy

**Major version (X.0.0):**
- Breaking API changes
- Major architectural changes
- Significant new features

**Minor version (x.Y.0):**
- New features (backward compatible)
- Significant enhancements
- New glider type support

**Patch version (x.y.Z):**
- Bug fixes
- Documentation updates
- Performance improvements
- Security patches

## Deprecation Policy

Features marked for deprecation:
- Will be clearly documented in CHANGELOG
- Will remain functional for at least one minor version
- Will issue warnings when used
- Will include migration instructions

## Support Policy

**Active Support:**
- Current major version (1.x)
- Security updates and critical bug fixes

**Maintenance Mode:**
- Previous major version (when 2.0 releases)
- Critical security issues only

**End of Life:**
- Versions older than previous major
- No updates or support

## Acknowledgments

This package builds upon:
- NOAA IOOS NGDAC infrastructure
- ERDDAP data server technology
- Open source scientific Python ecosystem
- Contributions from NANOOS team members
- Feedback from glider operators

## License

[Specify license] - See LICENSE file for details.

---

For questions about releases or version history:
- Check GitHub releases page
- Review this CHANGELOG
- Contact package maintainers
