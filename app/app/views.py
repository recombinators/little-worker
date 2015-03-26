import os
import subprocess
from pyramid.view import view_config


@view_config(route_name='home', renderer='json')
def my_view(request):
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

    import pdb; pdb.set_trace()

    # Create a subdirectory
    subprocess.call(['mkdir', scene])

    # Download a sacrificial band.
    subprocess.call(['landsat', 'download', scene, '--bands', '1'])

    # Strip the geospatial metadata from a legitimate Landsat band.
    subprocess.call(['listgeo', '-tfw', scene + '_B1.TIF'])

    # Create a world.tfw to reapply to previews.
    subprocess.call(['mv', scene + '_B1.tfw', 'world.tfw'])

    # Curl previews from AWS
    subprocess.call(['wget', o1])
    subprocess.call(['wget', o2])
    subprocess.call(['wget', o3])

    return o1

    # # Apply the stripped world file to the band previews.
    # subprocess.call(['geotifcp', '-e', 'world.tfw', scene + '_B2.TIF', 'B2-thumbnail.TIF'])
    # subprocess.call(['geotifcp', '-e', 'world.tfw', scene + '_B3.TIF', 'B3-thumbnail.TIF'])
    # subprocess.call(['geotifcp', '-e', 'world.tfw', scene + '_B5.TIF', 'B5-thumbnail.TIF'])

    # # Resize each band
    # subprocess.call(['gdal_translate', '-outsize', '15%', '15%', 'B2.TIF', sceneID + '/' + sceneID + '_B2.TIF'])
    # subprocess.call(['gdal_translate', '-outsize', '15%', '15%', 'B3.TIF', sceneID + '/' + sceneID + '_B3.TIF'])
    # subprocess.call(['gdal_translate', '-outsize', '15%', '15%', 'B5.TIF', sceneID + '/' + sceneID + '_B5.TIF'])

    # # Call landsat-util
    # subprocess.call(['landsat', 'process', sceneID, '--bands', '532'])

    # # Convert black to transparent and save as PNG
    # lsUtilPath = '/Users/Jacques/landsat/processed/' + sceneID + '/'
    # print lsUtilPath

    # subprocess.call(['convert', '-transparent', 'black', lsUtilPath + sceneID + '_bands_532.TIF', 'final.png'])

    # return {'project': 'app'}

