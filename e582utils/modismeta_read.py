#!/usr/bin/env python
"""
   defines a class that reads the NASA hdfeos CoreMetadata.0 attribute
   and stores the orbitnumber, equator crossing time, 
   image lat/lon corners

   the function parseMeta creates an instance of this class
   and returns a dictionary containing the information
"""
from __future__ import print_function

import types
import numpy as np
import h5py
import argparse

class metaParse:
    def __init__(self,metaDat):
        import re
        self.metaDat=str(metaDat,'utf-8')
        #search for the string following the words "VALUE= "
        self.stringObject=\
             re.compile('.*VALUE\s+=\s"(?P<value>.*)"',re.DOTALL)
        #search for a string that looks like 11:22:33
        self.timeObject=\
             re.compile('.*(?P<time>\d{2}\:\d{2}\:\d{2}).*',re.DOTALL)
        #search for a string that looks like 2006-10-02
        self.dateObject=\
             re.compile('.*(?P<date>\d{4}-\d{2}-\d{2}).*',\
                        re.DOTALL)
        #search for a string that looks like "(anything between parens)"
        self.coordObject=re.compile('.*\((?P<coord>.*)\)',re.DOTALL)
        #search for a string that looks like "1234"
        self.orbitObject=\
             re.compile('.*VALUE\s+=\s(?P<orbit>\d+)\n',re.DOTALL)

    def getstring(self,theName):
        theString=self.metaDat.split(theName)
        theString = [str(item) for item in theString]
        #should break into three pieces, we want middle
        out=[item[:50] for item in theString]
        if len(theString) ==3:
            theString=theString[1]
        else:
            
            altString=self.altrDat.split(theName)
            altString = [str(item) for item in altString]
            if len(altString) == 3:
                theString=altString[1]
            else:
                raise Exception("couldn't parse %s" % (theName,))
        return theString
        

    def __call__(self,theName):
        if theName=='CORNERS':
            import string
            #look for the corner coordinates by searching for
            #the GRINGPOINTLATITUDE and GRINGPOINTLONGITUDE keywords
            #and then matching the values inside two round parenthesis
            #using the coord regular expression
            theString= self.getstring('GRINGPOINTLATITUDE')
            theMatch=self.coordObject.match(theString)
            theLats=theMatch.group('coord').split(',')
            theLats=[float(item) for item in theLats]
            theString= self.getstring('GRINGPOINTLONGITUDE')
            theMatch=self.coordObject.match(theString)
            theLongs=theMatch.group('coord').split(',')
            theLongs=[float(item) for item in theLongs]
            lon_list,lat_list = np.array(theLongs),np.array(theLats)
            min_lat,max_lat=np.min(lat_list),np.max(lat_list)
            min_lon,max_lon=np.min(lon_list),np.max(lon_list)
            lon_0 = (max_lon + min_lon)/2.
            lat_0 = (max_lat + min_lat)/2.
            corner_dict = dict(lon_list=lon_list,lat_list=lat_list,
                               min_lat=min_lat,max_lat=max_lat,min_lon=min_lon,
                               max_lon=max_lon,lon_0=lon_0,lat_0=lat_0)
            value=corner_dict
        #regular value
        else:
            theString= self.getstring(theName)
            #orbitnumber doesn't have quotes
            if theName=='ORBITNUMBER':
                theMatch=self.orbitObject.match(theString)
                if theMatch:
                    value=theMatch.group('orbit')
                else:
                    raise Exception("couldn't fine ORBITNUMBER")
            #expect quotes around anything else:
            else:
                theMatch=self.stringObject.match(theString)
                if theMatch:
                    value=theMatch.group('value')
                    theDate=self.dateObject.match(value)
                    if theDate:
                        value=theDate.group('date') + " UCT"
                    else:
                        theTime=self.timeObject.match(value)
                        if theTime:
                            value=theTime.group('time') + " UCT"
                else:
                    raise Exception("couldn't parse %s" % (theName,))
        return value

def parseMeta(filename):
    """
    Parameters
    ----------

    filename: str
       name of an h5 modis level1b file

    Returns
    -------
    
    outDict: dict
        key, value:

         lat_list: np.array
            4 corner latitudes
         lon_list: np.array
            4 corner longitudes
         max_lat: float
            largest corner latitude
         min_lat: float
            smallest corner latitude
         max_lon: float
            largest corner longitude
         min_lon: float
            smallest corner longitude
         daynight: str
            'Day' or 'Night'
         starttime: str
            swath start time in UCT
         stoptime: str
            swath stop time in UCT
         startdate: str
            swath start datein UCT
         orbit: str
            orbit number
         equatordate: str
            equator crossing date in UCT
         equatortime: str
            equator crossing time in UCT
         nasaProductionDate: str
            date file was produced, in UCT

    
    """
    if not isinstance(filename,str):
        raise Exception('expecting an h5 filename, got {}'.format(filename))
    with h5py.File(filename,'r') as infile:
        attr_list=list(infile.attrs)
        for item in attr_list:
            if item[:8]=='CoreMeta':
                key=item
                metaDat=infile.attrs[item]
            if item[:8] =='ArchiveM':
                altrDat=infile.attrs[item]
            else:
                altrDat=None

    parseIt=metaParse(metaDat)
    outDict={}
    outDict['orbit']=parseIt('ORBITNUMBER')
    outDict['filename']=parseIt('LOCALGRANULEID')
    outDict['stopdate']=parseIt('RANGEENDINGDATE')
    outDict['startdate']=parseIt('RANGEBEGINNINGDATE')
    outDict['starttime']=parseIt('RANGEBEGINNINGTIME')
    outDict['stoptime']=parseIt('RANGEENDINGTIME')
    outDict['equatortime']=parseIt('EQUATORCROSSINGTIME')
    outDict['equatordate']=parseIt('EQUATORCROSSINGDATE')
    outDict['nasaProductionDate']=parseIt('PRODUCTIONDATETIME')
    outDict['daynight']=parseIt('DAYNIGHTFLAG')
    corners=parseIt('CORNERS')
    outDict.update(corners)
    return outDict

if __name__=='__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('h5_file',type=str,help='name of h5 file')
    args=parser.parse_args()
    out=parseMeta(args.h5_file)
    print(out)
