import os
import subprocess
from pyramid.view import view_config


@view_config(route_name='home', renderer='json')
def my_view(request):
    scene = request.matchdict['id']
    b1 = request.matchdict['b1']
    b2 = request.matchdict['b2']
    b3 = request.matchdict['b3']
    awsRoot = 'http://landsat-pds.s3.amazonaws.com/L8/'
    path = scene[3:6]
    row = scene[6:9]

    # Create a subdirectory
    subprocess.call(['mkdir', scene])

    # Strip the geospatial metadata from a legitimate Landsat band.
    subprocess.call(['listgeo', '-tfw', 'SACRIFICE.TIF'])

    # Apply the stripped world file to the band previews.
    subprocess.call(['geotifcp', '-e', 'SACRIFICE.tfw', sceneID + '_B2.TIF', 'B2.TIF'])
    subprocess.call(['geotifcp', '-e', 'SACRIFICE.tfw', sceneID + '_B3.TIF', 'B3.TIF'])
    subprocess.call(['geotifcp', '-e', 'SACRIFICE.tfw', sceneID + '_B5.TIF', 'B5.TIF'])

    # Resize each band
    subprocess.call(['gdal_translate', '-outsize', '15%', '15%', 'B2.TIF', sceneID + '/' + sceneID + '_B2.TIF'])
    subprocess.call(['gdal_translate', '-outsize', '15%', '15%', 'B3.TIF', sceneID + '/' + sceneID + '_B3.TIF'])
    subprocess.call(['gdal_translate', '-outsize', '15%', '15%', 'B5.TIF', sceneID + '/' + sceneID + '_B5.TIF'])

    # Call landsat-util
    subprocess.call(['landsat', 'process', sceneID, '--bands', '532'])

    # Convert black to transparent and save as PNG
    lsUtilPath = '/Users/Jacques/landsat/processed/' + sceneID + '/'
    print lsUtilPath

    subprocess.call(['convert', '-transparent', 'black', lsUtilPath + sceneID + '_bands_532.TIF', 'final.png'])

    return {'project': 'app'}

