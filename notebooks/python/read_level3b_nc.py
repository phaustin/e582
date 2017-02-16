
# coding: utf-8

# ### Read data from an ocean color level3b netcdf file that is really an h5 file
# 
# Format is described here:
# 
# https://oceancolor.gsfc.nasa.gov/docs/technical/ocean_level-3_binned_data_products.pdf
# 
# unlike the file used in the calc_chlor and plot_chlor notebooks, downloads from the 
# https://oceancolor.gsfc.nasa.gov/cgi/l3 have a nc suffix but don't open as nc files.
# Try  as an h5 file instead.
# 
# This notebook verifies that the data is the same format used in the calc_chlor notebook

# In[10]:

from e582utils.data_read import download
from e582utils import h5dump
import h5py


# In[3]:

infile='A2007010.L3b_DAY_PAR.nc'
download(infile)


# In[7]:

out=h5dump.dumph5(infile)


# In[25]:

root_key='level-3_binned_data'
with h5py.File(infile,'r') as in_h5:
    print('root keys: ',list(in_h5.keys()))
    print('group keys: ',list(in_h5[root_key].keys()))
    par=in_h5[root_key]['par'][...]
    binlist=in_h5[root_key]['BinList'][...]


# In[26]:

print(par.dtype)
print(binlist.dtype)


# In[ ]:



