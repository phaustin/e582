
# coding: utf-8

# ## Notebook demo: parsing NASA EOSDIS core metadata
# 
# requires pyparsing:
# 
#     conda install pyparsing
#     
# uses parse_odl.py which was part of the 0.8.1 version of pyhdf (removed in 0.8.2)
# written by: 
# 
#     Andre Gosselin
#     Maurice Lamontagne Institute
#     Fisheries and Oceans Department
#     Government of Canada
#     Mont-Joli, Canada
#     Andre.Gosselin@dfo-mpo.gc.ca

# In[1]:

import h5py
from e582utils.parse_odl import parse_odl
import pprint
from e582utils.data_read import download
from dateutil.parser import parse
import datetime, pytz
pp=pprint.PrettyPrinter(indent=4)


# In[2]:

filename='AST_L1T_00305192005181928_20150509132931_70445.h5'
download(filename)


# ### The metadata attributes are saved as byte strings in hdf
# 
# Convert to utf-8 encoding and strip any blanks and newlines before
# calling parse_odl on the string
# 
# parse_odl returns the key,value pairs as nested dictionaries, and converts
# numbers to float

# In[3]:

keep_dict={}
with h5py.File(filename,'r') as infile:
    for key in infile.attrs.keys():
        if key.find('metadata') < 0:
            continue
        the_attr=infile.attrs[key].decode('utf-8').strip()
        cleanup=[]
        for line in the_attr.split('\n'):
            cleanup.append(line.strip())
        cleanup=' '.join(cleanup)
        keep_dict[key]=parse_odl(cleanup)                  


# In[4]:

print(list(keep_dict.keys()))


# ### Write all metadata to a text file
# 
# Use prettyprint to indent the nested dictionaries

# In[5]:

with open('metadata.txt','w') as outfile:
    for key,value in keep_dict.items():
        outfile.write('\n---------{}----------\n{}'.format(
            key,pprint.pformat(value,indent=4,width=200)))


# ### Example: bounding rectangle in lat lon

# In[6]:

rectangle= keep_dict['coremetadata.0_GLOSDS']['INVENTORYMETADATA']['BOUNDINGRECTANGLE']
pp.pprint(rectangle)


# In[7]:

right_lon= keep_dict['coremetadata.0_GLOSDS']['INVENTORYMETADATA']                 ['BOUNDINGRECTANGLE']['EASTBOUNDINGCOORDINATE']['VALUE']
print(right_lon)


# ### Bounding rectangle in UTM

# In[8]:

pp.pprint(keep_dict['productmetadata.1_GLOSDS']['PRODUCTGENERICMETADATA']                      ['SCENEFOURCORNERSMETERS'])


# ### Convert the timestamp string to a datetime object

# In[9]:

image_date=keep_dict['coremetadata.0_GLOSDS']['INVENTORYMETADATA']                    ['SINGLEDATETIME']['CALENDARDATE']['VALUE']
image_time=keep_dict['coremetadata.0_GLOSDS']['INVENTORYMETADATA']                      ['SINGLEDATETIME']['TIMEOFDAY']['VALUE']
image_date,image_time


# In[10]:

image_dt=parse(image_date)
hours,minutes,seconds=(int(image_time[:2]),
                           int(image_time[2:4]),float(image_time[4:9]))
seconds,milliseconds=divmod(seconds,1000)
seconds,microseconds=int(seconds),int(milliseconds*1000)


# In[11]:

image_dt=datetime.datetime(image_dt.year,image_dt.month,
                             image_dt.day,hours,minutes,seconds,microseconds,tzinfo=pytz.utc)


# In[12]:

image_dt

