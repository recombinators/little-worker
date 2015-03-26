from sqlalchemy import Column, update, Index, Integer, Boolean, UnicodeText, func, DateTime, Float, or_, and_
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from zope.sqlalchemy import ZopeTransactionExtension
import transaction
from datetime import datetime

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

    # @classmethod
    # def add(cls, jobid, currentlyrend):
    #     '''Method adds entry into db given jobid and optional url.'''
    #     jobQuery = DBSession.query(UserJob_Model).get(jobid)
    #     job = Rendered_Model(entityid=jobQuery.entityid,
    #                          jobid=jobid,
    #                          band1=jobQuery.band1,
    #                          band2=jobQuery.band2,
    #                          band3=jobQuery.band3,
    #                          currentlyrend=currentlyrend)
    #     DBSession.add(job)

    @classmethod
    def preview_available(cls, scene, band1, band2, band3):
        '''Check if preview image is already rendered'''
        try:
            output = DBSession.query(cls).filter(cls.entityid == scene,
                                                 cls.band1 == band1,
                                                 cls.band2 == band2,
                                                 cls.band3 == band3,
                                                 cls.previewurl.isnot(None))
            import pdb; pdb.set_trace()
            return output.one().previewurl
        except:
            print 'Database query failed'
            return None

    # @classmethod
    # def update(cls, jobid, currentlyrend, renderurl):
    #     '''Method updates entry into db given jobid and optional url.'''
    #     try:
    #         DBSession.query(cls).filter(cls.jobid == jobid).update({"currentlyrend": currentlyrend,"renderurl": renderurl})
    #     except:
    #         print 'could not update db'

    # @classmethod
    # def available(cls, entityid):
    #     '''Return list of existing jobs for a given sceneID.'''
    #     try:
    #         rendered = DBSession.query(cls).filter(cls.entityid == entityid).all()
    #     except:
    #         print 'Database query failed'
    #         return None
    #     return rendered

    # @classmethod
    # def already_available(cls, entityid, band1, band2, band3):
    #     '''Check if given image is already rendered'''
    #     try:
    #         output = DBSession.query(cls).filter(cls.entityid == entityid,
    #                                              cls.band1 == band1,
    #                                              cls.band2 == band2,
    #                                              cls.band3 == band3,
    #                                              cls.renderurl.isnot(None)).count()
    #     except:
    #         print 'Database query failed'
    #         return None
    #     if output != 0:
    #         # if this scene/band has already been requested, increase the count
    #         existing = DBSession.query(cls).filter(cls.entityid == entityid,
    #                                                cls.band1 == band1,
    #                                                cls.band2 == band2,
    #                                                cls.band3 == band3).update({
    #                                                "rendercount": cls.rendercount+1})
    #     return output != 0
