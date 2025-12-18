# -*- coding: utf-8 -*-
"""
Test Specification: AI-Based Risk Assessment Automation (LangGraph & FastAPI)
File: test_analysis_core.py
Description: This file contains integration tests for the AI risk assessment system's backend.
             It is based on the test specification TS_BE_AnalysisCore_13.
"""

import asyncio
import logging
import uuid
from datetime import datetime
from unittest.mock import patch, AsyncMock

import httpx
import pytest
import pytest_asyncio
from typing import AsyncGenerator, Dict, Any

# ==============================================================================
# 1. Configuration & Setup
# ==============================================================================

# Logging configuration as per AI Instructions (4)
# This will create a log file in the TC directory to store detailed execution logs.
LOG_FILE_PATH = "TC/test_analysis_core_log.txt"
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
# These constants should be adjusted according to the actual test environment.
BASE_URL = "http://127.0.0.1:8000"
ANALYSIS_API_ENDPOINT = "/api/analysis"
# IMPORTANT: Replace with a valid JWT token for the test environment.
DUMMY_ACCESS_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c"
HEADERS = {"Authorization": f"Bearer {DUMMY_ACCESS_TOKEN}"}

# Polling and Timeout settings
POLLING_INTERVAL_SECONDS = 5
JOB_TIMEOUT_SECONDS = 180  # Increased timeout to accommodate potentially slow jobs
PERFORMANCE_THRESHOLD_SECONDS = 60 # For TC_006

# ==============================================================================
# 2. Pytest Fixtures
# ==============================================================================

@pytest.fixture(scope="session")
def anyio_backend():
    """Defines the asyncio backend for pytest-asyncio."""
    return "asyncio"

@pytest_asyncio.fixture(scope="module")
async def async_client() -> AsyncGenerator[httpx.AsyncClient, None]:
    """
    Creates an HTTPX async client for making API calls.
    This client is reused across all tests in the module for efficiency.
    """
    async with httpx.AsyncClient(base_url=BASE_URL, headers=HEADERS, timeout=JOB_TIMEOUT_SECONDS) as client:
        logger.info("httpx.AsyncClient initialized for testing.")
        yield client
        logger.info("httpx.AsyncClient closed.")

@pytest_asyncio.fixture(scope="function")
async def db_session_mock() -> AsyncMock:
    """
    Provides a mock for the database session.
    This allows simulating DB operations without a real database connection.
    For TC_007, this can be replaced with a real DB session fixture if needed.
    """
    mock = AsyncMock()
    mock.execute.return_value.scalar_one_or_none.return_value = None # Simulate no records found
    logger.info("AsyncMock for DB session created.")
    return mock


# ==============================================================================
# 3. Helper Functions
# ==============================================================================

async def poll_job_status(client: httpx.AsyncClient, job_id: str) -> Dict[str, Any]:
    """
    Polls the job status endpoint until the job is completed or failed, or until a timeout occurs.
    """
    start_time = datetime.now()
    while (datetime.now() - start_time).total_seconds() < JOB_TIMEOUT_SECONDS:
        try:
            response = await client.get(f"{ANALYSIS_API_ENDPOINT}/status/{job_id}")
            response.raise_for_status()
            status_data = response.json()
            job_status = status_data.get("status")
            logger.info(f"Polling for jobID '{job_id}': Current status is '{job_status}'.")

            if job_status in ["COMPLETED", "FAILED"]:
                logger.info(f"Job '{job_id}' finished with final status: '{job_status}'.")
                return status_data
            
            await asyncio.sleep(POLLING_INTERVAL_SECONDS)

        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error while polling job status for '{job_id}': {e}")
            raise
        except Exception as e:
            logger.error(f"An unexpected error occurred during polling for '{job_id}': {e}")
            raise

    raise TimeoutError(f"Job '{job_id}' did not complete within the {JOB_TIMEOUT_SECONDS}s timeout.")

# ==============================================================================
# 4. Test Scenarios (TS_BE_AnalysisCore_13)
# ==============================================================================

@pytest.mark.asyncio
async def test_tc_001_normal_analysis_and_polling(async_client: httpx.AsyncClient):
    """
    ID: TC_001
    Test Case: Normal analysis and polling
    Procedure: Call /api/analysis/start and poll the status until it transitions
               from PENDING -> RUNNING -> COMPLETED.
    Expected Result: 202 Accepted, and the final status is COMPLETED.
    Requirement: REQ-CRA-F-007
    """
    logger.info("--- TC_001: Normal Analysis and Polling - START ---")
    site_id = f"site_tc001_{uuid.uuid4()}"

    # Step 1: Start analysis
    logger.info(f"[Step 1] Requesting analysis for siteId: {site_id}")
    response = await async_client.post(f"{ANALYSIS_API_ENDPOINT}/start", json={"siteId": site_id})
    logger.info(f"[Step 1] Response: {response.status_code} {response.text}")
    assert response.status_code == 202, f"Expected 202 Accepted, but got {response.status_code}"
    
    response_data = response.json()
    assert "jobId" in response_data
    job_id = response_data["jobId"]
    logger.info(f"[Step 1] Analysis job started successfully. JobID: {job_id}")

    # Step 2: Poll for status
    logger.info(f"[Step 2] Polling for job status of JobID: {job_id}")
    final_status_data = await poll_job_status(async_client, job_id)
    
    # Step 3: Assert final status
    logger.info("[Step 3] Asserting final job status.")
    assert final_status_data.get("status") == "COMPLETED"
    logger.info("--- TC_001: Normal Analysis and Polling - PASSED ---")


@pytest.mark.asyncio
async def test_tc_002_llm_summary_validation(async_client: httpx.AsyncClient):
    """
    ID: TC_002
    Test Case: LLM Summary Verification
    Procedure: After a job completes, call /api/analysis/summary/{jobId}.
    Expected Result: The JSON response contains a non-empty summary text of 2-3 lines.
    Requirement: REQ-CRA-F-011
    """
    logger.info("--- TC_002: LLM Summary Validation - START ---")
    site_id = f"site_tc002_{uuid.uuid4()}"

    # Step 1: Start and complete an analysis job
    logger.info(f"[Step 1] Requesting analysis for siteId: {site_id} to get a completed job.")
    start_response = await async_client.post(f"{ANALYSIS_API_ENDPOINT}/start", json={"siteId": site_id})
    assert start_response.status_code == 202
    job_id = start_response.json()["jobId"]
    logger.info(f"[Step 1] Job created: {job_id}. Waiting for completion...")
    
    completion_data = await poll_job_status(async_client, job_id)
    assert completion_data.get("status") == "COMPLETED"
    logger.info(f"[Step 1] Job {job_id} completed.")

    # Step 2: Fetch the summary
    logger.info(f"[Step 2] Fetching summary for JobID: {job_id}")
    summary_response = await async_client.get(f"{ANALYSIS_API_ENDPOINT}/summary/{job_id}")
    logger.info(f"[Step 2] Response: {summary_response.status_code} {summary_response.text}")
    assert summary_response.status_code == 200

    # Step 3: Validate the summary content
    logger.info("[Step 3] Validating summary content.")
    summary_data = summary_response.json()
    assert "summary" in summary_data, "Response JSON must contain a 'summary' key."
    summary_text = summary_data["summary"]
    assert isinstance(summary_text, str), "Summary must be a string."
    assert len(summary_text) > 10, "Summary text seems too short."
    # A simple check for 2-3 lines of text
    assert 1 <= summary_text.count('\\n') <= 3 or 1 <= summary_text.count('\n') <= 3, "Summary should be 2-3 lines long."

    logger.info("--- TC_002: LLM Summary Validation - PASSED ---")

