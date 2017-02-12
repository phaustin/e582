
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
from e582lib.modis_chans import chan_dict

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
from e582lib.channels_reproject import subsample,find_corners
get_ipython().magic('matplotlib notebook')
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

chan_list=['1','2']
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

reflectivity_list


# In[6]:

llcrnr=dict(lat=45,lon= -125)
urcrnr=dict(lat=50,lon= -120)
subsample_list=subsample(*reflectivity_list,lats=lat_data,lons=lon_data,llcrnr=llcrnr,urcrnr=urcrnr)
lats,lons=subsample_list[:2]
numchans=len(subsample_list) -2
rows,cols=lats.shape
chan_array=np.empty([rows,cols,numchans],dtype=np.float32)
for chan in range(numchans):
    chan_array[:,:,chan]=subsample_list[chan+2]


# In[7]:

corner_dict=find_corners(subsample_list[0],subsample_list[1])
corner_dict


# In[8]:

proj_id = 'laea'
datum = 'WGS84'
lat_0_txt = '{lat_0:5.2f}'.format_map(corner_dict)
lon_0_txt = '{lon_0:5.2f}'.format_map(corner_dict)
area_dict = dict(
    datum=datum, lat_0=lat_0_txt, lon_0=lon_0_txt, proj=proj_id, units='m')
area_dict


# In[9]:

from e582lib.channels_reproject import resample_channels
chan_list=['1','2']
result_dict=       resample_channels(chan_array,lats,lons,corner_dict)


# In[10]:

result_dict.keys()


# ### Now use the red and nearir channels to get the ndvi

# In[11]:

ch1=result_dict['channels'][:,:,0]
ch2=result_dict['channels'][:,:,1]
ndvi = (ch2 - ch1)/(ch2 + ch1)


# ### check out the correlation using a 2-d histogram

# In[12]:

from e582lib.geolocate import fast_hist, fast_count
ch1_min= 0.
ch1_max = 1.
num_ch1_bins=120

ch2_min = 0
ch2_max = 0.8
num_ch2_bins=100

ch1_hist = fast_hist(ch1.ravel(),ch1_min,ch1_max,numbins=num_ch1_bins)
ch2_hist =  fast_hist(ch2.ravel(),ch2_min,ch2_max,numbins=num_ch2_bins)
heatmap = fast_count(ch2_hist,ch1_hist)



# ### Why the strong correlation between channels 1 and 2?
# 
# Even the same surface can have very different reflectance values as the sun-satellite angle changes.  These changes due to geometry affect both channel 1 and channel 2 approximately equally.   That is why need to remove this spurious variability by creating the the "normalized" vegetation difference index.  By ratioing
# (chan2 - chan1)/(chan2 + chan1) you remove much of the change due to geometry -- the difference between high and low reflectivities is smoothed, as long as it occurs in both channels.
# 
# Below we'll use the "perceptually uniform" magma colormap. For other colormap choices see:
# 
# http://matplotlib.org/users/colormaps.html

# In[13]:


cmap=cm.get_cmap('magma')
with np.errstate(divide='ignore'): #use a context manager (with)
    log_counts=np.log10(heatmap)  #turn off divide by zero warning
masked_counts = np.ma.masked_invalid(log_counts)
fig, ax = plt.subplots(1,1,figsize=(10,10))
CS=ax.pcolormesh(ch1_hist['centers_vec'],ch2_hist['centers_vec'],masked_counts,cmap=cmap)
cax=fig.colorbar(CS,ax=ax)
ax.set(xlim=(0,1.),ylim=(0,0.8))
out=cax.ax.set_ylabel('log10(counts)')
out.set_rotation(270)
out.set_verticalalignment('bottom')
ax.set(xlabel='ch1 reflectance',ylabel='ch2 reflectance',
       title='Vancouver ch1 vs. ch2');



# In[14]:

interactive=False
if interactive:
    sns.choose_diverging_palette(as_cmap=True);


# In[15]:

cmap=sns.diverging_palette(261, 153,sep=6, s=85, l=66,as_cmap=True)
vmin= -0.9
vmax=  0.9
cmap.set_over('c')
cmap.set_under('k',alpha=0.8)
cmap.set_bad('k',alpha=0.1)
the_norm=Normalize(vmin=vmin,vmax=vmax,clip=False)


# In[16]:

masked_ndvi = np.ma.masked_invalid(ndvi)
fig,ax=plt.subplots(1,1,figsize=(14,14))
basemap_args=result_dict['basemap_args']
basemap_args['ax']=ax
basemap_args['resolution']='c'
bmap=Basemap(**basemap_args)
lat_sep,lon_sep= 5,5
parallels = np.arange(30, 60, lat_sep)
meridians = np.arange(-135, -100, lon_sep)
bmap.drawparallels(parallels, labels=[1, 0, 0, 0],
                       fontsize=10, latmax=90)
bmap.drawmeridians(meridians, labels=[0, 0, 0, 1],
                       fontsize=10, latmax=90)


with warnings.catch_warnings():
    warnings.simplefilter("ignore")
    col = bmap.imshow(masked_ndvi,origin='upper', norm=the_norm,cmap=cmap)
    cax,kw = matplotlib.colorbar.make_axes(ax,location='bottom',pad=0.05,shrink=0.7)
    out=fig.colorbar(col,cax=cax,extend='both',**kw)
    out.set_label('ndvi',size=20)
    ax.set_title('modis ndvi vancouver',size=25)
    print(kw)
bmap.drawcoastlines(linewidth=1.5, linestyle='solid', color='k')


# In[17]:

dir(bmap)
bmap.xmin,bmap.xmax,bmap.ymin,bmap.ymax
bmap.proj4string


# ### can save some time by reusing the bmap instance with a new axis

# In[18]:

fig,ax=plt.subplots(1,1,figsize=(12,12))
bmap.ax=ax
with warnings.catch_warnings():
    warnings.simplefilter("ignore")
    col = bmap.imshow(masked_ndvi,origin='upper', norm=the_norm,cmap=cmap)
    cax,kw = matplotlib.colorbar.make_axes(ax,location='bottom',pad=0.05,shrink=0.7)
    out=fig.colorbar(col,cax=cax,extend='both',**kw)
    out.set_label('ndvi',size=20)
    ax.set_title('modis ndvi vancouver -- replot me   ',size=25)
    print(kw)
bmap.drawcoastlines(linewidth=1.5, linestyle='solid', color='k');


# In[19]:

import pickle
pkl_file='map.pkl'
pickle.dump(bmap,open(pkl_file,'wb'),-1)


# In[20]:

bmap_new = pickle.load(open(pkl_file,'rb'))


# In[ ]:



