"""
File: database.py
Last Modified: 2025-11-24
Version: v02
Description: PostgreSQL Datawarehouse connection and query utilities (Based on ERD v02.2)
Change History:
    - 2025-11-22: v01 - Initial creation
    - 2025-11-24: v02 - Updated to match actual ERD schema
"""
import os
import psycopg2
from psycopg2.extras import RealDictCursor
from typing import List, Dict, Any, Optional
from contextlib import contextmanager
import logging


class DatabaseManager:
    """
    PostgreSQL Datawarehouse connection and query manager
    Connects to skala_datawarehouse (port 5433) by default
    """

    def __init__(self, database_url: Optional[str] = None):
        """
        Initialize DatabaseManager

        Args:
            database_url: PostgreSQL connection URL (from env if not provided)
                         Default: Datawarehouse (port 5433)
        """
        self.database_url = database_url or os.getenv('DATABASE_URL')
        if not self.database_url:
            raise ValueError("DATABASE_URL is not set")

        self.logger = logging.getLogger(__name__)

    @contextmanager
    def get_connection(self):
        """
        Database connection context manager

        Yields:
            psycopg2 connection object
        """
        conn = psycopg2.connect(self.database_url)
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            self.logger.error(f"Database error: {e}")
            raise
        finally:
            conn.close()

    def execute_query(self, query: str, params: Optional[tuple] = None) -> List[Dict[str, Any]]:
        """
        Execute SELECT query and return results

        Args:
            query: SQL query
            params: Query parameters (tuple)

        Returns:
            List of query results (as dictionaries)
        """
        with self.get_connection() as conn:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute(query, params)
            results = cursor.fetchall()
            cursor.close()

            # Convert RealDictRow to dict
            return [dict(row) for row in results]

    def execute_update(self, query: str, params: Optional[tuple] = None) -> int:
        """
        Execute INSERT/UPDATE/DELETE query

        Args:
            query: SQL query
            params: Query parameters (tuple)

        Returns:
            Number of affected rows
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            rowcount = cursor.rowcount
            cursor.close()
            return rowcount

    # ==================== Location Queries ====================

    def find_nearest_grid(
        self,
        latitude: float,
        longitude: float
    ) -> Optional[Dict[str, Any]]:
        """
        Find nearest climate grid point for given coordinates

        Args:
            latitude: Latitude (WGS84)
            longitude: Longitude (WGS84)

        Returns:
            Nearest grid info (grid_id, distance)
        """
        query = """
            SELECT
                grid_id,
                longitude,
                latitude,
                ST_Distance(
                    geom,
                    ST_SetSRID(ST_MakePoint(%s, %s), 4326)::geography
                ) as distance_meters
            FROM location_grid
            ORDER BY geom <-> ST_SetSRID(ST_MakePoint(%s, %s), 4326)
            LIMIT 1
        """
        results = self.execute_query(query, (longitude, latitude, longitude, latitude))
        return results[0] if results else None

    def find_admin_by_code(self, admin_code: str) -> Optional[Dict[str, Any]]:
        """
        Find administrative region by admin_code

        Args:
            admin_code: Administrative code (e.g., "1101010100")

        Returns:
            Admin region info
        """
        query = """
            SELECT
                admin_id, admin_code, admin_name,
                sido_code, sigungu_code, emd_code,
                level, population_2020, population_2050
            FROM location_admin
            WHERE admin_code = %s
        """
        results = self.execute_query(query, (admin_code,))
        return results[0] if results else None

    def find_admin_by_coords(
        self,
        latitude: float,
        longitude: float
    ) -> Optional[Dict[str, Any]]:
        """
        Find administrative region containing the coordinates

        Args:
            latitude: Latitude (WGS84)
            longitude: Longitude (WGS84)

        Returns:
            Admin region info
        """
        query = """
            SELECT
                admin_id, admin_code, admin_name,
                sido_code, sigungu_code, emd_code,
                level, population_2020, population_2050
            FROM location_admin
            WHERE ST_Contains(
                geom,
                ST_Transform(ST_SetSRID(ST_MakePoint(%s, %s), 4326), 5174)
            )
            ORDER BY level DESC
            LIMIT 1
        """
        results = self.execute_query(query, (longitude, latitude))
        return results[0] if results else None

    # ==================== Monthly Grid Climate Data (Wide Format) ====================

    def fetch_monthly_grid_data(
        self,
        grid_id: int,
        start_date: str,
        end_date: str,
        scenario: Optional[str] = None,
        variables: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Fetch monthly climate data for a grid point (Wide format - ERD v03)

        Args:
            grid_id: Grid ID from location_grid
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            scenario: SSP scenario to select ('ssp1', 'ssp2', 'ssp3', 'ssp5')
                     If None, returns all 4 scenarios
            variables: List of variable codes (ta, rn, ws, rhm, si, spei12)
                      Default: ['ta', 'rn', 'ws']

        Returns:
            Dictionary with data for each variable
            Each row contains: observation_date, ssp1, ssp2, ssp3, ssp5
            (or single scenario column if scenario is specified)
        """
        if variables is None:
            variables = ['ta', 'rn', 'ws']

        result = {}

        # Table mapping
        table_map = {
            'ta': 'ta_data',
            'rn': 'rn_data',
            'ws': 'ws_data',
            'rhm': 'rhm_data',
            'si': 'si_data',
            'spei12': 'spei12_data'
        }

        # Validate scenario
        valid_scenarios = ['ssp1', 'ssp2', 'ssp3', 'ssp5']
        if scenario and scenario not in valid_scenarios:
            self.logger.warning(f"Invalid scenario: {scenario}. Using all scenarios.")
            scenario = None

        for var in variables:
            if var not in table_map:
                self.logger.warning(f"Unknown variable: {var}")
                continue

            table_name = table_map[var]

            # Select columns based on scenario parameter
            if scenario:
                columns = f"observation_date, {scenario}"
            else:
                columns = "observation_date, ssp1, ssp2, ssp3, ssp5"

            query = f"""
                SELECT
                    {columns}
                FROM {table_name}
                WHERE grid_id = %s
                    AND observation_date BETWEEN %s AND %s
                ORDER BY observation_date
            """

            result[var] = self.execute_query(
                query,
                (grid_id, start_date, end_date)
            )

        return result

    # ==================== Daily Admin Climate Data (Wide Format) ====================

    def fetch_daily_admin_data(
        self,
        admin_id: int,
        start_date: str,
        end_date: str,
        variables: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Fetch daily temperature data for administrative region (Wide format)

        Args:
            admin_id: Admin ID from location_admin
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            variables: List of variable codes (tamax, tamin)
                      Default: ['tamax', 'tamin']

        Returns:
            Dictionary with data for each variable
            Each row contains: time, ssp1, ssp2, ssp3, ssp5
        """
        if variables is None:
            variables = ['tamax', 'tamin']

        result = {}

        table_map = {
            'tamax': 'tamax_data',
            'tamin': 'tamin_data'
        }

        for var in variables:
            if var not in table_map:
                self.logger.warning(f"Unknown variable: {var}")
                continue

            table_name = table_map[var]
            query = f"""
                SELECT
                    time,
                    ssp1, ssp2, ssp3, ssp5
                FROM {table_name}
                WHERE admin_id = %s
                    AND time BETWEEN %s AND %s
                ORDER BY time
            """

            result[var] = self.execute_query(
                query,
                (admin_id, start_date, end_date)
            )

        return result

    # ==================== Yearly Grid Climate Data (Wide Format) ====================

    def fetch_yearly_grid_data(
        self,
        grid_id: int,
        start_year: int,
        end_year: int,
        scenario: Optional[str] = None,
        variables: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Fetch yearly climate indices for a grid point (Wide format - ERD v03)

        Args:
            grid_id: Grid ID from location_grid
            start_year: Start year (2021-2100)
            end_year: End year (2021-2100)
            scenario: SSP scenario to select ('ssp1', 'ssp2', 'ssp3', 'ssp5')
                     If None, returns all 4 scenarios
            variables: List of variable codes
                      (csdi, wsdi, rx1day, rx5day, cdd, rain80, sdii, ta_yearly)
                      Default: ['csdi', 'wsdi', 'rx1day', 'rx5day']

        Returns:
            Dictionary with data for each variable
            Each row contains: year, ssp1, ssp2, ssp3, ssp5
            (or single scenario column if scenario is specified)
        """
        if variables is None:
            variables = ['csdi', 'wsdi', 'rx1day', 'rx5day']

        result = {}

        table_map = {
            'csdi': 'csdi_data',
            'wsdi': 'wsdi_data',
            'rx1day': 'rx1day_data',
            'rx5day': 'rx5day_data',
            'cdd': 'cdd_data',
            'rain80': 'rain80_data',
            'sdii': 'sdii_data',
            'ta_yearly': 'ta_yearly_data'
        }

        # Validate scenario
        valid_scenarios = ['ssp1', 'ssp2', 'ssp3', 'ssp5']
        if scenario and scenario not in valid_scenarios:
            self.logger.warning(f"Invalid scenario: {scenario}. Using all scenarios.")
            scenario = None

        for var in variables:
            if var not in table_map:
                self.logger.warning(f"Unknown variable: {var}")
                continue

            table_name = table_map[var]

            # Select columns based on scenario parameter
            if scenario:
                columns = f"year, {scenario}"
            else:
                columns = "year, ssp1, ssp2, ssp3, ssp5"

            query = f"""
                SELECT
                    {columns}
                FROM {table_name}
                WHERE grid_id = %s
                    AND year BETWEEN %s AND %s
                ORDER BY year
            """

            result[var] = self.execute_query(
                query,
                (grid_id, start_year, end_year)
            )

        return result

    # ==================== Sea Level Data ====================

    def fetch_sea_level_data(
        self,
        latitude: float,
        longitude: float,
        start_year: int,
        end_year: int,
        scenario: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Fetch sea level rise data for coastal location (Wide format - ERD v03)

        Args:
            latitude: Latitude (WGS84)
            longitude: Longitude (WGS84)
            start_year: Start year (2015-2100)
            end_year: End year (2015-2100)
            scenario: SSP scenario to select ('ssp1', 'ssp2', 'ssp3', 'ssp5')
                     If None, returns all 4 scenarios

        Returns:
            List of sea level data
            Each row contains: year, ssp1, ssp2, ssp3, ssp5 (cm)
            (or single scenario column if scenario is specified)
        """
        # First, find nearest sea level grid point
        grid_query = """
            SELECT
                grid_id,
                ST_Distance(
                    geom,
                    ST_SetSRID(ST_MakePoint(%s, %s), 4326)::geography
                ) as distance_meters
            FROM sea_level_grid
            ORDER BY geom <-> ST_SetSRID(ST_MakePoint(%s, %s), 4326)
            LIMIT 1
        """
        grid_result = self.execute_query(
            grid_query,
            (longitude, latitude, longitude, latitude)
        )

        if not grid_result:
            return []

        grid_id = grid_result[0]['grid_id']

        # Validate scenario
        valid_scenarios = ['ssp1', 'ssp2', 'ssp3', 'ssp5']
        if scenario and scenario not in valid_scenarios:
            self.logger.warning(f"Invalid scenario: {scenario}. Using all scenarios.")
            scenario = None

        # Select columns based on scenario parameter
        if scenario:
            columns = f"year, {scenario} as sea_level_rise_cm"
        else:
            columns = "year, ssp1, ssp2, ssp3, ssp5"

        # Fetch sea level data
        data_query = f"""
            SELECT
                {columns}
            FROM sea_level_data
            WHERE grid_id = %s
                AND year BETWEEN %s AND %s
            ORDER BY year
        """

        return self.execute_query(
            data_query,
            (grid_id, start_year, end_year)
        )

    # ==================== Spatial Analysis Cache ====================

    def fetch_spatial_landcover(self, site_id: str) -> Optional[Dict[str, Any]]:
        """
        Fetch cached landcover analysis for a site

        Args:
            site_id: Site UUID from application DB

        Returns:
            Landcover analysis results
        """
        query = """
            SELECT
                urban_ratio, forest_ratio, agriculture_ratio,
                water_ratio, grassland_ratio, wetland_ratio, barren_ratio,
                landcover_year, analyzed_at, is_valid
            FROM spatial_landcover
            WHERE site_id = %s
                AND is_valid = true
            ORDER BY analyzed_at DESC
            LIMIT 1
        """
        results = self.execute_query(query, (site_id,))
        return results[0] if results else None

    def fetch_spatial_dem(self, site_id: str) -> Optional[Dict[str, Any]]:
        """
        Fetch cached DEM analysis for a site

        Args:
            site_id: Site UUID from application DB

        Returns:
            DEM analysis results (elevation, slope, aspect)
        """
        query = """
            SELECT
                elevation_point, elevation_mean, elevation_min, elevation_max,
                slope_point, slope_mean, slope_max,
                aspect_point, aspect_dominant,
                terrain_class, flood_risk_terrain,
                analyzed_at, is_valid
            FROM spatial_dem
            WHERE site_id = %s
                AND is_valid = true
            ORDER BY analyzed_at DESC
            LIMIT 1
        """
        results = self.execute_query(query, (site_id,))
        return results[0] if results else None

    # ==================== API Cache Queries ====================

    def fetch_nearby_hospitals(
        self,
        latitude: float,
        longitude: float,
        radius_km: float = 5.0
    ) -> List[Dict[str, Any]]:
        """
        Fetch hospitals within radius

        Args:
            latitude: Latitude
            longitude: Longitude
            radius_km: Search radius (km)

        Returns:
            List of hospitals
        """
        query = """
            SELECT
                yadm_nm as name,
                addr as address,
                clcd_nm as type,
                tel_no as phone,
                x_pos, y_pos,
                ST_Distance(
                    location,
                    ST_SetSRID(ST_MakePoint(%s, %s), 4326)::geography
                ) as distance_meters
            FROM api_hospitals
            WHERE ST_DWithin(
                location,
                ST_SetSRID(ST_MakePoint(%s, %s), 4326)::geography,
                %s * 1000
            )
            ORDER BY distance_meters
        """
        return self.execute_query(
            query,
            (longitude, latitude, longitude, latitude, radius_km)
        )

    def fetch_nearby_shelters(
        self,
        admin_code: str
    ) -> Optional[Dict[str, Any]]:
        """
        Fetch shelter information for administrative region

        Args:
            admin_code: Administrative code

        Returns:
            Shelter statistics
        """
        query = """
            SELECT
                regi as region,
                target_popl as target_population,
                accpt_rt as acceptance_rate,
                shelt_abl_popl_smry as total_shelter_capacity,
                gov_shelts_shelts as government_shelters,
                pub_shelts_shelts as public_shelters
            FROM api_shelters
            WHERE regi = %s
            ORDER BY bas_yy DESC
            LIMIT 1
        """
        results = self.execute_query(query, (admin_code,))
        return results[0] if results else None

    def fetch_typhoon_history(
        self,
        latitude: float,
        longitude: float,
        radius_km: float = 100.0,
        start_year: Optional[int] = None,
        end_year: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Fetch historical typhoon tracks near location

        Args:
            latitude: Latitude
            longitude: Longitude
            radius_km: Search radius (km)
            start_year: Start year (optional)
            end_year: End year (optional)

        Returns:
            List of typhoon events
        """
        query = """
            SELECT
                typhoon_year, typhoon_number,
                typhoon_name_kr, typhoon_name_en,
                observation_time,
                latitude, longitude,
                central_pressure, max_wind_speed,
                typhoon_grade,
                ST_Distance(
                    location,
                    ST_SetSRID(ST_MakePoint(%s, %s), 4326)::geography
                ) as distance_meters
            FROM typhoon_besttrack
            WHERE ST_DWithin(
                location,
                ST_SetSRID(ST_MakePoint(%s, %s), 4326)::geography,
                %s * 1000
            )
        """

        params = [longitude, latitude, longitude, latitude, radius_km]

        if start_year:
            query += " AND typhoon_year >= %s"
            params.append(start_year)

        if end_year:
            query += " AND typhoon_year <= %s"
            params.append(end_year)

        query += " ORDER BY observation_time DESC"

        return self.execute_query(query, tuple(params))

    # ==================== Comprehensive Data Collection ====================

    def collect_all_climate_data(
        self,
        latitude: float,
        longitude: float,
        start_year: int,
        end_year: int,
        scenario: Optional[str] = None,  # Changed from scenario_id to scenario (ERD v03)
        admin_code: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Comprehensive climate data collection for a location (ERD v03 Wide Format)

        Args:
            latitude: Latitude
            longitude: Longitude
            start_year: Start year
            end_year: End year
            scenario: SSP scenario ('ssp1', 'ssp2', 'ssp3', 'ssp5')
                     If None, returns all 4 scenarios (default behavior)
            admin_code: Optional admin code (if known)

        Returns:
            Dictionary containing all climate data
            All data uses Wide format (ssp1, ssp2, ssp3, ssp5 columns)
        """
        result = {
            'location': {
                'latitude': latitude,
                'longitude': longitude
            },
            'period': {
                'start_year': start_year,
                'end_year': end_year
            },
            'scenario': scenario or 'all'  # Changed from scenario_id
        }

        # 1. Find nearest grid
        grid = self.find_nearest_grid(latitude, longitude)
        if grid:
            result['grid'] = grid
            grid_id = grid['grid_id']

            # 2. Fetch monthly grid data (Wide format)
            start_date = f"{start_year}-01-01"
            end_date = f"{end_year}-12-31"
            result['monthly_data'] = self.fetch_monthly_grid_data(
                grid_id, start_date, end_date, scenario
            )

            # 3. Fetch yearly grid data (Wide format)
            result['yearly_data'] = self.fetch_yearly_grid_data(
                grid_id, start_year, end_year, scenario
            )

        # 4. Find admin region
        if admin_code:
            admin = self.find_admin_by_code(admin_code)
        else:
            admin = self.find_admin_by_coords(latitude, longitude)

        if admin:
            result['admin'] = admin
            admin_id = admin['admin_id']

            # 5. Fetch daily admin data (Already Wide format)
            start_date = f"{start_year}-01-01"
            end_date = f"{end_year}-12-31"
            result['daily_data'] = self.fetch_daily_admin_data(
                admin_id, start_date, end_date
            )

        # 6. Sea level data (Wide format)
        result['sea_level_data'] = self.fetch_sea_level_data(
            latitude, longitude, start_year, end_year, scenario
        )

        return result
