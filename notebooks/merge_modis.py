
# coding: utf-8

# ### Objective -- move center of image from Seattle to UBC 
# 
# We want to take an image centered on Seattle and move the image center to UBC

# In[1]:

from e582utils.data_read import download

import numpy as np
import h5py
import warnings
from matplotlib import pyplot as plt
from mpl_toolkits.basemap import Basemap
from matplotlib.colors import Normalize
import seaborn as sns
from e582lib.modis_chans import chan_dict
from e582lib.channels_reproject import subsample,find_corners
from e582lib.channels_reproject import resample_channels
from e582lib.map_slices import get_corners_centered, make_basemap_xy,make_xy
import pyproj
from affine import Affine
from rasterio.warp import calculate_default_transform
from rasterio.warp import reproject, Resampling
warnings.filterwarnings("ignore")
from pyresample import kd_tree, geometry
import pyresample


# #### convenience function to take lon,lat to row and column

# In[2]:

def lon_lat_to_row_col(lon,lat,transform,projection):
    x,y=projection(lon,lat)
    col,row = ~transform*(x,y)
    return col,row

projection_dict={'lon_0':-125,'lat_0':40}
projection_dict['datum']='WGS84'
projection_dict['proj'] = 'laea'
projection=pyproj.Proj(projection_dict)
ll_lon,ll_lat,ur_lon,ur_lat= -140,13,-70,51
ll_x,ll_y=projection(ll_lon,ll_lat)
ur_x,ur_y=projection(ur_lon,ur_lat)

area_extent = [ll_x, ll_y, ur_x, ur_y]
xsize=300
ysize=500

area_id='west'
area_name='westcoast'
proj_id='laea'

area_def_args = dict(
    area_id=area_id,
    area_name=area_name,
    proj_id=proj_id,
    area_dict=projection_dict,
    xsize=xsize,
    ysize=ysize,
    area_extent=area_extent)

area_def = geometry.AreaDefinition(area_id, area_name, proj_id, projection_dict,
                                       xsize, ysize, area_extent)


# In[3]:

myd02file="MYD021KM.A2016224.2100.006.2016225153002.h5"
download(myd02file)
myd03file="MYD03.A2016224.2100.006.2016225152335.h5"
download(myd03file)

# In[4]:

def extract_channels(myd02file,myd03file,chan_list):
    reflectivity_list=[]
    for the_chan in chan_list:
        #
        # read channel channels
        #
        index = chan_dict[the_chan]['index']
        field_name = chan_dict[the_chan]['field_name']
        scale_name = chan_dict[the_chan]['scale']
        offset_name = chan_dict[the_chan]['offset']
        with h5py.File(myd02file, 'r') as h5_file:
            chan = h5_file['MODIS_SWATH_Type_L1B']['Data Fields'][field_name][
                index, :, :]
            scale = h5_file['MODIS_SWATH_Type_L1B']['Data Fields'][
                field_name].attrs[scale_name][...]
            offset = h5_file['MODIS_SWATH_Type_L1B']['Data Fields'][
                field_name].attrs[offset_name][...]
            chan_calibrated = (chan - offset[index]) * scale[index]
            chan_calibrated = chan_calibrated.astype(
                np.float32)  #convert from 64 bit to 32bit to save space
            reflectivity_list.append(chan_calibrated)
    with h5py.File(myd03file) as geo_file:
        lon_data = geo_file['MODIS_Swath_Type_GEO']['Geolocation Fields'][
            'Longitude'][...]
        lat_data = geo_file['MODIS_Swath_Type_GEO']['Geolocation Fields'][
            'Latitude'][...]
    return reflectivity_list,lon_data,lat_data

chan_list=['1','2','3','4']
reflectivity_list,lon_data,lat_data=extract_channels(myd02file,myd03file,chan_list)
numchans=len(chan_list)
rows,cols=reflectivity_list[0].shape
chan_array=np.empty([rows,cols,numchans],dtype=np.float32)
for chan in range(numchans):
    chan_array[:,:,chan]=reflectivity_list[chan]

swath_def = geometry.SwathDefinition(lons=lon_data, lats=lat_data)

fill_value = -99999.

channels = kd_tree.resample_nearest(
    swath_def,
    chan_array,
    area_def,
    radius_of_influence=5000,
    nprocs=2,
    fill_value=fill_value)

fill_value = np.array([np.nan], dtype=np.float32)[0]
channels[channels < 0] = fill_value

adfgeotransform = [
    area_def.area_extent[0], area_def.pixel_size_x, 0,
    area_def.area_extent[3], 0, -area_def.pixel_size_y
]
proj4_string = area_def.proj4_string
proj_id = area_def.proj_id
height, width, num_chans = channels.shape
transform = Affine.from_gdal(*adfgeotransform)

#
# add ndvi as a new layer so that channels
# grows to shape= rows x cols x 5
# 
ch1=channels[:,:,0]
ch2=channels[:,:,1]
ndvi=(ch2 - ch1)/(ch2 + ch1)

cmap=sns.diverging_palette(261, 153,sep=6, s=95, l=76,as_cmap=True)
vmin= -0.9
vmax=  0.9
cmap.set_over('r')
cmap.set_under('k',alpha=0.8)
cmap.set_bad('w',alpha=0.1)
the_norm=Normalize(vmin=vmin,vmax=vmax,clip=False)

plt.close('all')
fig,ax = plt.subplots(1,1,figsize=(10,10))
ax.imshow(ndvi,origin='upper',cmap=cmap,norm=the_norm);


myd02file='MYD021KM.A2016224.2055.006.2016225153258.h5'
download(myd02file)
myd03file='MYD03.A2016224.2055.006.2016225152423.h5'
download(myd03file)
reflectivity_list,lon_data,lat_data=extract_channels(myd02file,myd03file,chan_list)
numchans=len(chan_list)
rows,cols=reflectivity_list[0].shape
chan_array=np.empty([rows,cols,numchans],dtype=np.float32)
for chan in range(numchans):
    chan_array[:,:,chan]=reflectivity_list[chan]

swath_def = geometry.SwathDefinition(lons=lon_data, lats=lat_data)

fill_value = -99999.

channels_south = kd_tree.resample_nearest(
    swath_def,
    chan_array,
    area_def,
    radius_of_influence=5000,
    nprocs=2,
    fill_value=fill_value)

fill_value = np.array([np.nan], dtype=np.float32)[0]
channels_south[channels_south < 0] = fill_value

ch1=channels_south[:,:,0]
ch2=channels_south[:,:,1]
ndvi_south=(ch2 - ch1)/(ch2 + ch1)
fig,ax = plt.subplots(1,1,figsize=(10,10))
ax.imshow(ndvi_south,origin='upper',cmap=cmap,norm=the_norm);

south_good_hit=np.logical_and(np.logical_not(np.isnan(ndvi_south)),np.isnan(ndvi))
ndvi[south_good_hit]=ndvi_south[south_good_hit]

fig,ax = plt.subplots(1,1,figsize=(10,10))
ax.imshow(ndvi,origin='upper',cmap=cmap,norm=the_norm);


height, width=ndvi.shape
ll_x,ll_y = transform*(0,height)
ur_x,ur_y = transform*(width,0)
lon_0,lat_0 = projection(0,0,inverse=True)
ll_lon,ll_lat = projection(ll_x,ll_y,inverse=True)
ur_lon,ur_lat = projection(ur_x,ur_y,inverse=True)
ll_lon,ll_lat= -130,17
ur_lon,ur_lat = -90,54
ll_dict=dict(llcrnrlat=ll_lat,llcrnrlon=ll_lon,urcrnrlat=ur_lat,
              urcrnrlon=ur_lon,lon_0=lon_0,lat_0=lat_0)

a, b = pyresample.plot.ellps2axis('wgs84')
rsphere = (a, b)
basemap_args = dict()
basemap_args['rsphere'] = rsphere
basemap_args.update(ll_dict)
basemap_args['projection'] = projection_dict['proj']
basemap_args['lat_0'] = projection_dict['lat_0']
basemap_args['lon_0'] = projection_dict['lon_0']


ndvi_masked=np.ma.masked_invalid(ndvi)
basemap_args['resolution']='c'
bmap=Basemap(**basemap_args)
ur_row=0
ll_row=height
ll_col=0
ur_col=width
xvals,yvals = make_basemap_xy(ur_row,ll_row,ll_col,ur_col,bmap,transform)

fig, ax = plt.subplots(1,1,figsize=(10,10))
ax.pcolormesh(xvals,yvals,ndvi_masked,cmap=cmap,norm=the_norm)

fig, ax = plt.subplots(1,1,figsize=(10,10))
basemap_args['ax']=ax
bmap=Basemap(**basemap_args)
bmap.pcolormesh(xvals,yvals,ndvi_masked,cmap=cmap,norm=the_norm)
bmap.drawcoastlines()
lat_sep,lon_sep= 5, 5
parallels = np.arange(10, 60, lat_sep)
meridians = np.arange(-150,-90, lon_sep)
bmap.drawparallels(parallels, labels=[1, 0, 0, 0],
                        fontsize=10, latmax=90)
bmap.drawmeridians(meridians, labels=[0, 0, 0, 1],
                       fontsize=10, latmax=90);
x0,y0=bmap(lon_0,lat_0)
bmap.plot(x0,y0,'bo',markersize=10)



plt.show()

