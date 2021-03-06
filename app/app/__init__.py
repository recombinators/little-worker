import os
from pyramid.config import Configurator
from sqlalchemy import engine_from_config

from .models import DBSession, Base


def main(global_config, **settings):
    """ This function returns a Pyramid WSGI application.
    """
    settings['sqlalchemy.url'] = os.environ.get('DATABASE_URL')
    print(settings)
    engine = engine_from_config(settings, 'sqlalchemy.')
    DBSession.configure(bind=engine)
    Base.metadata.bind = engine
    config = Configurator(settings=settings)
    config.add_route('home', '/{id}/{b1}/{b2}/{b3}/preview.png')
    config.scan()
    return config.make_wsgi_app()
