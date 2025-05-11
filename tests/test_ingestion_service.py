# tests/test_ingestion_service.py

import os
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
<DistinctParties>
    <DistinctParty>
        <uid>123</uid>
        <first_name>John</first_name>
        <last_name>Doe</last_name>
        <sdn_type>Individual</sdn_type>
        <remarks>Test remarks</remarks>
        <programList>
            <program>Program1</program>
        </programList>
        <akaList>
            <aka>
                <wholeName>John D.</wholeName>
            </aka>
        </akaList>
        <nationalityList>
            <nationality>
                <isoCode>US</isoCode>
            </nationality>
        </nationalityList>
        <addressList>
            <address>
                <street>123 Main St</street>
                <city>New York</city>
                <state>NY</state>
                <postalCode>10001</postalCode>
                <country>USA</country>
            </address>
        </addressList>
        <documentList>
            <document>
                <idType>Passport</idType>
                <number>123456789</number>
                <country>US</country>
            </document>
        </documentList>
    </DistinctParty>
</DistinctParties>
"""

SAMPLE_XSD = """<?xml version="1.0"?>
<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema">
    <xs:element name="DistinctParties">
        <xs:complexType>
            <xs:sequence>
                <xs:element name="DistinctParty" maxOccurs="unbounded">
                    <xs:complexType>
                        <xs:sequence>
                            <xs:element name="uid" type="xs:string"/>
                            <xs:element name="first_name" type="xs:string"/>
                            <xs:element name="last_name" type="xs:string"/>
                            <xs:element name="sdn_type" type="xs:string"/>
                            <xs:element name="remarks" type="xs:string" minOccurs="0"/>
                            <xs:element name="programList" minOccurs="0">
                                <xs:complexType>
                                    <xs:sequence>
                                        <xs:element name="program" type="xs:string" maxOccurs="unbounded"/>
                                    </xs:sequence>
                                </xs:complexType>
                            </xs:element>
                            <xs:element name="akaList" minOccurs="0">
                                <xs:complexType>
                                    <xs:sequence>
                                        <xs:element name="aka" minOccurs="0" maxOccurs="unbounded">
                                            <xs:complexType>
                                                <xs:sequence>
                                                    <xs:element name="wholeName" type="xs:string"/>
                                                </xs:sequence>
                                            </xs:complexType>
                                        </xs:element>
                                    </xs:sequence>
                                </xs:complexType>
                            </xs:element>
                            <xs:element name="nationalityList" minOccurs="0">
                                <xs:complexType>
                                    <xs:sequence>
                                        <xs:element name="nationality" minOccurs="0" maxOccurs="unbounded">
                                            <xs:complexType>
                                                <xs:sequence>
                                                    <xs:element name="isoCode" type="xs:string"/>
                                                </xs:sequence>
                                            </xs:complexType>
                                        </xs:element>
                                    </xs:sequence>
                                </xs:complexType>
                            </xs:element>
                            <xs:element name="addressList" minOccurs="0">
                                <xs:complexType>
                                    <xs:sequence>
                                        <xs:element name="address" minOccurs="0" maxOccurs="unbounded">
                                            <xs:complexType>
                                                <xs:sequence>
                                                    <xs:element name="street" type="xs:string"/>
                                                    <xs:element name="city" type="xs:string"/>
                                                    <xs:element name="state" type="xs:string"/>
                                                    <xs:element name="postalCode" type="xs:string"/>
                                                    <xs:element name="country" type="xs:string"/>
                                                </xs:sequence>
                                            </xs:complexType>
                                        </xs:element>
                                    </xs:sequence>
                                </xs:complexType>
                            </xs:element>
                            <xs:element name="documentList" minOccurs="0">
                                <xs:complexType>
                                    <xs:sequence>
                                        <xs:element name="document" minOccurs="0" maxOccurs="unbounded">
                                            <xs:complexType>
                                                <xs:sequence>
                                                    <xs:element name="idType" type="xs:string"/>
                                                    <xs:element name="number" type="xs:string"/>
                                                    <xs:element name="country" type="xs:string"/>
                                                </xs:sequence>
                                            </xs:complexType>
                                        </xs:element>
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

def test_parse_advanced_sdn_xml(mock_open_file):
    mock_open_file.return_value.read.return_value = SAMPLE_XML
    result = parse_sdn_xml("sdn_advanced.xml")
    assert len(result) == 1
    assert result[0]["uid"] == "123"
    assert result[0]["first_name"] == "John"

def test_store_sdn_data(mock_db_session):
    sdn_data = parse_sdn_xml("sdn_advanced.xml")
    store_sdn_data(sdn_data, mock_db_session)
    assert mock_db_session.add.called
    assert mock_db_session.commit.called

