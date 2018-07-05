# coding: utf-8

# # Create ERDDAP dataset.xml from NetCDF file
# Create an ERDDAP <dataset> snippet by reading a NetCDF CF-1.6 DSG **`featureType=TimeSeries`** file
# copied from https://github.com/rsignell-usgs/notebook/blob/master/ERDDAP/ooi_datasets_xml.py
# In[1]:

import numpy as np
import netCDF4
import uuid
import glob
import os
import string
from jinja2 import Environment, FileSystemLoader
import pprint
env = Environment(loader=FileSystemLoader('templates'))


# In[2]:

# generate random 12 digit string for DatasetID
def random_name():
    rstr = uuid.uuid4().hex[0:12]
    rstr = ('_{}_{}_{}'.format(rstr[:4],rstr[4:8],rstr[8:]))
    return rstr


# In[3]:

print(random_name())


# ERDDAP Valid values are: double (64-bit floating point), float (32-bit floating point), long (64-bit signed integer), int (32-bit signed integer), short (16-bit signed integer), byte (8-bit signed integer), char (essentially: 16-bit unsigned integer), boolean, and String (any length).

# In[4]:

dmap = {'float64':'double',
        'float32':'float',
        'int64':'long',
        'int32':'int',
        'int16':'short',
        'b':'byte',
        'uint16':'char',
        'bool':'boolean',
        'S1':'String',
        'bytes8':'String',
        'string':'String'}


# In[5]:

def dvar_info(nc, dmap=None):
    # Assign sourceName:[destinationName, ioos_category, dataType, colorBarMinimum, colorBarMaximum]
    dvars = {}
    for var in list(nc.variables):
        # default is ioos_category "Unknown".  Don't calculate limits yet.
        erddap_type = dmap[nc[var].dtype.name]
        dvars[var]={'destin)ationName':var, 
                    'ioos_category':'Unknown', 
                    'dataType':erddap_type, 
                    'colorBarMinimum':None, 
                    'colorBarMaximum':None,
                    'units':None}
        # calculate limits for all vars that are not strings
        if nc[var].units:
            dvars[var]['units']=nc[var].units
        if erddap_type is not 'String':
            dvars[var]['colorBarMinimum']= nc[var][:].min()
            dvars[var]['colorBarMaximum']= nc[var][:].max()
        if np.ma.is_masked(dvars[var]['colorBarMaximum']):
             dvars[var]['colorBarMaximum'] = None
        if np.ma.is_masked(dvars[var]['colorBarMinimum']):
             dvars[var]['colorBarMinimum'] = None
#        pprint.pprint(dvars)
#        print(nc[var].units)
#        sys.exit()
    # set destinationName, ioos_category, datatype and limits for coordinate variables
   # tvar = nc.get_variables_by_attributes(long_name='time')[0]
   # dvars[tvar.name] = {'destinationName':'time', 
   #             'ioos_category':'Time', 
   #             'dataType':dmap[tvar.dtype.name], 
   #             'colorBarMinimum':None, 
   #             'colorBarMaximum':None}

   # xvar = nc.get_variables_by_attributes(long_name='array of u-grid longitudes')[0]
   # dvars[xvar.name] = {'destinationName':'longitude', 
   #             'ioos_category':'Location', 
   #             'dataType':dmap[xvar.dtype.name], 
   #             'colorBarMinimum':-180.0, 
   #             'colorBarMaximum':180.0}

   # yvar = nc.get_variables_by_attributes(long_name='array of u-grid latitudes')[0]
   # dvars[yvar.name] = {'destinationName':'latitude', 
   #             'ioos_category':'Location', 
   #             'dataType':dmap[yvar.dtype.name], 
   #             'colorBarMinimum':-90.0, 
   #             'colorBarMaximum':90.0}

   # zvar = nc.get_variables_by_attributes(long_name='ocean depth at U points')[0]
   # dvars[zvar.name] = {'destinationName':'altitude', 
   #             'ioos_category':'Location', 
   #             'dataType':dmap[zvar.dtype.name], 
   #             'colorBarMinimum':-8000.0, 
   #             'colorBarMaximum':8000.0,
   #             'units':'cm'}
    return dvars


# In[6]:

opath = 'xml'
ncpath = '*.nc'
for ncfile in glob.glob(ncpath):
    drive, path = os.path.splitdrive(ncfile)
    path, filename = os.path.split(path)
    print(ncfile)
    fileDir = path
    nodeID = '3192'
    versDate = '20051108'
    datasetID = nodeID+'v'+versDate # do we start with bcodmo?
    reloadEveryNMinutes = '10080'
    fileNameRegex = filename
    subsetVariables = 'latitude, longitude, altitude, feature_type_instance'
    infoUrl = 'http://usjgofs.whoi.edu/mzweb/smppi/doney3.html'
    cdm_timeseries_variables = subsetVariables
    # open a NetCDF CF-1.6+, DSG featureType=timeSeries file
    nc = netCDF4.Dataset(ncfile)
    keywords = ','.join(list(nc.variables))
    dvars = dvar_info(nc, dmap=dmap)
#    if 'timeSeries' in nc.featureType:
    template = env.get_template('timeSeries.xml')
    ds_xml = template.render(datasetID=datasetID,
                          reloadEveryNMinutes=reloadEveryNMinutes,
                          fileDir=fileDir,
                          fileNameRegex=fileNameRegex,
                          subsetVariables=subsetVariables,
                          infoUrl=infoUrl,
                          cdm_timeseries_variables=cdm_timeseries_variables,
                          keywords=keywords,
                          dvars=dvars)   
    ofile = os.path.join(opath,'{}.xml'.format(filename))

    with open(ofile, "w") as text_file:
        text_file.write("{}".format(ds_xml))
