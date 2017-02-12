
# coding: utf-8

# ### Calculate mean and variance of monthly chlorophyll data from the Ocean Color repository
# 
# 
# #### Resources
# 
# 
# [NASA Ocean Biology Processing Group](https://oceancolor.gsfc.nasa.gov/about)
# 
# https://oceancolor.gsfc.nasa.gov/docs/format/Ocean_Level-3_Binned_Data_Products.pdf
# 
# [Ocean color web site](http://www.oceanopticsbook.info/view/absorption/physics_of_absorption)
# 

# #### Write the bin number, mean and variance out as a dataframe
# 
# This notebook reads in data vectors from the level3 binned chlorophyll-A file, which gives  monthly averaged 
# chlorophyll concentrations at 4km resolution for the month of June, 2010.  It writes the bin number, mean and variance out as three columns in a Pandas DataFrame
# 
# For a brief intro to dataframes see [Pandas DataFrames -- chapter 3](http://nbviewer.jupyter.org/github/jakevdp/PythonDataScienceHandbook/blob/master/notebooks/03.01-Introducing-Pandas-Objects.ipynb).  
# 
# For more information two good books are:
# 
# [The Python Data Science Handbook](http://shop.oreilly.com/product/0636920034919.do)
# 
# and
# 
# [Python for Data Analysis](http://shop.oreilly.com/product/0636920023784.do)

# In[1]:

from e582utils.data_read import download
from contexttimer import Timer
import h5py
import pandas as pd
import datetime as dt
import numpy as np
import time

chlor_file='A20101522010181.L3b_MO_CHL.h5'
download(chlor_file)


# ### dump the monthly level3 binned chlorophyll metadata

# In[2]:

from e582utils.h5dump import dumph5
outstring=dumph5(chlor_file)
print(outstring)


# ### Structured arrays
# 
# The hdf file stores the array chlor_a as a vector with 11384896 values, each with two fields: chlor_a_sum and chlor_a_sum_sq
# 
#     member of group: /Level-3 Binned Data: <HDF5 dataset "chlor_a": shape (11384896,), type "|V8">
#         TITLE: b'chlor_a'
#         CLASS: b'TABLE'
#         FIELD_0_NAME: b'chlor_a_sum'
#         FIELD_1_NAME: b'chlor_a_sum_sq'
#         HDF4_OBJECT_TYPE: b'Vdata'
#         HDF4_OBJECT_NAME: b'chlor_a'
#         HDF4_REF_NUM: 5
#         VERSION: b'1.0'
#         
# To calculate the mean and the variance
# we need to divide these sums by the number if datapoints in the bin, which is stored the "weights" field in
# the BinList vector
# 
#     member of group: /Level-3 Binned Data: <HDF5 dataset "BinList": shape (11384896,), type "|V19">
#         TITLE: b'BinList'
#         CLASS: b'TABLE'
#         VERSION: b'1.0'
#         FIELD_0_NAME: b'bin_num'
#         FIELD_1_NAME: b'nobs'
#         FIELD_2_NAME: b'nscenes'
#         FIELD_3_NAME: b'time_rec'
#         FIELD_4_NAME: b'weights'
#         FIELD_5_NAME: b'sel_cat'
#         FIELD_6_NAME: b'flags_set'
#         HDF4_OBJECT_TYPE: b'Vdata'
#         HDF4_OBJECT_NAME: b'BinList'
#         HDF4_REF_NUM: 4
#         
# The h5py module reads the vectors in as numpy structured arrays, which are described in 
# [Chapter 2 of the Python Data Science Handbook](http://nbviewer.jupyter.org/github/jakevdp/PythonDataScienceHandbook/blob/master/notebooks/02.09-Structured-Data-NumPy.ipynb)

# ### calculate the chlorophyll bin number, mean and variance and save in a record array with three columns

# In[3]:

with  h5py.File(chlor_file,'r') as infile:
    root_key='Level-3 Binned Data'
    #
    # turn day of year into a month and day
    # and save so we can write out as attributes
    # of our output files
    #
    start_day=int(infile.attrs['Start Day_GLOSDS'])  #convert from 16 bit to 64 bit int
    start_year=infile.attrs['Start Year_GLOSDS']
    #
    # go to the last day of the previous year and add the days to that start
    #
    start=dt.datetime(start_year-1,12,31) + dt.timedelta(days=start_day)
    end_day=int(infile.attrs['End Day_GLOSDS'])
    end_year=infile.attrs['End Year_GLOSDS']
    end=dt.datetime(end_year-1,12,31) + dt.timedelta(days=end_day)
    start_date=start.strftime('%Y-%m-%d')
    end_date=end.strftime('%Y-%m-%d')
    binlist=infile[root_key]['BinList']
    chlor_a=infile[root_key]['chlor_a']
    veclength=binlist.shape[0]
    print('number of bins in dataset: ',veclength)
    #
    # extract the sum, summed squares and weights
    #
    chlor_a_data=chlor_a['chlor_a_sum'][:veclength]
    chlor_a_sq_data=chlor_a['chlor_a_sum_sq'][:veclength]
    weights_data=binlist['weights'][:veclength]
    binnums=binlist['bin_num'][:veclength]
#
# create a 3 column structured array to hold the output
#
out = np.empty((veclength,),dtype=[('binnum','>i4'),('chlor_a_mean','>f4'),('chlor_a_var','>f4')])


# ### now transfer the record array to a dataframe indexed by bin number

# In[6]:

#
# first run needs to set write=True to save dataframe
# file size is for output file is 174 Mbytes
# this takes a couple of minutes
#
write=True
out_h5 = 'chlor_pandas.h5'

if write:
    with Timer() as t:
        #
        # fill the structured array with bin,chlorophyll pairs
        # mean and variance. See the level3 user guide
        # for mean, variance formula
        #
        for i in range(veclength):
            meanval=chlor_a_data[i]/weights_data[i]
            variance=(chlor_a_sq_data[i]/weights_data[i]) - meanval**2.
            out[i]=(binnums[i],meanval,variance)
        print("time to create structured array: ",t.elapsed)
        #
        # create a pandas dataframe using the structured array
        # indexed by bin number
        #
        the_df=pd.DataFrame.from_records(out,index='binnum')
        print("time to create dataframe: ",t.elapsed)
        with pd.HDFStore(out_h5,'w') as store:
            store.put('chlor_a_mean',the_df,format='fixed')
        #
        # open the file a second time to write the attributes
        #
        with  h5py.File(out_h5,'a') as f:
            f.attrs['history']='created by chlorophyl.ipynb'
            f.attrs['created_on']=time.strftime("%c")
            f.attrs['start_date']=start_date
            f.attrs['end_date']=end_date
            units='micrograms/m^3'
            title='mean chlorophyll concentration'
            f['/chlor_a_mean'].attrs['mean_units']=units
            f['/chlor_a_mean'].attrs['mean_title']=title
            units='(micrograms/m^3)^2'
            title='variance of chlorophyll concentration'
            f['/chlor_a_mean'].attrs['variance_units']=units
            f['/chlor_a_mean'].attrs['variance_title']=title
        print('time to write dataframe: ',t.elapsed)
else:
    #
    # reuse data 
    #
    with Timer() as t:
        with pd.HDFStore(out_h5,'r') as store:
            the_df=store['chlor_a_mean']
        print('time to read dataframe: ',t.elapsed)       


# In[5]:

the_df.head()


# In[ ]:



