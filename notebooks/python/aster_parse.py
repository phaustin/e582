
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

# In[11]:

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


# ### get an example value

# In[6]:

rectangle= keep_dict['coremetadata.0_GLOSDS']['INVENTORYMETADATA']['BOUNDINGRECTANGLE']
rectangle


# In[13]:

right_lon= keep_dict['coremetadata.0_GLOSDS']['INVENTORYMETADATA']                 ['BOUNDINGRECTANGLE']['EASTBOUNDINGCOORDINATE']['VALUE']
print(right_lon)


# In[ ]:



