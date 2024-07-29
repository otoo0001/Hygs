import geopandas as gpd
import numpy as np
from scipy.spatial import cKDTree
from tqdm import tqdm
import os

# Load the shapefile and specify the CRS
shapefile_path = '/scratch/depfg/otoo0001/data/Daniel_develop/Hygs/shapefile/'
gdf = gpd.read_file(shapefile_path, crs='EPSG:4326')  # Assuming WGS84 (EPSG:4326)

# Function to check and fix invalid geometries
def check_and_fix_invalid_geometries(gdf):
    if not gdf.empty and not gdf.is_valid.all():
        # Attempt to fix invalid geometries
        gdf = gdf[gdf.is_valid]  # Remove invalid geometries
        gdf.reset_index(drop=True, inplace=True)  # Reset index after dropping rows
    
    return gdf

# Check and fix invalid geometries
gdf = check_and_fix_invalid_geometries(gdf)

# Function to calculate the declustering rate using cKDTree
def calculate_dcl_rate_cdkTree(gdf):
    try:
        # Create an array of coordinates (assuming WGS84)
        coords = np.vstack((gdf['x_wgs84'], gdf['y_wgs84'])).T
        
        # Build a cKDTree for efficient nearest neighbor search
        tree = cKDTree(coords)
        
        # Query the tree for the distance to the second nearest neighbor (k=2)
        # Set min_distance to avoid self-matching issues
        min_distance = 1e-6
        distances, _ = tree.query(coords, k=2, distance_upper_bound=np.inf)
        
        # Replace infinite distances with a large value
        distances[np.isinf(distances)] = 1e6
        
        # Assign the second nearest distance as the declustering rate
        gdf['dcl_rate'] = distances[:, 1]
        
    except Exception as e:
        raise ValueError(f"Error calculating declustering rate: {str(e)}")
    
    return gdf

# Apply the declustering rate calculation to the GeoDataFrame with progress bar
print("Calculating declustering rate...")
try:
    gdf = calculate_dcl_rate_cdkTree(gdf)
except ValueError as ve:
    print(f"Error: {ve}")

# Check if GeoDataFrame is not empty before normalizing
if not gdf.empty:
    # Normalize the declustering rate (dcl_rate)
    if 'dcl_rate' not in gdf.columns:
        raise ValueError("Column 'dcl_rate' is required for normalization.")
    
    min_dcl_rate = gdf['dcl_rate'].min()
    max_dcl_rate = gdf['dcl_rate'].max()
    gdf['dcl_rate'] = (gdf['dcl_rate'] - min_dcl_rate) / (max_dcl_rate - min_dcl_rate)
    
    # Calculate the well weight for each row using normalized dcl_rate
    # Well weight formula: (dcl_rate + n_years) / sum(dcl_rate + n_years for all wells)
    print("Calculating well weights...")
    if 'dcl_rate' not in gdf.columns or 'n_years' not in gdf.columns:
        raise ValueError("Columns 'dcl_rate' and 'n_years' are required for calculating well weights.")
    total_weight = np.sum(gdf['dcl_rate'] + gdf['n_years'])
    gdf['weight'] = (gdf['dcl_rate'] + gdf['n_years']) / total_weight
    
    # Normalize the well weight
    min_weight = gdf['weight'].min()
    max_weight = gdf['weight'].max()
    gdf['weight'] = (gdf['weight'] - min_weight) / (max_weight - min_weight)
    
    # Specify the save folder
    save_folder = '/scratch/depfg/otoo0001/data/Daniel_develop/Hygs/shapefile/output/'
    os.makedirs(save_folder, exist_ok=True)  # Create the folder if it doesn't exist
    
    # Save the updated GeoDataFrame to a new shapefile with progress bar
    output_path = os.path.join(save_folder, 'gwh_data_updated.shp')
    print("Saving updated shapefile...")
    with tqdm(total=len(gdf)) as pbar:
        gdf.to_file(output_path)
        pbar.update()

    print(f"Process complete. Shapefile '{output_path}' created with the necessary declustering rate and normalized well weight data.")
else:
    print("Error: GeoDataFrame is empty after cleaning invalid geometries.")
