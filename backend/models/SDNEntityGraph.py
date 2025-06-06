# backend/models/SDNEntityGraph.py

# Import dependencies
import logging
from neomodel import StructuredNode, StringProperty, IntegerProperty, RelationshipTo, RelationshipFrom, BooleanProperty

# Configure logging
logger = logging.getLogger(__name__)

class SDNEntity(StructuredNode):
    uid = IntegerProperty(unique_index=True, required=True)
    first_name = StringProperty()
    last_name = StringProperty()
    sdn_type = StringProperty()
    remarks = StringProperty()

    # Define relationships
    addresses = RelationshipTo('Address', 'HAS_ADDRESS')
    programs = RelationshipTo('Program', 'ENROLLED_IN')
    nationalities = RelationshipTo('Nationality', 'HAS_NATIONALITY')
    vessel = RelationshipTo('Vessel', 'OWNS')
    ids = RelationshipTo('ID', 'HAS_ID')
    aka_list = RelationshipTo('AKA', 'ALSO_KNOWN_AS')
    date_of_birth_list = RelationshipTo('DateOfBirth', 'BORN_ON')
    place_of_birth_list = RelationshipTo('PlaceOfBirth', 'BORN_AT')
    citizenships = RelationshipTo('Citizenship', 'HOLDS_CITIZENSHIP')

class Address(StructuredNode):
    uid = IntegerProperty(required=True)
    address1 = StringProperty()
    address2 = StringProperty()
    address3 = StringProperty()
    city = StringProperty()
    state_or_province = StringProperty()
    postal_code = StringProperty()
    country = StringProperty()
    region = StringProperty()
    sdn_entity = RelationshipFrom('SDNEntity', 'HAS_ADDRESS')

class Program(StructuredNode):
    name = StringProperty(required=True)
    sdn_entity = RelationshipFrom('SDNEntity', 'ENROLLED_IN')

class ID(StructuredNode):
    uid = IntegerProperty(required=True)
    id_type = StringProperty()
    id_number = StringProperty()
    id_country = StringProperty()
    issue_date = StringProperty()
    expiration_date = StringProperty()
    sdn_entity = RelationshipFrom('SDNEntity', 'HAS_ID')

class AKA(StructuredNode):
    uid = IntegerProperty(required=True)
    type = StringProperty(required=True)
    category = StringProperty(required=True)
    last_name = StringProperty()
    first_name = StringProperty()
    sdn_entity = RelationshipFrom('SDNEntity', 'ALSO_KNOWN_AS')

class DateOfBirth(StructuredNode):
    uid = IntegerProperty(required=True)
    date_of_birth = StringProperty(required=True)
    main_entry = BooleanProperty(required=True)
    sdn_entity = RelationshipFrom('SDNEntity', 'BORN_ON')

class PlaceOfBirth(StructuredNode):
    uid = IntegerProperty(required=True)
    place_of_birth = StringProperty(required=True)
    main_entry = BooleanProperty(required=True)
    sdn_entity = RelationshipFrom('SDNEntity', 'BORN_AT')

class Citizenship(StructuredNode):
    uid = IntegerProperty(required=True)
    country = StringProperty(required=True)
    main_entry = BooleanProperty(required=True)
    sdn_entity = RelationshipFrom('SDNEntity', 'HOLDS_CITIZENSHIP')

class Nationality(StructuredNode):
    uid = IntegerProperty(required=True)
    country = StringProperty(required=True)
    main_entry = BooleanProperty(required=True)
    sdn_entity = RelationshipFrom('SDNEntity', 'HAS_NATIONALITY')

class Vessel(StructuredNode):
    call_sign = StringProperty()
    vessel_type = StringProperty()
    vessel_flag = StringProperty()
    vessel_owner = StringProperty()
    tonnage = IntegerProperty()
    gross_registered_tonnage = IntegerProperty()
    sdn_entity = RelationshipFrom('SDNEntity', 'OWNS')