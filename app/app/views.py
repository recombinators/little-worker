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
from shutil import rmtree
from pyramid.httpexceptions import exception_response
from models import Rendered_Model


direc = os.getcwd()

AWS_ACCESS_KEY_ID = os.environ['AWS_ACCESS_KEY_ID']
AWS_SECRET_ACCESS_KEY = os.environ['AWS_SECRET_ACCESS_KEY']

@view_config(route_name='home', renderer='json')
def my_view(request):
    direc = os.getcwd() + '/scenes'
    scene = request.matchdict['id']
    root = 'http://landsat-pds.s3.amazonaws.com/L8/'
    path = scene[3:6]
    row = scene[6:9]
    b1 = request.matchdict['b1']
    b2 = request.matchdict['b2']
    b3 = request.matchdict['b3']

    # Check if image already exists.
    out = Rendered_Model.preview_available(scene, b1, b2, b3)
    if out:
        return HTTPFound(location=out)

    try:
        direc_scene = '{direc}/{scene}'.format(direc=direc, scene=scene)

        direc_scene_scene = '{direc}/{scene}/{scene}'.format(direc=direc, scene=scene)

        # Builds a string pointing towards the AWS Landsat datasets
        # IE: http://landsat-pds.s3.amazonaws.com/L8/139/045/LC81390452014295LGN00/LC81390452014295LGN00_B3.TIF.ovr
        o1 = '{root}{path}/{row}/{scene}/{scene}_B{band}.TIF.ovr'.format(
                        root=root, path=path, row=row, scene=scene, band=b1)
        o2 = '{root}{path}/{row}/{scene}/{scene}_B{band}.TIF.ovr'.format(
                        root=root, path=path, row=row, scene=scene, band=b2)
        o3 = '{root}{path}/{row}/{scene}/{scene}_B{band}.TIF.ovr'.format(
                        root=root, path=path, row=row, scene=scene, band=b3)

        # o1 = root + path + '/' + row + '/' + scene + '/' + scene + '_B' + b1 + '.TIF.ovr'
        # o2 = root + path + '/' + row + '/' + scene + '/' + scene + '_B' + b2 + '.TIF.ovr'
        # o3 = root + path + '/' + row + '/' + scene + '/' + scene + '_B' + b3 + '.TIF.ovr'

        # Create a subdirectory
        if not os.path.exists(direc):
            os.makedirs(direc)

        # Download a sacrificial band(1) using Landsat-util
        dl = Downloader(verbose=True, download_dir=direc)
        dl.download([str(scene)], ['1'])

        # Strip the geospatial metadata from a legitimate Landsat band.
        # Create a world.tfw to reapply to previews.
        subprocess.call(['listgeo', '-tfw', direc_scene_scene + '_B1.TIF'])
        os.rename(direc_scene_scene + '_B1.tfw', direc + '/' + 'world.tfw')

        # Download previews from AWS
        download(url=o1, path=direc)
        download(url=o2, path=direc)
        download(url=o3, path=direc)
        print 'done downloding previews from aws'

        direc_world = '{}/world.tfw'.format(direc)
        # direc_scene_band = '{direc}/{scene}_{band}.TIF.ovr'.format(direc=direc, scene=scene, band=b1)
        # Apply the stripped world file to the band previews.
        subprocess.call(['geotifcp', '-e', direc_world, '{direc}/{scene}_B{band}.TIF.ovr'.format(direc=direc, scene=scene, band=b1), direc + '/B' + b1 + '-geo.TIF'])
        subprocess.call(['geotifcp', '-e', direc_world, '{direc}/{scene}_B{band}.TIF.ovr'.format(direc=direc, scene=scene, band=b2), direc + '/B' + b2 + '-geo.TIF'])
        subprocess.call(['geotifcp', '-e', direc_world, '{direc}/{scene}_B{band}.TIF.ovr'.format(direc=direc, scene=scene, band=b3), direc + '/B' + b3 + '-geo.TIF'])
        print 'done applying world file to previews'

        # Resize each band
        # subprocess.call(['mkdir', direc + '/ready'])
        subprocess.call(['gdal_translate', '-outsize', '15%', '15%', direc + '/B' + b1 + '-geo.TIF', direc_scene_scene + '_B' + b1 + '.TIF'])
        subprocess.call(['gdal_translate', '-outsize', '15%', '15%', direc + '/B' + b2 + '-geo.TIF', direc_scene_scene + '_B' + b2 + '.TIF'])
        subprocess.call(['gdal_translate', '-outsize', '15%', '15%', direc + '/B' + b3 + '-geo.TIF', direc_scene_scene + '_B' + b3 + '.TIF'])
        print 'done resizing 3 images'

        # Call landsat-util
        t = direc + '/' + scene
        processor = Process(t, [b1, b2, b3], direc, verbose=True)
        processor.run(pansharpen=False)

        # Convert black to transparent and save as PNG
        file_in = '{}_bands_{}{}{}.TIF'.format(direc_scene_scene, b1, b2, b3)
        subprocess.call(['convert', '-transparent', 'black', file_in, direc + '/final.png'])

        conne = boto.connect_s3(aws_access_key_id=AWS_ACCESS_KEY_ID,
             aws_secret_access_key=AWS_SECRET_ACCESS_KEY)
        b = conne.get_bucket('landsatproject')
        k = Key(b)
        k.key = scene + b1 + b2 + b3 + '.png'
        k.set_contents_from_filename(direc + '/final.png')
        k.get_contents_to_filename(direc + '/final.png')
        hello = b.get_key(scene + b1 + b2 + b3 + '.png')
        # make public
        hello.set_canned_acl('public-read')
        out = hello.generate_url(0, query_auth=False, force_http=True)

        # store url in db
        Rendered_Model.update_p_url(scene, b1, b2, b3, out)
    except:
        print 'error rendering files'
        raise exception_response(500)

    # # delete files
    # print 'deleting directory: {}'.format(direc)
    # try:
    #     rmtree(direc)           # band images and composite
    # except OSError:
    #     print 'error deleting files'


    return HTTPFound(location=out)
