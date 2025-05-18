# backend/ingestion/main.py

# Import dependencies
import logging
from fastapi import FastAPI, APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from contextlib import asynccontextmanager
import os

# Import custom modules
from backend.data_layer.database import get_db, init_db
from backend.ingestion.service import (
    download_sdn_files,
    validate_sdn_xml,
    parse_sdn_xml,
    store_sdn_data
)

# Initialize the FastAPI router
router = APIRouter()

# Configure logging
logger = logging.getLogger(__name__)

# Initialize the scheduler
scheduler = BackgroundScheduler()

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

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan event handler for the FastAPI application.
    This function initializes the database and scheduler, and loads SDN data at startup.
    It also handles the shutdown of the scheduler at the end of the application lifecycle.
    Args:
        app (FastAPI): The FastAPI application instance.
    Yields:
        None: This function does not yield any value.
    """
    # Skip startup logic during tests
    if "PYTEST_CURRENT_TEST" not in os.environ:
        logger.info("Application startup: Triggering SDN data load.")
        # Initialize the database and create tables
        init_db()
        try:
            db = next(get_db())
            load_sdn_data(db=db)
            scheduler.add_job(
                func=lambda: load_sdn_data(db=next(get_db())),
                trigger=CronTrigger(hour=0, minute=0),
                id="daily_sdn_data_load",
                replace_existing=True
            )
            scheduler.start()
        except Exception as e:
            logger.error(f"Failed to initialize SDN data load: {e}")
    yield
    logger.info("Shutting down scheduler.")
    if scheduler.running:
        scheduler.shutdown()

# Initialize FastAPI app
app = FastAPI(lifespan=lifespan)
app.include_router(router, prefix="/ingestion", tags=["ingestion"])