
# coding: utf-8

# # Repeat the raw image plot from satellite_III

# In[1]:

from e582utils.data_read import download
import numpy as np
import h5py
import sys
from e582lib.radiation import planckInvert
from e582lib.modis_reproject import modisl1b_resample
from mpl_toolkits.basemap import Basemap
from matplotlib.colors import Normalize
import warnings
myd02file = 'MYD021KM.A2016136.2015.006.2016138123353.h5'
download(myd02file)
myd03file='MYD03.A2016136.2015.006.2016138121537.h5'
download(myd03file)


# Here is the corresponding red,green,blue color composite for the granule.

# In[2]:

from IPython.display import Image
Image(url='http://clouds.eos.ubc.ca/~phil/courses/atsc301/downloads/aqua_136_2015.jpg',width=600)


# In[3]:

chan_list=['31']
result_dict=       modisl1b_resample(myd02file,myd03file,chan_list)


# Now call the planckInvert function imported at the top of the notebook to convert radiance to brightness temperature

# In[4]:

result_dict['channels'].shape


# In[5]:

wavel=11.e-6  #chan 31 central wavelength, meters
chan31_mks = result_dict['channels'][:,:,0]*1.e6  #W/m^2/m/sr
Tbright = planckInvert(wavel,chan31_mks)
Tbright = Tbright - 273.15 #convert to Centigrade


# In[11]:

get_ipython().magic('matplotlib inline')
from matplotlib import pyplot as plt
from matplotlib import cm
cmap=cm.get_cmap('plasma')
vmin= -5
vmax=  30
cmap.set_over('w')
cmap.set_under('k',alpha=0.3)
cmap.set_bad('b',alpha=0.1)
the_norm=Normalize(vmin=vmin,vmax=vmax,clip=False)


# In[12]:

plt.close('all)')
fig,ax=plt.subplots(1,1,figsize=(14,14))
basemap_args=result_dict['basemap_args']
basemap_args['ax']=ax
basemap_args['resolution']='c'
import warnings
warnings.filterwarnings("ignore")
bmap=Basemap(**basemap_args)
CS=bmap.imshow(Tbright,cmap=cmap,norm=the_norm)
cax=fig.colorbar(CS,ax=ax,extend='both')
lat_sep,lon_sep= 5,5
parallels = np.arange(30, 80, lat_sep)
meridians = np.arange(-135, -80, lon_sep)
bmap.drawparallels(parallels, labels=[1, 0, 0, 0],
                       fontsize=10, latmax=90)
bmap.drawmeridians(meridians, labels=[0, 0, 0, 1],
                       fontsize=10, latmax=90)
bmap.drawcoastlines(linewidth=1.5, linestyle='solid', color='k')


# In[8]:




# In[ ]:




# In[ ]:




# In[9]:




# In[ ]:

from importlib import reload
import a301lib.geolocate
reload(a301lib.geolocate)
from a301lib.geolocate import find_corners
corners=find_corners(lat_data,lon_data)
corners


# ### The corners dictionary will be used by basemap below.  For now we can use the corner positions and the pixel spacing to get histogram limits:
# 
# Note that [fast_hist](http://clouds.eos.ubc.ca/~phil/courses/atsc301/_modules/a301lib/geolocate.html#fast_hist) now takes either a numbins or a binsize keyword argument to make the histogram bins.

# In[ ]:

lon_min= -144
lon_max = -92

lat_min = 47
lat_max = 70
binsize = 0.1

lon_hist = fast_hist(lon_data.ravel(),lon_min,lon_max,binsize=binsize)
lat_hist =  fast_hist(lat_data.ravel(),lat_min,lat_max,binsize=binsize)
gridded_image = fast_avg(lat_hist,lon_hist,Tbright.ravel())


# In[ ]:

out=np.meshgrid([-1,-2,-3], [1.,2.,3.,4.,5.])
type(out)
len(out)
out[0]
out[1]


# In[ ]:

lat_centers=(lat_hist['edges_vec'][1:] + lat_hist['edges_vec'][:-1])/2.
lon_centers=(lon_hist['edges_vec'][1:] + lon_hist['edges_vec'][:-1])/2.
lon_array,lat_array=np.meshgrid(lon_centers,lat_centers)
print(lon_array.shape)
masked_temps = np.ma.masked_invalid(gridded_image)


# In[ ]:

from matplotlib import cm
from matplotlib.colors import Normalize

cmap=cm.autumn  #see http://wiki.scipy.org/Cookbook/Matplotlib/Show_colormaps
cmap.set_over('w')
cmap.set_under('b',alpha=0.1)
cmap.set_bad('0.75') #75% grey
#
# set the range over which the pallette extends so I use
# use all my colors on data 10 and 40 degrees centigrade
#
vmin= 10
vmax= 40
the_norm=Normalize(vmin=vmin,vmax=vmax,clip=False)
fig,ax = plt.subplots(1,1,figsize=(14,18))
corners['ax'] = ax
corners['resolution']='l'
corners['projection']='lcc'
corners['urcrnrlon'] = -70.
corners['urcrnrlat'] = 65.
corners['llcrnrlat'] = 46.
corners['llcrnrlon'] = -140.
proj = make_plot(corners)
lat_centers=(lat_hist['edges_vec'][1:] + lat_hist['edges_vec'][:-1])/2.
lon_centers=(lon_hist['edges_vec'][1:] + lon_hist['edges_vec'][:-1])/2.
lon_array,lat_array=np.meshgrid(lon_centers,lat_centers)
#
# translate every lat,lon pair in the scene to x,y plotting coordinates 
# for th Lambert projection
#
x,y=proj(lon_array,lat_array)
CS=proj.pcolormesh(x, y,masked_temps, cmap=cmap, norm=the_norm)
CBar=proj.colorbar(CS, 'right', size='5%', pad='5%',extend='both')
CBar.set_label('Channel 31 brightness temps (deg C))',
               rotation=270,verticalalignment='bottom',size=18)
_=ax.set_title('Modis Channel 11, May 15, 2016 -- Fort McMurray',size=22)


# In[ ]:



