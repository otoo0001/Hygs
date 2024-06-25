"""
    In this script you can check some exampled how to:
        -   connect to a postgresql database on the UU server
        -   select data from the database based on different conditions
        -   perfom spatial queries
"""

#   first import some python libraries
import psycopg2     #   this is the most important one, used to perform all the SQL commands
import pandas as pd
import geopandas as gpd
import rasterio

#   now define the database information for connecting, this is a read-only account so you wont be able to change anything
#   also you have to be in the UU domain - so either sitting in the office or use VPN to connect to UU network..
db_name = 'geowat'
db_user = 'geowat_user'
db_host = 'ages-db01.geo.uu.nl'
db_pass = 'utrecht1994'
db_port = 5432

#   lets connect to the database now! create a connection string and then use psycopg to connect
#   Note: if you perform a wrong SQL query or anything that throws back an error the cursor closes and then you need
#         to make a new database connection.
conn_string = str("dbname=%s port=%s user=%s host=%s password=%s") % (db_name, db_port, db_user, db_host, db_pass)
conn = psycopg2.connect(conn_string)
#   set the cursor, this we will use for navigating the database tables, rows etc..
cur = conn.cursor()

#   to avoid that we can just make a simple function that we can use to connect to the database
def connect_to_dtbase(dbname, dbuser, dbhost, dbpass, dbport):
    #   create connection string
    connstring = str("dbname=%s port=%s user=%s host=%s password=%s") % (dbname, dbport, dbuser, dbhost, dbpass)
    connection = psycopg2.connect(connstring)
    print("Successfully connected to database : " + str(dbname))
    #   set the cursor and return both
    cursor = connection.cursor()
    return connection, cursor


"""     --------------------------------------------------------------------------------------------------
                    Some Python and SQL coding examples 
        --------------------------------------------------------------------------------------------------     """

#   Lets try to get some data from the database, the process is quite simple, first we connec to the database,
#   then we define our SQL command, run the SQL command and retrieve the results.
#   Let's say we want to get all the rows/records from the _lookup_tb for Afghanistan, so we select all columns (*) from
#   the lookup_tb - we have to specify a schema that the table is in (dont worry about this..) which is called gerbil
#   for some reason (my brain) so the table full name is gerbil._lookup_tb, finally we specify the condition so
#   we just say the that column country_name has to be equal to Afghanistan

#   First connect to the database
db_con, db_cur = connect_to_dtbase(db_name, db_user, db_host, db_pass, db_port)

#   Now make an SQL query to find all rows in the _lookup_tb (gerbil is the name of the database schema.. not important
#   for now its just a technical thing) where the column country_name contains Afghanistan. You can of course query
#   the data however you want based on multiple columns etc..
sql_cmd = "SELECT * FROM gerbil._lookup_tb WHERE country_name = '%s'" % 'Afghanistan'
db_cur.execute(sql_cmd)
dbase_ids_sql = db_cur.fetchall()

#   lets see what we got
print(dbase_ids_sql)

#   would be a good idea to add the column names to the output dataframe as well
db_con, db_cur = connect_to_dtbase(db_name, db_user, db_host, db_pass, db_port)
sql_cmd = "SELECT * FROM gerbil._lookup_tb"
db_cur.execute(sql_cmd)

# Extract the column names
col_names = []
for elt in db_cur.description:
    col_names.append(elt[0])

#   we can also make a dataframe out of it.. then you can export it as csv or whatever (geo)pandas output format you want
df = pd.DataFrame(dbase_ids_sql, columns = col_names)


#   Now lets try something more complicated and extract some groundwater well data. We will try to get total average
#   groundwater level (in meters below surface level) for all the wells in the database. Additional information will be
#   the amount of yearly average measurements, x and y coordinates, ID number (both original and gerbil), and source
#   of surface elevation measurmenet - either original from the IGRAC dbase or GLO_90m_DEM, and lithology type - we will
#   add that in the end by extracting values from a raster..

#   Make new connection to the database
db_con, db_cur = connect_to_dtbase(db_name, db_user, db_host, db_pass, db_port)

#   First lets grap all the rows from the table that contains yearly groundwater head data - that will be the
#   in the _gwh_yearly_tb table
sql_cmd = "SELECT * FROM gerbil._gwh_yearly_tb"
db_cur.execute(sql_cmd)
gwh_yearly = db_cur.fetchall()

#   Extract the column names
col_names = []
for elt in db_cur.description:
    col_names.append(elt[0])

#   Lets make a datafram out of the database, some further post-processing is easier in (geo)pandas..
df_raw = pd.DataFrame(gwh_yearly, columns = col_names)

#   To get the mean GWH value lets just use the groupby function in pandas and group the rows by id_gerbil
df_raw['mean_gwh_mbsl'] = df_raw.groupby('id_gerbil')['gw_head_m'].transform('mean')

#   The raw data are in centimeters (it takes less space to store integer values in the database..)
#   so transform from centimeters to meters
df_raw['mean_gwh_mbsl'] = df_raw['mean_gwh_mbsl'].round(0) / 100.

#   Now lets get the number of yearly measurements for each well
df_raw['n_years'] = df_raw.groupby('id_gerbil')['year'].transform('size')

#   Finally we can now trim the dataframe to only get one row per well (id_gerbil)
df_gwh = df_raw.drop_duplicates(subset = 'id_gerbil', keep = "last")

#   We can also drop the redundant columns now, no need to keep the year and gwh_head_m columns from the raw data
df_gwh = df_gwh.drop(columns=['year', 'gw_head_m'])

#   The rest of the information we want to include in our dataframe output is stored in another table - the _lookup_tb.
#   First we can just get all the rows from the lookup_tb and then use pandas to join with the previous dataframe.
sql_cmd = "SELECT id_gerbil, id_orig_src, x_wgs84, y_wgs84, orig_elev_m_asl, glo90_elev_m_asl FROM gerbil._lookup_tb"
db_cur.execute(sql_cmd)
lookup_vals = db_cur.fetchall()

#   Extract the column names
col_names = []
for elt in db_cur.description:
    col_names.append(elt[0])

#   Make a dataframe from the values
df_lookup = pd.DataFrame(lookup_vals, columns = col_names)

#   We can now join the two dataframes by matching ID_gerbil values and in that way we will have all the columns we needed
df_out = pd.merge(df_gwh, df_lookup, on = 'id_gerbil').drop_duplicates().reset_index(drop = True)

#   Finally we can export the dataframe as a shapefile, first make it a geodataframe
geometry = gpd.points_from_xy(df_out.x_wgs84, df_out.y_wgs84, crs = "EPSG:4326")
gdf = gpd.GeoDataFrame(df_out, geometry = geometry)

#   Well not finally.. still have to add the lithology information, i will put the reclassified raster on yoda
#   with the same name as the one below
glim_dir = r'g:\_ORIGINAL_DATA\GLIM\glim_world2_wb.tif'

#   get the elevation values (rounded up to 2 decimal points from the DEM tile)
glim_raw_lst = []
coord_lst = list(zip(gdf.x_wgs84, gdf.y_wgs84))
with rasterio.open(glim_dir, 'r') as src:
    for val in src.sample(coord_lst):
        #print(val[0])
        glim_raw_lst.append(int(val[0]))

