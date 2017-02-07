"""
 functions for handling slices of images for basemap
"""
import numpy as np
from affine import Affine
import rasterio
import h5py
from ast import literal_eval
import pyproj

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

def write_h5(out_file=None,
             channels=None,
             affine_transform=None,
             projection_dict=None,
             fill_value=None,
             chan_list=None,
             comments=None):
    """
    Create an hdf5 file that contains resampled data (channels)
    and supporting map projection dictionaries that can be used to
    create a Basemap instance or a geotiff file


    Parameters
    ----------
    out_file: str
       name of output file
    channels: ndarray rows x cols x channels
       data to be written
    affine_transform: affine instance
       six coefficient transform
    projection_dict: dict
       dictionary with arguments for pyproj
    fill_value: float
       number that denotes missing data
    chan_list: list
       list of string channel names that become the dataset name, 
       for each channel. length should be same
       as last dimension in channels 
    comments: str
       history, author, etc. as single string

    Returns
    -------

       side effect: write information into hdf5 file outfile
    """
    print('inside write_h5: channels shape= ', channels.shape)
    height, width, num_chans = channels.shape
    with h5py.File(out_file, 'w') as outf:
        group = outf.create_group('channels')
        for index,chan_name in enumerate(chan_list):
            the_chan = channels[:, :, index]
            dset = group.create_dataset(
                chan_name, the_chan.shape, dtype=the_chan.dtype)
            dset[...] = the_chan[...]
        a,b,c,d,e,f,_,_,_ = affine_transform
        affine_coeffs=np.array([a,b,c,d,e,f])
        outf.attrs['affine_coeffs']=affine_coeffs
        outf.attrs['projection_dict'] = repr(projection_dict)
        outf.attrs['fill_value'] = fill_value
        outf.attrs['chan_list'] = repr(chan_list)
        outf.attrs['comments'] = comments
    return None


def read_h5(in_file):
    out_dict=dict(channels=dict())
    with h5py.File(in_file, 'r') as f:
        for chan in f['channels'].keys():
            out_dict['channels'][chan]=f['channels'][chan][...]
        out_dict['affine_transform']=Affine(*list(f.attrs['affine_coeffs']))
        for key in ['projection_dict','chan_list']:
            print('key: ',key,f.attrs[key])
            out_dict[key]=literal_eval(f.attrs[key])
        out_dict['fill_value']=f.attrs['fill_value']
        out_dict['comments']=f.attrs['comments']
    return out_dict
        

def write_tif(h5_filename,tif_filename):
    """
    take an h5 file produced by write_h5 and output a tif file
    file

    Parameters
    ----------

    h5_filename: str
      name of input h5 file

    tif_filename: str
      name of output tif file


    Returns
    -------

    None -- writes tif file as side effect

    """
    file_dict=read_h5(h5_filename)
    chan_list=file_dict['chan_list']
    num_chans=len(chan_list)
    transform=file_dict['affine_transform']
    crs = file_dict['projection_dict']
    fill_value = file_dict['fill_value']
    height, width = file_dict['channels'][chan_list[0]].shape
    data_type=file_dict['channels'][chan_list[0]].dtype
    with rasterio.open(tif_filename,'w',driver='GTiff',
                       height=height,width=width,
                       count=num_chans,dtype=data_type,
                       crs=crs,transform=transform,nodata= fill_value) as dst:
        for index,chan_name in enumerate(chan_list):
            result=file_dict['channels'][chan_list[index]][...]
            dst.write(result,index+1)
            dst.update_tags(index+1,name=chan_list[index])
        dst.update_tags(comments=file_dict['comments'])
    return None

def get_basemap(width,height,crs,transform):
    basemap_args = dict()
    basemap_args['ellps'] = crs['datum']
    basemap_args['projection'] = crs['proj']
    basemap_args['lat_0'] = crs['lat_0']
    basemap_args['lon_0'] = crs['lon_0']
    left_col=0
    right_col=width
    top_row=0
    bot_row=height
    ll_x,ll_y = transform*(left_col,bot_row)
    ur_x,ur_y = transform*(right_col,top_row)
    projection=pyproj.Proj(crs)
    ll_lon,ll_lat = projection(ll_x,ll_y,inverse=True)
    ur_lon,ur_lat = projection(ur_x,ur_y,inverse=True)
    ll_dict=dict(llcrnrlat=ll_lat,llcrnrlon=ll_lon,urcrnrlat=ur_lat,
                  urcrnrlon=ur_lon)
    basemap_args.update(ll_dict)
    return basemap_args

