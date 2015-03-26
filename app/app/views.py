import os
import subprocess
from pyramid.view import view_config

@view_config(route_name='home', renderer='json')
def my_view(request):
    dir = os.path.dirname(os.path.abspath(__file__))
    scene = request.matchdict['id']
    root = 'http://landsat-pds.s3.amazonaws.com/L8/'
    path = scene[3:6]
    row = scene[6:9]
    b1 = request.matchdict['b1']
    b2 = request.matchdict['b2']
    b3 = request.matchdict['b3']
    o1 = root + path + '/' + row + '/' + scene + '/' + scene + '_B' + b1 + '.TIF.ovr'
    o2 = root + path + '/' + row + '/' + scene + '/' + scene + '_B' + b2 + '.TIF.ovr'
    o3 = root + path + '/' + row + '/' + scene + '/' + scene + '_B' + b3 + '.TIF.ovr'

    # Create a subdirectory
    print 'Creating folder'
    subprocess.call(['mkdir', scene])

    # Download a sacrificial band.
    print 'Downloading sacrificial band'
    subprocess.call(['landsat', 'download', scene, '--bands', '1'])

    # Strip the geospatial metadata from a legitimate Landsat band.
    # Create a world.tfw to reapply to previews.
    print 'Extracting TFW'
    subprocess.call(['listgeo', '-tfw', scene + '_B1.TIF'])
    subprocess.call(['mv', scene + '_B1.tfw', 'world.tfw'])

    # Curl previews from AWS
    print 'Downloading preview images'
    subprocess.call(['wget', '-P', dir, o1])
    subprocess.call(['wget', '-P', dir, o2])
    subprocess.call(['wget', '-P', dir, o3])

    # Apply the stripped world file to the band previews.
    print 'Applying TFW to preview images'
    subprocess.call(['geotifcp', '-e', 'world.tfw', scene + '_B2.TIF', 'B2-thumbnail.TIF'])
    subprocess.call(['geotifcp', '-e', 'world.tfw', scene + '_B3.TIF', 'B3-thumbnail.TIF'])
    subprocess.call(['geotifcp', '-e', 'world.tfw', scene + '_B5.TIF', 'B5-thumbnail.TIF'])

    # # Resize each band
    # print 'Resizing preview images'
    # subprocess.call(['gdal_translate', '-outsize', '15%', '15%', 'B2.TIF', sceneID + '/' + sceneID + '_B2.TIF'])
    # subprocess.call(['gdal_translate', '-outsize', '15%', '15%', 'B3.TIF', sceneID + '/' + sceneID + '_B3.TIF'])
    # subprocess.call(['gdal_translate', '-outsize', '15%', '15%', 'B5.TIF', sceneID + '/' + sceneID + '_B5.TIF'])

    # # Call landsat-util
    # print 'Generating preview composite'
    # subprocess.call(['landsat', 'process', sceneID, '--bands', '532'])

    # # Convert black to transparent and save as PNG
    # print 'Convert pure black to transparent and save as png.'
    # lsUtilPath = '/Users/Jacques/landsat/processed/' + sceneID + '/'
    # print lsUtilPath

    # subprocess.call(['convert', '-transparent', 'black', lsUtilPath + sceneID + '_bands_532.TIF', 'final.png'])
