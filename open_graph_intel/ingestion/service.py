# open_graph_intel/ingestion/service.py

# Import dependencies
import logging
import requests
from lxml import etree

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

def parse_advanced_sdn_xml(xml_path: str) -> list[dict]:
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
    # Extract relevant information
    sdn_data = []
    for sdn in root.findall(".//DistinctParty"):
        uid = sdn.findtext("uid"),
        first_name = sdn.findtext("first_name")
        last_name = sdn.findtext("last_name")
        sdn_type = sdn.findtext("sdn_type")
        remarks = sdn.findtext("remarks")

        programs = [p.text for p in sdn.findall("programList/program")]

        aliases = [aka.findtext("wholeName") for aka in sdn.findall("akaList/aka")]

        nationalities = [n.findtext("isoCode") for n in sdn.findall("nationalityList/nationality")]

        address = []
        for addr in sdn.findall("addressList/address"):
            address.append({
                "street": addr.findtext("street"),
                "city": addr.findtext("city"),
                "state": addr.findtext("state"),
                "postal_code": addr.findtext("postalCode"),
                "country": addr.findtext("country")
            })

        documents = []
        for doc in sdn.findall("documentList/document"):
            documents.append({
                "doc_type": doc.findtext("idType"),
                "doc_number": doc.findtext("number"),
                "issuing_country": doc.findtext("country")
            })

        vessel_info = []
        if sdn_type and sdn_type.lower() == "vessel":
            vessel_info = {
                "call_sign": sdn.findtext("vesselInfo/callSign"),
                "vessel_type": sdn.findtext("vesselInfo/vesselType"),
                "tonnage": sdn.findtext("vesselInfo/tonnage"),
                "grt": sdn.findtext("vesselInfo/grt"),
                "flag": sdn.findtext("vesselInfo/flag"),
                "owner": sdn.findtext("vesselInfo/owner")
            }

        aircraft_info = []
        if sdn_type and sdn_type.lower() == "aircraft":
            aircraft_info = {
                "tail_number": sdn.findtext("aircraftInfo/tailNumber"),
                "aircraft_type": sdn.findtext("aircraftInfo/aircraftType"),
                "manufacturer": sdn.findtext("aircraftInfo/manufacturer"),
                "model": sdn.findtext("aircraftInfo/model"),
                "registration_location": sdn.findtext("aircraftInfo/registrationLocation")
            }

        sdn_data.append({
            "uid": uid,
            "first_name": first_name,
            "last_name": last_name,
            "sdn_type": sdn_type,
            "remarks": remarks,
            "programs": programs,
            "aliases": aliases,
            "nationalities": nationalities,
            "address": address,
            "documents": documents,
            "vessel_info": vessel_info,
            "aircraft_info": aircraft_info
        })


    return sdn_data
