
# coding: utf-8

# # Intro to satellite data  II -- regridding
# 
# In this notebook we look at:
# 
# 1) how to plot an image using imshow with a colorbar
# 
# 2) how to find out which pixels are in a particular lon/lat grid cell so that we can
#    regrid the radiances onto a uniform grid
#    

# In[14]:

from e582utils.data_read import download
import numpy as np
import h5py
import sys
filename = 'MYD021KM.A2016136.2015.006.2016138123353.h5'
download(filename)


# Here is the corresponding red,green,blue color composite for the granule.

# In[15]:

from IPython.display import Image
Image(url='http://clouds.eos.ubc.ca/~phil/courses/atsc301/downloads/aqua_136_2015.jpg',width=600)


# In[16]:

### now use h5py to read some of the satellite channels

h5_file=h5py.File(filename)
index31=10
my_name = 'EV_1KM_Emissive'
chan31=h5_file['MODIS_SWATH_Type_L1B']['Data Fields'][my_name][index31,:,:]
scale=h5_file['MODIS_SWATH_Type_L1B']['Data Fields']['EV_1KM_Emissive'].attrs['radiance_scales'][...]
offset=h5_file['MODIS_SWATH_Type_L1B']['Data Fields']['EV_1KM_Emissive'].attrs['radiance_offsets'][...]
chan31_calibrated =(chan31 - offset[index31])*scale[index31]


# ### New -- plot the radiances as an image

# In[17]:

get_ipython().magic('matplotlib inline')
from matplotlib import pyplot as plt


# In[18]:

fig,ax = plt.subplots(1,1,figsize = (10,14))
CS=ax.imshow(chan31_calibrated)
cax=fig.colorbar(CS)
ax.set_title('calibrated radiance, Ft. McMurray')
out=cax.ax.set_ylabel('Chan 31 radiance $(W\,m^{-2}\,\mu m^{-1}\,sr^{-1}$)')
out.set_rotation(270)
out.set_verticalalignment('bottom')


# get the full latitude and longitude arrays from the MYD03file (download using wildcard search at Laadsweb)

# In[19]:

filename='MYD03.A2016136.2015.006.2016138121537.h5'
download(filename)
geo_file = h5py.File(filename)
lon_data=geo_file['MODIS_Swath_Type_GEO']['Geolocation Fields']['Longitude'][...]
lat_data=geo_file['MODIS_Swath_Type_GEO']['Geolocation Fields']['Latitude'][...]


# In[20]:

#
# work through what's going on in this function, using print statements
# if you need them. and answering the 8 questions inline
#
get_ipython().magic('debug')
import pdb

def do_hist(data_vec,numbins,minval,maxval):
    #
    # Q1) describe in words the 6 variables defined between
    # here and the for loop, include what the array shapes are when
    # given 
    #
    #  data_vec -- data pixel values to be binned
    #  binsize -- width of the histogram bin
    #  bin_count -- vector (length 30) holding number of pixels in each of the bins
    #  bin_index  -- vector (length 800) holding longitude values to be binned
    #  lowcount -- number of longitudes smaller than left bin
    #  lowcount -- number of longitudes bigger than right bin
    #  
    #
    #  turn question 1 info on or off with q1 flag
    #
    #
    q1=False
    if q1:
        minval = -124
        maxval = -93
        numbins=30
        #
    # 
    #
    # Q2) Why did I set bin_index to
    #      -1 instead of 0?
    #
    #
    #
    binsize= (maxval - minval)/numbins
    bin_count = np.zeros([numbins,],dtype=np.int)
    bin_index = np.zeros(data_vec.shape,dtype = np.int)
    bin_index[:] = -1
    lowcount=0
    highcount=0 
    #
    #  Q3) which bin number would longitude = -102 go into?
    #
    #
    #
    #
    #  Q4) what are the left and right bin edges of this bin?
    #
    #
    #
    #
    for i in range(len(data_vec)):
        float_bin =  ((data_vec[i] - minval) /binsize)
        if float_bin < 0:
            lowcount+=1
            bin_index[i]= -999.
            continue
        if float_bin >= numbins:
            highcount += 1
            bin_index[i] = -888.
            continue
        int_bin = int(float_bin)
        bin_count[int_bin]+=1
        bin_index[i]=int_bin
    bin_edges=[minval + (i*binsize) for i in range(numbins+1)]
    bin_edges = np.array(bin_edges)
    out = dict(index_vec=bin_index,count_vec=bin_count,edges_vec=bin_edges,
             lowcount=lowcount,highcount=highcount)
    if q1:
        #
        # stop the python debugger here to print variables
        #
        pdb.set_trace()
    return out
