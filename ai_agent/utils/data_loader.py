"""
File: data_loader.py
Last Modified: 2025-12-15
Version: v01
Description: Data loading utilities for Node 0 of TCFD report generation.
"""
import os
import asyncio
from typing import List, Dict, Any, Optional
import logging
from anyio import to_thread # Import to_thread for running sync functions in a threadpool
from .database import DatabaseManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DataLoader:
    """
    Loads data from both application and datawarehouse databases for TCFD report generation.
    """
    def __init__(self):
        # Initialize DatabaseManager for the application DB
        app_db_url = os.getenv('DATABASE_URL_APPLICATION')
        if not app_db_url:
            raise ValueError("DATABASE_URL_APPLICATION is not set in environment variables.")
        self.app_db_manager = DatabaseManager(database_url=app_db_url)
        logger.info("Initialized Application DatabaseManager.")

        # Initialize DatabaseManager for the datawarehouse DB
        data_db_url = os.getenv('DATABASE_URL_DATAWAREHOUSE')
        if not data_db_url:
            raise ValueError("DATABASE_URL_DATAWAREHOUSE is not set in environment variables.")
        self.data_db_manager = DatabaseManager(database_url=data_db_url)
        logger.info("Initialized Datawarehouse DatabaseManager.")

    async def fetch_site_basic_info(self, site_id: str) -> Optional[Dict[str, Any]]:
        """
        Fetches basic site information from the application database.
        """
        query = """
            SELECT
                id, user_id, name, road_address, jibun_address,
                latitude, longitude, type
            FROM sites
            WHERE id = %s
        """
        results = await to_thread.run_sync(self.app_db_manager.execute_query, query, (site_id,))
        return results[0] if results else None

    async def fetch_modelops_results_for_site(
        self,
        site_id: str, # Added site_id as parameter
        latitude: float,
        longitude: float,
        risk_types: Optional[List[str]] = None,
        target_years: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Fetches all relevant ModelOps calculation results for a given site's coordinates.
        """
        # Ensure risk_types are defined
        if risk_types is None:
            # Assuming a default list of risk types for comprehensive fetching
            risk_types = [
                'extreme_heat', 'extreme_cold', 'wildfire', 'drought',
                'water_stress', 'sea_level_rise', 'river_flood',
                'urban_flood', 'typhoon'
            ]
        
        # Ensure target_years are defined
        if target_years is None:
            target_years = ["2030", "2050", "2080"] # Default target years

        all_results = {}
        
        # Fetch results for each risk type and target year combination
        for risk_type in risk_types:
            all_results[risk_type] = {}
            for year in target_years:
                all_results[risk_type][year] = await self._fetch_single_modelops_combination(
                    site_id, latitude, longitude, risk_type, year
                )
        
        return all_results

    async def _fetch_single_modelops_combination(
        self,
        site_id: str, # Added site_id as parameter
        latitude: float,
        longitude: float,
        risk_type: str,
        target_year: str
    ) -> Dict[str, Any]:
        """
        Fetches ModelOps results for a specific risk type and target year.
        """
        # Hazard and Probability results use lat/lon
        hazard_res = await to_thread.run_sync(
            self.data_db_manager.fetch_hazard_results, latitude, longitude, target_year, risk_type
        )
        prob_res = await to_thread.run_sync(
            self.data_db_manager.fetch_probability_results, latitude, longitude, target_year, risk_type
        )

        # Exposure, Vulnerability, AAL Scaled results use site_id
        exp_res = await to_thread.run_sync(
            self.data_db_manager.fetch_exposure_results, site_id, target_year, risk_type
        )
        vuln_res = await to_thread.run_sync(
            self.data_db_manager.fetch_vulnerability_results, site_id, target_year, risk_type
        )
        aal_scaled_res = await to_thread.run_sync(
            self.data_db_manager.fetch_aal_scaled_results, site_id, target_year, risk_type
        )
        
        return {
            "hazard_results": hazard_res,
            "probability_results": prob_res,
            "exposure_results": exp_res,
            "vulnerability_results": vuln_res,
            "aal_scaled_results": aal_scaled_res
        }
    
    async def fetch_sites_data(
        self,
        site_ids: List[str],
        risk_types: Optional[List[str]] = None,
        target_years: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Fetches all necessary data for multiple sites, including basic info and ModelOps results.
        """
        all_sites_data = []
        for site_id in site_ids:
            site_info = await self.fetch_site_basic_info(site_id)
            if site_info:
                modelops_results = await self.fetch_modelops_results_for_site(
                    site_id, # Pass site_id here
                    site_info['latitude'],
                    site_info['longitude'],
                    risk_types,
                    target_years
                )
                site_data = {
                    **site_info, # Unpack basic site info
                    "modelops_results": modelops_results
                }
                all_sites_data.append(site_data)
            else:
                logger.warning(f"Site with ID {site_id} not found in application database.")
        return all_sites_data
