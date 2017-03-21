
# coding: utf-8

# ### Read the start and end times for a 1 day par file and find files 1 day before and 1 day after
# 
#  

# In[1]:

from netCDF4 import Dataset
from e582utils.data_read import download
import warnings
warnings.filterwarnings("ignore")
import pdir
import pytz
import dateutil as du
import datetime
import json

l3file='A2007008.L3m_DAY_PAR_par_9km.nc'
download(l3file)


# ### get the time string from the netcdf attributes

# In[2]:

with Dataset(l3file,'r') as ncdat:
    start=getattr(ncdat,'time_coverage_start')
    end=getattr(ncdat,'time_coverage_end') 
    print('start: {}\nend: {}'.format(start,end))


# ### convert strings to datetime objects and find the middle of the period

# In[3]:

start_dt=du.parser.parse(start)
end_dt=du.parser.parse(end)
interval=end_dt - start_dt
mid_dt=start_dt + interval/2.
#
#  remove the hours and minutes, leaving the day
#
mid_dt = datetime.datetime(mid_dt.year,mid_dt.month,mid_dt.day,tzinfo=pytz.utc)
#
# make a 1 day timedelta and subtract and add to get before and after
#
one_day=datetime.timedelta(days=1)
before = mid_dt - one_day
after = mid_dt + one_day


# ### write functions to get day of year from datetime, and make url

# In[4]:

def day_of_year(the_dt):
    year,month,day=the_dt.year,the_dt.month,the_dt.day
    start_of_year=datetime.datetime(year-1,12,31,tzinfo=pytz.utc)
    days=(the_dt - start_of_year).days
    return(year,days)

def make_url(satellite,year,julian_day):
    url_file='{}{}{:0>3}.L3m_DAY_PAR_par_4km.nc'.format(satellite,year,julian_day)
    return url_file

day_before,day_mid,day_after=day_of_year(before),day_of_year(mid_dt),day_of_year(after)
print(make_url('A',*day_before))
print(make_url('A',*day_after))


# ### storing the bad days
# 
# suppose you have two sites 'baja' and 'barb'  (barbados) with missing days
# 
# keep the year,day,site tuples in a list and save the list to a json file

# In[5]:

bad_list=[(2007,235,'baja'),(2007,235,'barb')]
filename='bad_days.json'
with open(filename,'w') as out:
    json.dump(bad_list,out,indent=4)


# ### here is what the file looks like

# In[6]:

# %load bad_days.json
[
    [
        2007,
        235,
        "baja"
    ],
    [
        2007,
        235,
        "barb"
    ]
]


# ### read it back in

# In[7]:

with open(filename,'r') as infile:
    bad_list=json.load(infile)
print(bad_list)


# In[ ]:



