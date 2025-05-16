# backend/ingestion/main.py

# Import dependencies
import logging
from fastapi import FastAPI, APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from starlette.routing import Router


# Import custom modules
from backend.data_layer.database import get_db
from backend.ingestion.service import (
    download_sdn_files,
    validate_sdn_xml,
    parse_sdn_xml,
    store_sdn_data
)

from backend.ingestion.model import (
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

# Initialize the FastAPI router
router = APIRouter()

# Initialize FastAPI app
app = FastAPI()
app.include_router(router, prefix="/ingestion", tags=["ingestion"])

# Configure logging
logger = logging.getLogger(__name__)

@router.post("/load/sdn_data")
def load_sdn_data(
    db: Session = Depends(get_db),
    xml_url: str = "https://sanctionslistservice.ofac.treas.gov/api/PublicationPreview/exports/SDN.XML",
    xsd_url: str = "https://sanctionslistservice.ofac.treas.gov/api/PublicationPreview/exports/XML.xsd"
) -> dict[str, str]:
    """
    Load SDN data from the provided XML and XSD URLs.

    Args:
        db (Session): The database session.
        xml_url (str): The URL of the SDN XML file.
        xsd_url (str): The URL of the XSD file.

    Returns:
        dict: A message indicating the success or failure of the operation.
    """
    try:
        logger.info("Starting SDN data ingestion process.")

        # Download and validate files
        logger.info(f"Downloading files from {xml_url} and {xsd_url}.")
        xml_path, xsd_path = download_sdn_files(xml_url, xsd_url)

        logger.info("Validating XML file against XSD schema.")
        if not validate_sdn_xml(xml_path, xsd_path):
            logger.error("XML validation failed.")
            raise HTTPException(status_code=400, detail="Invalid XML file")

        # Parse and save data to database
        logger.info("Parsing XML file.")
        sdn_data = parse_sdn_xml(xml_path)

        logger.info("Saving parsed data to the database.")
        store_sdn_data(sdn_data, db)

        logger.info("SDN advanced data loaded successfully.")
        return {"message": "SDN advanced data loaded successfully"}
    except HTTPException as http_exc:
        logger.error(f"HTTP error occurred: {http_exc.detail}")
        raise http_exc
    except Exception as e:
        logger.exception("An unexpected error occurred.")
        raise HTTPException(status_code=500, detail="An internal server error occurred.")
