
# coding: utf-8

# # Intro to satellite data  I
# 
# In this notebook we take a quick look at a 5 minutes of satellite data acquired from the MODIS instrument on the  Aqua polar orbiting satellite. Aqua flies in the [A-train]( <http://atrain.nasa.gov), which is  formation of satellites that orbit separated by a minute or so.  The granule covers the period from 20:15 to 20:20 UCT on May 15, 2016 (Julian day 136) while Aqua flew over Ft. McMurray, Alberta.  I downloaded the granule from the [Laadsweb NASA site]( https://ladsweb.nascom.nasa.gov/data/search.html) and converted it from HDF4 to HDF5 format (more on [this](https://www.hdfgroup.org/h5h4-diff.html) later).  The structure of HDF5 files can be explored with the [HDFViewer tool](https://www.hdfgroup.org/products/java/release/download.html) (install version 2.13 from that link).  The gory details are in the [Modis Users Guide](http://clouds.eos.ubc.ca/~phil/courses/atsc301/downloads/modis_users_guide.pdf).
# 
# First, download the file from our course website:

# In[1]:

from a301utils.a301_readfile import download
import h5py
filename = 'MYD021KM.A2016136.2015.006.2016138123353.h5'
download(filename)


# Here is the corresponding red,green,blue color composite for the granule.

# In[2]:

from IPython.display import Image
Image(url='http://clouds.eos.ubc.ca/~phil/courses/atsc301/downloads/aqua_136_2015.jpg',width=600)


# ### now use h5py to read some of the satellite channels

# In[3]:

h5_file=h5py.File(filename)


# h5 files have attributes -- stored as a dictionary

# In[4]:

print(list(h5_file.attrs.keys()))


# ### print two of the attributes

# In[5]:

print(h5_file.attrs['Earth-Sun Distance_GLOSDS'])


# In[6]:

print(h5_file.attrs['HDFEOSVersion_GLOSDS'])


# h5 files have variables -- stored in a dictionary.
# The fields are aranged in a hierarchy of groups similar to a set of nested folders

# Here is what HDFViewer reports for the structure of the "EV_1KM_Emissive"  dataset, which stands for "Earth View, 1 km pixel resolution, thermal emission channels".  It is showing a 3 dimensional array of integers of shape (16,2030,1354).  These are radiometer counts in 16 different wavelength channels for the 2030 x 1354 pixel granule.

# In[7]:

Image('screenshots/HDF_file_structure.png')


# **Read the radiance data from MODIS_SWATH_Type_L1B/Data Fields/EV_1KM_Emissive**

# Note the correspondence between the keys and the fields you see in HDFView:
# 
# Here are the top level groups:

# In[8]:

print(list(h5_file.keys()))


# and the 'MODIS_SWATH_Type_L1B' group contains 3 subgroups:

# In[9]:

print(list(h5_file['MODIS_SWATH_Type_L1B'].keys()))


# and the 'Data Fields' subgroup contains 27 more groups:

# In[10]:

print(list(h5_file['MODIS_SWATH_Type_L1B/Data Fields'].keys()))


# Print out the 16 channel numbers stored in Band_1KM_Emissive data array.  The [...] means "read everything".  The 16 thermal channels are channels 20-36.  Their wavelength ranges and common uses are listed 
# [here](https://modis.gsfc.nasa.gov/about/specifications.php)

# In[11]:

print(h5_file['MODIS_SWATH_Type_L1B/Data Fields/Band_1KM_Emissive'][...])


# **note that channel 31, which covers the wavelength range 10.78-11.28 $\mu m$  occurs at index value 10 (remember python counts from 0)**

# In[12]:

index31=10


# **the data are stored as unsigned (i.e. only positive values), 2 byte (16 bit) integers which can hold values from 0 to $2^{16}$ - 1 = 65,535.
# The ">u2" notation below for the datatype (dtype) says that the data is unsigned, 2 byte, with the most significant
# byte stored first ("big endian", which is the same way we write numbers)**  
# 
# (Although the 2 byte words contain 16 bits, only  12 bits are significant).
# 
# (h5py let's you specify the group names one at a time, instead of using '/' to separate them.  This is convenient if you are storing your field name in a variable, for example.)

# In[13]:

my_name = 'EV_1KM_Emissive'
chan31=h5_file['MODIS_SWATH_Type_L1B']['Data Fields'][my_name][index31,:,:]
print(chan31.shape,chan31.dtype)


# **Print the first 3 rows and columns**

# In[14]:

chan31[:3,:3]


# ** we need to apply a
# scale and offset to convert counts to radiance, with units of $(W\,m^{-2}\,\mu m^{-1}\,sr^{-1}$).  More about the
# sr units later**

# $Data = (RawData - offset) \times scale$
# 
# this information is included in the attributes of each variable.
# 
# (see page 36 of the [Modis Users Guide](http://clouds.eos.ubc.ca/~phil/courses/atsc301/downloads/modis_users_guide.pdf))

# **here is the scale for all 16 channels**

# In[15]:

scale=h5_file['MODIS_SWATH_Type_L1B']['Data Fields']['EV_1KM_Emissive'].attrs['radiance_scales'][...]
print(scale)


# **and here is the offset for 16 channels**

# In[16]:

offset=h5_file['MODIS_SWATH_Type_L1B']['Data Fields']['EV_1KM_Emissive'].attrs['radiance_offsets'][...]
print(offset)


# **note that as the satellite ages and wears out, these calibration coefficients change**

# In[17]:

chan31_calibrated =(chan31 - offset[index31])*scale[index31]


# In[18]:

get_ipython().magic('matplotlib inline')


# **histogram the raw counts -- note that hist doesn't know how to handle 2-dim arrays, so flatten to 1-d**

# In[19]:

import matplotlib.pyplot as plt
out=plt.hist(chan31.flatten())
#
# get the current axis to add title with gca()
#
ax = plt.gca()
_=ax.set(title='Aqua Modis raw counts')


# **histogram the calibrated radiances and show that they lie between
# 0-10 $W\,m^{-2}\,\mu m^{-1}\,sr^{-1}$ **

# In[20]:

import matplotlib.pyplot as plt
fig,ax = plt.subplots(1,1)
ax.hist(chan31_calibrated.flatten())
_=ax.set(xlabel='radiance $(W\,m^{-2}\,\mu m^{-1}\,sr^{-1}$)',
      title='channel 31 radiance for Aqua Modis')


# ** Next Read MODIS_SWATH_Type_L1B/Geolocation Fields/Longitude**

# note that the longitude and latitude arrays are (406,271) while the actual
# data are (2030,1354).   These lat/lon arrays show only every fifth row and column to
# save space.  The full lat/lon arrays are stored in a separate file.

# In[21]:

lon_data=h5_file['MODIS_SWATH_Type_L1B']['Geolocation Fields']['Longitude'][...]
lat_data=h5_file['MODIS_SWATH_Type_L1B']['Geolocation Fields']['Latitude'][...]
_=plt.plot(lon_data[:10,:10],lat_data[:10,:10],'b+')


# **Note two things:  1) the pixels overlap and 2) they don't line up on lines of constant longitude and latitude**
# 
# **The pixels are also not all the same size -- this distortion is called the [bowtie effect](http://eoweb.dlr.de:8080/short_guide/D-MODIS.html)**
# 
# **Next -- plotting image data**

# In[ ]:



