"""
module for resampling and storing modis level1b swath data
at 1 km resolution

functions:

* make_projectname:  make an output h5 filename with same root as 
  level1b file, but include the string reproject

* modisl1b_resample:  read channel 1 radiance and lat/lon
  for each pixel and resample onto a lambert equal azimuth projection

* write_h5: write an h5 file with the resampled channel 1 plus projection
  information
"""

import h5py
import numpy as np
import pyproj
import pyresample
from pyresample import kd_tree
from pyresample import geometry
from matplotlib import pyplot as plt
from e582utils.modismeta_read import parseMeta
from e582utils.data_read import download
from mpl_toolkits.basemap import Basemap
import json
from e582lib.modis_chans import chan_dict

def make_projectname(mxd02file,chan_list):
    """
    given a level1b Modis radiance file name, 
    produce a new name that includes the word reproject
    and the channels that were resampled

    usage:

    make_projectname('MYD021KM.A2016224.2100.006.2016225153002.h5',['8','9'])

    returns  MYD021KM.A2016224.2100.006.reproject.c_8_9.h5

    Parameters
    ----------

    mxd02file: str
       level1b MYD021KM or MOD021KM radiance file name

    chan_list: list
       channels to resample onto lambert azimuthal projections, i.e. ['1','4','3']


    Returns
    -------
    
    out_file: str
       name of reprojected file written by modis_to_h5.py
    """
    rad_parts = mxd02file.split('.')[:4]
    #['MYD021KM', 'A2016224', '2100', '006']
    chan_string='_'.join(chan_list)
    suffix='reproject.c_{}.h5'.format(chan_string)
    rad_parts.extend([suffix])
    out_file='.'.join(rad_parts)
    return out_file


def modisl1b_resample(mxd02file,mxd03file,chan_list,fill_value= -99999.):
    """
    given level1b 1km radiance file and geometry file
    return projected images plus supporting data.
    The resampling uses pyresample with a lambert azimuthal
    equal area projection with lat_0 and lon_0 at
    the scene center

    
    Parameters
    ----------

    mxd02file: str
        file name NASA Laadsweb level1b Terra (MOD02) or Aqua (MYD02) hdf file converted to h5
        format

    mxd03file: str
        file name NASA Laadsweb level geometry file for Terra (MOD03) or Aqua (MYD03) hdf file converted to h5 format

    chan_list: vecto of strings
        channels to resample onto lambert azimuthal projections, i.e. ['1','4','3']

    fill_value: float
        number to indicate missing grid data.  Make sure this number is not in the range of actual
        data values

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
           dictionary with projection information for geotiff

        fill_value: float32
           fill value for missing data in channels (these resampled pixels are set to
           np.nan after resample)
    """
    radiance_list=[]
    for the_chan in chan_list:
    #
    # read channel channels
    #
        index = chan_dict[the_chan]['index']
        field_name = chan_dict[the_chan]['field_name']
        scale_name=chan_dict[the_chan]['scale']
        offset_name=chan_dict[the_chan]['offset']
        
        with h5py.File(mxd02file,'r') as h5_file:
            chan=h5_file['MODIS_SWATH_Type_L1B']['Data Fields'][field_name][index,:,:]
            hdf_fill_value=h5_file['MODIS_SWATH_Type_L1B']['Data Fields'][field_name].attrs['_FillValue']
            chan=chan.astype(np.float32)
            #
            # problem with modis fill_value for channel 29 -- says it should be 65535 but it is actually 65531
            # accept anything larger than 60000
            #
            if hdf_fill_value == 65535:
                hit = chan > 65530
            else:
                hit = chan == hdf_fill_value
            chan[hit]=np.nan
            scale=h5_file['MODIS_SWATH_Type_L1B']['Data Fields'][field_name].attrs[scale_name][...]
            offset=h5_file['MODIS_SWATH_Type_L1B']['Data Fields'][field_name].attrs[offset_name][...]
            chan_calibrated =(chan - offset[index])*scale[index]
            chan_calibrated = chan_calibrated.astype(np.float32)  #convert from 64 bit to 32bit to save space
            print('in e582lib.modis_resample: found {} bad pixels'.format(np.sum(np.isnan(chan_calibrated))))
            chan_calibrated=np.ma.masked_invalid(chan_calibrated)
            radiance_list.append(chan_calibrated)
    for index,chan in enumerate(radiance_list):
        print('index and mean {} {}'.format(index,np.mean(chan.ravel())))

    with h5py.File(mxd03file) as geo_file:
        lon_data=geo_file['MODIS_Swath_Type_GEO']['Geolocation Fields']['Longitude'][...]
        lat_data=geo_file['MODIS_Swath_Type_GEO']['Geolocation Fields']['Latitude'][...]
    #
    # set up the lambert azimuthal equal area projection with corners large enough
    # to fit image
    #
    corners=parseMeta(mxd02file)
    proj_id = 'laea'
    datum = 'WGS84'
    lat_0_txt = '{lat_0:5.2f}'.format_map(corners)
    lon_0_txt= '{lon_0:5.2f}'.format_map(corners)
    area_dict = dict(datum=datum,lat_0=lat_0_txt,lon_0=lon_0_txt,
                     proj=proj_id,units='m')
    prj=pyproj.Proj(area_dict)
    x, y = prj(corners['lon_list'], corners['lat_list'])
    minx,maxx=np.min(x),np.max(x)
    miny,maxy=np.min(y),np.max(y)
    #
    # back transform these to lon/lat
    #
    llcrnrlon,llcrnrlat=prj(minx,miny,inverse=True)
    urcrnrlon,urcrnrlat=prj(maxx,maxy,inverse=True)
    #
    # 1300 m pixels are a reasonable compromise between the smallest 1km pixels and the biggest
    # 4 km pixels at the sides of the swath
    #
    area_extent=[minx,miny,maxx,maxy]
    x_pixel=1.3e3
    y_pixel=1.3e3
    #
    # figure out how many pixels in the image
    #
    xsize=int((area_extent[2] - area_extent[0])/x_pixel)
    ysize=int((area_extent[3] - area_extent[1])/y_pixel)
    #
    #  here's the dictionary we need for basemap
    #
    basemap_args=dict()
    basemap_args['ellps'] = 'WGS84'
    basemap_args['llcrnrlon'] = llcrnrlon
    basemap_args['llcrnrlat'] = llcrnrlat
    basemap_args['urcrnrlon'] = urcrnrlon
    basemap_args['urcrnrlat'] = urcrnrlat
    basemap_args['projection'] = area_dict['proj']
    basemap_args['lat_0']=corners['lat_0']
    basemap_args['lon_0']=corners['lon_0']
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
    # first copy each of the reprojected channels into input_array,
    # which is dimensioned [height,width,num_chans]
    #
    #  pyresample will resample all num_chans channels onto the same grid
    #
    num_chans=len(chan_list)
    dim_list=list(radiance_list[0].shape)
    dim_list.append(num_chans)
    input_array=np.empty(dim_list,dtype=np.float32)
    for index,chan in enumerate(radiance_list):
        input_array[:,:,index]=chan[:,:]
    #
    # now project all the images onto the lambert map
    #
    area_def_args=dict(area_id=area_id,area_name=area_name,proj_id=proj_id,
                      area_dict=area_dict,xsize=xsize,ysize=ysize,area_extent=area_extent)
    area_def = geometry.AreaDefinition(area_id, area_name, proj_id, 
                                       area_dict, xsize,ysize, area_extent)
    swath_def = geometry.SwathDefinition(lons=lon_data, lats=lat_data)
    #
    # here is the resample step using 5 km region of influence (see pyresample docs)
    #
    channels = kd_tree.resample_nearest(swath_def, input_array,
                                         area_def, radius_of_influence=25000, nprocs=2,fill_value=None)
    # channels = kd_tree.resample_gauss(swath_def, input_array,
    #                                     area_def, radius_of_influence=50000,sigmas=[25000,25000],nprocs=2,fill_value=None)
    #
    # replace the  number used for fill_value with np.nan
    #
    # nan_fill_value = np.array([np.nan],dtype=np.float32)[0]
    # channels[channels==fill_value]=nan_fill_value
    print('running modisl1b_resample: here are the channels to be resampled')
    for index in range(num_chans):
        print('channel and mean {} {}'.format(chan_list[index],np.nanmean(channels[:,:,index].ravel())))
    #
    # replace negative fill_value with np.nan (32 bit)
    #
    print('pyresample area_def information:')
    print('\ndump area definition:\n{}\n'.format(area_def))
    print('\nx and y pixel dimensions in meters:\n{}\n{}\n'.format(area_def.pixel_size_x,area_def.pixel_size_y))
    #
    # here is the dictionary for geotiff creation -- save for future use in rasterio
    #
    adfgeotransform = [area_def.area_extent[0], area_def.pixel_size_x, 0,
                   area_def.area_extent[3], 0, -area_def.pixel_size_y]
    proj4_string=area_def.proj4_string
    proj_id = area_def.proj_id
    height,width,num_chans=channels.shape
    geotiff_args = dict(width=width,height=height,adfgeotransform=adfgeotransform,
         proj4_string=proj4_string,proj_id=proj_id)
    out_dict=dict(channels=channels,area_def_args=area_def_args,basemap_args=basemap_args,geotiff_args=geotiff_args,
                  fill_value=fill_value)
    print('completed modisl1b_resample')
    return out_dict


def write_h5(out_file=None,channels=None,area_def_args=None,
             basemap_args=None,geotiff_args=None,
             fill_value=None,chan_list=None,in_file=None):
    """
    Create an hdf5 file that contains resampled modis level1b data (channels)
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
       list of string channel names used by modis_chans.chan_dict to
       select modis channels in the channels array

    Returns
    -------

       side effect: write information into hdf5 file outfile
    """
    print('hit: ',channels.shape)
    geotiff_string = json.dumps(geotiff_args,indent=4)
    basemap_string = json.dumps(basemap_args,indent=4)
    print('here: --\n{}--\n'.format(area_def_args))
    area_def_string = json.dumps(area_def_args,indent=4)
    height,width,num_chans=channels.shape
    with h5py.File(out_file,'w') as f:
        group=f.create_group('channels')
        for index,chan_name in enumerate(chan_list):
            the_chan=channels[:,:,index]
            dset=group.create_dataset(chan_name,the_chan.shape,dtype=the_chan.dtype)
            dset[...]=the_chan[...]
            dset.attrs['units']=chan_dict[chan_name]['units']
            dset.attrs['wavelength_um']=chan_dict[chan_name]['wavelength_um']
            dset.attrs['modis_chan']=chan_name
        f.attrs['geotiff_args']=geotiff_string
        f.attrs['basemap_args']=basemap_string
        f.attrs['area_def_args']=area_def_string
        f.attrs['fill_value']=fill_value
        f.attrs['level1b_file']=in_file
    return None


if __name__ == "__main__":

    myd02_name='MYD021KM.A2016224.2100.006.2016225153002.h5'
    download(myd02_name)
    myd03_name='MYD03.A2016224.2100.006.2016225152335.h5'
    download(myd03_name)
    
    out_file='test.h5'
    chan_list=['1','4','31']
    project_channels=modisl1b_resample(myd02_name,myd03_name,chan_list)
    project_channels['out_file']='test.h5'
    project_channels['in_file']=myd02_name
    project_channels['chan_list']=chan_list
    write_h5(**project_channels)
    
    from matplotlib import cm
    cmap=cm.autumn  #see http://wiki.scipy.org/Cookbook/Matplotlib/Show_colormaps
    cmap.set_over('w')
    cmap.set_under('b',alpha=0.2)
    cmap.set_bad('c',alpha=0.4) 

    cmap_div=cm.YlGnBu_r 
    cmap_div.set_over('w')
    cmap_div.set_under('b',alpha=0.2)
    cmap_div.set_bad('c',alpha=0.4) 

    
    plt.close('all')
    fig,ax = plt.subplots(2,2, figsize=(16,16))
    #
    # add the resolutiona and axis in separately, so we can
    # change in other plots
    #
    num_meridians=180
    num_parallels = 90
    lon_sep, lat_sep = 5,5
    parallels = np.arange(-90, 90, lat_sep)
    meridians = np.arange(0, 360, lon_sep)
    limits={0:{'vmin':0,'vmax':0.4},
            1:{'vmin':0,'vmax':0.4},
            2:{'vmin':5,'vmax':10},
            3:{'vmin':-0.05,'vmax':0.05}}
    for index,the_ax in enumerate(ax.ravel()):
        basemap_kws=dict(resolution='c',ax=the_ax)
        basemap_kws.update(project_channels['basemap_args'])
        bmap=Basemap(**basemap_kws)
        if index==3:
            channel=project_channels['channels'][:,:,0] - project_channels['channels'][:,:,1]
            chan_list.append('1-4')
            cmap=cmap_div
            cbar_label='reflectivity difference'
        elif index==2:
            channel=project_channels['channels'][:,:,index]
            cbar_label='radiance W/m^2/sr/um'
        else:
            cbar_label='reflectance'
            channel=project_channels['channels'][:,:,index]
        col = bmap.imshow(channel, origin='upper',cmap=cmap, **limits[index])
        bmap.drawparallels(parallels, labels=[1, 0, 0, 0],
                           fontsize=10, latmax=90)
        bmap.drawmeridians(meridians, labels=[0, 0, 0, 1],
                           fontsize=10, latmax=90)
        bmap.drawcoastlines()
        _=the_ax.set(title='vancouver chan {}'.format(chan_list[index]))
        colorbar=fig.colorbar(col, shrink=0.5, pad=0.05,extend='both',ax=the_ax)
        colorbar.set_label(cbar_label,rotation=-90,verticalalignment='bottom')
    plt.show()
