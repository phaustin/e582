"""
module for resampling images with pixel lat/lon
values

functions:

* subsample:  clip a set of files to a lat/lon blox

* find_corners:  construct a dictionary with the corners and cetral
  latitude and longitude for a lat/lon image

* resample_channels:  use pyresample to create lambert azimuthal equal
  area reprojection with 1.3 km pixels

"""

import h5py
import numpy as np
import pyproj
from affine import Affine
from pyresample import kd_tree, geometry
import json


def subsample(*datalist, lats=None, lons=None, llcrnr=None, urcrnr=None):
    """
    return a list of satellite scene variables (radiances, reflectivies, ndvi, etc.)
      each cropped to a subset of lats, lons and data where:
      llcnr['lat'] < lats < urcnr['lat'] and
      llcnr['lon'] < lon < urcnr['lon']

    Parameters
    ----------
    datalist: list of vectors or arrays of pixel values to be clipped,
        each is same size as lats and lons

    lats: vector or array of pixel lats
       units: degrees N

    lons: vector or array of pixel lons
        units: degrees E

    llcnr: dictionary
       lower left corner dictionary with keys ['lat','lon']
       containing the latitude and longitude of the lower left corner

     urcnr: dictionary
       upper right corner dictionary with keys ['lat','lon']
       containing the latitude and longitude of the upper right corner

    Returns
    -------

    list: lats, lons followed by all variables in *datalist, cropped
      to the corners

      i.e. if datatlist=[chan1,chan2] the the returned list should be
        [chan1[hit],chan2[hit],lat[hit],lon[hit]]  where hit
        is the logical vector that identifies all the pixels in
        the lat/lon box
    """
    rows,cols=lats.shape
    keep_rows=[]
    keep_cols=[]
    #
    # loop over each row, throwing out rows that have no pixels in the lattitude band.
    # If the row does have a pixel in the lattitude band, find those pixels that
    # are also within the longitude band, and add those column indices to the keep_column list and
    # the row index to the keep_row list
    #
    for the_row in range(rows):
        latvals=lats[the_row,:]
        lonvals=lons[the_row,:]
        lathit=np.logical_and(latvals >= llcrnr['lat'],latvals <= urcrnr['lat'])
        if np.sum(lathit) == 0:
            continue
        lonhit=np.logical_and(lonvals >= llcrnr['lon'],lonvals <= urcrnr['lon'])
        in_box=np.logical_and(lathit,lonhit)
        if np.sum(in_box) == 0:
            continue
        col_indices=np.where(in_box)[0]
        keep_cols.extend(col_indices.tolist())
        keep_rows.append(the_row)
        #print('here: \n{}\n{}\n'.format(keep_rows[-5:],keep_cols[-5:]))
    keep_rows,keep_cols=np.array(keep_rows),np.array(keep_cols)
    #
    # find the left and right columns and the top and bottom
    # rows and create slices to subset the data files
    #
    minrow,mincol=np.min(keep_rows),np.min(keep_cols)
    maxrow,maxcol=np.max(keep_rows),np.max(keep_cols)
    row_slice=slice(minrow,maxrow)
    col_slice=slice(mincol,maxcol)
    #
    # return a list with the lats and lons in front, followed
    # by the cnannels
    #
    outlist = [lats[row_slice,col_slice], lons[row_slice,col_slice]]
    for item in datalist:
        outlist.append(item[row_slice,col_slice])
    return outlist


def find_corners(lats,lons):
    """
    guess values for the upper right and lower left corners of the
    lat/lon grid and the grid center based on max/min lat lon in the
    data and return a dictionary that can be passed to Basemap to set
    the laea projection. 

    Parameters
    ----------

    lons: ndarray
       array of longitudes from a Modis scene

    lats: ndarray
       array of latitudes from a Modis scene

    Returns
    -------

    a dictionary with these keys 

    out_dict: dictionary with the following keys

    llcrnrlon:  longitude (deg E) of the lower left corner
    llcrnrllat: latitude (deg N)  of the lower left corner
    urcrnrlon:  longitude (deg E) of the upper right corner
    urcrnrllat: latitude (deg N)  of the upper right corner
    lat_0:  latitude of center of scene
    lon_0:  longitude of center of the scene
    """

    min_lat, min_lon = np.min(lats.ravel()), np.min(lons.ravel())
    max_lat, max_lon = np.max(lats.ravel()), np.max(lons.ravel())
    llcrnrlon, llcrnrlat = min_lon, min_lat
    urcrnrlon, urcrnrlat = max_lon, max_lat
    lat_0=(llcrnrlat+urcrnrlat)/2.
    lon_0=(llcrnrlon + urcrnrlon)/2.
    lon_list=[llcrnrlon,urcrnrlon]
    lat_list=[llcrnrlat,urcrnrlat]
    out_dict=dict(llcrnrlon=llcrnrlon,llcrnrlat=llcrnrlat,
                  urcrnrlon=urcrnrlon,urcrnrlat=urcrnrlat,
                  lat_0=lat_0,lon_0=lon_0,lat_list=lat_list,lon_list=lon_list)
    return out_dict
    
def resample_channels(chan_array, lat_array, lon_array,corner_dict, fill_value=-99999.,area_def=None):
    """
       given an array of radiances and/or reflectances 
       and the corresponding
       lat_array and lon_array for every pixel
       return projected images plus supporting data.
       The resampling uses pyresample with a lambert azimuthal
       equal area projection with lat_0 and lon_0 at
       the scene center


       Parameters
       ----------

       chan_array: ndarray float with shape [rows,cols,numchans]
           3 dimensional array with shape rows x cols x numchans, where numchans is the
           number of satellite channels to be resampled

       lat_array: ndarray float with shape [rows,cols]
           array of pixel latitudes

       lon_array: ndarray float with shape [rows,cols]

       corner_dict: corner dictionary returned by find_corners


       Returns
       -------

       dictionary with keys/values:

           channels: float32 3-dim array
              projected for each channel radiances (W/m^2/sr/micron for EV channels) or reflectances (no units for RefSB channels)
              dimensions:  [height,width,numchans]

           area_def_args: dict
              dictionary with projection information for pyresample

           basemap_args: dict
              dictionary with projection information for basemap

           geotiff_args: dict
              dictionary with projection information for geotiff/rasterio

           fill_value: float32
              fill value for missing data in channels (these resampled pixels are set to
                np.nan after resample)
    """
    #
    # set up the lambert azimuthal equal area projection with corners large enough
    # to fit image
    #
    proj_id = 'laea'
    datum = 'WGS84'
    lat_0_txt = '{lat_0:17.13f}'.format_map(corner_dict).strip()
    lon_0_txt = '{lon_0:17.13f}'.format_map(corner_dict).strip()
    area_dict = dict(datum=datum, lat_0=lat_0_txt, lon_0=lon_0_txt, proj=proj_id, units='m')
    prj = pyproj.Proj(area_dict)
    x, y = prj(corner_dict['lon_list'], corner_dict['lat_list'])
    minx, maxx = np.min(x), np.max(x)
    miny, maxy = np.min(y), np.max(y)
    #
    # back transform these to lon/lat
    #
    llcrnrlon, llcrnrlat = prj(minx, miny, inverse=True)
    urcrnrlon, urcrnrlat = prj(maxx, maxy, inverse=True)
    #
    # 1300 m pixels are a reasonable compromise between the smallest 1km pixels and the biggest
    # 4 km pixels at the sides of the swath
    #
    area_extent = [minx, miny, maxx, maxy]
    x_pixel = 1.3e3
    y_pixel = 1.3e3
    #
    # figure out how many pixels in the image
    #
    xsize = int((area_extent[2] - area_extent[0]) / x_pixel)
    ysize = int((area_extent[3] - area_extent[1]) / y_pixel)
    #
    #  here's the dictionary we need for basemap
    #
    basemap_args = dict()
    basemap_args['ellps'] = 'WGS84'
    basemap_args['llcrnrlon'] = llcrnrlon
    basemap_args['llcrnrlat'] = llcrnrlat
    basemap_args['urcrnrlon'] = urcrnrlon
    basemap_args['urcrnrlat'] = urcrnrlat
    basemap_args['projection'] = area_dict['proj']
    basemap_args['lat_0'] = corner_dict['lat_0']
    basemap_args['lon_0'] = corner_dict['lon_0']
    #
    #
    # here is the dictionary for pyresample
    #
    area_id = 'granule'
    area_name = 'modis swath 5min granule'
    #
    # here are all the arguments pyresample needs to regrid the swath
    #
    #
    shape_tup=chan_array.shape
    if len(shape_tup)==2:
        chan_array=chan_array[...,np.newaxis]
        shape_tup=chan_array.shape
    num_chans = shape_tup[2]
    #
    # now project all the images onto the lambert map
    #
    
    area_extent = [minx, miny, maxx, maxy]
    x_pixel = 1.3e3
    y_pixel = 1.3e3
    #
    # figure out how many pixels in the image
    #
    xsize = int((area_extent[2] - area_extent[0]) / x_pixel)
    ysize = int((area_extent[3] - area_extent[1]) / y_pixel)

    
    area_def_args = dict(
        area_id=area_id,
        area_name=area_name,
        proj_id=proj_id,
        area_dict=area_dict,
        xsize=xsize,
        ysize=ysize,
        area_extent=area_extent)
    area_def = geometry.AreaDefinition(area_id, area_name, proj_id, area_dict,
                                       xsize, ysize, area_extent)
    swath_def = geometry.SwathDefinition(lons=lon_array, lats=lat_array)
    #
    # here is the resample step using 5 km region of influence (see pyresample docs)
    #
    channels = kd_tree.resample_nearest(
        swath_def,
        chan_array,
        area_def,
        radius_of_influence=5000,
        nprocs=2,
        fill_value=fill_value)
    #
    # replace the negative number used for fill_value with np.nan
    #
    fill_value = np.array([np.nan], dtype=np.float32)[0]
    channels[channels < 0] = fill_value
    print('running resample_chans: here are the mean values of the channels to be resampled')
    for index in range(num_chans):
        print('channum and mean {} {}'.format(
            index, np.nanmean(channels[:, :, index].ravel())))
    #
    # replace negative fill_value with np.nan (32 bit)
    #
    print('pyresample area_def information:')
    print('\ndump area definition:\n{}\n'.format(area_def))
    print('\nx and y pixel dimensions in meters:\n{}\n{}\n'.format(
        area_def.pixel_size_x, area_def.pixel_size_y))
    #
    # here is the dictionary for geotiff creation -- save for future use in rasterio
    #
    adfgeotransform = [
        area_def.area_extent[0], area_def.pixel_size_x, 0,
        area_def.area_extent[3], 0, -area_def.pixel_size_y
    ]
    proj4_string = area_def.proj4_string
    proj_id = area_def.proj_id
    height, width, num_chans = channels.shape
    geotiff_args = dict(
        width=width,
        height=height,
        adfgeotransform=adfgeotransform,
        affine_transform=Affine.from_gdal(*adfgeotransform),
        proj4_string=proj4_string,
        proj_id=proj_id)
    out_dict = dict(
        channels=channels,
        area_def_args=area_def_args,
        basemap_args=basemap_args,
        geotiff_args=geotiff_args,
        fill_value=fill_value)
    print('completed channels_resample')
    return out_dict


    
def write_h5(out_file=None,
             channels=None,
             area_def_args=None,
             basemap_args=None,
             geotiff_args=None,
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
    area_def_args: dict
       dictionary of arguments used by pyresample in modisl1b_resample
    basemap_args: dict
       dictionary of arguments to pass to basemap to produce the 
       pyresample projection calculated in modisl1b_resample
    geotiff_args: dict
       dictionary of arguments to pass to rasterio geotiff writer
       to produce geotiff with this projection
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
    print('inside write_h5: ', channels.shape)
    geotiff_string = json.dumps(geotiff_args, indent=4)
    basemap_string = json.dumps(basemap_args, indent=4)
    print('inside write_h5: area_def --\n{}--\n'.format(area_def_args))
    area_def_string = json.dumps(area_def_args, indent=4)
    height, width, num_chans = channels.shape
    with h5py.File(out_file, 'w') as f:
        group = f.create_group('channels')
        for index,chan_name in enumerate(chan_list):
            the_chan = channels[:, :, index]
            dset = group.create_dataset(
                chan_name, the_chan.shape, dtype=the_chan.dtype)
            dset[...] = the_chan[...]
        f.attrs['geotiff_args'] = geotiff_string
        f.attrs['basemap_args'] = basemap_string
        f.attrs['area_def_args'] = area_def_string
        f.attrs['fill_value'] = fill_value
        f.attrs['comments'] = comments
    return None


