- Interactive Hydrometric Stations Map
  
  This script generates an interactive map (using folium) of hydrometric stations using location data and water level time series.

- Each station appears on the map with:

  basic station information
  
  percentage of missing data
  
  a plot of recent water levels (last 3 years, you can change it on PLOT_DAYS)
  The final map is saved as an HTML file

- Required Data
Two CSV files are needed:

    stations.csv — station metadata (coordinates, type, code, etc.)
  
    water_levels.csv — water level time series (one column per station)

- Usage
  
    Place the files in the dataset/ folder
  
    Adjust file paths if needed
  
    Run 
