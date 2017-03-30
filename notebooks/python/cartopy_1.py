
# coding: utf-8

# ### Plotting with cartopy
# 
# 
# Redo the seaice.ipynb notebook maps using [cartopy](http://scitools.org.uk/cartopy/docs/latest/index.html) instead of [Basemap](https://github.com/matplotlib/basemap/issues/267#issuecomment-225179958):
# 
#     conda install cartopy
# 
# (requires save19.npz produced by seaice_II.ipynb)
# 
# The main differences between cartopy and basemap are:
# 
# 1) the way they create plotting axes
# 
# Basemap:  create the Basemap instance using bmap=Basemap(...,ax=ax),  redefine [plot and imshow](https://github.com/matplotlib/basemap/blob/master/lib/mpl_toolkits/basemap/__init__.py#L3255-L3283)
# 
# Cartopy, create the plotting axis by passing the projection to the axes constructor, which
# creates a [geoaxes subclass](https://github.com/SciTools/cartopy/blob/master/lib/cartopy/mpl/geoaxes.py#L222-L234) of the axes class:
# 
#     fig, ax = plt.subplots(1, 1, figsize=(10,10),
#                        subplot_kw={'projection': projection})
#                        
# 2) the way the set the plot extent
# 
# Basemap:  pass the x,y corners of the plot either as lon,lat values for the upper right and lower left corners,
# or as a width and height in x,y units
# 
# Cartopy:  pass the x,y corners using:
# 
#     ax.set_extent(new_extent,projection)
#     
# or for imshow:
# 
#     cs=ax.imshow(temp19V,origin='upper',cmap=cmap,norm=the_norm,
#              transform=projection,extent=new_extent,alpha=0.8)
# 
# 
#                        
#                     

# In[1]:

get_ipython().magic('matplotlib inline')
import cartopy.crs as ccrs
import matplotlib.pyplot as plt
import shapely.geometry as sgeom
import numpy as np
import matplotlib
import cartopy
from e582lib.map_slices import make_xy
from rasterio.transform import from_bounds
import pdir


# ### projection and map coords don't change

# In[2]:

#http://nsidc.org/data/gis/headers/NL.hdr
cornerx=9024309  #meters, from NL.hdr
cornery=cornerx
newcornerx=cornerx/2.
newcornery=newcornerx
new_extent=[-newcornerx,-newcornery,newcornerx,newcornery]
radius=6371228
van_lon,van_lat = [-123.1207,49.2827]


# ### keep palette the same

# In[3]:

cmap=matplotlib.cm.get_cmap('viridis')
vmin=220
vmax=260
the_norm=matplotlib.colors.Normalize(vmin=vmin,vmax=vmax,clip=False)


# ### load 19V data from seaice.ipynb

# In[4]:

temp19V=np.load('save19.npz')['temps19V']
fig,ax=plt.subplots(1,1)
ax.imshow(temp19V,origin='upper');


# ### Define the dataum and the projections for the EASE northern hemisphere grid
# 
# but shift the central longitude to center north america on plot

# In[5]:

globe = ccrs.Globe(ellipse=None, semimajor_axis=radius, 
                   semiminor_axis=radius)
projection=ccrs.LambertAzimuthalEqualArea(central_latitude=90,
                                          central_longitude= -90,globe=globe)
print('pro4_params: ',projection.proj4_params)
#Note that, unlike Basemap, cartopy doesn't add x_0 or y_0 to the projection


# ### Plot the map only -- note you need to create an axis with the map projection and call set_extent
# 
# Also use the Geodetic transform to locate the Vancouver (lon,lat) as a red dot on the laea projection
# and add the coastiine, rivers and lakes 

# In[6]:

fig, ax = plt.subplots(1, 1, figsize=(10,10),
                       subplot_kw={'projection': projection})
new_extent=[-newcornerx,newcornerx,-newcornery,newcornery]
ax.set_extent(new_extent,projection)
van_x,van_y=projection.transform_point(van_lon,van_lat,ccrs.Geodetic())
ax.plot(van_x,van_y,'ro',markersize=10);
ax.gridlines(linewidth=2)
ax.add_feature(cartopy.feature.GSHHSFeature(scale='coarse', levels=[1,2,3]));


# ### Add the 19V brightness temperature from seaice.ipynb using imshow
# 
# Note that the imshow function needs the enxtent and the projection
# 
# Also add a colorbar at the bottom

# In[10]:

fig, ax = plt.subplots(1, 1, figsize=(10,10),
                       subplot_kw={'projection': projection})
new_extent=[-newcornerx,newcornerx,-newcornery,newcornery]
ax.set_extent(new_extent,projection)
van_x,van_y=projection.transform_point(van_lon,van_lat,ccrs.Geodetic())
ax.plot(van_x,van_y,'ro',markersize=10);
ax.gridlines(linewidth=2)
ax.add_feature(cartopy.feature.GSHHSFeature(scale='coarse', levels=[1,2,3]));
cs=ax.imshow(temp19V,origin='upper',cmap=cmap,norm=the_norm,
             transform=projection,extent=new_extent,alpha=0.8)
cax,kw = matplotlib.colorbar.make_axes(ax,location='bottom',pad=0.05,shrink=0.7)
out=fig.colorbar(cs,cax=cax,extend='both',**kw)
out.set_label('Brightness temperature (K)',size=10)
ax.set_title('19V Brightness temperature');
print(ax.projection)


# ### Repeat using pcolormesh, which requires x and y values in the laea projection
# 
# Note that, unlike Basemap, cartopy doesn't add a easting or westing to the projection, so
# pyproj or projection.transform will both give the same x,y coordinates for a geodetic lon,lat pair
# 
# Position the colorbar at the side

# In[8]:

fig, ax = plt.subplots(1, 1, figsize=(10,10),
                       subplot_kw={'projection': projection})
new_extent=[-newcornerx,newcornerx,-newcornery,newcornery]
nrows,ncols=temp19V.shape
transform = from_bounds(-newcornerx,-newcornery,newcornerx,newcornery, ncols, nrows)
xvals,yvals = make_xy(0,nrows,0,ncols,transform)
ax.set_extent(new_extent,projection)
van_x,van_y=projection.transform_point(van_lon,van_lat,ccrs.Geodetic())
ax.plot(van_x,van_y,'ro',markersize=10);
ax.gridlines(linewidth=2);
ax.add_feature(cartopy.feature.GSHHSFeature(scale='coarse', levels=[1,2,3]))
temp19V_mask=np.ma.masked_invalid(temp19V)
cs=ax.pcolormesh(xvals,yvals,temp19V_mask,cmap=cmap,transform=projection,alpha=0.8,norm=the_norm);
cax,kw = matplotlib.colorbar.make_axes(ax,location='right',pad=0.05,shrink=0.7)
out=fig.colorbar(cs,cax=cax,extend='both',**kw)
label=out.set_label('Brightness temperature (K)',size=10,rotation= -90,verticalalignment='bottom')
ax.set_title('19V Brightness temperature');


# In[ ]:



