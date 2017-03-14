
# coding: utf-8

# ### Assignment -- for the following image, use [histogram2d](https://docs.scipy.org/doc/numpy/reference/generated/numpy.histogram2d.html) to make a 2-dimensional histogram
# 
# Use the channel 1 reflectivity for your y-axis bins, and the channel 31 brightness temperature for your x-axis bins

# In[32]:

from IPython.display import Image
from e582utils.data_read import download
from matplotlib import pyplot as plt
from mpl_toolkits.basemap import Basemap
from e582lib.radiation import planckInvert
import numpy as np
import matplotlib
import warnings
from e582lib.modis_chans import chan_dict
import h5py
from IPython.display import Image
import seaborn as sns
from matplotlib.colors import ListedColormap


# In[2]:

Image('MOBRGB.A2012240.0235.006.2015311151021.jpg',width=500)


# In[3]:

l1b_file='MOD021KM.A2012240.0235.006.2014220124853.h5'
geom_file='MOD03.A2012240.0235.006.2012287184700.h5'
mask_file='MOD35_L2.A2012240.0235.006.2015059110241.h5'
cloud_file='MOD06_L2.A2012240.0235.006.2015062132158.h5'
files=[l1b_file,geom_file,mask_file,cloud_file]
for the_file in files:
    download(the_file)


# ### Look at the raw data and show that scan lines are missing for channel 29

# In[4]:

get_ipython().magic('matplotlib inline')
chan_list=['29','31']
radiance_list=[]
for the_chan in chan_list:
    #
    # read channel channels
    #
        index = chan_dict[the_chan]['index']
        field_name = chan_dict[the_chan]['field_name']
        scale_name=chan_dict[the_chan]['scale']
        offset_name=chan_dict[the_chan]['offset']
    
        
        with h5py.File(l1b_file,'r') as h5_file:
            chan=h5_file['MODIS_SWATH_Type_L1B']['Data Fields'][field_name][index,:,:]
            fill_value=h5_file['MODIS_SWATH_Type_L1B']['Data Fields'][field_name].attrs['_FillValue']
            scale=h5_file['MODIS_SWATH_Type_L1B']['Data Fields'][field_name].attrs[scale_name][...]
            offset=h5_file['MODIS_SWATH_Type_L1B']['Data Fields'][field_name].attrs[offset_name][...]
            print('here is fill_value: ',fill_value)
            correct_fill = fill_value - 4
            print('here is the correct fill value: ',correct_fill)
            hit=chan == correct_fill
            chan=chan.astype(np.float32)
            chan[hit]=np.nan
            chan_calibrated =(chan - offset[index])*scale[index]
            radiance_list.append(chan_calibrated)


# ### For some reason the fill value listed in the attribute is not the one used in the data

# In[5]:

chan29,chan31=radiance_list
print('channel29 bad pixels: ',np.sum(np.isnan(chan29.ravel())))
fig,ax=plt.subplots(1,2,figsize=(14,10))
ax[0].imshow(chan29,origin='upper')
ax[1].imshow(chan31,origin='upper');


# In[6]:

from e582lib.modis_reproject import modisl1b_resample
result_dict=       modisl1b_resample(l1b_file,geom_file,chan_list)


# In[7]:

wavel=11.e-6  #chan 31 central wavelength, meters
chan31_mks = result_dict['channels'][:,:,1]*1.e6  #W/m^2/m/sr
Tbright31 = planckInvert(wavel,chan31_mks)
Tbright31 = Tbright31 - 273.15 #convert to Centigrade


# In[8]:

wavel=8.55e-6  #chan 31 central wavelength, meters
chan29_mks = result_dict['channels'][:,:,0]*1.e6  #W/m^2/m/sr
Tbright29 = planckInvert(wavel,chan29_mks)
Tbright29 = Tbright29 - 273.15 #convert to Centigrade


# In[9]:

bad=np.logical_or(np.isnan(Tbright29),Tbright29>50.)
Tbright29[bad]=np.nan
plt.hist(Tbright29[~bad]);


# In[13]:


basemap_args=result_dict['basemap_args']
fig,ax=plt.subplots(1,1,figsize=(14,14))
basemap_args['ax']=ax
basemap_args['resolution']='l'
bmap=Basemap(**result_dict['basemap_args'])
CS=bmap.imshow(Tbright31,origin='upper')
bmap.drawcoastlines();
CBar=bmap.colorbar(CS, 'right', size='3%', pad='5%',extend='both')
ax.set_title('Channel 31 Brightness Temperature (deg C)')


# In[14]:

fig,ax=plt.subplots(1,1,figsize=(14,14))
basemap_args['ax']=ax
basemap_args['resolution']='l'
bmap=Basemap(**result_dict['basemap_args'])
CS=bmap.imshow(Tbright29,origin='upper')
bmap.drawcoastlines();
CBar=bmap.colorbar(CS, 'right', size='3%', pad='5%',extend='both')
ax.set_title('Channel 29 Brightness Temperature (deg C)')


# In[15]:

fig,ax=plt.subplots(1,1,figsize=(14,14))
basemap_args['ax']=ax
basemap_args['resolution']='l'
bmap=Basemap(**result_dict['basemap_args'])
CS=bmap.imshow(Tbright29-Tbright31,origin='upper')
bmap.drawcoastlines();
CBar=bmap.colorbar(CS, 'right', size='3%', pad='5%',extend='both')
ax.set_title('Channel 29-31 Brightness Temperature difference (deg C)')


# In[19]:

Image('cloud_phase_06.png',width=1000)


# In[37]:

colors = ["baby blue",  "eggshell"]
print([the_color for the_color in colors])
colors=[sns.xkcd_rgb[the_color] for the_color in colors]
pal=ListedColormap(colors,N=2)
pal.set_bad('k',alpha=0.1)


# In[38]:

diff=Tbright29-Tbright31
threshold=1
diff[diff < threshold]= -1
diff[diff >= threshold] = 1
fig,ax=plt.subplots(1,1,figsize=(14,14))
basemap_args['ax']=ax
basemap_args['resolution']='l'
bmap=Basemap(**result_dict['basemap_args'])
CS=bmap.imshow(diff,origin='upper',cmap=pal)
bmap.drawcoastlines();
CBar=bmap.colorbar(CS, 'right', size='3%', pad='5%',extend='both')
ax.set_title('Channel 29-31 Brightness Temperature difference (deg C)');


# In[ ]:



