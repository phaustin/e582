
# coding: utf-8

# ### Read a netcdf formated smi par file and plot on a world map
# 
# this notebook reads and maps par in standard mapped image format
# 
# https://oceancolor.gsfc.nasa.gov/docs/technical/ocean_level-3_smi_products.pdf

# In[7]:

from netCDF4 import Dataset
import numpy as np
import matplotlib
from matplotlib import pyplot as plt
from mpl_toolkits.basemap import Basemap
from e582utils.data_read import download
import warnings
warnings.filterwarnings("ignore")

l3file='A2007008.L3m_DAY_PAR_par_9km.nc'
download(l3file)


# In[8]:

get_ipython().system('ncdump -h A2007008.L3m_DAY_PAR_par_9km.nc')


# #### Extract the variables and the _FillValue and replace missing data with np.nan
# 
# See http://unidata.github.io/netcdf4-python/

# In[2]:

with Dataset(l3file,'r') as ncdat:
    ncdat.set_auto_mask(False)
    par=ncdat.variables['par'][...]
    lat=ncdat.variables['lat'][...]
    lon=ncdat.variables['lon'][...]
    fill_value=ncdat.variables['par']._FillValue
hit= par == fill_value
par[hit] = np.nan


# #### set up the palette

# In[3]:

cmap=matplotlib.cm.YlGn_r  #see http://wiki.scipy.org/Cookbook/Matplotlib/Show_colormaps
cmap.set_over('r')
cmap.set_under('0.85')
cmap.set_bad('0.75') #75% grey
vmin= 0
vmax= 100
the_norm=matplotlib.colors.Normalize(vmin=vmin,vmax=vmax,clip=False)


# #### plot using https://nsidc.org/data/atlas/epsg_4326.html

# In[4]:

get_ipython().magic('matplotlib inline')
bmap=Basemap(epsg=4326)
lonvals,latvals = np.meshgrid(lon,lat)
fig, ax = plt.subplots(1,1,figsize=(24,20))
xvals,yvals=bmap(lonvals,latvals)
cs=bmap.pcolormesh(xvals,yvals,par,cmap=cmap,norm=the_norm)
bmap.fillcontinents(color='grey',lake_color='cyan');
colorbar=fig.colorbar(cs, shrink=0.5, pad=0.05,extend='both')


# In[ ]:



