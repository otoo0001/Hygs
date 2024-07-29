This is a repository with example scripts to access observed groundwater parameters.Connect to the database with the sample Query.py script. Tables in the database:
geography_columns
geometry_columns
spatial_ref_sys
_depth_su_tb
_gwh_monthly_tb
_contributors_tb
_gwe_monthly_tb
_gws_yearly_tb
_well_gwe_tb
_well_gwh_tb
_gwh_yearly_tb
_lookup_tb
_well_gws_tb
litho_classes_tb
_gwe_yearly_tb
_gws_monthly_tb
_src_tb
_src_type_tb
_bore_litho_tb
Connection to the database can also be made via SQL viewer softwares such as qgis , arc gis. This is the database connection information:
db_name = 'geowat'
db_user = 'geowat_user'
db_host = 'ages-db01.geo.uu.nl'
db_pass = 'utrecht1994'
db_port = 5432
