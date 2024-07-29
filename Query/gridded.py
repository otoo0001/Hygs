import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
from scipy import stats
import os
from tqdm import tqdm
import pandas as pd

def calculate_bias(shapefile_path, attribute1, attribute2):
    """
    Calculate the bias (difference) between two attributes in a shapefile.

    Parameters:
    - shapefile_path (str): Path to the input shapefile.
    - attribute1 (str): Name of the first attribute.
    - attribute2 (str): Name of the second attribute.

    Returns:
    - GeoDataFrame: GeoDataFrame with added 'bias' column.
    """
    # Load the shapefile
    gdf = gpd.read_file(shapefile_path)

    # Calculate the bias (difference)
    gdf['bias'] = gdf[attribute1] - gdf[attribute2]

    return gdf

def reclassify_glim_raw(gdf):
    """
    Reclassify 'glim_raw' values in a GeoDataFrame.

    Parameters:
    - gdf (GeoDataFrame): Input GeoDataFrame.

    Returns:
    - GeoDataFrame: GeoDataFrame with added 'reclassified_glim' column.
    """
    gdf['reclassified_glim'] = gdf['glim_raw'].apply(lambda x: 1 if x == 100 else (2 if pd.notnull(x) else -1))
    return gdf

def plot_bias_cdf(bias_values, plot_output_path):
    """
    Plot the cumulative distribution function (CDF) of bias values.

    Parameters:
    - bias_values (numpy array): Array of bias values.
    - plot_output_path (str): Path to save the plot.
    """
    sorted_bias = np.sort(bias_values)
    yvals = np.arange(len(sorted_bias)) / float(len(sorted_bias) - 1)

    plt.figure(figsize=(8, 6))
    plt.plot(sorted_bias, yvals, marker='.', linestyle='none', markersize=3)
    plt.title('Cumulative Distribution Function (CDF) of Bias')
    plt.xlabel('Bias')
    plt.ylabel('Cumulative Probability')
    plt.grid(True)
    plt.tight_layout()

    # Save the plot
    plt.savefig(plot_output_path)
    plt.show()

def main(input_folder, output_folder, shapefile_name, attribute1, attribute2):
    """
    Main function to calculate bias, save results, reclassify 'glim_raw', and plot CDF.

    Parameters:
    - input_folder (str): Path to input folder containing shapefile.
    - output_folder (str): Path to output folder to save results.
    - shapefile_name (str): Name of the shapefile (without extension).
    - attribute1 (str): Name of the first attribute.
    - attribute2 (str): Name of the second attribute.
    """
    # Input shapefile path
    shapefile_path = os.path.join(input_folder, f'{shapefile_name}.shp')

    # Output shapefile path for bias results
    output_shapefile_path = os.path.join(output_folder, f'{shapefile_name}_with_bias_and_reclassified.shp')

    # Output plot path for CDF plot
    plot_output_path = os.path.join(output_folder, f'bias_cdf_{shapefile_name}.png')

    # Calculate bias
    gdf = calculate_bias(shapefile_path, attribute1, attribute2)

    # Reclassify 'glim_raw'
    gdf = reclassify_glim_raw(gdf)

    # Save GeoDataFrame with bias and reclassified 'glim_raw' as a new shapefile
    gdf.to_file(output_shapefile_path)

    # Plot CDF of bias values
    plot_bias_cdf(gdf['bias'].values, plot_output_path)

if __name__ == '__main__':
    # Define input and output folders
    input_folder = '/scratch/depfg/otoo0001/data/Daniel_develop/Hygs/shapefile/output/new/'
    output_folder = '/scratch/depfg/otoo0001/data/Daniel_develop/Hygs/shapefile/output/plots/'

    # Define shapefile name and attributes
    shapefile_name = 'gw_data_'  # Exclude extension (.shp)
    attribute1 = 'mean_gwh_m'  # Replace with your attribute name
    attribute2 = 'sim_gw_mea'  # Replace with your attribute name

    # Call main function
    main(input_folder, output_folder, shapefile_name, attribute1, attribute2)