#   The reclassification key is in the dictionary below.. nevermind the color and hatch that is for plotting (for other scripts)
litho_class_styles = {'su': {'lith' : 'su', 'lith_full' : 'unconsolidated sediments', 'lith_num' : 100, 'hatch': '', 'color': 'gold'},
                      'su_ad': {'lith' : 'su_ad', 'lith_full' : 'alluvial deposits', 'lith_num' : 101, 'hatch': '-.', 'color': '#ffd757'},
                      'su_ds': {'lith' : 'su_ds', 'lith_full' : 'dune sands', 'lith_num' : 102, 'hatch': '-.', 'color': '#fcc100'},
                      'su_lo': {'lith' : 'su_lo', 'lith_full' : 'loess', 'lith_num' : 103, 'hatch': '-.', 'color': '#8a6a00'},
                      'su_mx': {'lith' : 'su_mx', 'lith_full' : 'sand - mixed grain size', 'lith_num' : 104, 'hatch': 'O', 'color': '#ffd95f'},
                      'su_ss': {'lith' : 'su_ss', 'lith_full' : 'sand - coarse grained', 'lith_num' : 105, 'hatch': 'o', 'color': '#ffd95f'},
                      'su_sh': {'lith' : 'su_sh', 'lith_full' : 'sand - fine grained', 'lith_num' : 106, 'hatch': '.', 'color': '#ffd95f'},
                      'su_cl': {'lith' : 'su_cl', 'lith_full' : 'clay', 'lith_num' : 107, 'hatch': '.', 'color': 'grey'},
                      'su_gr': {'lith' : 'su_gr', 'lith_full' : 'gravel', 'lith_num' : 108, 'hatch': 'o', 'color': 'olivedrab'},
                      'su_sl': {'lith' : 'su_sl', 'lith_full' : 'silt', 'lith_num' : 109, 'hatch': '..', 'color': 'lawngreen'},
                      'ss': {'lith' : 'ss', 'lith_full' : 'siliclastic sedimentary rocks', 'lith_num' : 200, 'hatch': 'o-', 'color': 'forestgreen'},
                      'sm': {'lith' : 'sm', 'lith_full' : 'mixed sedimentary rocks', 'lith_num' : 210, 'hatch': 'o-', 'color': 'turquoise'},
                      'sc': {'lith' : 'sc', 'lith_full' : 'carbonate sedimentary rocks', 'lith_num' : 220, 'hatch': 'o-', 'color': 'aqua'},
                      'vb': {'lith' : 'vb', 'lith_full' : 'basic volcanic rocks', 'lith_num' : 300, 'hatch': 'o', 'color': 'darkorange'},
                      'vi': {'lith' : 'vi', 'lith_full' : 'intermediate volcanic rocks', 'lith_num' : 310, 'hatch': 'O', 'color': 'darkorange'},
                      'va': {'lith' : 'va', 'lith_full' : 'acid volcanic rocks', 'lith_num' : 320, 'hatch': 'oo', 'color': 'darkorange'},
                      'pb': {'lith' : 'pb', 'lith_full' : 'basic plutonic rocks', 'lith_num' : 400, 'hatch': 'o', 'color': 'fuchsia'},
                      'pi': {'lith' : 'pi', 'lith_full' : 'intermediate plutonic rocks', 'lith_num' : 410, 'hatch': 'O', 'color': 'fuchsia'},
                      'pa': {'lith' : 'pa', 'lith_full' : 'acid plutonic rocks', 'lith_num' : 420, 'hatch': 'oo', 'color': 'fuchsia'},
                      'mt': {'lith' : 'mt', 'lith_full' : 'metamorphic rocks', 'lith_num' : 500, 'hatch': '-|', 'color': 'plum'},
                      'py': {'lith' : 'py', 'lith_full' : 'pyroclastics', 'lith_num' : 600, 'hatch': 'x', 'color': 'crimson'},
                      'ev': {'lith' : 'ev', 'lith_full' : 'evaporites', 'lith_num' : 700, 'hatch': 'o', 'color': 'darkorchid'},
                      'rock': {'lith' : 'rock', 'lith_full' : 'rocks', 'lith_num' : 800, 'hatch': '++', 'color': 'dimgrey'},
                      'soil': {'lith' : 'soil', 'lith_full' : 'soil', 'lith_num' : 900, 'hatch': 'o', 'color': 'tan'},
                      'coal': {'lith' : 'coal', 'lith_full' : 'coal', 'lith_num' : 1000, 'hatch': '-|', 'color': 'black'},
                      'nd': {'lith' : 'nd', 'lith_full' : 'not defined', 'lith_num' : 0, 'hatch': 'x', 'color': 'snow'}}

#   For this case we are interested only in 4 classes - Unconsolidated sediments fine (1) and coarse (2), sedimentary rocks (3) and rocks (4).
#   We will also add fifth one which is not-defined or no data (-1). But first add a column to the geodataframe.
gdf['glim_raw'] = glim_raw_lst

#   Now we can reclassify the column into our 5 categories, create new column first, set all values to NaN
gdf['litho_class'] = -1
gdf.loc[gdf['glim_raw'].isin([100, 101, 102, 104, 108, 900]), 'litho_class'] = 1
gdf.loc[gdf['glim_raw'].isin([103, 105, 106, 107, 109]), 'litho_class'] = 2
gdf.loc[gdf['glim_raw'].between(199, 299), 'litho_class'] = 3
gdf.loc[gdf['glim_raw'].between(299, 801), 'litho_class'] = 4

#   Now we can finally export the geodataframe to shapefile
gdf.to_file(r'\scratch\depfg\otoo0001\data\_HyGS\_database\_output\_gwh_mean.shp', driver = 'ESRI Shapefile')