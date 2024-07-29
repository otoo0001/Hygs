import geopandas as gpd
import matplotlib.pyplot as plt
import os

# Load the shapefile for wells data
wells_shapefile_path = '/scratch/depfg/otoo0001/data/Daniel_develop/Hygs/shapefile/output/gwh_data_updated.shp'
gdf = gpd.read_file(wells_shapefile_path)

# Load the shapefile for boundary 
boundary_shapefile_path = "/scratch/depfg/otoo0001/data/shapefiles/WB_countries_Admin0_10m/WB_countries_Admin0_10m.shp"  
boundary_gdf = gpd.read_file(boundary_shapefile_path)

# Create a folder to save plots if it doesn't exist
save_folder = '/scratch/depfg/otoo0001/data/Daniel_develop/Hygs/shapefile/output/plots/'
os.makedirs(save_folder, exist_ok=True)

# Function to save and display plots
def save_and_display_plot(fig, title, filename):
    plt.axis('off')  # Turn off x and y axes
    plt.tight_layout()
    plt.savefig(os.path.join(save_folder, filename))
    plt.close(fig)

# Plot 1: Scatter plot of n_years vs. x and y coordinates with boundary
fig1 = plt.figure(figsize=(10, 8))
plt.scatter(gdf['x_wgs84'], gdf['y_wgs84'], c=gdf['n_years'], cmap='viridis', s=20, alpha=0.7)
plt.colorbar(label='Number of years', orientation='horizontal', pad=0.1)
boundary_gdf.plot(ax=plt.gca(), edgecolor='black', linewidth=1, facecolor='none')  # No facecolor for the boundary
save_and_display_plot(fig1, 'Scatter plot of n_years with Boundary', 'scatter_n_years.png')

# Plot 2: Scatter plot of well_weight vs. x and y coordinates with boundary (using legend)
fig2 = plt.figure(figsize=(10, 8))
# Since well_weight ranges from 0 to 1, we use custom markers with labels
for i, weight in enumerate(gdf['weight'].unique()):
    subset = gdf[gdf['weight'] == weight]
    plt.scatter(subset['x_wgs84'], subset['y_wgs84'], label=f'well_weight {weight:.2f}', s=20, alpha=0.7)
plt.legend(title='Well Weight', loc='best')
boundary_gdf.plot(ax=plt.gca(), edgecolor='black', linewidth=1, facecolor='none')  # No facecolor for the boundary
save_and_display_plot(fig2, 'Scatter plot of well_weight with Boundary', 'scatter_well_weight.png')

# Plot 3: Scatter plot of mean_gwh_m vs. x and y coordinates with boundary
fig3 = plt.figure(figsize=(10, 8))
plt.scatter(gdf['x_wgs84'], gdf['y_wgs84'], c=gdf['mean_gwh_m'], cmap='inferno', s=20, alpha=0.7, vmin=-20, vmax=170)
plt.colorbar(label='mean_gwh_m')
boundary_gdf.plot(ax=plt.gca(), edgecolor='black', linewidth=1, facecolor='none')  # No facecolor for the boundary
save_and_display_plot(fig3, 'Scatter plot of mean_gwh_m with Boundary', 'scatter_mean_gwh_m.png')

# Plot 4: Scatter plot of litho_class vs. x and y coordinates with boundary (using legend)
fig4 = plt.figure(figsize=(10, 8))

# Define colors for litho_class
colors = { -1: 'grey', 1: 'tab:blue', 2: 'tab:orange', 3: 'tab:green', 4: 'tab:red' }
legend_labels = { -1: '-1 (Grey)', 1: '1 (Blue)', 2: '2 (Orange)', 3: '3 (Green)', 4: '4 (Red)' }

for litho_class, color in colors.items():
    subset = gdf[gdf['litho_class'] == litho_class]
    plt.scatter(subset['x_wgs84'], subset['y_wgs84'], c=color, label=legend_labels[litho_class], s=20, alpha=0.7)

plt.legend(title='litho_class', loc='best')
boundary_gdf.plot(ax=plt.gca(), edgecolor='black', linewidth=1, facecolor='none')  # No facecolor for the boundary
save_and_display_plot(fig4, 'Scatter plot of litho_class with Boundary', 'scatter_litho_class.png')