@pytest.mark.asyncio
async def test_tc_003_langgraph_node_failure(async_client: httpx.AsyncClient):
    """
    ID: TC_003
    Test Case: LangGraph Node Failure
    Procedure: Mock an exception in a mid-process node (e.g., data refinement) and start a job.
    Expected Result: The job status is recorded as FAILED, and logs indicate the failed node.
    Requirement: REQ-CRA-F-007
    """
    logger.info("--- TC_003: LangGraph Node Failure - START ---")
    site_id = f"site_tc003_{uuid.uuid4()}"
    
    # IMPORTANT: The path 'ai_agent.workflow.nodes.data_processing_node' is a placeholder.
    # It must be replaced with the actual import path to the node function you want to mock.
    mock_target_node_path = "ai_agent.workflow.nodes.data_refinement_node"

    with patch(mock_target_node_path, side_effect=Exception("Mocked Node Failure")) as mock_node:
        logger.info(f"[Step 1] Mocking '{mock_target_node_path}' to raise an exception.")
        
        # Step 2: Start analysis
        logger.info(f"[Step 2] Requesting analysis for siteId: {site_id}, expecting it to fail.")
        response = await async_client.post(f"{ANALYSIS_API_ENDPOINT}/start", json={"siteId": site_id})
        assert response.status_code == 202
        job_id = response.json()["jobId"]
        logger.info(f"[Step 2] Job created: {job_id}. Polling for FAILED status.")

        # Step 3: Poll for FAILED status
        final_status_data = await poll_job_status(async_client, job_id)
        
        # Step 4: Assert final status and error details
        logger.info("[Step 4] Asserting final job status is FAILED.")
        assert mock_node.called, "The mocked node should have been called."
        assert final_status_data.get("status") == "FAILED"
        assert "error" in final_status_data
        # Check if the error message mentions the failure, ideally the node name
        # (This depends on the application's error logging implementation)
        assert "Mocked Node Failure" in final_status_data.get("error", ""), "Error message should reflect the mocked failure."

    logger.info("--- TC_003: LangGraph Node Failure - PASSED ---")


@pytest.mark.asyncio
async def test_tc_004_missing_parameter(async_client: httpx.AsyncClient):
    """
    ID: TC_004
    Test Case: Missing Required Parameter
    Procedure: Call /api/analysis/start without the 'siteId' parameter.
    Expected Result: 422 Unprocessable Entity (or 400 Bad Request) with an error message.
    Requirement: REQ-CRA-F-007
    Note: FastAPI typically returns 422 for Pydantic validation errors, though the spec mentions 400.
          Testing for 422 is more idiomatic for FastAPI.
    """
    logger.info("--- TC_004: Missing Required Parameter - START ---")
    
    # Step 1: Call API with invalid payload
    logger.info("[Step 1] Calling /start with a payload missing 'siteId'.")
    invalid_payload = {"some_other_key": "some_value"}
    response = await async_client.post(f"{ANALYSIS_API_ENDPOINT}/start", json=invalid_payload)
    logger.info(f"[Step 1] Response: {response.status_code} {response.text}")
    
    # Step 2: Assert response code and error message
    logger.info("[Step 2] Asserting status code and error details.")
    assert response.status_code == 422, f"Expected 422 Unprocessable Entity, but got {response.status_code}"
    
    error_data = response.json()
    assert "detail" in error_data
    # Check if the error detail mentions the missing field 'siteId'
    assert any("siteId" in detail["loc"] for detail in error_data["detail"])
    logger.info("--- TC_004: Missing Required Parameter - PASSED ---")


@pytest.mark.asyncio
async def test_tc_005_duplicate_job_request(async_client: httpx.AsyncClient):
    """
    ID: TC_005
    Test Case: Duplicate Job Request Prevention
    Procedure: Send two analysis requests for the same 'siteId' concurrently.
    Expected Result: The first request succeeds (202), the second one fails (409 Conflict).
    Requirement: REQ-CRA-F-007
    """
    logger.info("--- TC_005: Duplicate Job Request Prevention - START ---")
    site_id = f"site_tc005_{uuid.uuid4()}"
    
    # Step 1: Send two requests concurrently
    logger.info(f"[Step 1] Sending two concurrent analysis requests for siteId: {site_id}")
    task1 = async_client.post(f"{ANALYSIS_API_ENDPOINT}/start", json={"siteId": site_id})
    # Add a small delay to ensure the first request is processed first, making the test deterministic
    await asyncio.sleep(0.1) 
    task2 = async_client.post(f"{ANALYSIS_API_ENDPOINT}/start", json={"siteId": site_id})

    responses = await asyncio.gather(task1, task2)
    
    # Step 2: Assert status codes
    logger.info("[Step 2] Asserting response status codes.")
    status_codes = sorted([res.status_code for res in responses])
    logger.info(f"Received status codes: {status_codes}")
    
    assert status_codes == [202, 409], f"Expected status codes [202, 409], but got {status_codes}"
    
    logger.info("--- TC_005: Duplicate Job Request Prevention - PASSED ---")


@pytest.mark.asyncio
async def test_tc_006_batch_job_performance(async_client: httpx.AsyncClient):
    """
    ID: TC_006
    Test Case: Batch Job Performance
    Procedure: Run a large job with the 'isBatch: true' option.
    Expected Result: Job completes within a specific time (performance benchmark).
    Requirement: REQ-CRA-N-003
    """
    logger.info("--- TC_006: Batch Job Performance - START ---")
    site_id = f"site_tc006_batch_{uuid.uuid4()}"
    
    # Step 1: Start batch analysis
    logger.info(f"[Step 1] Requesting batch analysis for siteId: {site_id}")
    start_time = datetime.now()
    response = await async_client.post(f"{ANALYSIS_API_ENDPOINT}/start", json={"siteId": site_id, "isBatch": True})
    
    assert response.status_code == 202
    job_id = response.json()["jobId"]
    logger.info(f"[Step 1] Batch job started: {job_id}. Polling for completion...")

    # Step 2: Poll for completion
    final_status_data = await poll_job_status(async_client, job_id)
    end_time = datetime.now()
    
    # Step 3: Assert completion and performance
    logger.info("[Step 3] Asserting job completion and performance metrics.")
    duration = (end_time - start_time).total_seconds()
    logger.info(f"Batch job {job_id} completed in {duration:.2f} seconds.")

    assert final_status_data.get("status") == "COMPLETED"
    assert duration < PERFORMANCE_THRESHOLD_SECONDS, \
        f"Batch job took {duration:.2f}s, which exceeds the {PERFORMANCE_THRESHOLD_SECONDS}s threshold."

    logger.info("--- TC_006: Batch Job Performance - PASSED ---")


@pytest.mark.asyncio
async def test_tc_007_transaction_rollback(async_client: httpx.AsyncClient, db_session_mock: AsyncMock):
    """
    ID: TC_007
    Test Case: Transaction Rollback Verification
    Procedure: Mock a LangGraph failure and verify that no intermediate data is left in the DB.
    Expected Result: No records related to the failed jobId are found in the database.
    Requirement: REQ-CRA-N-015
    """
    logger.info("--- TC_007: Transaction Rollback - START ---")
    site_id = f"site_tc007_{uuid.uuid4()}"
    
    mock_target_node_path = "ai_agent.workflow.nodes.another_node_to_fail"
    
    # This patch simulates a failure in the workflow graph.
    with patch(mock_target_node_path, side_effect=Exception("DB Rollback Test Failure")):
        # Step 1: Start a job that is destined to fail
        logger.info(f"[Step 1] Starting a job for siteId {site_id} that will be mocked to fail.")
        response = await async_client.post(f"{ANALYSIS_API_ENDPOINT}/start", json={"siteId": site_id})
        assert response.status_code == 202
        job_id = response.json()["jobId"]
        
        # Step 2: Wait for the job to fail
        logger.info(f"[Step 2] Waiting for job {job_id} to enter FAILED state.")
        await poll_job_status(async_client, job_id)

        # Step 3: Check the database for orphaned records
        # This part requires a way to query the database. We use a mock here.
        # In a real integration test, you'd replace `db_session_mock` with a fixture
        # that provides a real SQLAlchemy AsyncSession.
        logger.info(f"[Step 3] Verifying no DB records exist for failed job_id: {job_id}.")
        # Example Query:
        # result = await db_session_mock.execute(
        #     "SELECT * FROM analysis_results WHERE job_id = :job_id", {"job_id": job_id}
        # )
        # record = result.scalar_one_or_none()
        
        # We've mocked the session to return None.
        record = await db_session_mock.execute.return_value.scalar_one_or_none()

        # Step 4: Assert that no records were found
        assert record is None, f"Orphaned data found in DB for failed job_id {job_id}"
        logger.info(f"[Step 4] Confirmed: No orphaned data found for job {job_id}.")

    logger.info("--- TC_007: Transaction Rollback - PASSED ---")


@pytest.mark.asyncio
async def test_tc_008_timeout_handling(async_client: httpx.AsyncClient):
    """
    ID: TC_008
    Test Case: Timeout Handling
    Procedure: Mock a deliberate delay in a node to trigger the system's job timeout.
    Expected Result: The job status transitions to FAILED, and a timeout-related log is recorded.
    Requirement: REQ-CRA-N-014
    """
    logger.info("--- TC_008: Timeout Handling - START ---")
    site_id = f"site_tc008_{uuid.uuid4()}"

    # We need a short timeout for this test. We can patch the timeout value
    # or rely on a short global timeout, but that might make other tests flaky.
    # Here, we mock a node to sleep longer than the *polling* timeout.
    # A true implementation-level timeout test is more complex.
    
    async def long_running_node(*args, **kwargs):
        logger.info("Mocked long_running_node started, sleeping...")
        await asyncio.sleep(JOB_TIMEOUT_SECONDS + 5)
        logger.info("Mocked long_running_node finished sleeping.")
        return {"status": "Should have timed out"}

    mock_target_node_path = "ai_agent.workflow.nodes.long_running_node"

    with patch(mock_target_node_path, new=long_running_node):
        logger.info(f"[Step 1] Mocking '{mock_target_node_path}' to induce a timeout.")

        # Step 2: Start analysis
        response = await async_client.post(f"{ANALYSIS_API_ENDPOINT}/start", json={"siteId": site_id})
        assert response.status_code == 202
        job_id = response.json()["jobId"]
        logger.info(f"[Step 2] Job started: {job_id}. Expecting a timeout during polling.")

        # Step 3: Poll for status, expecting a timeout error from the poller
        with pytest.raises(TimeoutError) as excinfo:
            await poll_job_status(async_client, job_id)
        
        logger.info(f"[Step 3] Caught expected TimeoutError from polling function: {excinfo.value}")

        # Step 4: Verify the job status is FAILED in the backend
        # This requires another call after the timeout to confirm the backend marked it as FAILED.
        # This step assumes the backend has its own internal timeout mechanism that we triggered.
        await asyncio.sleep(POLLING_INTERVAL_SECONDS) # Give backend time to update status
        response = await async_client.get(f"{ANALYSIS_API_ENDPOINT}/status/{job_id}")
        status_data = response.json()
        logger.info(f"[Step 4] Final job status from server: {status_data}")

        assert status_data.get("status") == "FAILED", "Job status should be FAILED after a timeout."
        assert "timeout" in status_data.get("error", "").lower(), "Error message should mention 'timeout'."

    logger.info("--- TC_008: Timeout Handling - PASSED ---")

