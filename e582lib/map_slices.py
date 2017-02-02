"""
 functions for handling slices of images for basemap
"""
import numpy as np

def make_xy(ur_row,ll_row,ll_col,ur_col,transform):
    """
    get map coordinates for a slice
    note that row count increases from ur_row to ll_row

    Parameters
    ----------

    ur_row,ll_row,ll_col,ur_col
       slice edges
    transform:
       affine transform for image

    Returns
    -------

    xvals, yvals: ndarrays 
       map coords with shape of row_slice by colslice
    """
    rownums=np.arange(ur_row,ll_row)
    colnums=np.arange(ll_col,ur_col)
    xline=[]
    yline=[]
    for the_col in colnums:
        x,y = transform*(the_col,0)
        xline.append(x)
    for the_row in rownums:
        x,y= transform*(0,the_row)
        yline.append(y)
    xline,yline=np.array(xline),np.array(yline)
    xvals, yvals = np.meshgrid(xline,yline)
    return xvals,yvals


def make_basemap_xy(ur_row,ll_row,ll_col,ur_col,bmap,transform):
    """
    get map coordinates for a slice including basemap
    easting and northing
    note that row count increases from ur_row to ll_row

    Parameters
    ----------

    ur_row,ll_row,ll_col,ur_col
       slice edges
    bmap: basemap instance
       used to get easting and northing
    transform:
       affine transform for image

    Returns
    -------

    xvals, yvals: ndarrays 
       map coords with shape of row_slice by colslice
    """
    xvals,yvals=make_xy(ur_row,ll_row,ll_col,ur_col,transform)
    xvals = xvals + bmap.projparams['x_0']
    yvals=yvals + bmap.projparams['y_0']
    return xvals,yvals



def get_corners_centered(numrows,numcols,projection,transform):
    """
    return crnr lats  and lons centered on lon_0,lat_0
    with width numcols and height numrows

    Parameters
    ----------

    numrows: int
       number of rows in slice
    numcols: int
       number of columns in slice
    pyrojection: proj object
       pyproj map project giving lon_0 and lat_0
    transform:
       affine transform for image

    Returns:
       ll_dict: dict
         ll and ur corner lat lons plus lon_0 and lat_0
       xy_dict
         ll and ur corner xy (without basemap easting or northing
       slice_dict
         slices to get columns and rows from original image, xvals and yvals
    """
    cen_col,cen_row = ~transform*(0,0)
    left_col = int(cen_col - numcols/2.)
    right_col = int(cen_col + numcols/2.)
    top_row = int(cen_row - numrows/2.)
    bot_row = int(cen_row + numrows/2.)
    ll_x,ll_y = transform*(left_col,bot_row)
    ur_x,ur_y = transform*(right_col,top_row)
    lon_0,lat_0 = projection(0,0,inverse=True)
    ll_lon,ll_lat = projection(ll_x,ll_y,inverse=True)
    ur_lon,ur_lat = projection(ur_x,ur_y,inverse=True)
    ll_dict=dict(llcrnrlat=ll_lat,llcrnrlon=ll_lon,urcrnrlat=ur_lat,
                  urcrnrlon=ur_lon,lon_0=lon_0,lat_0=lat_0)
    xy_dict = dict(ll_x=ll_x,ll_y=ll_y,ur_x=ur_x,ur_y=ur_y)
    slice_dict=dict(row_slice=slice(top_row,bot_row),col_slice=slice(left_col,right_col))
    return ll_dict,xy_dict,slice_dict


# In[6]:

def get_corners(ur_row,ll_row,ll_col,ur_col,projection,transform):
    """
    return crnr lats  for a box with the contiguous
    rows in between ur_row and ll_row and columns between ll_col and
    ur_col
    Note that rowlist increases downward, so toprow is rowlist[0]

    Parameters
    ----------

    ur_row,ll_row,ll_col,ur_col
       slice edges
    pyrojection: proj object
       pyproj map project giving lon_0 and lat_0
    transform:
       affine transform for image

    Returns:
       ll_dict: dict
         ll and ur corner lat lons plus lon_0 and lat_0
       xy_dict
         ll and ur corner xy (without basemap easting or northing
       slice_dict
         slices to get columns and rows from original image, xvals and yvals
    """
    ll_x,ll_y = transform*(ll_col,ll_row)
    ur_x,ur_y = transform*(ur_col,ur_row)
    lon_0,lat_0 = projection(0,0,inverse=True)
    ll_lon,ll_lat = projection(ll_x,ll_y,inverse=True)
    ur_lon,ur_lat = projection(ur_x,ur_y,inverse=True)
    ll_dict=dict(llcrnrlat=ll_lat,llcrnrlon=ll_lon,urcrnrlat=ur_lat,
                  urcrnrlon=ur_lon,lon_0=lon_0,lat_0=lat_0)
    xy_dict = dict(ll_x=ll_x,ll_y=ll_y,ur_x=ur_x,ur_y=ur_y)
    slice_dict=dict(row_slice=slice(ur_row,ll_row),col_slice=slice(ll_col,ur_col))
    return ll_dict,xy_dict,slice_dict

