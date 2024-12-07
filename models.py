
from sqlalchemy import Column, Float, ForeignKey, String, create_engine
from sqlalchemy.orm import relationship
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from sqlalchemy.ext.asyncio import AsyncAttrs
import uuid

engine = create_engine("sqlite:///db.sqlite3", echo=True)

# Фабрика сессий
Session = sessionmaker(bind=engine)

class Base(AsyncAttrs, DeclarativeBase):
    pass


class Unit(Base):
    __tablename__ = 'Unit'
    Unit_id = Column(String(36), primary_key=True,default=lambda :str(uuid.uuid4()))
    zc = Column(Float, nullable=True)
    a = Column(Float, nullable=True)
    Ky = Column(Float, nullable=True)
    Kv = Column(Float, nullable=True)
    Ky_v = Column(Float, nullable=True)
    Km = Column(Float, nullable=True)
    N = Column(Float, nullable=True)
    delta = Column(Float, nullable=True)

    # Связь "один-ко-многим" с Detail
    details = relationship("Detail", back_populates="unit", cascade="all, delete-orphan")

    def __init__(self, unit_id = None, zc=None, a=None, Ky=None, Kv=None, Ky_v=None, Km=None, N=None, delta=None):
        self.Unit_id = unit_id
        self.zc = zc
        self.a = a
        self.Ky = Ky
        self.Kv = Kv
        self.Ky_v = Ky_v
        self.Km = Km
        self.N = N
        self.delta = delta

class Detail(Base):
    __tablename__ = 'Detail'
    Detail_id = Column(String(36), primary_key=True,default=lambda :str(uuid.uuid4()))
    a = Column(Float, nullable=True)
    z1 = Column(Float, nullable=True)
    z2 = Column(Float, nullable=True)
    n1 = Column(Float, nullable=True)
    j = Column(Float, nullable=True)

    # Внешний ключ для связи с Unit
    Unit_id = Column(String, ForeignKey('Unit.Unit_id'), nullable=False)

    # Связь "многие-к-одному" с Unit
    unit = relationship("Unit", back_populates="details")

    def __init__(self,detail_id = None, a = None, z1 = None, z2 = None, n1 = None, j = None, unit_id = None):
        self.Detail_id = detail_id
        self.a = a
        self.z1 = z1
        self.z2 = z2
        self.n1 = n1
        self.j = j
        self.Unit_id = unit_id


def init_db():
    # Создание таблиц
    Base.metadata.create_all(engine)