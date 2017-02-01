
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
import warnings
warnings.filterwarnings("ignore")


myd02file="MYD021KM.A2016224.2100.006.2016225153002.h5"
download(myd02file)


# In[2]:


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

llcrnr=dict(lat=45,lon= -125)
urcrnr=dict(lat=50,lon= -120)
subsample_list=subsample(*reflectivity_list,lats=lat_data,lons=lon_data,llcrnr=llcrnr,urcrnr=urcrnr)
lats,lons=subsample_list[:2]
numchans=len(subsample_list) -2
rows,cols=lats.shape
chan_array=np.empty([rows,cols,numchans],dtype=np.float32)
for chan in range(numchans):
    chan_array[:,:,chan]=subsample_list[chan+2]


# In[6]:

corner_dict=find_corners(subsample_list[0],subsample_list[1])
corner_dict


# In[7]:

from e582lib.channels_reproject import resample_channels
chan_list=['1','2','3','4']
result_dict= resample_channels(chan_array,lats,lons,corner_dict)
#
# add ndvi as a new layer so that channels
# grows to shape= rows x cols x 5
# 
channels=result_dict['channels']
ch1=channels[:,:,0]
ch2=channels[:,:,1]
ndvi=(ch2 - ch1)/(ch2 + ch1)

# In[8]:

result_dict.keys()


# ### write out a geotiff file for the ndvi using rasterio

# In[10]:

from affine import Affine
import rasterio
geotiff_args = result_dict['geotiff_args']
transform = Affine.from_gdal(*geotiff_args['adfgeotransform'])
crs = geotiff_args['proj4_string']
fill_value=result_dict['fill_value']

# In[11]:

plt.close('all')
fig,ax=plt.subplots(1,1,figsize=(12,12))
ax.imshow(ndvi)


# In[12]:


fig, ax = plt.subplots(1,1,figsize=(14,14))
ll_col=200
ll_row=200
ur_col=300
ur_row=100
ndvi_zoom=ndvi[ur_row:ll_row,ll_col:ur_col]
ax.imshow(ndvi_zoom);


# In[13]:

from e582lib.geolocate import xy_to_col_row,col_row_to_xy


# In[14]:

cmap=sns.diverging_palette(261, 153,sep=6, s=85, l=66,as_cmap=True)
vmin= -0.9
vmax=  0.9
cmap.set_over('c')
cmap.set_under('k',alpha=0.8)
cmap.set_bad('k',alpha=0.1)
the_norm=Normalize(vmin=vmin,vmax=vmax,clip=False)


# In[15]:

geotiff_args['adfgeotransform']
result_dict['basemap_args']


# In[18]:


fig, ax = plt.subplots(1,1,figsize=(14,14))
basemap_args=result_dict['basemap_args']
basemap_args['ax'] = ax
basemap_args['resolution']='h'
bmap = Basemap(**basemap_args)


def make_basemap_xy(rownums,colnums,bmap,transform):
    xline=[]
    yline=[]
    for the_col in colnums:
        x,y = transform*(the_col,0)
        xline.append(x)
    for the_row in rownums:
        x,y= transform*(0,the_row)
        yline.append(y)
    xline,yline=np.array(xline),np.array(yline)
    xline = xline + bmap.projparams['x_0']
    yline = yline + bmap.projparams['y_0']
    xvals, yvals = np.meshgrid(xline,yline)
    return xvals,yvals


colnums=np.arange(ll_col,ur_col,dtype=np.int)
rownums=np.arange(ur_row,ll_row,dtype=np.int)
xvals,yvals = make_basemap_xy(rownums,colnums,bmap,transform)
ll_x,ur_x=xvals[-1,0],xvals[0,-1]
ll_y,ur_y =yvals[-1,0],yvals[0,-1]
col=bmap.pcolormesh(xvals,yvals,ndvi_zoom,cmap=cmap,norm=the_norm)
colorbar=bmap.ax.figure.colorbar(col, shrink=0.5, pad=0.05,extend='both')
bmap.ax.set_xlim(ll_x,ur_x)
bmap.ax.set_ylim(ur_y,ll_y)
bmap.drawcoastlines();
bmap.drawrivers();
plt.show()





