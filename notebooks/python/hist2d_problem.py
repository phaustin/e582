
# coding: utf-8

# ### Assignment -- for the following image, use [histogram2d](https://docs.scipy.org/doc/numpy/reference/generated/numpy.histogram2d.html) to make a 2-dimensional histogram
# 
# Use the channel 1 reflectivity for your y-axis bins, and the channel 31 brightness temperature for your x-axis bins

# In[6]:

from IPython.display import Image
from e582utils.data_read import download


# In[5]:

Image('MOBRGB.A2012240.0235.006.2015311151021.jpg',width=500)


# In[9]:

l1b_file='MOD021KM.A2012240.0235.006.2014220124853.h5'
geom_file='MOD03.A2012240.0235.006.2012287184700.h5'
mask_file='MOD35_L2.A2012240.0235.006.2015059110241.h5'
cloud_file='MOD06_L2.A2012240.0235.006.2015062132158.h5'
files=[l1b_file,geom_file,mask_file,cloud_file]
for the_file in files:
    download(the_file)


# In[ ]:



