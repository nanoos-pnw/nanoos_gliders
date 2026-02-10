# Troubleshooting Guide

Common issues and their solutions for the nanoos_gliders package.

## Table of Contents

1. [Installation Issues](#installation-issues)
2. [ERDDAP Connection Problems](#erddap-connection-problems)
3. [Data Processing Errors](#data-processing-errors)
4. [Plotting Issues](#plotting-issues)
5. [Section Detection Problems](#section-detection-problems)
6. [Performance Issues](#performance-issues)
7. [Configuration Errors](#configuration-errors)
8. [Common Error Messages](#common-error-messages)

---

## Installation Issues

### Conda Environment Creation Fails

**Problem:** `conda env create -f gliders_env.yml` fails

**Solutions:**

1. **Update conda:**
   ```bash
   conda update -n base conda
   conda env create -f gliders_env.yml
   ```

2. **Try with specific channels:**
   ```bash
   conda env create -f gliders_env.yml --channel conda-forge
   ```

3. **Create minimal environment first:**
   ```bash
   conda create -n gliders_env python=3.9
   conda activate gliders_env
   pip install erddapy numpy pandas matplotlib xarray scipy
   ```

4. **Check for conflicting environments:**
   ```bash
   conda env list
   conda env remove -n gliders_env  # If exists
   conda env create -f gliders_env.yml
   ```

### GDAL Installation Fails

**Problem:** GDAL fails to install or compile

**Solutions:**

1. **Use conda-forge:**
   ```bash
   conda install -c conda-forge gdal=3.3.0
   ```

2. **Skip GDAL if not needed:**
   - Comment out GDAL in `gliders_env.yml`
   - Only needed for advanced geospatial operations

3. **Platform-specific wheels:**
   ```bash
   # Windows
   pip install GDAL-3.3.0-cp39-cp39-win_amd64.whl
   
   # Linux
   sudo apt-get install gdal-bin libgdal-dev
   pip install gdal==3.3.0
   ```

### Module Import Errors

**Problem:** `ModuleNotFoundError: No module named 'erddapy'`

**Solutions:**

1. **Verify environment is activated:**
   ```bash
   conda activate gliders_env
   python -c "import sys; print(sys.prefix)"  # Should show gliders_env path
   ```

2. **Reinstall package:**
   ```bash
   conda activate gliders_env
   pip install erddapy
   ```

3. **Check installation:**
   ```python
   import erddapy
   print(erddapy.__version__)
   ```

---

## ERDDAP Connection Problems

### Cannot Connect to ERDDAP Server

**Problem:** Connection timeout or refused

**Diagnostic steps:**

```python
from erddapy import ERDDAP
import requests

# Test connection
try:
    response = requests.get('https://gliders.ioos.us/erddap/', timeout=10)
    print(f"Status: {response.status_code}")
except Exception as e:
    print(f"Error: {e}")
```

**Solutions:**

1. **Check internet connection:**
   - Try accessing https://gliders.ioos.us/erddap in web browser
   - Ping the server: `ping gliders.ioos.us`

2. **Check firewall settings:**
   ```bash
   # Temporarily disable firewall for testing
   # Or add exception for Python/conda
   ```

3. **Use proxy if required:**
   ```python
   import os
   os.environ['http_proxy'] = 'http://proxy.example.com:8080'
   os.environ['https_proxy'] = 'http://proxy.example.com:8080'
   ```

4. **Increase timeout:**
   ```python
   import requests
   from requests.adapters import HTTPAdapter
   from requests.packages.urllib3.util.retry import Retry
   
   session = requests.Session()
   retry = Retry(total=5, backoff_factor=1)
   adapter = HTTPAdapter(max_retries=retry)
   session.mount('http://', adapter)
   session.mount('https://', adapter)
   ```

### Dataset Not Found

**Problem:** `Dataset 'xyz-123' not found`

**Solutions:**

1. **Verify dataset ID:**
   ```python
   from erddapy import ERDDAP
   import pandas as pd
   
   e = ERDDAP(server='NGDAC')
   url = e.get_search_url(search_for='washelf', response='csv')
   datasets = pd.read_csv(url)
   print(datasets[['Dataset ID', 'Title']])
   ```

2. **Check dataset status:**
   - Visit https://gliders.ioos.us/erddap/tabledap/index.html
   - Search for your dataset
   - Verify it's still active

3. **Use correct server:**
   ```python
   # NGDAC (National Glider Data Assembly Center)
   e = ERDDAP(server='NGDAC')
   # Or full URL
   e = ERDDAP(server='https://gliders.ioos.us/erddap')
   ```

### Invalid Variable Names

**Problem:** `Variable 'xyz' not found in dataset`

**Solutions:**

1. **Get available variables:**
   ```python
   from erddapy import ERDDAP
   import pandas as pd
   
   e = ERDDAP(server='NGDAC')
   e.dataset_id = 'your-dataset-id'
   info = pd.read_csv(e.get_info_url())
   variables = info[info['Row Type'] == 'variable']['Variable Name'].values
   print("Available variables:")
   for var in variables:
       print(f"  {var}")
   ```

2. **Check spelling and case:**
   - Variable names are case-sensitive
   - Use exact names from ERDDAP (e.g., 'precise_time', not 'time')

3. **Update dataset configuration:**
   ```python
   dataset.dac_variables = ['temperature', 'salinity']  # Use correct names
   ```

---

## Data Processing Errors

### No Data Retrieved

**Problem:** ERDDAP query returns empty DataFrame

**Diagnostic:**

```python
print(f"Dataset ID: {e.dataset_id}")
print(f"Constraints: {e.constraints}")
print(f"Variables: {e.variables}")
print(f"Data URL: {e.get_download_url()}")
```

**Solutions:**

1. **Check time range:**
   ```python
   # Get dataset time coverage
   info = pd.read_csv(e.get_info_url())
   time_start = info[info['Attribute Name'] == 'time_coverage_start']['Value'].values[0]
   time_end = info[info['Attribute Name'] == 'time_coverage_end']['Value'].values[0]
   print(f"Data available: {time_start} to {time_end}")
   ```

2. **Broaden constraints:**
   ```python
   # Remove or relax constraints
   e.constraints = {}  # Get all data
   ```

3. **Test with small query:**
   ```python
   e.constraints = {}
   e.variables = ['precise_time', 'precise_lat', 'precise_lon']
   df = e.to_pandas(nrows=10)  # Just first 10 rows
   print(df.head())
   ```

### Missing or NaN Values

**Problem:** Critical variables contain NaN values

**Solutions:**

1. **Identify extent of missing data:**
   ```python
   print(df.isnull().sum())
   print(f"Total rows: {len(df)}")
   print(f"Complete rows: {len(df.dropna())}")
   ```

2. **Drop rows with critical NaNs:**
   ```python
   # Keep only rows with position and depth
   df_clean = df.dropna(subset=['precise_lon', 'precise_lat', 'depth'])
   ```

3. **Interpolate if appropriate:**
   ```python
   # Linear interpolation for small gaps
   df['temperature'] = df['temperature'].interpolate(method='linear', limit=5)
   ```

4. **Use different variable:**
   ```python
   # If 'precise_lon' is NaN, try 'longitude'
   if 'longitude' in df.columns and df['precise_lon'].isnull().all():
       df['precise_lon'] = df['longitude']
   ```

### Memory Errors

**Problem:** `MemoryError` when processing large datasets

**Solutions:**

1. **Process in chunks:**
   ```python
   # Split time range
   time_ranges = [
       ('2023-01-01T00:00:00Z', '2023-01-15T23:59:59Z'),
       ('2023-01-16T00:00:00Z', '2023-01-31T23:59:59Z'),
   ]
   
   for start, end in time_ranges:
       e.constraints = {'precise_time>=': start, 'precise_time<=': end}
       df = e.to_pandas()
       process_chunk(df)
   ```

2. **Request fewer variables:**
   ```python
   # Process one variable at a time
   for var in dataset.dac_vars:
       e.variables = dataset.dac_timelocdepth + [var]
       df = e.to_pandas()
       make_plots(df, var)
   ```

3. **Increase system memory or use 64-bit Python**

4. **Use data subsampling:**
   ```python
   # Take every Nth data point
   df_subsample = df.iloc[::5, :]  # Every 5th row
   ```

---

## Plotting Issues

### Matplotlib Backend Errors

**Problem:** `RuntimeError: Invalid DISPLAY variable`

**Solutions:**

1. **Use non-interactive backend:**
   ```python
   import matplotlib
   matplotlib.use('Agg')  # Must be before importing pyplot
   import matplotlib.pyplot as plt
   ```

2. **Set in script header:**
   ```python
   #!/usr/bin/env python
   import matplotlib
   matplotlib.use('Agg')
   ```

3. **Configure in matplotlibrc:**
   ```bash
   echo "backend: Agg" > ~/.matplotlib/matplotlibrc
   ```

### Plots Are Blank or Empty

**Problem:** Generated plot files are blank

**Diagnostic:**

```python
import matplotlib.pyplot as plt

# Check if data exists
print(f"Data shape: {data.shape}")
print(f"X range: {data['longitude'].min()} to {data['longitude'].max()}")
print(f"Y range: {data['depth'].min()} to {data['depth'].max()}")
print(f"Z range: {data['temperature'].min()} to {data['temperature'].max()}")

# Test simple plot
plt.figure()
plt.scatter(data['longitude'], data['depth'], c=data['temperature'])
plt.colorbar()
plt.savefig('test_plot.png')
plt.close()
```

**Solutions:**

1. **Check data ranges:**
   ```python
   # Ensure data is within plot limits
   data_filtered = data[
       (data['longitude'] >= lon_limits[0]) &
       (data['longitude'] <= lon_limits[1]) &
       (data['depth'] >= depth_limits[0]) &
       (data['depth'] <= depth_limits[1])
   ]
   ```

2. **Verify variable limits:**
   ```python
   # Check if colorbar limits make sense
   print(f"Variable range: {data['temp'].min():.2f} to {data['temp'].max():.2f}")
   print(f"Colorbar limits: {vmin} to {vmax}")
   ```

3. **Close figures properly:**
   ```python
   plt.savefig('plot.png', dpi=150, bbox_inches='tight')
   plt.close('all')  # Free memory
   ```

### Poor Plot Quality

**Problem:** Plots look pixelated or unclear

**Solutions:**

1. **Increase DPI:**
   ```python
   plt.savefig('plot.png', dpi=300)  # Higher quality
   ```

2. **Adjust figure size:**
   ```python
   plt.figure(figsize=(12, 6))  # Width, height in inches
   ```

3. **Improve interpolation:**
   ```python
   dataset.num_interp_pts = 200  # More interpolation points
   ```

4. **Use vector format for publications:**
   ```python
   plt.savefig('plot.pdf')  # Vector format
   plt.savefig('plot.svg')  # Scalable vector graphics
   ```

---

## Section Detection Problems

### No Sections Detected

**Problem:** `get_min_max` returns only 2 points (start and end)

**Diagnostic:**

```python
import numpy as np
import matplotlib.pyplot as plt

# Plot longitude data
plt.figure(figsize=(12, 4))
plt.plot(lon_data, 'b-')
plt.xlabel('Data point')
plt.ylabel('Longitude')
plt.title('Glider Longitude Path')
plt.grid(True)
plt.savefig('lon_path.png')
plt.close()

# Check data range
print(f"Longitude range: {lon_data.min():.3f} to {lon_data.max():.3f}")
print(f"Longitude span: {lon_data.max() - lon_data.min():.3f}")
print(f"Current tolerance: {tolerance}")
```

**Solutions:**

1. **Lower tolerance:**
   ```python
   # More sensitive to turning points
   tolerance = 0.1  # Try 0.05 to 0.15
   sections = get_min_max(lon_data, Tolerance=tolerance, expPts=exppts)
   ```

2. **Check if glider actually turned:**
   ```python
   # Calculate turning points manually
   diffs = np.diff(lon_data)
   print(f"Max longitude change: {np.max(np.abs(diffs)):.3f}")
   ```

3. **Use latitude if longitude constant:**
   ```python
   # Try latitude-based detection for N-S transects
   sections = get_min_max(lat_data, Tolerance=tolerance, expPts=exppts)
   ```

### Too Many Sections Detected

**Problem:** Excessive sections from minor glider wandering

**Solutions:**

1. **Increase tolerance:**
   ```python
   tolerance = 0.3  # Less sensitive, try 0.25 to 0.40
   sections = get_min_max(lon_data, Tolerance=tolerance, expPts=exppts)
   ```

2. **Filter out small sections:**
   ```python
   # Remove sections with too few points
   min_section_size = 50  # Minimum points per section
   
   filtered_sections = [sections[0]]
   for i in range(1, len(sections)):
       if sections[i] - sections[i-1] >= min_section_size:
           filtered_sections.append(sections[i])
   ```

3. **Smooth data before detection:**
   ```python
   from scipy.signal import savgol_filter
   
   # Smooth longitude data
   lon_smooth = savgol_filter(lon_data, window_length=51, polyorder=3)
   sections = get_min_max(lon_smooth, Tolerance=tolerance, expPts=exppts)
   ```

### Section Detection Crashes

**Problem:** `IndexError` or infinite loop in get_min_max

**Solutions:**

1. **Check for NaN values:**
   ```python
   # Remove NaN before section detection
   valid_idx = ~np.isnan(lon_data)
   lon_clean = lon_data[valid_idx]
   sections = get_min_max(lon_clean, Tolerance=tolerance, expPts=exppts)
   
   # Map back to original indices
   original_indices = np.where(valid_idx)[0]
   sections_original = [original_indices[i] for i in sections]
   ```

2. **Verify input array:**
   ```python
   # Check array properties
   print(f"Array type: {type(lon_data)}")
   print(f"Array shape: {lon_data.shape}")
   print(f"Any NaN: {np.any(np.isnan(lon_data))}")
   print(f"Any Inf: {np.any(np.isinf(lon_data))}")
   ```

3. **Adjust expected points:**
   ```python
   # Set realistic expectation
   exppts = int(len(lon_data) / 100)  # Roughly 100 points per section
   ```

---

## Performance Issues

### Slow Data Retrieval

**Problem:** ERDDAP queries take too long

**Solutions:**

1. **Reduce time range:**
   ```python
   # Process smaller time chunks
   from datetime import datetime, timedelta
   
   start = datetime.strptime(datetime_start, '%Y-%m-%dT%H:%M:%SZ')
   end = start + timedelta(days=7)  # One week at a time
   ```

2. **Request fewer variables:**
   ```python
   # Only get variables you need
   e.variables = ['precise_time', 'precise_lon', 'depth', 'temperature']
   ```

3. **Cache downloaded data:**
   ```python
   import pickle
   import os
   
   cache_file = f'cache_{dataset_id}.pkl'
   
   if os.path.exists(cache_file):
       with open(cache_file, 'rb') as f:
           df = pickle.load(f)
   else:
       df = e.to_pandas()
       with open(cache_file, 'wb') as f:
           pickle.dump(df, f)
   ```

4. **Use parallel processing:**
   ```python
   from multiprocessing import Pool
   
   def process_deployment(dataset):
       # Your processing code
       pass
   
   with Pool(processes=4) as pool:
       results = pool.map(process_deployment, datasets)
   ```

### Slow Plotting

**Problem:** Plot generation is very slow

**Solutions:**

1. **Reduce interpolation points:**
   ```python
   dataset.num_interp_pts = 50  # Lower from 100+
   ```

2. **Subsample dense data:**
   ```python
   # Plot every Nth point if data is very dense
   if len(data) > 10000:
       plot_data = data.iloc[::5, :]  # Every 5th point
   else:
       plot_data = data
   ```

3. **Use faster interpolation:**
   ```python
   from scipy.interpolate import griddata
   
   # Use 'linear' instead of 'cubic'
   grid = griddata(points, values, (grid_x, grid_y), method='linear')
   ```

4. **Close figures promptly:**
   ```python
   import matplotlib.pyplot as plt
   import gc
   
   for section in sections:
       make_plot(section)
       plt.close('all')
       gc.collect()  # Force garbage collection
   ```

---

## Configuration Errors

### Path Not Found

**Problem:** `FileNotFoundError: [Errno 2] No such file or directory`

**Solutions:**

1. **Check path configuration:**
   ```python
   import json
   
   with open('info_jsons/pathdirs.json', 'r') as f:
       paths = json.load(f)
   print(f"Configured output path: {paths['outputdir']}")
   ```

2. **Create missing directories:**
   ```python
   import os
   
   output_path = '/path/to/output'
   os.makedirs(output_path, exist_ok=True)
   ```

3. **Use absolute paths:**
   ```python
   import os
   
   # Convert to absolute path
   basedir = os.path.dirname(os.path.abspath(__file__))
   output_path = os.path.join(basedir, 'output')
   ```

4. **Check permissions:**
   ```bash
   # Linux/Mac
   ls -ld /path/to/directory
   chmod 755 /path/to/directory
   
   # Windows
   # Check folder properties -> Security tab
   ```

### JSON Format Errors

**Problem:** `JSONDecodeError: Expecting value`

**Solutions:**

1. **Validate JSON:**
   ```python
   import json
   
   try:
       with open('config.json', 'r') as f:
           data = json.load(f)
   except json.JSONDecodeError as e:
       print(f"JSON error at line {e.lineno}, column {e.colno}")
       print(f"Error: {e.msg}")
   ```

2. **Check for common issues:**
   - Trailing commas
   - Single quotes instead of double quotes
   - Missing quotes around keys
   - Unescaped special characters

3. **Use JSON validator:**
   - Online: https://jsonlint.com
   - Command line: `python -m json.tool config.json`

4. **Regenerate if corrupted:**
   ```bash
   # Backup and recreate
   mv config.json config.json.bak
   # Create new config.json with correct format
   ```

---

## Common Error Messages

### "erddapy.errors.ERDDAPServerError"

**Cause:** ERDDAP server returned an error

**Check:**
```python
print(e.get_download_url())  # Copy URL and test in browser
```

**Fixes:**
- Verify dataset_id is correct
- Check constraints are valid
- Ensure variables exist in dataset
- Check server status

### "ValueError: arrays must all be same length"

**Cause:** Inconsistent array lengths in data

**Fix:**
```python
# Ensure all arrays same length
min_len = min(len(lon), len(lat), len(depth))
lon = lon[:min_len]
lat = lat[:min_len]
depth = depth[:min_len]
```

### "KeyError: 'precise_lon'"

**Cause:** Expected column not in DataFrame

**Fix:**
```python
# Check available columns
print(df.columns.tolist())

# Use correct column name
if 'longitude' in df.columns:
    df['precise_lon'] = df['longitude']
```

### "TypeError: 'NoneType' object is not subscriptable"

**Cause:** Variable is None when shouldn't be

**Debug:**
```python
# Add checks
if data is None:
    print("ERROR: Data is None!")
    return

if len(data) == 0:
    print("WARNING: Data is empty!")
    return
```

### "Cannot pickle lambda function"

**Cause:** Trying to parallelize code with lambda

**Fix:**
```python
# Use regular function instead of lambda
def process_func(x):
    return x ** 2

# Instead of:
# func = lambda x: x ** 2
```

---

## Getting Help

### Before Asking for Help

1. **Check this guide** for your specific error
2. **Read error messages carefully** - they often indicate the problem
3. **Test with minimal example** to isolate issue
4. **Check package versions** match requirements
5. **Verify installation** is complete and correct

### When Asking for Help

Include:
- **Error message** (full traceback)
- **Code that produces error** (minimal example)
- **Python version**: `python --version`
- **Package versions**: `conda list | grep erddapy`
- **Operating system**
- **What you've already tried**

### Resources

- **Documentation**: README.md, USAGE_GUIDE.md, API_REFERENCE.md
- **ERDDAP docs**: https://coastwatch.pfeg.noaa.gov/erddap/index.html
- **NGDAC**: https://gliders.ioos.us/
- **Package issues**: [GitHub issues page]

---

## Debugging Tools

### Enable Verbose Logging

```python
import logging

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='glider_processing.log'
)

logger = logging.getLogger(__name__)
logger.info("Starting processing...")
```

### Profile Performance

```python
import cProfile
import pstats

profiler = cProfile.Profile()
profiler.enable()

# Your code here

profiler.disable()
stats = pstats.Stats(profiler)
stats.sort_stats('cumulative')
stats.print_stats(20)
```

### Check Memory Usage

```python
import tracemalloc

tracemalloc.start()

# Your code here

current, peak = tracemalloc.get_traced_memory()
print(f"Current memory: {current / 1024**2:.1f} MB")
print(f"Peak memory: {peak / 1024**2:.1f} MB")
tracemalloc.stop()
```

---

## Still Having Issues?

If you've tried solutions in this guide and still have problems:

1. Create a minimal reproducible example
2. Document exactly what happens vs. what you expect
3. Include all error messages
4. Share your configuration (without sensitive data)
5. Contact package maintainers with details

Remember: Most issues have simple solutions. Work through this guide systematically and you'll likely find your answer!
