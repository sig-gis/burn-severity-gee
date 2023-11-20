# burn_severity_gee

This is a tool for generating burn severity maps in Google Earth Engine from inputted fire perimeters. 

## Basic steps to Map Burn Severity:
1. Download Fire Perimeter vector data from a reliable source. 
    * On our latest use of this repository, we used pull_nifc_fires.py, but we also have CLI scripts for CalFIRE and MTBS fire perimeters. 
    * python scripts/pull_nifc_fires.py -y 2023 -a 100 -o C:\path\to\burn-severity-gee
2. Upload those Fire Perimeters to GEE as a FeatureCollection.
3. Use the BS_Mapper ipynb (latest run used BS_Mapper_FF3.ipynb) to produce categorical burn severity ee.Images, plugging the Fire Perimeter ee.FeatureCollection in as the inputs. Then export either to GEE Asset or Google Drive.

![NRT_readme_pic_conus](https://user-images.githubusercontent.com/51868526/162246851-099b789a-7942-4b0f-8989-f62c8386660d.JPG)

## Description 

The tool calculates wildfire burn severities both in ‘historical’ (greater than one year ago) and ‘recent’ (less than one year) situations. The severity scores are categorized into four classes (unburned/low, low, medium, high) based on the relative differenced Normalized Burn Ratio (RdNBR) using thresholds from Miller & Thode (2007).

The fire windows are the date ranges used to create mean Landsat composite images, calculate dNBR for pre and post fire, and subtracted from each other to create the RdNBR which is then classified into the severity categories.
For recent (within one year) fires, we have available three different ways of calculating pre and post fire windows. 

‘Fixed’: the original post-fire window had been defined as a fixed 90-day window starting the day after fire discovery (‘Discovery’). The pre-fire window was bounded by the same days, but the year previous. In the edge cases where 90 days had not elapsed between Discovery and run date, the post-fire window end is cut at the run date. The pre-fire window was created in the previous year based on the nominal post-fire window.

‘Expanding’: A variant where the post-fire window starts the day after Discovery and is of variable length, ending with the run date. The pre-fire window is of the same length, in the previous year. In the edge case of where 90 days had not elapsed between Discovery and run date, the post-fire window end was cut at the run date. The pre-fire window was created in the previous year based on a (minimum) 90-day post-fire window. 

‘Sliding’: A variant where the post-fire window is of 90-days, but slides along to always be the most recent 90-days (to the simulation run date). In the edge cases where 90 days had not elapsed between Discovery and run date, the post-fire window end was cut at the run date. The pre-fire window was created in the previous year based on the nominal post-fire window, same pattern as in‘Fixed’.


## Reference
Miller, J. D., & Thode, A. E. (2007). Quantifying burn severity in a heterogeneous landscape with a relative version of the delta Normalized Burn Ratio (dNBR). Remote sensing of Environment, 109(1), 66-80.


## FireFactor notes
NOTE: This is used in the FireFactor product cycle. Export yearly CONUS-wide BS to ee.Images under this GEE Asset folder: `projects/pyregence-ee/assets/workflow_assets/` and use the base name prefix - BS_[perimetersSource]_[YEAR]. Those ee.Images will be consumed by CLI scripts for FireFactor: [https://github.com/pyregence/firefactor-fuels](https://github.com/pyregence/firefactor-fuels). 