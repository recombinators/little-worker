# Pansharpened Image Process using Rasterio
# Landsat Util
# License: CC0 1.0 Universal

import warnings
import sys
from os.path import join
import tarfile
import numpy
import rasterio
import glob
from rasterio.warp import reproject, RESAMPLING, transform

from skimage import img_as_ubyte, exposure
from skimage import transform as sktransform

import settings
from mixins import VerbosityMixin
from utils import get_file, timer, check_create_folder, exit


class FileDoesNotExist(Exception):
    pass


class Process(VerbosityMixin):
    """
    Image procssing class
    """

    def __init__(self, path, bands=None, dst_path=None, verbose=False):
        """
        @params
        scene - the scene ID
        bands - The band sequence for the final image. Must be a python list
        src_path - The path to the source image bundle
        dst_path - The destination path
        zipped - Set to true if the scene is in zip format and requires unzipping
        verbose - Whether to sh ow verbose output
        """

        self.projection = {'init': 'epsg:3857'}
        self.dst_crs = {'init': u'epsg:3857'}
        self.scene = get_file(path).split('.')[0]
        self.bands = bands if isinstance(bands, list) else [4, 3, 2]

        # Landsat source path
        self.src_path = path.replace(get_file(path), '')

        # Build destination folder if doesn't exits
        self.dst_path = dst_path if dst_path else settings.PROCESSED_IMAGE
        self.dst_path = check_create_folder(join(self.dst_path, self.scene))
        self.verbose = verbose

        # Path to the unzipped folder
        self.scene_path = join(self.src_path, self.scene)

        if self._check_if_zipped(path):
            self._unzip(join(self.src_path, get_file(path)), join(self.src_path, self.scene), self.scene)

        self.bands_path = []
        for band in self.bands:
            self.bands_path.append(join(self.scene_path, self._get_full_filename(band)))

    def run(self, pansharpen=True):

        self.output("* Image processing started for bands %s" % "-".join(map(str, self.bands)), normal=True)

        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            with rasterio.drivers():
                bands = []

                # Add band 8 for pansharpenning
                if pansharpen:
                    self.bands.append(8)

                bands_path = []

                for band in self.bands:
                    bands_path.append(join(self.scene_path, self._get_full_filename(band)))

                try:
                    for i, band in enumerate(self.bands):
                        bands.append(self._read_band(bands_path[i]))
                except IOError as e:
                    exit(e.message, 1)

                src = rasterio.open(bands_path[-1])

                # Get pixel size from source
                self.pixel = src.affine[0]

                # Only collect src data that is needed and delete the rest
                src_data = {
                    'transform': src.transform,
                    'crs': src.crs,
                    'affine': src.affine,
                    'shape': src.shape
                }
                del src

                crn = self._get_boundaries(src_data)

                dst_shape = src_data['shape']
                y_pixel = (max(crn['ul']['y'][1][0],crn['ur']['y'][1][0])- min(crn['lr']['y'][1][0],crn['ll']['y'][1][0]))/dst_shape[0]
                x_pixel = (max(crn['lr']['x'][1][0],crn['ur']['x'][1][0]) - min(crn['ul']['x'][1][0],crn['ll']['x'][1][0]))/dst_shape[1]

                dst_transform = (min(crn['ul']['x'][1][0],crn['ll']['x'][1][0]), x_pixel, 0.0, max(crn['ul']['y'][1][0],crn['ur']['y'][1][0]), 0.0, -y_pixel)
                # Delete crn since no longer needed
                del crn

                new_bands = []
                for i in range(0, 3):
                    new_bands.append(numpy.empty(dst_shape, dtype=numpy.uint16))

                if pansharpen:
                    bands[:3] = self._rescale(bands[:3])
                    new_bands.append(numpy.empty(dst_shape, dtype=numpy.uint16))

                self.output("Projecting", normal=True, arrow=True)
                for i, band in enumerate(bands):
                    self.output("band %s" % self.bands[i], normal=True, color='green', indent=1)
                    reproject(band, new_bands[i], src_transform=src_data['transform'], src_crs=src_data['crs'],
                              dst_transform=dst_transform, dst_crs=self.dst_crs, resampling=RESAMPLING.nearest)

                # Bands are no longer needed
                del bands

                if pansharpen:
                    new_bands = self._pansharpenning(new_bands)
                    del self.bands[3]

                self.output("Final Steps", normal=True, arrow=True)

                output_file = '%s_bands_%s' % (self.scene, "".join(map(str, self.bands)))

                if pansharpen:
                    output_file += '_pan'

                output_file += '.TIF'
                output_file = join(self.dst_path, output_file)

                output = rasterio.open(output_file, 'w', driver='GTiff',
                                       width=dst_shape[1], height=dst_shape[0],
                                       count=3, dtype=numpy.uint8,
                                       nodata=0, transform=dst_transform, photometric='RGB',
                                       crs=self.dst_crs)

                for i, band in enumerate(new_bands):
                    # Color Correction
                    band = self._color_correction(band, self.bands[i])

                    # Gamma Correction
                    if i == 0:
                        band = self._gamma_correction(band, 1.1)

                    if i == 2:
                        band = self._gamma_correction(band, 0.9)

                    
                    output.write_band(i+1, img_as_ubyte(band))

                    new_bands[i] = None
                self.output("Writing to file", normal=True, color='green', indent=1)
                return output_file

    def _pansharpenning(self, bands):

        self.output("Pansharpening", normal=True, arrow=True)
        # Pan sharpening
        m = sum(bands[:3])
        m = m + 0.1

        self.output("calculating pan ratio", normal=True, color='green', indent=1)
        pan = 1/m * bands[-1]

        del m
        del bands[3]
        self.output("computing bands", normal=True, color='green', indent=1)

        for i, band in enumerate(bands):
            bands[i] = band * pan

        del pan

        return bands

    def _gamma_correction(self, band, value):
        return exposure.adjust_gamma(band, value)

    def _color_correction(self, band, band_id):
        band = band.astype(numpy.uint16)

        self.output("Color correcting band %s" % band_id, normal=True, color='green', indent=1)
        p2, p98 = self._percent_cut(band)
        band = exposure.rescale_intensity(band, in_range=(p2, p98))

        return band

    def _read_band(self, band_path):
        """ Reads a band with rasterio """
        return rasterio.open(band_path).read_band(1)

    def _rescale(self, bands):
        """ Rescale bands """
        self.output("Rescaling", normal=True, arrow=True)

        for key, band in enumerate(bands):
            self.output("band %s" % self.bands[key], normal=True, color='green', indent=1)
            bands[key] = sktransform.rescale(band, 2)
            bands[key] = (bands[key] * 65535).astype('uint16')

        return bands

    def _get_boundaries(self, src):

        self.output("Getting boundaries", normal=True, arrow=True)
        output = {'ul': {'x': [0, 0], 'y': [0, 0]},  # ul: upper left
                  'ur': {'x': [0, 0], 'y': [0, 0]},  # ur: upper right
                  'll': {'x': [0, 0], 'y': [0, 0]},  # ll: lower left
                  'lr': {'x': [0, 0], 'y': [0, 0]}}  # lr: lower right

        output['ul']['x'][0] = src['affine'][2]
        output['ul']['y'][0] = src['affine'][5]
        output['ur']['x'][0] = output['ul']['x'][0] + self.pixel * src['shape'][1]
        output['ur']['y'][0] = output['ul']['y'][0]
        output['ll']['x'][0] = output['ul']['x'][0]
        output['ll']['y'][0] = output['ul']['y'][0] - self.pixel * src['shape'][0]
        output['lr']['x'][0] = output['ul']['x'][0] + self.pixel * src['shape'][1]
        output['lr']['y'][0] = output['ul']['y'][0] - self.pixel * src['shape'][0]

        output['ul']['x'][1], output['ul']['y'][1] = transform(src['crs'], self.projection,
                                                               [output['ul']['x'][0]],
                                                               [output['ul']['y'][0]])

        output['ur']['x'][1], output['ur']['y'][1] = transform(src['crs'], self.projection,
                                                               [output['ur']['x'][0]],
                                                               [output['ur']['y'][0]])

        output['ll']['x'][1], output['ll']['y'][1] = transform(src['crs'], self.projection,
                                                               [output['ll']['x'][0]],
                                                               [output['ll']['y'][0]])

        output['lr']['x'][1], output['lr']['y'][1] = transform(src['crs'], self.projection,
                                                               [output['lr']['x'][0]],
                                                               [output['lr']['y'][0]])

        return output

    def _percent_cut(self, color):
        return numpy.percentile(color[numpy.logical_and(color > 0, color < 65535)], (2, 98))

    def _unzip(self, src, dst, scene):
        """ Unzip tar files """
        self.output("Unzipping %s - It might take some time" % scene, normal=True, arrow=True)
        tar = tarfile.open(src)
        tar.extractall(path=dst)
        tar.close()

    def _get_full_filename(self, band):

        base_file = '%s_B%s.*' % (self.scene, band)

        try:
            return glob.glob(join(self.scene_path, base_file))[0].split('/')[-1]
        except IndexError:
            raise FileDoesNotExist('%s does not exist' % '%s_B%s.*' % (self.scene, band))

    def _check_if_zipped(self, path):
        """ Checks if the filename shows a tar/zip file """
        filename = get_file(path).split('.')

        if filename[-1] in ['bz', 'bz2']:
            return True

        return False


if __name__ == '__main__':

    with timer():
        p = Process(sys.argv[1])

        print p.run(sys.argv[2] == 't')
