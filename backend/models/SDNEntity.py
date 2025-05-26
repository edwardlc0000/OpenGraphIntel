# backend/ingestion/SDNEntity.py

# Import dependencies
import logging
from sqlalchemy import Column, Integer, String, Text, Boolean, ForeignKey
from sqlalchemy.orm import relationship

# Import custom modules
from backend.data_layer.database import DatabaseManager

# Configure logging
logger = logging.getLogger(__name__)

# Initialize the database manager and get the Base
from backend.models.base import Base

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
    addresses = relationship("Address",
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
                          cascade="all, delete-orphan",
                          uselist=False)
    ids = relationship("ID",
                       back_populates="sdn_entity",
                       cascade="all, delete-orphan")
    aka_list = relationship("AKA",
                            back_populates="sdn_entity",
                            cascade="all, delete-orphan")
    date_of_birth_list = relationship("DateOfBirth",
                                      back_populates="sdn_entity",
                                      cascade="all, delete-orphan")
    place_of_birth_list = relationship("PlaceOfBirth",
                                       back_populates="sdn_entity",
                                       cascade="all, delete-orphan")
    citizenships = relationship("Citizenship",
                                 back_populates="sdn_entity",
                                 cascade="all, delete-orphan")


class PublishInformation(Base):
    """
    SQLAlchemy model for storing publish information.
    """
    __tablename__ = "publish_information"
    id = Column(Integer, primary_key=True, index=True)
    publish_date = Column(String, nullable=True)
    record_count = Column(Integer, nullable=True)


class ID(Base):
    """
    SQLAlchemy model for storing IDs.
    """
    __tablename__ = "ids"
    id = Column(Integer, primary_key=True, index=True)
    uid = Column(Integer, nullable=False)
    id_type = Column(String, nullable=True)
    id_number = Column(String, nullable=True)
    id_country = Column(String, nullable=True)
    issue_date = Column(String, nullable=True)
    expiration_date = Column(String, nullable=True)
    sdn_entity_id = Column(Integer, ForeignKey("sdn_entities.id"))
    # Relationships
    sdn_entity = relationship("SDNEntity", back_populates="ids")


class AKA(Base):
    """
    SQLAlchemy model for storing aliases (AKA).
    """
    __tablename__ = "aka_list"
    id = Column(Integer, primary_key=True, index=True)
    uid = Column(Integer, nullable=False)
    type = Column(String, nullable=False)
    category = Column(String, nullable=False)
    last_name = Column(String, nullable=True)
    first_name = Column(String, nullable=True)
    sdn_entity_id = Column(Integer, ForeignKey("sdn_entities.id"))
    # Relationships
    sdn_entity = relationship("SDNEntity", back_populates="aka_list")


class DateOfBirth(Base):
    """
    SQLAlchemy model for storing dates of birth.
    """
    __tablename__ = "date_of_birth_list"
    id = Column(Integer, primary_key=True, index=True)
    uid = Column(Integer, nullable=False)
    date_of_birth = Column(String, nullable=False)
    main_entry = Column(Boolean, nullable=False)
    sdn_entity_id = Column(Integer, ForeignKey("sdn_entities.id"))
    # Relationships
    sdn_entity = relationship("SDNEntity", back_populates="date_of_birth_list")


class PlaceOfBirth(Base):
    """
    SQLAlchemy model for storing places of birth.
    """
    __tablename__ = "place_of_birth_list"
    id = Column(Integer, primary_key=True, index=True)
    uid = Column(Integer, nullable=False)
    place_of_birth = Column(String, nullable=False)
    main_entry = Column(Boolean, nullable=False)
    sdn_entity_id = Column(Integer, ForeignKey("sdn_entities.id"))
    # Relationships
    sdn_entity = relationship("SDNEntity", back_populates="place_of_birth_list")


class Citizenship(Base):
    """
    SQLAlchemy model for storing citizenships.
    """
    __tablename__ = "citizenships"
    id = Column(Integer, primary_key=True, index=True)
    uid = Column(Integer, nullable=False)
    country = Column(String, nullable=False)
    main_entry = Column(Boolean, nullable=False)
    sdn_entity_id = Column(Integer, ForeignKey("sdn_entities.id"))
    # Relationships
    sdn_entity = relationship("SDNEntity", back_populates="citizenships")


class Address(Base):
    """
    SQLAlchemy model for storing addresses.
    """
    __tablename__ = "addresses"
    id = Column(Integer, primary_key=True, index=True)
    uid = Column(Integer, nullable=False)
    address1 = Column(String, nullable=True)
    address2 = Column(String, nullable=True)
    address3 = Column(String, nullable=True)
    city = Column(String, nullable=True)
    state_or_province = Column(String, nullable=True)
    postal_code = Column(String, nullable=True)
    country = Column(String, nullable=True)
    region = Column(String, nullable=True)
    sdn_entity_id = Column(Integer, ForeignKey("sdn_entities.id"))
    # Relationships
    sdn_entity = relationship("SDNEntity", back_populates="addresses")


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
    uid = Column(Integer, nullable=False)
    country = Column(String, nullable=False)
    main_entry = Column(Boolean, nullable=False)
    sdn_entity_id = Column(Integer, ForeignKey("sdn_entities.id"))
    # Relationships
    sdn_entity = relationship("SDNEntity", back_populates="nationalities")


class Vessel(Base):
    """
    SQLAlchemy model for storing vessel information.
    """
    __tablename__ = "vessels"
    id = Column(Integer, primary_key=True, index=True)
    call_sign = Column(String, nullable=True)
    vessel_type = Column(String, nullable=True)
    vessel_flag = Column(String, nullable=True)
    vessel_owner = Column(String, nullable=True)
    tonnage = Column(Integer, nullable=True)
    gross_registered_tonnage = Column(Integer, nullable=True)
    sdn_entity_id = Column(Integer, ForeignKey("sdn_entities.id"))
    # Relationships
    sdn_entity = relationship("SDNEntity", uselist=False)