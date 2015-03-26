import os
import sys
sys.path.append('landsat-util/landsat')
import subprocess
import boto
from boto.s3.key import Key
from pyramid.view import view_config
from homura import download
from downloader import Downloader
from image import Process
from pyramid.httpexceptions import HTTPFound

dir = os.getcwd()

AWS_ACCESS_KEY_ID = os.environ['AWS_ACCESS_KEY_ID']
AWS_SECRET_ACCESS_KEY = os.environ['AWS_SECRET_ACCESS_KEY']


@view_config(route_name='home', renderer='json')
def my_view(request):
    dir = os.getcwd() + '/scenes'
    scene = request.matchdict['id']
    root = 'http://landsat-pds.s3.amazonaws.com/L8/'
    path = scene[3:6]
    row = scene[6:9]
    b1 = request.matchdict['b1']
    b2 = request.matchdict['b2']
    b3 = request.matchdict['b3']

    # Builds a string pointing towards the AWS Landsat datasets
    # IE: http://landsat-pds.s3.amazonaws.com/L8/139/045/LC81390452014295LGN00/LC81390452014295LGN00_B3.TIF.ovr
    o1 = root + path + '/' + row + '/' + scene + '/' + scene + '_B' + b1 + '.TIF.ovr'
    o2 = root + path + '/' + row + '/' + scene + '/' + scene + '_B' + b2 + '.TIF.ovr'
    o3 = root + path + '/' + row + '/' + scene + '/' + scene + '_B' + b3 + '.TIF.ovr'

    # Create a subdirectory
    if not os.path.exists(dir):
        os.makedirs(dir)

    # Download a sacrificial band using Landsat-util
    dl = Downloader(verbose=True, download_dir=dir)
    dl.download(['LC81390452014295LGN00'], ['1'])

    # Strip the geospatial metadata from a legitimate Landsat band.
    # Create a world.tfw to reapply to previews.
    subprocess.call(['listgeo', '-tfw', dir + '/' + scene + '/' + scene + '_B1.TIF'])
    os.rename(dir + '/' + scene + '/' + scene + '_B1.tfw', dir + '/' + 'world.tfw')

    # Download previews from AWS
    download(url=o1, path=dir)
    download(url=o2, path=dir)
    download(url=o3, path=dir)

    # Apply the stripped world file to the band previews.
    subprocess.call(['geotifcp', '-e', dir + '/world.tfw', dir + '/' + scene + '_B2.TIF.ovr', dir + '/B2-geo.TIF'])
    subprocess.call(['geotifcp', '-e', dir + '/world.tfw', dir + '/' + scene + '_B3.TIF.ovr', dir + '/B3-geo.TIF'])
    subprocess.call(['geotifcp', '-e', dir + '/world.tfw', dir + '/' + scene + '_B5.TIF.ovr', dir + '/B5-geo.TIF'])

    # Resize each band
    # subprocess.call(['mkdir', dir + '/ready'])
    subprocess.call(['gdal_translate', '-outsize', '15%', '15%', dir + '/B2-geo.TIF', dir + '/' + scene + '/' + scene + '_B2.TIF'])
    subprocess.call(['gdal_translate', '-outsize', '15%', '15%', dir + '/B3-geo.TIF', dir + '/' + scene + '/' + scene + '_B3.TIF'])
    subprocess.call(['gdal_translate', '-outsize', '15%', '15%', dir + '/B5-geo.TIF', dir + '/' + scene + '/' + scene + '_B5.TIF'])

    # Call landsat-util
    # import pdb; pdb.set_trace()
    t = dir + '/' + scene
    processor = Process(t, [5,3,2], dir, verbose=True)
    processor.run(pansharpen=False)

    # Convert black to transparent and save as PNG
    subprocess.call(['convert', '-transparent', 'black', dir + '/' + scene + '/' + scene + '_bands_532.TIF', dir + '/final.png'])

    conne = boto.connect_s3(aws_access_key_id=AWS_ACCESS_KEY_ID,
         aws_secret_access_key=AWS_SECRET_ACCESS_KEY)
    b = conne.get_bucket('landsatproject')
    k = Key(b)
    k.key = scene + b1 + b2 + b3 + '.png'
    k.set_contents_from_filename(dir + '/final.png')
    k.get_contents_to_filename(dir + '/final.png')
    hello = b.get_key(scene + b1 + b2 + b3 + '.png')
    # make public
    hello.set_canned_acl('public-read')
    out = hello.generate_url(0, query_auth=False, force_http=True)
    return HTTPFound(location=out)
