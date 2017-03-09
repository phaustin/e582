
# coding: utf-8

# ### Use Kmeans to find clusters in the 2d histogram of Tbright vs. reflectivity

# In[1]:

from IPython.display import Image
from e582utils.data_read import download
from matplotlib import pyplot as plt
from mpl_toolkits.basemap import Basemap
from e582lib.radiation import planckInvert
import numpy as np
import matplotlib
import warnings
from sklearn.cluster import KMeans
from numpy.random import randint,seed


# In[2]:

Image('MOBRGB.A2012240.0235.006.2015311151021.jpg',width=500)


# In[3]:

l1b_file='MOD021KM.A2012240.0235.006.2014220124853.h5'
geom_file='MOD03.A2012240.0235.006.2012287184700.h5'
files=[l1b_file,geom_file]
for the_file in files:
    download(the_file)


# ### get the radiances from channels 1 and 31 projected onto an laea grid

# In[4]:

from e582lib.modis_reproject import modisl1b_resample
chan_list=['1','31']
result_dict=       modisl1b_resample(l1b_file,geom_file,chan_list)


# In[5]:

result_dict['channels'].shape
result_dict['basemap_args']


# In[6]:

chan1=result_dict['channels'][...,0]


# ### convert the channel 31 radiance to brightness temperature in deg C

# In[7]:

wavel=11.e-6  #chan 31 central wavelength, meters
chan31_mks = result_dict['channels'][:,:,1]*1.e6  #W/m^2/m/sr
Tbright = planckInvert(wavel,chan31_mks)
Tbright = Tbright - 273.15 #convert to Centigrade


# ### remove all pixels that are np.nan

# In[8]:

hit=np.logical_not(np.logical_or(np.isnan(chan1),np.isnan(Tbright)))
chan1_hit=chan1[hit]
Tbright_hit=Tbright[hit]
Tbright.size


# ### We ar left with about 4 million pixels
# 
# The Kmeans algorithm won't work with this big a dataset.  Try subsampling 25000 pixels from
# a univorm distribution

# In[9]:

numvals=Tbright_hit.size
seed(50)
selection=randint(low=0,high=numvals,size=5000)


# In[15]:

X=np.vstack([Tbright_hit,chan1_hit])
X=X.T[selection,:]
kmeans = KMeans(n_clusters=2)
kmeans.fit(X)
centers=kmeans.cluster_centers_


# ### here are the cluster centers

# In[16]:

centers


# ### plot a 2-d histogram

# In[12]:

Tbright_bins=np.linspace(-80,30,25)
refl_bins=np.linspace(0,1,25)


# In[13]:

get_ipython().magic('matplotlib inline')
cmap=plt.cm.viridis
vmin=-4
vmax=-1
cmap.set_over('c')
cmap.set_under('k',alpha=0.1)
cmap.set_bad('k',alpha=0.1)
the_norm=matplotlib.colors.Normalize(vmin=vmin,vmax=vmax,clip=False)
with warnings.catch_warnings():
    warnings.simplefilter("ignore")
    H,y_edges,x_edges=np.histogram2d(chan1.flat[:],Tbright.flat[:],bins=(refl_bins,Tbright_bins))
    H=H/chan1.size
    Hmasked=np.ma.masked_invalid(H)
    fig,ax=plt.subplots(1,1,figsize=(14,14))
    CS=ax.pcolormesh(Tbright_bins,refl_bins,np.log10(Hmasked),cmap=cmap,norm=the_norm)
    ax.set(xlabel='channel 31 brightness temperature (deg C)',ylabel='channel 1 reflectivity')
    cax=fig.colorbar(CS, shrink=0.5, pad=0.05,extend='both')
    out=cax.ax.set_ylabel('log10(counts)')
    out.set_rotation(270)
    out.set_verticalalignment('bottom'); 


# ### add the kmeans cluster centers to the subsampled dataset

# In[14]:

get_ipython().magic('matplotlib inline')
cmap=plt.cm.viridis
vmin=-4
vmax=-1
cmap.set_over('c')
cmap.set_under('k',alpha=0.1)
cmap.set_bad('k',alpha=0.1)
the_norm=matplotlib.colors.Normalize(vmin=vmin,vmax=vmax,clip=False)
with warnings.catch_warnings():
    warnings.simplefilter("ignore")
    H,y_edges,x_edges=np.histogram2d(X[:,1],X[:,0],bins=(refl_bins,Tbright_bins))
    rows,cols=X.shape
    H=H/rows
    Hmasked=np.ma.masked_invalid(H)
    fig,ax=plt.subplots(1,1,figsize=(14,14))
    CS=ax.pcolormesh(Tbright_bins,refl_bins,np.log10(Hmasked),cmap=cmap,norm=the_norm,zorder=1)
    ax.set(xlabel='channel 31 brightness temperature (deg C)',ylabel='channel 1 reflectivity')
    cax=fig.colorbar(CS, shrink=0.5, pad=0.05,extend='both')
    out=cax.ax.set_ylabel('log10(counts)')
    out.set_rotation(270)
    out.set_verticalalignment('bottom'); 
    ax.scatter(centers[:,0],centers[:,1],c='red',s=180,alpha=1,zorder=2);


# In[ ]:



