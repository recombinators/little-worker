import os

from setuptools import setup, find_packages

here = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(here, 'README.txt')) as f:
    README = f.read()
with open(os.path.join(here, 'CHANGES.txt')) as f:
    CHANGES = f.read()

requires = ['affine',
            'boto',
            'Chameleon',
            'click',
            'cligj',
            'enum34',
            'homura',
            'humanize',
            'landsat-util',
            'Mako',
            'MarkupSafe ',
            'numpy',
            'PasteDeploy',
            'pip',
            'psycopg2',
            'pycurl',
            'Pygments',
            'pyramid',
            'pyramid-chameleon',
            'pyramid-debugtoolbar',
            'pyramid-mako',
            'pyramid-tm',
            'python-dateutil',
            'repoze.lru',
            'requests',
            'scikit-image',
            'scipy',
            'setuptools',
            'six',
            'SQLAlchemy',
            'termcolor',
            'transaction',
            'translationstring',
            'venusian',
            'waitress',
            'WebOb',
            'zope.deprecation',
            'zope.interface',
            'zope.sqlalchemy',
            ]

setup(name='app',
      version='0.0',
      description='app',
      long_description=README + '\n\n' + CHANGES,
      classifiers=[
        "Programming Language :: Python",
        "Framework :: Pyramid",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Internet :: WWW/HTTP :: WSGI :: Application",
        ],
      author='',
      author_email='',
      url='',
      keywords='web pyramid pylons',
      packages=find_packages(),
      include_package_data=True,
      zip_safe=False,
      install_requires=requires,
      tests_require=requires,
      test_suite="app",
      entry_points="""\
      [paste.app_factory]
      main = app:main
      """,
      )
