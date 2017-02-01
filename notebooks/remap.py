
# coding: utf-8

# # Zoom the satellite_ndvi image to a 5 degree bounding box
# 
# * write a new version of modisl1b_reproject called channels_reprojet
# 
# * write a new subsample function to clip to the bounding box
# 
# * write a new find_corners function to find the box corners of the clipped arrays
# 
# * use the %matplotlib notebook backend to pan and zoom

# In[1]:

from e582utils.data_read import download

import numpy as np
import h5py
import sys
import warnings
from matplotlib import pyplot as plt
from IPython.display import Image
from mpl_toolkits.basemap import Basemap
from matplotlib.colors import Normalize
import matplotlib
import matplotlib.cm as cm
import seaborn as sns
from e582lib.modis_chans import chan_dict
from e582lib.channels_reproject import subsample,find_corners
from e582lib.channels_reproject import resample_channels,write_h5
from e582lib.geolocate import xy_to_col_row,col_row_to_xy
import pyproj
from affine import Affine
import rasterio
import warnings
warnings.filterwarnings("ignore")

get_ipython().magic('matplotlib inline')
myd02file="MYD021KM.A2016224.2100.006.2016225153002.h5"
download(myd02file)


# In[2]:

Image('figures/MYBRGB.A2016224.2100.006.2016237025650.jpg')


# In[3]:

myd03file="MYD03.A2016224.2100.006.2016225152335.h5"
download(myd03file)


# ### Calibrate and resample the channel 1 and channel 2 reflectivities
# 
# 

# In[4]:

chan_list=['1','2','3','4']
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
    #            


# In[5]:

llcrnr=dict(lat=40,lon= -130)
urcrnr=dict(lat=55,lon= -115)
subsample_list=subsample(*reflectivity_list,lats=lat_data,lons=lon_data,llcrnr=llcrnr,urcrnr=urcrnr)
lats,lons=subsample_list[:2]
numchans=len(subsample_list) -2
rows,cols=lats.shape
chan_array=np.empty([rows,cols,numchans],dtype=np.float32)
for chan in range(numchans):
    chan_array[:,:,chan]=subsample_list[chan+2]
corner_dict=find_corners(subsample_list[0],subsample_list[1])
corner_dict


# In[6]:

from e582lib.channels_reproject import resample_channels
chan_list=['1','2','3','4']
result_dict=       resample_channels(chan_array,lats,lons,corner_dict)
lon_0,lat_0=result_dict['basemap_args']['lon_0'],result_dict['basemap_args']['lat_0']
ch1 = result_dict['channels'][:,:,0][...]
ch2= result_dict['channels'][:,:,1][...]
ndvi = (ch2 - ch1)/(ch2 + ch1)


# In[7]:

def make_basemap_xy(width,height,bmap,transform):
    xline=np.empty([width,],dtype=np.float32)
    yline=np.empty([height,],dtype=np.float32)
    for the_col in range(width):
        xline[the_col],y = transform*(the_col,0)
    for the_row in range(height):
        x,yline[the_row]= transform*(0,the_row)
    xline = xline + bmap.projparams['x_0']
    yline = yline + bmap.projparams['y_0']
    xvals, yvals = np.meshgrid(xline,yline)
    return xvals,yvals

def get_slice(width,height,transform):
    """
    return row and column slices centered around
    lon_0, lat_0
    
    """
    col_0,row_0 = ~transform*(0,0)
    col_slice=slice(int(col_0 - width/2.),int(col_0 + width/2.))
    row_slice=slice(int(row_0 - width/2.),int(row_0 + width/2.))
    return col_slice,row_slice


# In[8]:

projection ={'datum': 'WGS84', 'lat_0': lat_0, 'lon_0': lon_0, 'proj': 'laea', 'units': 'm'}
src_proj=pyproj.Proj(projection)
basemape_args={'lat_0': 47.011089324951172,
     'lon_0': -124.88102722167969,
     'projection': 'laea',
     'rsphere': (6378137.0, 6356752.314245179),
     'width':200000,
      'height':300000}
