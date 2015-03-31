import os
import sys
sys.path.append('landsat-util/landsat')
import subprocess
import boto
from boto.s3.key import Key
from pyramid.view import view_config
from homura import download
from image import Process
from pyramid.httpexceptions import HTTPFound
from shutil import rmtree
from models import Rendered_Model
import os.path


AWS_ACCESS_KEY_ID = os.environ['AWS_ACCESS_KEY_ID']
AWS_SECRET_ACCESS_KEY = os.environ['AWS_SECRET_ACCESS_KEY']

# path of world(geodata) file
direc_world = '{}/world.tfw'.format(os.getcwd())


def delete_directory(direc):
    # delete files
    try:
        if os.path.exists(direc):
            rmtree(direc)
    except OSError:
        pass
    #     raise Exception('error deleting files')


def process_image(direc, scene, root, path, row, b1, b2, b3):
    '''Method to process preview image'''
    direc_scene = '{direc}/{scene}'.format(direc=direc, scene=scene)

    direc_scene_scene = '{direc}/{sc}/{sc}'.format(direc=direc, sc=scene)

    band_list = [b1, b2, b3]
    o_list = []
    # Builds a string pointing towards the AWS Landsat datasets
    for b in band_list:
        o_list.append('{root}{path}/{row}/{scene}/{scene}_B{band}.TIF'.
                    format(root=root, path=path, row=row, scene=scene, band=b))

    # Create a subdirectory
    if not os.path.exists(direc_scene):
        os.makedirs(direc_scene)

    try:
        # Download previews from AWS
        for i in o_list:
            download(url=i, path=direc_scene)
    except:
        out = u'https://raw.githubusercontent.com/recombinators/little-worker/master/failimages/faileddownload.png'
        # return out
        raise Exception('Download failed')

    print 'done downloading previews from aws'
    # # Apply the stripped world file to the band previews.
    # for b in band_list:
    #     file_name = '{}/B{}-geo.TIF'.format(direc_scene, b)
    #     subprocess.call(['geotifcp', '-e', direc_world,
    #                      '{direc}/{scene}_B{band}.TIF.ovr'.format(
    #                      direc=direc_scene, scene=scene, band=b),
    #                      file_name])
    # print 'done applying world file to previews'

    # Resize each band
    for b in band_list:
        # file_name = '{}/B{}-geo.TIF'.format(direc_scene, b)
        file_name = '{direc}/{scene}_B{band}.TIF'.format(direc=direc_scene, scene=scene, band=b)
        file_name2 = '{}_B{}.TIF'.format(direc_scene_scene, b)
        subprocess.call(['gdal_translate', '-outsize', '15%', '15%',
                         file_name, file_name2])
        if not os.path.exists(file_name2):
            out = u'https://raw.githubusercontent.com/recombinators/little-worker/master/failimages/badmagicnumber.png'
            # return out
            raise Exception('Bad magic number')
    print 'done resizing 3 images'

    # Call landsat-util to merge images
    t = direc + '/' + scene
    try:
        processor = Process(t, [b1, b2, b3], direc, verbose=True)
        processor.run(pansharpen=False)
    except:
        out = u'https://raw.githubusercontent.com/recombinators/little-worker/master/failimages/processfailed.png'
        # return out
        raise Exception('Processing/landsat-util failed')

    # Convert black to transparent and save as PNG
    file_in = '{}_bands_{}{}{}.TIF'.format(direc_scene_scene, b1, b2, b3)
    subprocess.call(['convert', '-transparent', 'black',
                    file_in, direc_scene + '/final.png'])

    # check if final.png exists
    if not os.path.isfile('{}/final.png'.format(direc_scene)):
        out = u'https://raw.githubusercontent.com/recombinators/little-worker/master/failimages/finalpngnotcomposed.png'
        # return out
        raise Exception('Final.png not rendered')

    # upload to s3
    try:
        conne = boto.connect_s3(aws_access_key_id=AWS_ACCESS_KEY_ID,
                                aws_secret_access_key=AWS_SECRET_ACCESS_KEY)
        b = conne.get_bucket('landsatproject')
        k = Key(b)
        k.key = scene + b1 + b2 + b3 + '.png'
        k.set_contents_from_filename(direc_scene + '/final.png')
        k.get_contents_to_filename(direc_scene + '/final.png')
        hello = b.get_key(scene + b1 + b2 + b3 + 'pre.png')
        # make public
        hello.set_canned_acl('public-read')
        out = hello.generate_url(0, query_auth=False, force_http=True)
    except:
        out = u'https://raw.githubusercontent.com/recombinators/little-worker/master/failimages/connectiontoS3failed.png'
        # return out
        raise Exception('S3 upload failed')

    # store url in db
    Rendered_Model.update_p_url(scene, b1, b2, b3, out)
    # delete files
    delete_directory(direc)
    return out


@view_config(route_name='home', renderer='json')
def my_view(request):
    """A view for rendering or retreiving an image on demand."""
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
    if not out:
        try:
            out = process_image(direc, scene, root, path, row, b1, b2, b3)
        except:
            # If error in processing image, render aws image as default.
            # delete files
            delete_directory(direc)
            # out = "https://s3-us-west-2.amazonaws.com/landsat-pds/L8/{path}/{row}/{scene}/{scene}_thumb_large.jpg".format(
            #         path=path, row=row, scene=scene)
            # out = u'https://raw.githubusercontent.com/recombinators/little-worker/master/failimages/errordeletingfiles.png'

    return HTTPFound(location=out)
