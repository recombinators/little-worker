from sqlalchemy import Column, update, Index, Integer, Boolean, UnicodeText, func, DateTime, Float, or_, and_
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from zope.sqlalchemy import ZopeTransactionExtension

DBSession = scoped_session(sessionmaker(extension=ZopeTransactionExtension()))
Base = declarative_base()


class Rendered_Model(Base):
    '''Model for the already rendered files'''
    __tablename__ = 'render_cache'
    id = Column(Integer, primary_key=True)
    jobid = Column(Integer)
    entityid = Column(UnicodeText)
    band1 = Column(Integer)
    band2 = Column(Integer)
    band3 = Column(Integer)
    previewurl = Column(UnicodeText)
    renderurl = Column(UnicodeText)
    rendercount = Column(Integer, default=0)
    currentlyrend = Column(Boolean)

    @classmethod
    def preview_available(cls, scene, band1, band2, band3):
        '''Check if preview image is already rendered'''
        try:
            output = DBSession.query(cls).filter(cls.entityid == scene,
                                                 cls.band1 == band1,
                                                 cls.band2 == band2,
                                                 cls.band3 == band3,
                                                 cls.previewurl.isnot(None))
            return output.one().previewurl
        except:
            print 'Database query failed'
            return None

    @classmethod
    def update_p_url(cls, scene, band1, band2, band3, previewurl):
        '''Method updates entry into db with preview url.'''
        try:
            DBSession.query(cls).filter(cls.entityid == scene,
                                        cls.band1 == band1,
                                        cls.band2 == band2,
                                        cls.band3 == band3,
                                        cls.previewurl.is_(None)
                                        ).update({"previewurl": previewurl})
        except:
            print 'could not add preview url to db'