geotiff_args = result_dict['geotiff_args']
src_transform = Affine.from_gdal(*geotiff_args['adfgeotransform'])


# In[16]:

cmap=sns.diverging_palette(261, 153,sep=6, s=85, l=66,as_cmap=True)
vmin= -0.9
vmax=  0.9
cmap.set_over('c')
cmap.set_under('k',alpha=0.8)
cmap.set_bad('k',alpha=0.1)
the_norm=Normalize(vmin=vmin,vmax=vmax,clip=False)
slice_x,slice_y=get_slice(800,900,src_transform)
slice_x,slice_y


# In[17]:

plt.close('all')
fig, ax = plt.subplots(1,1,figsize=(14,14))
basemap_args=result_dict['basemap_args']
basemap_args['ax']=ax
basemap_args['resolution']='c'
basemap_args['width'] = 10000
basemap_args['height']=10000
bmap=Basemap(**basemap_args)
height, width = ndvi.shape
xvals,yvals = make_basemap_xy(width, height,bmap,src_transform)
bmap.drawcoastlines()
bmap.pcolormesh(xvals[slice_x,slice_y],yvals[slice_x,slice_y],
                ndvi[slice_x,slice_y],cmap=cmap,norm=the_norm)
ll_x,ur_x=xvals[slice_x,slice_y][-1,0],xvals[slice_x,slice_y][0,-1]
ll_y,ur_y =yvals[slice_x,slice_y][-1,0],yvals[slice_x,slice_y][0,-1]
bmap.ax.set_xlim(ll_x,ur_x)
bmap.ax.set_ylim(ur_y,ll_y);
lat_sep,lon_sep= 0.2, 0.2
parallels = np.arange(46, 51, lat_sep)
meridians = np.arange(-125,-121, lon_sep)
bmap.drawparallels(parallels, labels=[1, 0, 0, 0],
                        fontsize=10, latmax=90)
bmap.drawmeridians(meridians, labels=[0, 0, 0, 1],
                       fontsize=10, latmax=90);


# In[ ]:

src_crs={'datum': 'WGS84', 'lat_0': 47.4599990844727, 'lon_0': -122.7804641723633, 'proj': 'laea', 'units': 'm'}


# In[ ]:

result_dict.keys()


# ### write out a geotiff file for the ndvi using rasterio

# In[ ]:

from affine import Affine
import rasterio
geotiff_args = result_dict['geotiff_args']
transform = Affine.from_gdal(*geotiff_args['adfgeotransform'])
crs = geotiff_args['proj4_string']
fill_value=result_dict['fill_value']
ndvi = channels[:,:,4]
data_type = ndvi.dtype
height, width = ndvi.shape
print('ndvi.shape: {}'.format(ndvi.shape))
lat_0=result_dict['basemap_args']['lat_0']
lon_0=result_dict['basemap_args']['lon_0']
old_proj=pyproj.Proj(result_dict['geotiff_args']['proj4_string'])
x0, y0 = the_proj(lon_0,lat_0)
print('x0, y0: {}'.format((x0,y0)))
col0, row0 = xy_to_col_row(x0,y0,geotiff_args['adfgeotransform'])
print('col0, row0: {}'.format((col0, row0)))
x0_a, y0_a = col_row_to_xy(col0, row0,geotiff_args['adfgeotransform'])
print('roundtrip x0, y0: {}'.format((x0_a,y0_a)))
row_rot
corner_x
corner_y
colcrnr, rowcrnr = xy_to_col_row(corner_x,corner_y,geotiff_args['adfgeotransform'])
print('col, row for corner {}'.format((colcrnr,rowcrnr)))
tryx, tryy=col_row_to_xy(col0,row0,geotiff_args['adfgeotransform'])  
(tryx, tryy)


