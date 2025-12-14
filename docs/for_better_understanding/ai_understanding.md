# Polaris Backend FastAPI Project Understanding

## Overview

The Polaris backend is a well-structured FastAPI application designed to serve as an interface to a complex AI analysis engine, specifically for physical risk assessment. It follows a standard layered architecture, separating concerns into distinct modules for routes, services, schemas, and core functionalities.

## Core Architecture

The application adheres to a typical web service pattern:

- **`main.py`**: The application's main entry point, responsible for initializing the FastAPI app, including API routers, and managing the lifecycle of singleton services.
- **`src/core/`**: Contains cross-cutting concerns such as:
  - `config.py`: Defines application settings using Pydantic's `BaseSettings`, including database URLs, API keys, and a `USE_MOCK_DATA` flag for development.
  - `auth.py`: Implements API key-based security for endpoint protection.
  - `logging_config.py`: Configures the application's logging.
  - `errors.py`: Defines custom error handling.
  - `middleware.py`: Handles global middleware for requests.
- **`src/schemas/`**: Defines Pydantic models for request and response data validation and serialization across various API domains (e.g., `analysis`, `reports`).
- **`src/routes/`**: Defines API endpoints using FastAPI's APIRouter. These act as "thin controllers," primarily handling request parsing, authentication, and delegating business logic to the corresponding services.
- **`src/services/`**: Contains the core business logic for different domains. Services orchestrate operations, interact with data sources, and integrate with external components like the AI analysis engine.

## AI Agent Integration

A key component of this backend is its integration with an AI analysis engine, managed by the `ai_agent` module.

- The `ai_agent` module is a self-contained Python package, integrated directly into the FastAPI application rather than being a separate microservice.
- The `AnalysisService` (`src/services/analysis_service.py`) acts as the primary bridge, importing and invoking the `SKAXPhysicalRiskAnalyzer` class from the `ai_agent` package to perform complex AI-driven risk analysis.
- The `ai_agent` module itself appears to have a sophisticated internal structure, with `workflow/` and `agents/` subdirectories, suggesting a graph-based workflow orchestrating various specialized AI agents for different parts of the analysis. Further investigation is needed to fully understand its internal mechanics.

## Key Features

- **API Key Authentication**: Endpoints are secured using API keys defined in `src/core/auth.py`.
- **Configuration Management**: Centralized configuration via `src/core/config.py`, supporting environment-specific settings.
- **Mock Data Mode**: A `USE_MOCK_DATA` flag allows developers to run the application with mock data, facilitating development and testing without requiring a full data pipeline.
- **In-memory Caching**: Services utilize in-memory caching to optimize performance.

This document provides a high-level understanding of the Polaris backend. For deeper insights into specific components, refer to the individual module documentation and source code.
