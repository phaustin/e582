
# coding: utf-8

# ### Download all aqua and tera par files for all days from 2002 to 2017 inclusive
# 
# 1) use [e582utils.data_read.download](https://github.com/phaustin/e582/blob/6075f85947929df5a8e064f509a6c73b9f46b507/e582utils/data_read.py#L71-L84) to download the file
# 
# 2) try aqua (A) and tera (T) separately
# 
# 3) aqua data not available for 2002.  The website returns a 404 'Not found' error, and the download function
#    removes the tempfile and prints a message

# In[3]:

import numpy as np
import time
root="https://oceandata.sci.gsfc.nasa.gov/cgi/getfile"
from e582utils.data_read2 import download,NoDataException
for yearcount,year in enumerate(np.arange(2002,2018)):
    if yearcount > 1:
        break
    for count,day in enumerate(np.arange(1,366)):
        if count > 2:
            break
        for satellite in ['A','T']:
            filename='{}{}{:0>3}.L3m_DAY_PAR_par_4km.nc'.format(satellite,year,day)
            download(filename,root=root)
            time.sleep(3)
        print('-'*20)


# In[ ]:



