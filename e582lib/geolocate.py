"""
  functions to support geolocating/mapping satellite data::

      find_corners:  get ll and ur corners and resolution of a scene
      make_plot:  initialize a basemap plot  
      fast_hist:  vector histogramming
      slow_hist:  pure python historgramming
      fast_avg:  numba accelerated average of binned data
      slow_avg:  pure python average of binned data
"""
import numpy as np
import numba
import textwrap
from mpl_toolkits.basemap import Basemap
import pyproj


def find_corners(lats, lons):
    """
    guess values for the upper right and lower left corners of the
    lat/lon grid and the grid center based on max/min lat lon in the
    data and return a dictionary that can be passed to Basemap to set
    the lcc projection.  Also return the smallest lat and lon differences
    to get a feeling for the image resolution.

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
    lat_1:  latitude line of bottom of image
    lat_2:  latitude line of the top of the image
    lat_0:  latitude of center of scene
    lon_0:  longitude of center of the scene
    """
    min_lat, min_lon = np.min(lats.ravel()), np.min(lons.ravel())
    max_lat, max_lon = np.max(lats.ravel()), np.max(lons.ravel())
    llcrnrlon, llcrnrlat = min_lon, min_lat
    urcrnrlon, urcrnrlat = max_lon, max_lat
    # find longitude diffs across columns
    # 2040 x 1354 becomes 2040 x 1353
    #
    try:
        lon_diff = np.fabs(np.diff(lons, axis=1))
        #
        # sort accross columns
        #
        lon_diff.sort(axis=1)
        max_diff_lon = np.max(lon_diff[:, -1])
        #
        # find latitude diffs across rows
        # diff will be 2039 x 1354
        #
        lat_diff = np.fabs(np.diff(lats, axis=0))
        lat_diff.sort(axis=0)
        max_diff_lat = np.max(lat_diff[-1, :])
        text =\
            """
        space between pixels
        --------------------

        largest latitude spacing between rows:  {max_diff_lat:7.4f} deg
        largest longitude spacing between cols:  {max_diff_lon:7.4f} deg
        """
        out = textwrap.dedent(text.format_map(locals()))
        print(out)
    except:
        pass
    out_dict = dict(llcrnrlon=llcrnrlon, llcrnrlat=llcrnrlat,
                    urcrnrlon=urcrnrlon, urcrnrlat=urcrnrlat,
                    lat_1=llcrnrlat, lat_2=urcrnrlat, lat_0=(
                        llcrnrlat + urcrnrlat) / 2.,
                    lon_0=(llcrnrlon + urcrnrlon) / 2.)
    return out_dict


def make_plot(lcc_values, lat_sep=5, lon_sep=5):
    """
      set up the basic map projection details with coastlines and meridians
      return the projection object for further plotting

      Parameters
      ----------

      lcc_values: dictionary
         keyword arguments needed by Basemap

      lat_sep:  int
         spacing between lat  parallels, degrees

      lon_sep: int
         spacing between lon parallels, degrees

      Returns
      -------

      Basemap projection object for plotting
    """
    proj = Basemap(**lcc_values)
    parallels = np.arange(-90, 90, lat_sep)
    meridians = np.arange(0, 360, lon_sep)
    proj.drawparallels(parallels, labels=[1, 0, 0, 0],
                       fontsize=10, latmax=90)
    proj.drawmeridians(meridians, labels=[0, 0, 0, 1],
                       fontsize=10, latmax=90)
    # draw coast & fill continents
    # map.fillcontinents(color=[0.25, 0.25, 0.25], lake_color=None) # coral
    proj.drawcoastlines(linewidth=1.5, linestyle='solid', color='k')
    return proj


def fast_hist(data_vec, minval, maxval, numbins=None, binsize=None):
    """
    bin data_vec into numbins evenly spaced bins from left edge
    minval to right edge maxval

    Parameters
    ----------

    data_vec: numpy vector (float)
       data/pixels to be binned -- 1-d

    numbins:  int
       number of histogram bins
    minval:  float
        left edge
    maxval: float
        right edge

    Returns
    -------
      dictionary with keys:

      index_vec: ndarray 1-d float
        same size as data_vec, with entries containing bin number
        if data is smaller than left edge, missing value is -999
        if data is larger than right edge, missing value is -888

      count_vec: ndarray 1-d  int
        size numbins, with number of counts in each bin

      centers_vec: ndarray 1-d float
        center of bins, length numbins

      edges_vec: ndarray 1-d float
        size numbins+1 containing bin edges

      lowcount: int
         number of pixels smaller than left edge

      high count: 
         number of pixels larger than right edge
    """
    if numbins is None:
        numbins = int(np.ceil((maxval - minval) / binsize))
    else:
        binsize = (maxval - minval) / numbins
    bin_edges = [minval + (i * binsize) for i in range(numbins + 1)]
    bin_edges = np.array(bin_edges)
    bin_centers = (bin_edges[1:] + bin_edges[:-1]) / 2.
    #
    # searchsorted reserves index 0 for undercounts and index numbins + 1
    # for overcounts.  The insertion occurs to the right, so we need to
    # subtract 1 to get the left edge
    #
    bin_index = np.searchsorted(bin_edges, data_vec.ravel())
    bin_count = np.bincount(bin_index, minlength=(numbins + 2))
    lowcount = bin_count[0]
    highcount = bin_count[-1]
    bin_count = bin_count[1:-1]
    good_bins = np.arange(0, len(bin_count))
    hit = bin_count > 0
    good_bins = good_bins[hit]
    #
    # subtract 1 so low  counts labeled -1 and high counts are labeled numbins
    # replace these with -999 and -888
    #
    bin_index = bin_index - 1
    under_count = bin_index == -1
    bin_index[under_count] = -999
    over_count = bin_index == numbins
    bin_index[over_count] = -888
    out = dict(index_vec=bin_index, count_vec=bin_count, edges_vec=bin_edges,
               centers_vec=bin_centers, lowcount=lowcount, highcount=highcount, good_bins=good_bins)
    return out


@numba.jit('void(int32[:],int32[:],float32[:],int32[:,:],float32[:,:],b1)', nopython=True)
def numba_avg(lat_indices, lon_indices, raw_data, bin_count, gridded_image, bad_neg):
    """
    return a image binned by latitude and longitude

    Parameters
    ----------

       lat_indices: vector int32
          latitude bin number for every pixel

       lon_indices: vector int32
          longitude bin numer for every pixel

       raw_data:  vector float32
          pixel values at latitude/longitude points

       bin_count:  2d array int32
          number of values in each bin of gridded_image

       gridded_image: 2d array: float32
          binned array of shape num_lat_bins x num_lon_bins with
          average values of the raw_data for each bin

       bad_neg: bool
          optional flag -- if True then negative numbers are flagged as np.nan
    """
    for n in range(len(lat_indices)):  # lat_indices and lon_indices both size of raw data
        bin_row = lat_indices[n]
        bin_col = lon_indices[n]
        #

        # if the data is flagged as missing, assign that bin cell a value of np.nan
        # a single np.nan in the bin will cause that bin to be skipped subsequently
        #
        if (bin_row < 0 or bin_col < 0):
            continue
        else:
            if (bad_neg and raw_data[n] < 0):
                continue
            gridded_image[bin_row, bin_col] += raw_data[n]
            bin_count[bin_row, bin_col] += 1

    for row in range(gridded_image.shape[0]):
        for col in range(gridded_image.shape[1]):
            if bin_count[row, col] > 0:
                gridded_image[row, col] = gridded_image[row,
                                                        col] / bin_count[row, col]
            else:
                gridded_image[row, col] = np.nan


@numba.jit('void(int32[:],int32[:],int32[:,:])', nopython=True)
def numba_counts(lat_indices, lon_indices, bin_count):
    """
    return counts in latitude and longitude bins

    Parameters
    ----------

       lat_indices: vector int32
          latitude bin number for every pixel

       lon_indices: vector int32
          longitude bin numer for every pixel


       bin_count:  2d array int32
          number of values in each bin of gridded_image

    """
    for n in range(len(lat_indices)):  # lat_indices and lon_indices both size of raw data
        bin_row = lat_indices[n]
        bin_col = lon_indices[n]
        #

        # if the data is flagged as missing, assign that bin cell a value of np.nan
        # a single np.nan in the bin will cause that bin to be skipped subsequently
        #
        if (bin_row < 0 or bin_col < 0):
            continue
        else:
            bin_count[bin_row, bin_col] += 1


def fast_avg(lat_hist, lon_hist, data_vec, bad_neg=True):
    """

    use numba_avg to average values binned by lat_hist and lon_hist

    Parameters
    ----------

    lat_hist: dictionary
        dict returned from running fast_hist on
        the lat. vector corresponding to data_vec

    lon_hist:  dictionary
         dict returned from fast_hist on
         the lon. vector corresponding to data_vec

    data_vec: vector (float)
         pixel values of radiance, temperature, etc.

    bad_neg: bool
      optional flag -- if True then negative numbers are flagged as np.nan

    Returns
    -------

    gridded_image:  2d array (float)
        average values of data_vec pixels on lat_hist, lon_hist grid


    """
    num_lat_bins = len(lat_hist['edges_vec']) - 1
    num_lon_bins = len(lon_hist['edges_vec']) - 1
    gridded_image = np.zeros([num_lat_bins, num_lon_bins], dtype=np.float32)
    bin_count = np.zeros([num_lat_bins, num_lon_bins], dtype=np.int32)
    lat_indices = lat_hist['index_vec'].astype(np.int32)
    lon_indices = lon_hist['index_vec'].astype(np.int32)
    data_vec = data_vec.astype(np.float32)
    numba_avg(lat_indices, lon_indices, data_vec,
              bin_count, gridded_image, bad_neg)
    return gridded_image


def fast_count(lat_hist, lon_hist):
    """

    use numba_counts to count values binned by lat_hist and lon_hist

    Parameters
    ----------

    lat_hist: dictionary
        dict returned from running fast_hist on
        the lat. vector corresponding to data_vec

    lon_hist:  dictionary
         dict returned from fast_hist on
         the lon. vector corresponding to data_vec

    Returns
    -------

    bin_count:  2d array (int)
        number of pixels in each bin


    """
    num_lat_bins = len(lat_hist['edges_vec']) - 1
    num_lon_bins = len(lon_hist['edges_vec']) - 1
    bin_count = np.zeros([num_lat_bins, num_lon_bins], dtype=np.int32)
    lat_indices = lat_hist['index_vec'].astype(np.int32)
    lon_indices = lon_hist['index_vec'].astype(np.int32)
    numba_counts(lat_indices, lon_indices, bin_count)
    return bin_count


def find_bins(lat_hist, lon_hist, lat_index, lon_index):
    """
    identify all pixels that have lons in bin lon_index
    and lats in bin lat_index -- called by slow_avg

    Parameters
    ----------

    lat_hist: dictionary
        dict returned from do_hist

    lon_hist:  dictionary
         dict returned from do_hist

    lat_index:  int
           index of the latitude bin to retrieve

    lon_index: int
           index of the longitude bin to retrieve

    Returns
    -------

    pixel_list: list of ints
        indices of pixels with lon/lats in the specified lon/lat histogram bin
    """
    keep_lat = []
    keep_lon = []

    for count, the_index in enumerate(lat_hist['index_vec']):
        if the_index == lat_index:
            keep_lat.append(count)
    for count, the_index in enumerate(lon_hist['index_vec']):
        if the_index == lon_index:
            keep_lon.append(count)
    pixel_list = np.intersect1d(keep_lat, keep_lon)
    return pixel_list


def slow_avg(lat_hist, lon_hist, data_vec):
    """
    use pure python to average values binned by lat_hist and lon_hist

    Parameters
    ----------

    lat_hist: dictionary
        dict returned from running fast_hist on
        the lat. vector corresponding to data_vec

    lon_hist:  dictionary
         dict returned from fast_hist on
         the lon. vector corresponding to data_vec

    data_vec: vector (float)
         pixel values of radiance, temperature, etc.

    Returns
    -------

    gridded_image:  2d array (float)
        average values of data_vec pixels on lat_hist, lon_hist grid
    """
    num_lat_bins = len(lat_hist['edges_vec']) - 1
    num_lon_bins = len(lon_hist['edges_vec']) - 1
    gridded_image = np.full(
        [num_lat_bins, num_lon_bins], np.nan, dtype=np.float32)
    for lat_bin in range(num_lat_bins):
        for lon_bin in range(num_lon_bins):
            #
            # find the pixel numbers that belong in this bin
            #
            pixel_list = find_bins(lat_hist, lon_hist, lat_bin, lon_bin)
            if len(pixel_list) > 0:
                #
                # find the mean radiance if there are pixels
                #
                gridded_image[lat_bin, lon_bin] = data_vec[pixel_list].mean()
    return gridded_image


def slow_hist(data_vec, minval, maxval, numbins=None, binsize=None):
    """
    bin data_vec into numbins evenly spaced bins from left edge
    minval to right edge maxval

    Parameters
    ----------

    data_vec: numpy vector (float)
       data/pixels to be binned -- 1-d

    numbins:  int
       number of histogram bins
    minval:  float
        left edge
    maxval: float
        right edge

    Returns
    -------
      dictionary with keys:

      index_vec: ndarray 1-d float
        same size as data_vec, with entries containing bin number
        if data is smaller than left edge, missing value is -999
        if data is larger than right edge, missing value is -888

      count_vec: ndarray 1-d  int
        size numbins, with number of counts in each bin

      edges_vec: ndarray 1-d float
        size numbins+1 containing bin edges

      lowcount: int
         number of pixels smaller than left edge

      high count: 
         number of pixels larger than right edge
    """
    if numbins is None:
        numbins = int(np.ceil((maxval - minval) / binsize))
    else:
        binsize = (maxval - minval) / numbins
    bin_edges = [minval + (i * binsize) for i in range(numbins + 1)]
    bin_edges = np.array(bin_edges)
    bin_count = np.zeros([numbins, ], dtype=np.int)
    bin_index = np.zeros(data_vec.shape, dtype=np.int)
    bin_index[:] = -1
    lowcount = 0
    highcount = 0

    for i in range(len(data_vec)):
        float_bin = ((data_vec[i] - minval) / binsize)
        if float_bin < 0:
            lowcount += 1
            bin_index[i] = -999.
            continue
        if float_bin >= numbins:
            highcount += 1
            bin_index[i] = -888.
            continue
        int_bin = int(float_bin)
        bin_count[int_bin] += 1
        bin_index[i] = int_bin
    out = dict(index_vec=bin_index, count_vec=bin_count, edges_vec=bin_edges,
               lowcount=lowcount, highcount=highcount)

    return out


def xy_to_col_row(x, y, transform):
    """
    given x,y coordinates and the the asdfgeotransform from the modis_to_h5 file
    return the col, row of  the x,y point

    Parameters
    ----------

    x, y: float
       x and y mapprojection coordinates after any easting and northing have been removed

    transform: dict
        geotiff_args['adfgeotransform'] in the modis_to_h5 file

    Returns
    -------

    col, row: ints
       column and row of the pixel

    """
    corner_x, pix_width, row_rot, corner_y, col_rot, pix_height = transform
    col = (x - corner_x) / pix_width
    #
    # chop off the decimal
    #
    col = np.floor(col)
    row = (y - corner_y) / pix_height
    #
    # chop off the decimal
    #
    row = np.floor(row)
    return col.astype(np.int), row.astype(np.int)


def col_row_to_xy(col, row, transform):
    corner_x, pix_width, row_rot, corner_y, col_rot, pix_height = transform
    x = (col * pix_width) + corner_x
    y = (row * pix_height) + corner_y
    return x, y


def trim_track(x, y, image, transform, x0=0, y0=0):
    """
    find x,y indices that are inside image

    Parameters
    ----------

    image: float32 array
        Projected image produced by pyresample with valid values inside the boundaries, and np.nan
        outside

    x,y:  float, float
       x,y coords of lon,lat points of ground track

    x0,y0: float32, float32
       basemap.projparams easting and northing

    transform: vector
       adfgeotransform from pyresample projection

    Returns
    -------

    in_box: logical vecto
       vector of length len(x) -- true if index in image
    """
    x, y = np.asarray(x), np.asarray(y)
    x = x - x0
    y = y - y0
    col, row = xy_to_col_row(x, y, transform)
    in_box = []
    for the_row, the_col in zip(row, col):
        try:
            if np.isnan(image[the_row, the_col]):
                #
                # missing data, don't plot
                #
                in_box.append(False)
            else:
                #
                # good data, plot
                #
                in_box.append(True)
        except IndexError:
            in_box.append(False)
    in_box = np.array(in_box)
    return in_box


def gc_distance(lons, lats):
    """
    find the distance between a set of lon,lat points
    in km using a great circle

    Parameters
    ---------

    lons, lats: vector float
      lons and lats points (deg E and deg N

    Returns

    distance: vector float
       vector of length len(lons) with distance beteen points (km)

    """
    meters2km = 1.e3
    great_circle = pyproj.Geod(ellps='WGS84')
    distance = [0]
    start = (lons[0], lats[0])
    for index in np.arange(1, len(lons)):
        azi12, azi21, step = great_circle.inv(lons[index - 1], lats[index - 1],
                                              lons[index], lats[index])
        distance.append(distance[index - 1] + step)
    distance = np.array(distance) / meters2km
    return distance