# In[ ]:

from affine import Affine
a_trans=Affine.from_gdal(*geotiff_args['adfgeotransform'])
x0_b, y0_b = a_trans*(col0,row0)
col0_b, row0_b = ~a_trans*(x0_b,y0_b)
print(((col0_b, row0_b),(col0,row0)))
print(((x0, y0),(x0_b,y0_b)))


# In[ ]:

fig,ax=plt.subplots(1,1,figsize=(12,12))
ax.imshow(ndvi)


# In[ ]:

cmap=sns.diverging_palette(261, 153,sep=6, s=85, l=66,as_cmap=True)
vmin= -0.9
vmax=  0.9
cmap.set_over('c')
cmap.set_under('k',alpha=0.8)
cmap.set_bad('k',alpha=0.1)
the_norm=Normalize(vmin=vmin,vmax=vmax,clip=False)


# In[ ]:

geotiff_args['adfgeotransform']
result_dict['basemap_args']


# In[ ]:

def make_basemap_xy(width,height,bmap,transform):
    xline=np.empty([width,],dtype=np.float32)
    yline=np.empty([height,],dtype=np.float32)
    for the_col in range(cols):
        xline[the_col],y = transform*(the_col,0)
    for the_row in range(rows):
        x,yline[the_row]= transform*(0,the_row)
    xvals, yvals = np.meshgrid(xline,yline)
    retun xvals,yvals
    


# In[ ]:

# plt.close('all')
# fig, ax = plt.subplots(1,1,figsize=(14,14))
basemap_args=result_dict['basemap_args']
basemap_args['ax'] = ax
basemap_args['resolution']='c'
bmap = Basemap(**basemap_args)
top_row=np.arange(ll_col,ur_col,dtype=np.int)
left_col=np.arange(ur_row,ll_row,dtype=np.int)



xline=np.empty(top_row.shape,dtype=np.float)
yline=np.empty(left_col.shape,dtype=np.float)
for index,colnum in enumerate(top_row):
    x,y=col_row_to_xy(colnum,ur_row,geotiff_args['adfgeotransform'])
    xline[index] = x
for index,rownum in enumerate(left_col):
    x,y=col_row_to_xy(ll_col,rownum,geotiff_args['adfgeotransform'])
    yline[index]=y
xline = xline + bmap.projparams['x_0']
yline = yline + bmap.projparams['y_0']
xvals, yvals = np.meshgrid(xline,yline)
xvals.shape
# col=bmap.pcolormesh(xvals,yvals,ndvi_zoom,cmap=cmap,norm=the_norm)
# colorbar=bmap.ax.figure.colorbar(col, shrink=0.5, pad=0.05,extend='both')
# bmap.ax.set_xlim(xline[0],xline[-1])
# bmap.ax.set_ylim(yline[-1],yline[0]);
# bmap.drawcoastlines();
# bmap.drawrivers();
xvals_a, yvals_a = xvals - bmap.projparams['x_0'], yvals - bmap.projparams['y_0']
xcent,ycent=xvals_a[50,50],yvals_a[50,50]
cent_lon,cent_lat = the_proj(xcent,ycent,inverse=True)
print('new: ',cent_lon, cent_lat)
print('old: ',lon_0,lat_0)
ll_x, ll_y = col_row_to_xy(0,height,geotiff_args['adfgeotransform'])
ur_x, ur_y =  col_row_to_xy(width,0,geotiff_args['adfgeotransform'])
ll_x, ll_y = a_trans*(0,height)
ur_x, ur_y = a_trans*(width,0)
print(ll_x, ll_y, ur_x, ur_y)


# In[ ]:

ndvi.shape


# In[ ]:

src_crs={'datum': 'WGS84', 'lat_0': 47.4599990844727, 'lon_0': -122.7804641723633, 'proj': 'laea', 'units': 'm'}
import os
os.environ['CHECK_WITH_INVERT_PROJ']='YES'


