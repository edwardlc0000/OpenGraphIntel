# open_graph_intel/ingestion/service.py

# Import dependencies
import logging
import requests
from lxml import etree
from sqlalchemy.orm import Session

# Import custom modules
from open_graph_intel.ingestion.model import (
    SDNEntity,
    Address,
    Program,
    Nationality,
    Vessel,
    ID,
    AKA,
    DateOfBirth,
    PlaceOfBirth,
    Citizenship,
    PublishInformation
)


def download_sdn_files(xml_url: str, xsd_url: str) -> tuple[str, str]:
    """
    Download the SDN XML and XSD files from the provided URLs.
    Args:
        xml_url (str): The URL of the SDN XML file.
        xsd_url (str): The URL of the XSD file.
    Returns:
        tuple[str, str]: Paths to the downloaded XML and XSD files.
    """
    xml_path = "sdn_advanced.xml"
    xsd_path = "sdn_advanced.xsd"
    # Download XML file
    response = requests.get(xml_url)
    with open(xml_path, "wb") as xml_file:
        xml_file.write(response.content)
    # Download XSD file
    response = requests.get(xsd_url)
    with open(xsd_path, "wb") as xsd_file:
        xsd_file.write(response.content)
    return xml_path, xsd_path


def validate_sdn_xml(xml_path: str, xsd_path: str) -> bool:
    """
    Validate the SDN XML file against the provided XSD schema.
    Args:
        xml_path (str): The path to the XML file.
        xsd_path (str): The path to the XSD file.
    Returns:
        bool: True if the XML is valid, False otherwise.
    """
    # Parse the XSD file
    with open(xsd_path, "rb") as xsd_file:
        schema_root = etree.XML(xsd_file.read())
        schema = etree.XMLSchema(schema_root)

    # Parse the XML file
    with open(xml_path, "rb") as xml_file:
        xml_doc = etree.parse(xml_file)

    # Validate the XML file against the XSD schema
    try:
        schema.assertValid(xml_doc)
        return True
    except etree.DocumentInvalid as e:
        logging.error(f"XML validation error: {e}")
        return False


def parse_sdn_xml(xml_path: str) -> list[dict]:
    """
    Parse the advanced SDN XML file and extract relevant information.
    Args:
        xml_path (str): The path to the XML file.
    Returns:
        list[dict]: A list of dictionaries containing the extracted information.
    """
    # Parse the XML file
    tree = etree.parse(xml_path)
    root = tree.getroot()

    # Define the namespace
    ns = {"ns": "https://sanctionslistservice.ofac.treas.gov/api/PublicationPreview/exports/XML"}

    # Extract relevant information
    sdn_data = []
    for sdn in root.findall(".//ns:sdnEntry", namespaces=ns):  # Updated to include namespace
        uid = sdn.findtext("ns:uid", namespaces=ns)
        first_name = sdn.findtext("ns:firstName", namespaces=ns)
        last_name = sdn.findtext("ns:lastName", namespaces=ns)
        title = sdn.findtext("ns:title", namespaces=ns)
        sdn_type = sdn.findtext("ns:sdnType", namespaces=ns)
        remarks = sdn.findtext("ns:remarks", namespaces=ns)

        programs = [p.text for p in sdn.findall("ns:programList/ns:program", namespaces=ns)]

        aka_list = []
        for aka in sdn.findall("ns:akaList/ns:aka", namespaces=ns):
            aka_list.append({
                "uid": aka.findtext("ns:uid", namespaces=ns),
                "type": aka.findtext("ns:type", namespaces=ns),
                "category": aka.findtext("ns:category", namespaces=ns),
                "last_name": aka.findtext("ns:lastName", namespaces=ns),
                "first_name": aka.findtext("ns:firstName", namespaces=ns)
            })

        ids = []
        for id_elem in sdn.findall("ns:idList/ns:id", namespaces=ns):
            ids.append({
                "uid": id_elem.findtext("ns:uid", namespaces=ns),
                "id_type": id_elem.findtext("ns:idType", namespaces=ns),
                "id_number": id_elem.findtext("ns:idNumber", namespaces=ns),
                "id_country": id_elem.findtext("ns:idCountry", namespaces=ns),
                "issue_date": id_elem.findtext("ns:issueDate", namespaces=ns),
                "expiration_date": id_elem.findtext("ns:expirationDate", namespaces=ns)
            })

        nationalities = []
        for nationality in sdn.findall("ns:nationalityList/ns:nationality", namespaces=ns):
            nationalities.append({
                "uid": nationality.findtext("ns:uid", namespaces=ns),
                "country": nationality.findtext("ns:country", namespaces=ns),
                "main_entry": nationality.findtext("ns:mainEntry", namespaces=ns) == "true"
            })

        citizenships = []
        for citizenship in sdn.findall("ns:citizenshipList/ns:citizenship", namespaces=ns):
            citizenships.append({
                "uid": citizenship.findtext("ns:uid", namespaces=ns),
                "country": citizenship.findtext("ns:country", namespaces=ns),
                "main_entry": citizenship.findtext("ns:mainEntry", namespaces=ns) == "true"
            })

        date_of_birth_list = []
        for dob in sdn.findall("ns:dateOfBirthList/ns:dateOfBirthItem", namespaces=ns):
            date_of_birth_list.append({
                "uid": dob.findtext("ns:uid", namespaces=ns),
                "date_of_birth": dob.findtext("ns:dateOfBirth", namespaces=ns),
                "main_entry": dob.findtext("ns:mainEntry", namespaces=ns) == "true"
            })

        place_of_birth_list = []
        for pob in sdn.findall("ns:placeOfBirthList/ns:placeOfBirthItem", namespaces=ns):
            place_of_birth_list.append({
                "uid": pob.findtext("ns:uid", namespaces=ns),
                "place_of_birth": pob.findtext("ns:placeOfBirth", namespaces=ns),
                "main_entry": pob.findtext("ns:mainEntry", namespaces=ns) == "true"
            })

        address_list = []
        for addr in sdn.findall("ns:addressList/ns:address", namespaces=ns):
            address_list.append({
                "uid": addr.findtext("ns:uid", namespaces=ns),
                "address1": addr.findtext("ns:address1", namespaces=ns),
                "address2": addr.findtext("ns:address2", namespaces=ns),
                "address3": addr.findtext("ns:address3", namespaces=ns),
                "city": addr.findtext("ns:city", namespaces=ns),
                "state_or_province": addr.findtext("ns:stateOrProvince", namespaces=ns),
                "postal_code": addr.findtext("ns:postalCode", namespaces=ns),
                "country": addr.findtext("ns:country", namespaces=ns),
                "region": addr.findtext("ns:region", namespaces=ns)
            })

        vessel_info = {}
        if sdn.find("ns:vesselInfo", namespaces=ns) is not None:
            vessel_info = {
                "call_sign": sdn.findtext("ns:callSign", namespaces=ns),
                "vessel_type": sdn.findtext("ns:vesselType", namespaces=ns),
                "vessel_flag": sdn.findtext("ns:vesselFlag", namespaces=ns),
                "vessel_owner": sdn.findtext("ns:vesselOwner", namespaces=ns),
                "tonnage": sdn.findtext("ns:tonnage", namespaces=ns),
                "gross_registered_tonnage": sdn.findtext("ns:grossRegisteredTonnage", namespaces=ns)
            }

        sdn_data.append({
            "uid": uid,
            "first_name": first_name,
            "last_name": last_name,
            "title": title,
            "sdn_type": sdn_type,
            "remarks": remarks,
            "programs": programs,
            "aka_list": aka_list,
            "ids": ids,
            "nationalities": nationalities,
            "citizenships": citizenships,
            "date_of_birth_list": date_of_birth_list,
            "place_of_birth_list": place_of_birth_list,
            "address_list": address_list,
            "vessel_info": vessel_info
        })

    return sdn_data



def store_sdn_data(sdn_data: list[dict], db: Session):
    """
    Store the parsed SDN data into the database.
    Args:
        sdn_data (list[dict]): The parsed SDN data.
        db (Session): The database session.
    """
    for entry in sdn_data:
        if db.query(SDNEntity).filter(SDNEntity.uid == entry["uid"]).first():
            logging.warning(
                f"SDNEntity with UID {entry['uid']} already exists. Skipping.")
            continue

        # Create SDNEntity
        sdn_entity = SDNEntity(uid=entry["uid"],
                               first_name=entry["first_name"],
                               last_name=entry["last_name"],
                               sdn_type=entry["sdn_type"],
                               remarks=entry["remarks"])

        # Add programs
        sdn_entity.programs = [
            Program(name=program) for program in entry["programs"]
        ]

        # Add aka_list
        sdn_entity.aka_list = [
            AKA(**aka) for aka in entry["aka_list"]
        ]

        # Add IDs
        sdn_entity.ids = [
            ID(**id_elem) for id_elem in entry["ids"]
        ]

        # Add nationalities
        sdn_entity.nationalities = [
            Nationality(**nationality) for nationality in entry["nationalities"]
        ]

        # Add citizenships
        sdn_entity.citizenships = [
            Citizenship(**citizenship) for citizenship in entry["citizenships"]
        ]

        # Add dates of birth
        sdn_entity.date_of_birth_list = [
            DateOfBirth(**dob) for dob in entry["date_of_birth_list"]
        ]

        # Add places of birth
        sdn_entity.place_of_birth_list = [
            PlaceOfBirth(**pob) for pob in entry["place_of_birth_list"]
        ]

        # Add addresses
        sdn_entity.addresses = [
            Address(**address) for address in entry["address_list"]
        ]

        # Add vessel info
        if entry["vessel_info"]:
            sdn_entity.vessel = Vessel(**entry["vessel_info"])

        # Add the entity to the session
        db.add(sdn_entity)

    db.commit()