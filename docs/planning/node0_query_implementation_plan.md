# Node 0: DB Query Implementation Plan

**Date:** 2025-12-15
**Version:** v1.0
**Objective:** Implement Node 0's database query logic for TCFD report generation.

---

## 1. Overview

Node 0 is responsible for preprocessing data by loading information from the database for multiple sites and optionally processing Excel data. This plan focuses specifically on the database loading aspect. The goal is to efficiently retrieve all necessary site-specific and risk-related data to feed into subsequent nodes of the TCFD report generation workflow.

## 2. Referenced Documents

- `polaris_backend_fastapi/docs/Application.dbml`: Defines the schema for the application database (SpringBoot).
- `polaris_backend_fastapi/docs/Datawarehouse.dbml`: Defines the schema for the datawarehouse database (FastAPI + ModelOps).
- `polaris_backend_fastapi/docs/erd.md`: Integrated ERD for both databases.
- `polaris_backend_fastapi/docs/for_better_understanding/ai_understanding.md`: Provides an overview of the system and data flow.
- `polaris_backend_fastapi/docs/planning/report_plan_v3.md`: Outlines the 7-node refactored workflow, including Node 0's role.

## 3. Data Requirements for Node 0

Based on `report_plan_v3.md` and `ai_understanding.md`, Node 0 needs to output `sites_data`. This `sites_data` should contain:

- **Site Basic Info**: From `application.sites` table (id, user_id, name, road_address, jibun_address, latitude, longitude, type).
- **ModelOps Calculation Results**: From `datawarehouse` tables, joined or queried by site `latitude` and `longitude`, and `risk_type`/`target_year`.
    - `hazard_results`
    - `probability_results`
    - `exposure_results`
    - `vulnerability_results`
    - `aal_scaled_results`

## 4. Proposed Implementation Steps

### Step 1: Create Planning and Progress Documents (Completed)
- Create `node0_query_implementation_plan.md` (this file)
- Create `node0_query_implementation_progress.md`

### Step 2: Establish Database Connection (if not already existing)
- Ensure proper configuration for connecting to both `application` and `datawarehouse` PostgreSQL databases. The existing `fastapi/ai_agent/utils/database.py` likely handles this.

### Step 3: Implement `DataLoader` Utility
- Create a new Python file: `polaris_backend_fastapi/ai_agent/utils/data_loader.py`
- Define a class `DataLoader` with methods to fetch the required data.

### Step 4: Implement `fetch_site_data` Method
- This method will take `site_ids` (list of UUIDs) and optional `target_years` (list of strings, e.g., ["2030", "2050"]) as input.
- For each `site_id`:
    1. Query `application.sites` to get basic site information (name, coordinates, address, type).
    2. Using `latitude` and `longitude` from the site info, query the `datawarehouse` for ModelOps results for relevant `risk_type`s and `target_year`s.
        - `hazard_results`
        - `probability_results`
        - `exposure_results`
        - `vulnerability_results`
        - `aal_scaled_results`
    3. Aggregate all this information into a structured dictionary for each site.

### Step 5: Define Output Structure for `sites_data`

Each item in the `sites_data` list will be a dictionary similar to:

```python
{
    "site_id": "uuid-of-site",
    "user_id": "uuid-of-user",
    "name": "Site Name",
    "road_address": "Road Address",
    "jibun_address": "Jibun Address",
    "latitude": 37.xxx,
    "longitude": 127.xxx,
    "type": "Industry Type", # e.g., "data_center"
    "risk_results": [
        {
            "risk_type": "extreme_heat",
            "target_year": "2030",
            "hazard_score": {"ssp126": ..., "ssp245": ...},
            "probability_aal": {"ssp126": ..., "ssp245": ...},
            "exposure_score": ...,
            "vulnerability_score": ...,
            "final_aal": {"ssp126": ..., "ssp245": ...},
            # ... potentially other aggregated data
        },
        # ... for other risk types and target years
    ]
}
```

## 5. Timeline Estimation

- **Step 1 (Planning & Progress Docs):** 0.5 hours (Done)
- **Step 2 (DB Connection):** 0.5 hours (Verification, mostly existing)
- **Step 3-4 (DataLoader Implementation):** 4 hours
- **Step 5 (Output Structure Definition):** 1 hour
- **Testing and Refinement:** 2 hours

**Total Estimated Time:** ~8 hours

## 6. Dependencies

- PostgreSQL database (both `application` and `datawarehouse` schemas populated).
- Existing database utility functions in `fastapi/ai_agent/utils/database.py`.

## 7. Next Steps

- Implement `DataLoader` class and its `fetch_site_data` method.
- Integrate this data loading into Node 0 of the LangGraph workflow.

---