# In[ ]:

print(os.environ['CHECK_WITH_INVERT_PROJ'])


# In[ ]:

from rasterio.warp import calculate_default_transform, reproject
dest_crs={'datum': 'WGS84', 'lat_0': cent_lat, 'lon_0': cent_lon, 'proj': 'laea', 'units': 'm'}
height, width = ndvi.shape
resolution = 1300.,1300.
transform_out, new_width, new_height = calculate_default_transform(src_crs, dest_crs, 
                                          width, height, left=ll_x, bottom= ll_y, right = ur_x, 
                                          top=ur_y,resolution=resolution)
new_ndvi = np.empty([new_height, new_width],dtype=np.float32)
fill_value = result_dict['fill_value']
out = reproject(ndvi,new_ndvi,src_transform=a_trans,src_crs=src_crs,src_nodata=fill_value,
               dst_transform=transform_out,dest_crs=dest_crs)
fig,ax=plt.subplots(1,1,figsize=(12,12))
ax.imshow(new_ndvi)
new_proj = pyproj.Proj(dest_crs)
new_proj(0,0,inverse=True)
col,row = ~transform_out*(0,0)
print(col,row)
x, y = transform_out*(col,row)
lon, lat = new_proj(x,y,inverse=True)
print(lon,lat, x,y, col,row)
rows, cols = new_ndvi.shape
xline = np.empty([cols,],dtype=np.float32)
yline = np.empty([rows,],dtype=np.float32)
for the_col in range(cols):
    xline[the_col],y = transform_out*(the_col,0)
for the_row in range(rows):
    x,yline[the_row]= transform_out*(0,the_row)
xvals, yvals = np.meshgrid(xline,yline)


# In[ ]:

cmap=sns.diverging_palette(261, 153,sep=6, s=85, l=66,as_cmap=True)
vmin= -0.9
vmax=  0.9
cmap.set_over('c')
cmap.set_under('k',alpha=0.8)
cmap.set_bad('k',alpha=0.1)
the_norm=Normalize(vmin=vmin,vmax=vmax,clip=False)
fig,ax =plt.subplots(1,1,figsize=(12,12))
ax.pcolormesh(xvals,yvals,new_ndvi,cmap=cmap,norm=the_norm)
print(len(xvals))
print(len(yvals))
new_ndvi.shape


# In[ ]:

type(result_dict['fill_value'])


# In[ ]:

new_ndvi.shape


# In[ ]:

new_width


# In[ ]:

new_height


# In[ ]:

dest_crs


# In[ ]:

the_proj=pyproj.Proj(dest_crs)
the_proj(0,0,inverse=True)


# In[ ]:

xcent, yxent = the_proj(dest_crs['lon_0'],dest_crs['lat_0'])
xcent,ycent


# In[ ]:

crs ={'datum': 'WGS84',
 'lat_0': 49.01958255897051,
 'lon_0': -123.20382170970784,
 'proj': 'laea',
 'units': 'm'}
proj=pyproj.Proj(crs)
proj(-123.20382170970784, 49.01958255897051)


# In[ ]:

fig,ax = plt.subplots(1,1,figsize=(14,14))
bmap=Basemap(lat_0=cent_lat,lon_0=cent_lon,width=100000,height=100000,projection ='laea',ax=ax,resolution='h')
bmap.pcolormesh(xvals,yvals,new_ndvi,cmap=cmap,norm=the_norm)
lat_sep,lon_sep= 0.2, 0.2
parallels = np.arange(46, 51, lat_sep)
meridians = np.arange(-125,-121, lon_sep)
bmap.drawparallels(parallels, labels=[1, 0, 0, 0],
                       fontsize=10, latmax=90)
bmap.drawmeridians(meridians, labels=[0, 0, 0, 1],
                       fontsize=10, latmax=90);
bmap.drawcoastlines();
bmap.drawrivers();


# In[ ]:



