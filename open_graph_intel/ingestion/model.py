# open_graph_intel/ingestion/model.py

# Import dependencies
import logging
from sqlalchemy import Column, Integer, String, Text, ForeignKey
from sqlalchemy.orm import relationship

# Import custom modules
from open_graph_intel.data_layer.database import Base

# Configure logging
logger = logging.getLogger(__name__)


class SDNEntity(Base):
    """
    SQLAlchemy model for storing SDN data.
    """
    __tablename__ = "sdn_entities"
    id = Column(Integer, primary_key=True, index=True)
    uid = Column(Integer, unique=True, nullable=False)
    first_name = Column(String)
    last_name = Column(String)
    sdn_type = Column(String)
    remarks = Column(Text)

    # Relationships
    aliases = relationship("Alias",
                           back_populates="sdn_entity",
                           cascade="all, delete-orphan")
    addresses = relationship("Address",
                             back_populates="sdn_entity",
                             cascade="all, delete-orphan")
    documents = relationship("Document",
                             back_populates="sdn_entity",
                             cascade="all, delete-orphan")
    programs = relationship("Program",
                            back_populates="sdn_entity",
                            cascade="all, delete-orphan")
    nationalities = relationship("Nationality",
                                 back_populates="sdn_entity",
                                 cascade="all, delete-orphan")
    vessel = relationship("Vessel",
                           back_populates="sdn_entity",
                           cascade="all, delete-orphan")
    aircraft = relationship("Aircraft",
                            back_populates="sdn_entity",
                            cascade="all, delete-orphan")


class Alias(Base):
    """
    SQLAlchemy model for storing aliases.
    """
    __tablename__ = "aliases"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    sdn_entity_id = Column(Integer, ForeignKey("sdn_entities.id"))
    # Relationships
    sdn_entity = relationship("SDNEntity", back_populates="aliases")

class Address(Base):
    """
    SQLAlchemy model for storing addresses.
    """
    __tablename__ = "addresses"
    id = Column(Integer, primary_key=True, index=True)
    address = Column(String, nullable=False)
    city = Column(String)
    state = Column(String)
    country = Column(String)
    postal_code = Column(String)
    sdn_entity_id = Column(Integer, ForeignKey("sdn_entities.id"))
    # Relationships
    sdn_entity = relationship("SDNEntity", back_populates="addresses")

class Document(Base):
    """
    SQLAlchemy model for storing documents.
    """
    __tablename__ = "documents"
    id = Column(Integer, primary_key=True, index=True)
    doc_type = Column(String)
    doc_number = Column(String)
    issuing_country = Column(String)
    sdn_entity_id = Column(Integer, ForeignKey("sdn_entities.id"))
    # Relationships
    sdn_entity = relationship("SDNEntity", back_populates="documents")

class Program(Base):
    """
    SQLAlchemy model for storing programs.
    """
    __tablename__ = "programs"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    sdn_entity_id = Column(Integer, ForeignKey("sdn_entities.id"))
    # Relationships
    sdn_entity = relationship("SDNEntity", back_populates="programs")


class Nationality(Base):
    """
    SQLAlchemy model for storing nationalities.
    """
    __tablename__ = "nationalities"
    id = Column(Integer, primary_key=True, index=True)
    iso_code = Column(String)
    sdn_entity_id = Column(Integer, ForeignKey("sdn_entities.id"))
    # Relationships
    sdn_entity = relationship("SDNEntity", back_populates="nationalities")


class Vessel(Base):
    """
    SQLAlchemy model for storing vessels.
    """
    __tablename__ = "vessels"
    id = Column(Integer, primary_key=True, index=True)
    call_sign = Column(String)
    vessel_type = Column(String)
    tonnage = Column(String)
    grt = Column(String)
    flag = Column(String)
    owner = Column(String)
    # Relationships
    sdn_entity = relationship("SDNEntity", back_populates="vessel")


class Aircraft(Base):
    """
    SQLAlchemy model for storing aircraft.
    """
    __tablename__ = "aircraft"
    id = Column(Integer, primary_key=True, index=True)
    tail_number = Column(String)
    aircraft_type = Column(String)
    manufacturer = Column(String)
    model = Column(String)
    registration_location = Column(String)
    # Relationships
    sdn_entity = relationship("SDNEntity", back_populates="aircraft")