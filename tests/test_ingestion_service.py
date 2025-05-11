# tests/test_ingestion_service.py

import os
import io
import pytest
import requests
from unittest.mock import patch, mock_open, MagicMock
from lxml import etree
from sqlalchemy.orm import Session
from open_graph_intel.ingestion.service import (
    download_sdn_files,
    validate_sdn_xml,
    parse_sdn_xml,
    store_sdn_data
)

# Sample XML and XSD content for testing
SAMPLE_XML = """<?xml version="1.0"?>
<sdnList xmlns="https://sanctionslistservice.ofac.treas.gov/api/PublicationPreview/exports/XML">
    <publshInformation>
        <Publish_Date>2025-05-11</Publish_Date>
        <Record_Count>1</Record_Count>
    </publshInformation>
    <sdnEntry>
        <uid>123</uid>
        <firstName>John</firstName>
        <lastName>Doe</lastName>
        <title>Mr.</title>
        <sdnType>Individual</sdnType>
        <remarks>Test remarks</remarks>
        <programList>
            <program>Program1</program>
        </programList>
        <akaList>
            <aka>
                <uid>1</uid>
                <type>Alias</type>
                <category>Primary</category>
                <lastName>Doe</lastName>
                <firstName>John</firstName>
            </aka>
        </akaList>
        <idList>
            <id>
                <uid>1</uid>
                <idType>Passport</idType>
                <idNumber>123456789</idNumber>
                <idCountry>US</idCountry>
                <issueDate>2020-01-01</issueDate>
                <expirationDate>2030-01-01</expirationDate>
            </id>
        </idList>
        <nationalityList>
            <nationality>
                <uid>1</uid>
                <country>US</country>
                <mainEntry>true</mainEntry>
            </nationality>
        </nationalityList>
        <citizenshipList>
            <citizenship>
                <uid>1</uid>
                <country>US</country>
                <mainEntry>true</mainEntry>
            </citizenship>
        </citizenshipList>
        <dateOfBirthList>
            <dateOfBirthItem>
                <uid>1</uid>
                <dateOfBirth>1980-01-01</dateOfBirth>
                <mainEntry>true</mainEntry>
            </dateOfBirthItem>
        </dateOfBirthList>
        <placeOfBirthList>
            <placeOfBirthItem>
                <uid>1</uid>
                <placeOfBirth>New York</placeOfBirth>
                <mainEntry>true</mainEntry>
            </placeOfBirthItem>
        </placeOfBirthList>
        <addressList>
            <address>
                <uid>1</uid>
                <address1>123 Main St</address1>
                <address2>Apt 4B</address2>
                <address3></address3>
                <city>New York</city>
                <stateOrProvince>NY</stateOrProvince>
                <postalCode>10001</postalCode>
                <country>USA</country>
                <region>North America</region>
            </address>
        </addressList>
        <vesselInfo>
            <callSign>ABC123</callSign>
            <vesselType>Cargo</vesselType>
            <vesselFlag>US</vesselFlag>
            <vesselOwner>Owner Name</vesselOwner>
            <tonnage>5000</tonnage>
            <grossRegisteredTonnage>6000</grossRegisteredTonnage>
        </vesselInfo>
    </sdnEntry>
</sdnList>
"""

SAMPLE_XSD = """<?xml version="1.0"?>
<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema" xmlns="https://sanctionslistservice.ofac.treas.gov/api/PublicationPreview/exports/XML" targetNamespace="https://sanctionslistservice.ofac.treas.gov/api/PublicationPreview/exports/XML" elementFormDefault="qualified">
    <xs:element name="sdnList">
        <xs:complexType>
            <xs:sequence>
                <xs:element name="publshInformation" maxOccurs="1">
                    <xs:complexType>
                        <xs:sequence>
                            <xs:element name="Publish_Date" type="xs:string" minOccurs="0" maxOccurs="1"/>
                            <xs:element name="Record_Count" type="xs:int" minOccurs="0" maxOccurs="1"/>
                        </xs:sequence>
                    </xs:complexType>
                </xs:element>
                <xs:element name="sdnEntry" maxOccurs="unbounded">
                    <xs:complexType>
                        <xs:sequence>
                            <xs:element name="uid" type="xs:int"/>
                            <xs:element name="firstName" type="xs:string" minOccurs="0"/>
                            <xs:element name="lastName" type="xs:string"/>
                            <xs:element name="title" type="xs:string" minOccurs="0"/>
                            <xs:element name="sdnType" type="xs:string"/>
                            <xs:element name="remarks" type="xs:string" minOccurs="0"/>
                            <xs:element name="programList" minOccurs="1" maxOccurs="1">
                                <xs:complexType>
                                    <xs:sequence>
                                        <xs:element name="program" type="xs:string" minOccurs="0" maxOccurs="unbounded"/>
                                    </xs:sequence>
                                </xs:complexType>
                            </xs:element>
                            <xs:element name="akaList" maxOccurs="1" minOccurs="0">
                                <xs:complexType>
                                    <xs:sequence>
                                        <xs:element name="aka" minOccurs="0" maxOccurs="unbounded">
                                            <xs:complexType>
                                                <xs:sequence>
                                                    <xs:element name="uid" type="xs:int"/>
                                                    <xs:element name="type" type="xs:string"/>
                                                    <xs:element name="category" type="xs:string"/>
                                                    <xs:element name="lastName" type="xs:string" minOccurs="0"/>
                                                    <xs:element name="firstName" type="xs:string" minOccurs="0"/>
                                                </xs:sequence>
                                            </xs:complexType>
                                        </xs:element>
                                    </xs:sequence>
                                </xs:complexType>
                            </xs:element>
                            <xs:element name="idList" maxOccurs="1" minOccurs="0">
                                <xs:complexType>
                                    <xs:sequence>
                                        <xs:element name="id" minOccurs="0" maxOccurs="unbounded">
                                            <xs:complexType>
                                                <xs:sequence>
                                                    <xs:element name="uid" type="xs:int"/>
                                                    <xs:element name="idType" type="xs:string" minOccurs="0"/>
                                                    <xs:element name="idNumber" type="xs:string" minOccurs="0"/>
                                                    <xs:element name="idCountry" type="xs:string" minOccurs="0"/>
                                                    <xs:element name="issueDate" type="xs:string" minOccurs="0"/>
                                                    <xs:element name="expirationDate" type="xs:string" minOccurs="0"/>
                                                </xs:sequence>
                                            </xs:complexType>
                                        </xs:element>
                                    </xs:sequence>
                                </xs:complexType>
                            </xs:element>
                            <xs:element name="nationalityList" minOccurs="0" maxOccurs="1">
                                <xs:complexType>
                                    <xs:sequence>
                                        <xs:element name="nationality" minOccurs="0" maxOccurs="unbounded">
                                            <xs:complexType>
                                                <xs:sequence>
                                                    <xs:element name="uid" type="xs:int"/>
                                                    <xs:element name="country" type="xs:string"/>
                                                    <xs:element name="mainEntry" type="xs:boolean"/>
                                                </xs:sequence>
                                            </xs:complexType>
                                        </xs:element>
                                    </xs:sequence>
                                </xs:complexType>
                            </xs:element>
                            <xs:element name="citizenshipList" minOccurs="0" maxOccurs="1">
                                <xs:complexType>
                                    <xs:sequence>
                                        <xs:element name="citizenship" minOccurs="0" maxOccurs="unbounded">
                                            <xs:complexType>
                                                <xs:sequence>
                                                    <xs:element name="uid" type="xs:int"/>
                                                    <xs:element name="country" type="xs:string"/>
                                                    <xs:element name="mainEntry" type="xs:boolean"/>
                                                </xs:sequence>
                                            </xs:complexType>
                                        </xs:element>
                                    </xs:sequence>
                                </xs:complexType>
                            </xs:element>
                            <xs:element name="dateOfBirthList" minOccurs="0" maxOccurs="1">
                                <xs:complexType>
                                    <xs:sequence>
                                        <xs:element name="dateOfBirthItem" minOccurs="0" maxOccurs="unbounded">
                                            <xs:complexType>
                                                <xs:sequence>
                                                    <xs:element name="uid" type="xs:int"/>
                                                    <xs:element name="dateOfBirth" type="xs:string"/>
                                                    <xs:element name="mainEntry" type="xs:boolean"/>
                                                </xs:sequence>
                                            </xs:complexType>
                                        </xs:element>
                                    </xs:sequence>
                                </xs:complexType>
                            </xs:element>
                            <xs:element name="placeOfBirthList" minOccurs="0" maxOccurs="1">
                                <xs:complexType>
                                    <xs:sequence>
                                        <xs:element name="placeOfBirthItem" minOccurs="0" maxOccurs="unbounded">
                                            <xs:complexType>
                                                <xs:sequence>
                                                    <xs:element name="uid" type="xs:int"/>
                                                    <xs:element name="placeOfBirth" type="xs:string"/>
                                                    <xs:element name="mainEntry" type="xs:boolean"/>
                                                </xs:sequence>
                                            </xs:complexType>
                                        </xs:element>
                                    </xs:sequence>
                                </xs:complexType>
                            </xs:element>
                            <xs:element name="addressList" maxOccurs="1" minOccurs="0">
                                <xs:complexType>
                                    <xs:sequence>
                                        <xs:element name="address" minOccurs="0" maxOccurs="unbounded">
                                            <xs:complexType>
                                                <xs:sequence>
                                                    <xs:element name="uid" type="xs:int"/>
                                                    <xs:element name="address1" type="xs:string" minOccurs="0"/>
                                                    <xs:element name="address2" type="xs:string" minOccurs="0"/>
                                                    <xs:element name="address3" type="xs:string" minOccurs="0"/>
                                                    <xs:element name="city" type="xs:string" minOccurs="0"/>
                                                    <xs:element name="stateOrProvince" type="xs:string" minOccurs="0"/>
                                                    <xs:element name="postalCode" type="xs:string" minOccurs="0"/>
                                                    <xs:element name="country" type="xs:string" minOccurs="0"/>
                                                    <xs:element name="region" type="xs:string" minOccurs="0"/>
                                                </xs:sequence>
                                            </xs:complexType>
                                        </xs:element>
                                    </xs:sequence>
                                </xs:complexType>
                            </xs:element>
                            <xs:element name="vesselInfo" minOccurs="0" maxOccurs="1">
                                <xs:complexType>
                                    <xs:sequence>
                                        <xs:element name="callSign" type="xs:string" minOccurs="0"/>
                                        <xs:element name="vesselType" type="xs:string" minOccurs="0"/>
                                        <xs:element name="vesselFlag" type="xs:string" minOccurs="0"/>
                                        <xs:element name="vesselOwner" type="xs:string" minOccurs="0"/>
                                        <xs:element name="tonnage" type="xs:int" minOccurs="0"/>
                                        <xs:element name="grossRegisteredTonnage" type="xs:int" minOccurs="0"/>
                                    </xs:sequence>
                                </xs:complexType>
                            </xs:element>
                        </xs:sequence>
                    </xs:complexType>
                </xs:element>
            </xs:sequence>
        </xs:complexType>
    </xs:element>
</xs:schema>
"""

@pytest.fixture
def mock_requests_get():
    with patch("requests.get") as mock_get:
        yield mock_get

@pytest.fixture
def mock_open_file():
    with patch("builtins.open", mock_open()) as mock_file:
        yield mock_file

@pytest.fixture
def mock_db_session():
    return MagicMock(spec=Session)

def test_download_sdn_files(mock_requests_get, mock_open_file):
    mock_requests_get.return_value.content = b"test content"
    xml_path, xsd_path = download_sdn_files("http://example.com/sdn.xml", "http://example.com/sdn.xsd")
    assert xml_path == "sdn_advanced.xml"
    assert xsd_path == "sdn_advanced.xsd"
    mock_open_file.assert_called()

def test_validate_sdn_xml(mock_open_file):
    mock_open_file.side_effect = [
        mock_open(read_data=SAMPLE_XSD).return_value,
        mock_open(read_data=SAMPLE_XML).return_value
    ]
    assert validate_sdn_xml("sdn_advanced.xml", "sdn_advanced.xsd") is True

def test_parse_sdn_xml():
    # Pass io.StringIO directly to parse_sdn_xml
    result = parse_sdn_xml(io.StringIO(SAMPLE_XML))
    assert len(result) == 1
    assert result[0]["uid"] == "123"
    assert result[0]["first_name"] == "John"

def test_store_sdn_data(mock_db_session):
    # Configure the mock to simulate no existing entity
    mock_query = mock_db_session.query.return_value
    mock_query.filter.return_value.first.return_value = None

    # Pass io.StringIO directly to parse_sdn_xml
    sdn_data = parse_sdn_xml(io.StringIO(SAMPLE_XML))
    store_sdn_data(sdn_data, mock_db_session)

    # Assert that the add and commit methods were called
    assert mock_db_session.add.called
    assert mock_db_session.commit.called
