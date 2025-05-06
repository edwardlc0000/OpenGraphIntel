# open_graph_intel/ingestion/service.py

# Import dependencies
from lxml import etree

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