#


# In[21]:

# Q5) what do these two statements do?
#

lon_flat = lon_data.ravel()[:800]
lat_flat = lat_data.ravel()[:900]

lon_min= -124
lon_max = -93
numbins=30

lon_hist=do_hist(lon_flat,numbins,lon_min,lon_max)
lat_min = 47
lat_max = 55
numbins=40
#
# now run the function
#
lat_hist=do_hist(lat_flat,numbins,lat_min,lat_max)
print(list(lon_hist.keys()))


# In[22]:

def find_bins(lon_hist,lat_hist,lon_index,lat_index):
    """
    identify all pixels that have lons in bin lon_index
    and lats in bin lat_index
    
    Parameters
    ----------
    
    lon_hist:  dictionary
        dict returned from do_hist
        
    lat_hist: dictionary
        dict returned from do_hist
        
    lon_index = index of the longitude bin to retrieve
    lat_index = index of the latitude bin to retrieve
    
    Returns
    -------
    
    pixel_list: list
        indices of pixels with lon/lats in the specified lon/lat histogram bin
    """
    keep_lat=[]
    keep_lon=[]
    #
    # Q6) Describe in words what the following two loops do
    #
    #
    #
    #
    for count,the_index in enumerate(lat_hist['index_vec']):
        if the_index == lat_index:
            keep_lat.append(count)
    for count,the_index in enumerate(lon_hist['index_vec']):
        if the_index == lon_index:
            keep_lon.append(count)
    #
    # Q7) Describe what intersect1d does
    #
    #
    pixel_list=np.intersect1d(keep_lat,keep_lon)
    return pixel_list


# ### use find_bins to pick out the pixels near -111.1 deg W, 50.5 deg N

# In[23]:

# Q8) Explain in words why calling np.abs().argmin() in the first line below produces
#  the index of the  bin edge nearest 50.5 
#  Write a 1 line python statement to check whether I've found the
#  left edge of the bin and not the right edge
#
# 
#

lat_bin=np.abs(lat_hist['edges_vec'] - (50.5)).argmin()
lon_bin=np.abs(lon_hist['edges_vec'] - (-111.1)).argmin()


# In[24]:

#
#
# get the two edges for the lon and lat cell
#
lon_vals=lon_hist['edges_vec'][lon_bin:lon_bin+2]
lat_vals=lat_hist['edges_vec'][lat_bin:lat_bin+2]
#
# find the center between the edges
#
lon_center = np.sum(lon_vals)/2.
lat_center = np.sum(lat_vals)/2.
(lon_center,lat_center)


# In[25]:

pixel_ids = find_bins(lon_hist,lat_hist,lon_bin,lat_bin)
print('pixels in both lon bin {} and lat bin {}:\n\n {}'.format(lon_bin,lat_bin,pixel_ids))


# ### Now pull the radiances for these pixels

# In[26]:

radiances = chan31_calibrated.ravel()[pixel_ids]
fig, ax = plt.subplots(1,1)
ax.hist(radiances)
_=ax.set(ylabel='counts',xlabel='radiance ($W\,m^{-2}\,\mu m^{-1}\,sr^{-1}$)',
        title='radiances at lon: {:5.1f} deg W and lat: {:5.1f} deg N'
         .format(lon_center,lat_center))


# In[ ]:



