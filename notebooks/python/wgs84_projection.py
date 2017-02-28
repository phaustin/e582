
# coding: utf-8

# ### What is epsg:4326?

# Here are some links:
# 
# https://nsidc.org/data/atlas/epsg_4326.html
# 
# http://spatialreference.org/ref/epsg/wgs-84/
# 
# http://www.unoosa.org/pdf/icg/2012/template/WGS_84.pdf
# 
# 

# ### Now try this out with pyproj and basemap
# 
# Note the different results -- basemap uses degrees, pyproj uses radians
# 
# It looks like there is a bug in the pyproj proj4 string, units should be radians, not meters

# In[32]:

from mpl_toolkits.basemap import Basemap
import pyproj
import numpy as np


# In[38]:

epc_dict=dict(datum='WGS84',proj='eqc')
epc_proj=pyproj.Proj(epc_dict)
coord=( -125,45)
coord=(180,45)
print('coord in degrees: {}'.format(coord))
print('coord in radians: {}'.format(np.array(coord)*np.pi/180.))
print('\npyproj {}: {}\n'.format(epc_proj.srs,epc_proj(*coord)))
epsg_proj=pyproj.Proj(init='epsg:4326')
print('\npyproj {}: {}\n'.format(epsg_proj.srs,epsg_proj(*coord)))
epsg2_dict=dict(proj='longlat',ellps='WGS84',datum='WGS84')
epsg2_proj=pyproj.Proj(epsg2_dict)
print('\npyproj {}: {}\n'.format(epsg2_proj.srs,epsg2_proj(*coord)))
bmap_4326=Basemap(epsg=4326)
print('\nbasemap {}: {}\n'.format(bmap_4326.proj4string,bmap_4326(*coord)))
epsg_roundtrip=pyproj.Proj(bmap_4326.proj4string)
print('\nbasemap roundtrip {}: {}\n'.format(epsg_roundtrip.srs,epsg_roundtrip(*coord)))


# In[ ]:



