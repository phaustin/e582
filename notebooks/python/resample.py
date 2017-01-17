
# coding: utf-8

# ## working with projections
# 
# We have been using [fast_hist](https://clouds.eos.ubc.ca/~phil/courses/eosc582/_modules/e582lib/geolocate.html#fast_hist)
# and [fast_avg](https://clouds.eos.ubc.ca/~phil/courses/eosc582/_modules/e582lib/geolocate.html#fast_avg) to map our MODIS
# level 1b pixels to a uniform lat/lon grid for plotting.  There is one big problem with this approach:
# the actual ground spacing of a uniform longitude grid changes drastically from the equator to the poles, because
# longitude lines converge.   A better approach is to do the following:
# 
# 1) pick a map projection
# 
# 2) define an x,y in grid in meters based on that projection
# 
# 3) resample the satellite data onto that grid
# 
# 4) save it as a geotiff file, which maintains all the information about the projection we used
# 

# ## First, get channel 8 (blue) and the lat/lon files 
# 
# Note that channel 8 is at index 0 in the EV_250_Aggr1km_RefSB dataset
# 
# https://modis.gsfc.nasa.gov/about/specifications.php

# In[1]:

import h5py
from e582lib.geolocate import find_corners
import numpy as np
import pyproj
import pyresample
from pyresample import kd_tree,geometry
from pyresample.plot import area_def2basemap
from matplotlib import pyplot as plt
from e582utils.modismeta_read import parseMeta
from e582utils.data_read import download

data_name='MYD021KM.A2016224.2100.006.2016225153002.h5'
download(data_name)
geom='MYD03.A2016224.2100.006.2016225152335.h5'
download(geom)

index=0
my_name = 'EV_250_Aggr1km_RefSB'
with h5py.File(data_name,'r') as h5_file:
    chan1=h5_file['MODIS_SWATH_Type_L1B']['Data Fields'][my_name][index,:,:]
    scale=h5_file['MODIS_SWATH_Type_L1B']['Data Fields'][my_name].attrs['reflectance_scales'][...]
    offset=h5_file['MODIS_SWATH_Type_L1B']['Data Fields'][my_name].attrs['reflectance_offsets'][...]
chan1_calibrated =(chan1 - offset[index])*scale[index]
    
with h5py.File(geom) as geo_file:
    lon_data=geo_file['MODIS_Swath_Type_GEO']['Geolocation Fields']['Longitude'][...]
    lat_data=geo_file['MODIS_Swath_Type_GEO']['Geolocation Fields']['Latitude'][...]


# ### Next use a new function to get the corner points and the center lat and lon from MODIS metadata
# 
# The function is [parseMeta](https://clouds.eos.ubc.ca/~phil/courses/eosc582/_modules/e582utils/modismeta_read.html#parseMeta) and you
# can treat it as a black box unless you're interested in how regular expressions work in python. It does
# the same thing that [find_corners](https://clouds.eos.ubc.ca/~phil/courses/eosc582/_modules/e582lib/geolocate.html#find_corners) does, but
# skips the calculation, since NASA has already computed everything we need more accurately.

# In[2]:

corners=parseMeta(data_name)
proj_id = 'laea'
datum = 'WGS84'
lat_0 = '{lat_0:5.2f}'.format_map(corners)
lon_0= '{lon_0:5.2f}'.format_map(corners)
lon_bbox = [corners['min_lon'],corners['max_lon']]
lat_bbox = [corners['min_lat'],corners['max_lat']]


# ### 1.  Pick a map projection
# 
# The program that resamples modis data onto a particular projected grid is
# [pyresample](http://pyresample.readthedocs.io/en/latest/index.html).   I'll resample the swath
# using a [lambert azimuthal equal area](http://matplotlib.org/basemap/users/laea.html) projection
# 
# The output will be a 2500 x 2500 array called result which has the channel 1 data resampled onto
# a grid centered at the lat_0,lon_0 center of the swath.  The values will be determined by averaging the nearest
# neighbors to a particular cell location, using a zone of influence with a radius of 5000 meters, and
# a [kd-tree](https://en.wikipedia.org/wiki/K-d_tree)
# 
# The next cell puts the projection into a structure that pyresample understands, and does the resampling

# ### 2. and 3.: define an x,y grid and resample onto it

# In[3]:

area_dict = dict(datum=datum,lat_0=lat_0,lon_0=lon_0,
                proj=proj_id,units='m')
prj=pyproj.Proj(area_dict)
x, y = prj(lon_bbox, lat_bbox)
xsize=2200
ysize=2500
area_id = 'granule'
area_name = 'modis swath 5min granule'
area_extent = (x[0], y[0], x[1], y[1])
area_def = geometry.AreaDefinition(area_id, area_name, proj_id, 
                                   area_dict, xsize,ysize, area_extent)
swath_def = geometry.SwathDefinition(lons=lon_data, lats=lat_data)
result = kd_tree.resample_nearest(swath_def, chan1_calibrated.ravel(),
                                  area_def, radius_of_influence=5000, nprocs=2)
print(area_def)


# ### plot the reprojected image
# 
# pyresample can take its projection structure and turn it into a basemap instance using
# [area_def2basemap](https://github.com/pytroll/pyresample/blob/3fce7fc832e0b86369d452d504a21fb65205435c/pyresample/plot.py#L91)
# 
# This works because both pyresample and basemap use the same underlying projection code called
# [pyproj](https://github.com/jswhit/pyproj).  

# In[4]:

plt.close('all')
fig,ax = plt.subplots(1,1, figsize=(8,8))
bmap=area_def2basemap(area_def,ax=ax,resolution='c')
num_meridians=180
num_parallels = 90
vmin=None; vmax=None
col = bmap.imshow(result, origin='upper', vmin=0, vmax=0.4)
label='channel 1'
bmap.drawmeridians(np.arange(-180, 180, num_meridians),labels=[True,False,False,True])
bmap.drawparallels(np.arange(-90, 90, num_parallels),labels=[False,True,True,False])
bmap.drawcoastlines()
fig.colorbar(col, shrink=0.5, pad=0.05).set_label(label)
fig.canvas.draw()
plt.show()


# ## Why is this image clipped on the right?
# 
# 

# Note that I made a mistake above, in this sequence of commands:
# 
#     x, y = prj(lon_bbox, lat_bbox)
#     xsize=2200
#     ysize=2500
#     area_id = 'granule'
#     area_name = 'modis swath 5min granule'
#     area_extent = (x[0], y[0], x[1], y[1])
#     
# What was my mistake?  I first found the corners in lat/lon coordinates.  Here the are

# In[10]:

lon_bbox,lat_bbox


# This sets the lower left corner at [-141.3,35.1] and the upper right corner at [-103.9, 57.1].  Translated to x,y coordinates this produces the bounding box.   What I needed to do, however is to get the x coordinate of longitude 
# -103.9 deg West at a latitude of 35.1 degrees, not a latitude of 57.1 degrees.  The correct order that does this is:
# 
#     x, y = prj(corners['lon_list'], corners['lat_list'])
#     #
#     # find the corners in map space
#     #
#     minx,maxx=np.min(x),np.max(x)
#     miny,maxy=np.min(y),np.max(y)
#     #
#     # back transform these to lon/lat
#     #
#     llcrnrlon,llcrnrlat=prj(minx,miny,inverse=True)
#     urcrnrlon,urcrnrlat=prj(maxx,maxy,inverse=True)
#     
# That is, I need to find the largest and smallest x and y coordinates, then backtransform those to latitude and longitude, so that the upper right corner uses the y from the upper right corner but the x from the lower right corner to set the map frame.   You can see this in action in resample2.ipynb

# ### 4. Write ths out as a geotiff file
# 
# Here's how to create a tif file that saves all of the projection infomation along with
# the gridded raster image of channel 1

# In[5]:

from osgeo import gdal, osr
raster = gdal.GetDriverByName("GTiff")
gformat = gdal.GDT_Float32
channel=result.astype(np.float32)
opacity=0
fill_value=0
g_opts=[]
height,width=result.shape
tiffile='test.tif'
dst_ds = raster.Create(tiffile,width,height,
                       1,gformat,g_opts)
area=area_def
adfgeotransform = [area.area_extent[0], area.pixel_size_x, 0,
                   area.area_extent[3], 0, -area.pixel_size_y]
dst_ds.SetGeoTransform(adfgeotransform)
srs = osr.SpatialReference()
srs.ImportFromProj4(area.proj4_string)
srs.SetProjCS(area.proj_id)
srs = srs.ExportToWkt()
dst_ds.SetProjection(srs)
dst_ds.GetRasterBand(1).WriteArray(channel)
del dst_ds


# The gdal package has some scripts to dump the details about the tif file and the srs ("spatial reference system")

# In[6]:

get_ipython().system('gdalinfo test.tif')


# In[7]:

get_ipython().system('gdalsrsinfo test.tif')


# ### Read the projection data back in from the tif file using gdal:

# In[8]:

import gdal
from gdalconst import GA_ReadOnly
data = gdal.Open(tiffile, GA_ReadOnly)
geoTransform = data.GetGeoTransform()
minx = geoTransform[0]
maxy = geoTransform[3]
maxx = minx + geoTransform[1] * data.RasterXSize
miny = maxy + geoTransform[5] * data.RasterYSize
print('\nhere are the projected corners of the x,y raster\n{}'.format([minx, miny, maxx, maxy]))
print('\nhere are the attributes of the data instance:\n{}\n'.format(dir(data)))
data = None


# In[ ]:




# In[ ]:



