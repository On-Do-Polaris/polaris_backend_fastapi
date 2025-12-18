# -*- coding: utf-8 -*-
"""
Test Specification: Automated Risk Report Generation & PDF Download
File: test_report_pdf.py
Description: This file contains integration tests for the PDF report generation
             and download functionality, based on TS_BE_ReportPDF_21.
"""

import asyncio
import logging
import time
import io
from unittest.mock import patch, AsyncMock

import httpx
import pytest
import pytest_asyncio
from typing import AsyncGenerator, Dict, Any

# Attempt to import PyPDF2, required for TC_002
try:
    from PyPDF2 import PdfReader
except ImportError:
    PdfReader = None

# ==============================================================================
# 1. Configuration & Setup
# ==============================================================================

# Logging configuration
LOG_FILE_PATH = "TC/test_report_pdf_log.txt"
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE_PATH, mode='w', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# --- System Environment ---
BASE_URL = "http://127.0.0.1:8000"
# Assuming a RESTful structure for the reports API
REPORTS_API_ENDPOINT = "/api/reports"

# --- Security Tokens for TC_003 ---
# IMPORTANT: Replace with valid JWT tokens for two different users.
ACCESS_TOKEN_USER_A = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1c2VyX0EiLCJleHAiOjE3NjQ1NTg0MDB9.fake_token_A"
ACCESS_TOKEN_USER_B = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1c2VyX0IiLCJleHAiOjE3NjQ1NTg0MDB9.fake_token_B"
HEADERS_USER_A = {"Authorization": f"Bearer {ACCESS_TOKEN_USER_A}"}
HEADERS_USER_B = {"Authorization": f"Bearer {ACCESS_TOKEN_USER_B}"}

# --- Test Parameters ---
POLLING_INTERVAL_SECONDS = 3
REPORT_GENERATION_TIMEOUT_SECONDS = 60  # Timeout for the entire generation process
PDF_ENGINE_DELAY_SECONDS = 35  # For TC_006

# ==============================================================================
# 2. Pytest Fixtures
# ==============================================================================

@pytest.fixture(scope="session")
def anyio_backend():
    """Defines the asyncio backend for pytest-asyncio."""
    return "asyncio"

@pytest_asyncio.fixture(scope="function")
async def client_user_a() -> AsyncGenerator[httpx.AsyncClient, None]:
    """Provides an HTTP client authenticated as User A."""
    async with httpx.AsyncClient(base_url=BASE_URL, headers=HEADERS_USER_A, timeout=REPORT_GENERATION_TIMEOUT_SECONDS) as client:
        yield client

@pytest_asyncio.fixture(scope="function")
async def client_user_b() -> AsyncGenerator[httpx.AsyncClient, None]:
    """Provides an HTTP client authenticated as User B."""
    async with httpx.AsyncClient(base_url=BASE_URL, headers=HEADERS_USER_B, timeout=REPORT_GENERATION_TIMEOUT_SECONDS) as client:
        yield client

# ==============================================================================
# 3. Helper Functions
# ==============================================================================

async def generate_report_and_get_id(client: httpx.AsyncClient, site_id: Any) -> str:
    """Helper to request report generation and poll for completion."""
    logger.info(f"Requesting report generation for siteId: {site_id}")
    # Step 1: Request generation
    # Assuming a POST to /api/reports with a siteId creates a report job
    response = await client.post(REPORTS_API_ENDPOINT, json={"siteId": site_id})
    if response.status_code != 202:
        logger.error(f"Failed to request report generation. Status: {response.status_code}, Body: {response.text}")
    assert response.status_code == 202, "Report generation request failed."
    
    data = response.json()
    assert "reportId" in data, "Response should contain a 'reportId'."
    report_id = data["reportId"]
    logger.info(f"Report generation started. reportId: {report_id}")

    # Step 2: Poll for status
    start_time = time.time()
    while time.time() - start_time < REPORT_GENERATION_TIMEOUT_SECONDS:
        # Assuming a GET to /api/reports/{report_id}/status returns the job status
        status_response = await client.get(f"{REPORTS_API_ENDPOINT}/{report_id}/status")
        if status_response.status_code == 200:
            status_data = status_response.json()
            status = status_data.get("status")
            logger.info(f"Polling reportId '{report_id}': Status is '{status}'.")
            if status == "COMPLETED":
                logger.info(f"Report '{report_id}' generation completed.")
                return report_id
            if status == "FAILED":
                pytest.fail(f"Report generation failed for reportId '{report_id}'.")
        await asyncio.sleep(POLLING_INTERVAL_SECONDS)
    
    pytest.fail(f"Polling for reportId '{report_id}' timed out after {REPORT_GENERATION_TIMEOUT_SECONDS}s.")


# ==============================================================================
# 4. Test Scenarios (TS_BE_ReportPDF_21)
# ==============================================================================

@pytest.mark.asyncio
async def test_tc_001_pdf_generation_and_download(client_user_a: httpx.AsyncClient):
    """
    ID: TC_001
    Test Case: PDF Generation and Download
    Procedure: Generate a report for siteId=1 and request to download it.
    Expected Result: 200 OK, Content-Type is application/pdf, Content-Disposition is correct,
                     and the body starts with the PDF signature '%PDF-'.
    """
    logger.info("--- TC_001: PDF Generation and Download - START ---")
    
    # Step 1: Generate a report and get its ID
    report_id = await generate_report_and_get_id(client_user_a, site_id=1)
    
    # Step 2: Download the generated PDF
    logger.info(f"[Step 2] Downloading PDF for reportId: {report_id}")
    start_time = time.time()
    download_response = await client_user_a.get(f"{REPORTS_API_ENDPOINT}/{report_id}/download")
    duration = time.time() - start_time
    
    # Step 3: Verify the response
    logger.info("[Step 3] Verifying download response headers and content.")
    assert download_response.status_code == 200, f"Expected 200 OK, got {download_response.status_code}"
    
    # Verify headers
    assert download_response.headers.get("Content-Type") == "application/pdf"
    content_disposition = download_response.headers.get("Content-Disposition")
    assert content_disposition is not None
    assert content_disposition.startswith("attachment; filename="), "Content-Disposition should indicate an attachment."
    
    # Verify binary content (PDF signature)
    pdf_content = download_response.content
    assert pdf_content.startswith(b'%PDF-'), "Response body does not start with PDF signature '%PDF-'."
    
    file_size_kb = len(pdf_content) / 1024
    logger.info(f"PDF downloaded successfully: size={file_size_kb:.2f} KB, time={duration:.2f}s.")
    logger.info("--- TC_001: PDF Generation and Download - PASSED ---")

@pytest.mark.asyncio
@pytest.mark.skipif(PdfReader is None, reason="PyPDF2 is not installed, skipping TC_002.")
async def test_tc_002_data_integrity_validation(client_user_a: httpx.AsyncClient):
    """
    ID: TC_002
    Test Case: Data Integrity Verification
    Procedure: Generate a PDF, extract text from it, and compare key metrics with a source
               (e.g., a mock DB call or a predefined value).
    Expected Result: Key metrics like 'Asset Loss Ratio' match the source data.
    """
    logger.info("--- TC_002: Data Integrity Validation - START ---")
    
    # Step 1: Generate a report
    # For this test, we assume the report for siteId=2 has a known 'Asset Loss Ratio'.
    expected_asset_loss_ratio = "7.5%" # Dummy value
    logger.info(f"Expecting '자산손실률' to be '{expected_asset_loss_ratio}' in the generated report.")
    report_id = await generate_report_and_get_id(client_user_a, site_id=2)
    
    # Step 2: Download the PDF content
    logger.info(f"[Step 2] Downloading PDF for data integrity check (reportId: {report_id}).")
    download_response = await client_user_a.get(f"{REPORTS_API_ENDPOINT}/{report_id}/download")
    assert download_response.status_code == 200
    pdf_content = download_response.content
    
    # Step 3: Extract text from PDF and verify data
    logger.info("[Step 3] Extracting text from PDF using PyPDF2.")
    try:
        pdf_file = io.BytesIO(pdf_content)
        reader = PdfReader(pdf_file)
        full_text = ""
        for page in reader.pages:
            full_text += page.extract_text()
        
        logger.info("Successfully extracted text from PDF.")
        # This is a simplified check. A real-world scenario might need regex or more robust parsing.
        assert f"자산손실률: {expected_asset_loss_ratio}" in full_text or \
               f"자산손실률 {expected_asset_loss_ratio}" in full_text, \
               f"Could not find '자산손실률: {expected_asset_loss_ratio}' in the extracted PDF text."

    except Exception as e:
        pytest.fail(f"Failed to read or parse the PDF content: {e}")

    logger.info("--- TC_002: Data Integrity Validation - PASSED ---")


@pytest.mark.asyncio
async def test_tc_003_unauthorized_access_prevention(client_user_a: httpx.AsyncClient, client_user_b: httpx.AsyncClient):
    """
    ID: TC_003
    Test Case: Prevent access to unauthorized files
    Procedure: User A generates a report. User B attempts to download it using the report ID.
    Expected Result: User B's request is rejected with 403 Forbidden or 404 Not Found.
    """
    logger.info("--- TC_003: Unauthorized Access Prevention - START ---")
    
    # Step 1: User A generates a report.
    logger.info("[Step 1] User A is generating a report.")
    report_id_a = await generate_report_and_get_id(client_user_a, site_id=3)
    logger.info(f"User A generated reportId: {report_id_a}")
    
    # Step 2: User B attempts to download User A's report.
    logger.info("[Step 2] User B is attempting to download User A's report (should be blocked).")
    unauthorized_response = await client_user_b.get(f"{REPORTS_API_ENDPOINT}/{report_id_a}/download")
    
    # Step 3: Verify the rejection.
    logger.info(f"[Step 3] Verifying rejection. Status code received: {unauthorized_response.status_code}")
    assert unauthorized_response.status_code in [403, 404], \
        f"Expected 403 or 404 for unauthorized access, but got {unauthorized_response.status_code}."
        
    logger.info("--- TC_003: Unauthorized Access Prevention - PASSED ---")


@pytest.mark.asyncio
async def test_tc_004_template_standard_validation(client_user_a: httpx.AsyncClient):
    """
    ID: TC_004
    Test Case: Report Template Standard Compliance
    Procedure: Download a file and perform a basic check for compliance.
    Expected Result: Log file size for visual confirmation or basic heuristics.
    """
    logger.info("--- TC_004: Template Standard Validation - START ---")
    report_id = await generate_report_and_get_id(client_user_a, site_id=4)
    
    download_response = await client_user_a.get(f"{REPORTS_API_ENDPOINT}/{report_id}/download")
    assert download_response.status_code == 200
    
    # For this test, we log the file size as a proxy for layout validation.
    # A non-empty, reasonably-sized file suggests the template was likely applied.
    file_size_kb = len(download_response.content) / 1024
    logger.info(f"Downloaded report for template check. Size: {file_size_kb:.2f} KB.")
    
    # Assert that the file size is within a reasonable range (e.g., > 10KB)
    assert file_size_kb > 10, "PDF file size is suspiciously small, template may be missing."
    
    logger.info("--- TC_004: Template Standard Validation - PASSED ---")

@pytest.mark.asyncio
async def test_tc_005_pdf_engine_failure(client_user_a: httpx.AsyncClient):
    """
    ID: TC_005
    Test Case: PDF Generation Module Engine Error
    Procedure: Mock the PDF generation service to throw an exception.
    Expected Result: 500 Internal Server Error is returned, and an error is logged.
    """
    logger.info("--- TC_005: PDF Engine Failure - START ---")
    
    # IMPORTANT: The path 'src.services.report_service.ReportService.generate_and_save_pdf'
    # is a placeholder. It must be replaced with the actual import path to the PDF generation method.
    mock_target_path = "src.services.report_service.ReportService.generate_and_save_pdf"
    
    with patch(mock_target_path, side_effect=Exception("Mocked PDF Engine Failure")) as mock_method:
        logger.info(f"[Step 1] Mocking '{mock_target_path}' to raise an exception.")
        
        # Step 2: Request a report generation, which should now fail.
        # We don't use the helper here because we expect an error, not completion.
        response = await client_user_a.post(REPORTS_API_ENDPOINT, json={"siteId": 5})
        
        # Step 3: Verify the error response.
        # The exact response depends on implementation. It might be a 500 on the initial
        # request if generation is synchronous, or the status poll might show FAILED.
        # We assume the polling mechanism will catch the failure.
        assert response.status_code == 202, "The initial request should still be accepted."
        report_id = response.json()["reportId"]

        logger.info("[Step 2] Polling for status, expecting FAILED.")
        start_time = time.time()
        final_status = None
        while time.time() - start_time < REPORT_GENERATION_TIMEOUT_SECONDS:
            status_response = await client_user_a.get(f"{REPORTS_API_ENDPOINT}/{report_id}/status")
            if status_response.status_code == 200 and status_response.json().get("status") == "FAILED":
                final_status = status_response.json()
                break
            await asyncio.sleep(POLLING_INTERVAL_SECONDS)
        
        assert final_status is not None, "Polling did not result in a FAILED status within timeout."
        assert "error" in final_status
        assert "Mocked PDF Engine Failure" in final_status["error"]
        mock_method.assert_called_once()

    logger.info("--- TC_005: PDF Engine Failure - PASSED ---")


@pytest.mark.asyncio
async def test_tc_006_generation_process_timeout(client_user_a: httpx.AsyncClient):
    """
    ID: TC_006
    Test Case: Generation Process Timeout
    Procedure: Mock the PDF generation to take longer than the server's timeout threshold.
    Expected Result: A 504 Gateway Timeout or a 500 Internal Server Error is handled gracefully.
    """
    logger.info("--- TC_006: Generation Process Timeout - START ---")

    async def long_running_pdf_generation(*args, **kwargs):
        logger.info(f"Mocked PDF generation started, sleeping for {PDF_ENGINE_DELAY_SECONDS}s to trigger timeout...")
        await asyncio.sleep(PDF_ENGINE_DELAY_SECONDS)
        logger.info("Mocked PDF generation finished sleeping (should have been cancelled).")

    # IMPORTANT: The path is a placeholder. See TC_005.
    mock_target_path = "src.services.report_service.ReportService.generate_and_save_pdf"

    with patch(mock_target_path, new=long_running_pdf_generation) as mock_method:
        logger.info(f"[Step 1] Mocking '{mock_target_path}' to simulate a long delay.")
        
        # Step 2: Request report generation
        response = await client_user_a.post(REPORTS_API_ENDPOINT, json={"siteId": 6})
        assert response.status_code == 202
        report_id = response.json()["reportId"]

        # Step 3: Poll and expect a FAILED status due to timeout
        logger.info("[Step 2] Polling for status, expecting FAILED due to internal timeout.")
        start_time = time.time()
        final_status = None
        while time.time() - start_time < REPORT_GENERATION_TIMEOUT_SECONDS:
            status_response = await client_user_a.get(f"{REPORTS_API_ENDPOINT}/{report_id}/status")
            if status_response.status_code == 200:
                status_data = status_response.json()
                if status_data.get("status") == "FAILED":
                    final_status = status_data
                    break
            await asyncio.sleep(POLLING_INTERVAL_SECONDS)

        assert final_status is not None, "Job did not fail within the test polling timeout."
        # Check that the error message indicates a timeout
        assert "timeout" in final_status.get("error", "").lower(), \
            f"Error message should indicate a timeout, but was: {final_status.get('error')}"
        mock_method.assert_called_once()
        
    logger.info("--- TC_006: Generation Process Timeout - PASSED ---")


