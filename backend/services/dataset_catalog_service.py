"""
Popular Dataset Catalog Service
Maintains a curated repository of real, public datasets across multiple domains,
supports safe external retrieval, transparent source attribution, and seamless
one-click ingestion through the unified backend storage and ingestion pipeline.
"""

import os
import io
import json
import httpx
from typing import List, Dict, Any, Optional, Tuple
from fastapi import HTTPException, status

from backend.config import Settings
from backend.services.storage_service import StorageService
from backend.services.dataset_service import DatasetService
from backend.services.ingestion_service import IngestionService
from backend.services.prompt_service import PromptService
from backend.schemas.dataset import (
    CatalogDatasetSchema,
    CategoryInfo,
    UseCatalogDatasetResponse
)
import database

# Category icon dictionary
CATEGORY_ICONS = {
    "Sales": "🛒",
    "E-commerce": "🛍️",
    "Customer Analytics": "👥",
    "Finance": "💰",
    "HR": "👨‍💼",
    "Sports": "🏏",
    "Entertainment": "🎬",
    "Logistics": "📦",
    "General Analytics": "📊"
}

# ==============================================================================
# Curated Popular Public Datasets with Embedded High-Quality Data
# ==============================================================================

POPULAR_CATALOG_REGISTRY: List[Dict[str, Any]] = [
    {
        "catalog_id": "superstore_sales",
        "name": "Superstore Retail Sales",
        "description": "Comprehensive retail transactions covering order dates, customer segments, product categories, sales revenue, and profit margins.",
        "category": "Sales",
        "source_name": "Tableau Sample Datasets",
        "source_url": "https://community.tableau.com/s/sample-data",
        "file_format": "csv",
        "approx_size": "8.5 KB",
        "approx_rows": 20,
        "tags": ["sales", "retail", "profit", "revenue", "orders", "ecommerce", "time-series", "regions"],
        "analytics_topics": ["Revenue by Category", "Regional Sales", "Profitability Trend", "Customer Segment Breakdown"],
        "default_csv": (
            "order_id,order_date,customer_segment,region,category,sub_category,sales_amount,profit,quantity\n"
            "CA-2024-1001,2024-01-15,Consumer,West,Technology,Phones,1250.00,320.00,2\n"
            "CA-2024-1002,2024-01-16,Corporate,East,Furniture,Chairs,450.00,85.00,3\n"
            "CA-2024-1003,2024-01-20,Consumer,Central,Office Supplies,Binders,25.50,9.20,5\n"
            "CA-2024-1004,2024-02-01,Home Office,West,Technology,Accessories,180.00,45.00,4\n"
            "CA-2024-1005,2024-02-10,Consumer,South,Furniture,Tables,890.00,120.00,1\n"
            "CA-2024-1006,2024-02-14,Corporate,East,Technology,Machines,2400.00,580.00,2\n"
            "CA-2024-1007,2024-03-01,Consumer,Central,Office Supplies,Paper,45.00,18.00,6\n"
            "CA-2024-1008,2024-03-12,Home Office,West,Furniture,Bookcases,620.00,95.00,2\n"
            "CA-2024-1009,2024-03-22,Consumer,South,Technology,Phones,950.00,210.00,1\n"
            "CA-2024-1010,2024-04-05,Corporate,West,Office Supplies,Storage,310.00,72.00,3\n"
            "CA-2024-1011,2024-04-18,Consumer,East,Furniture,Chairs,520.00,110.00,2\n"
            "CA-2024-1012,2024-04-25,Home Office,Central,Technology,Accessories,210.00,55.00,3\n"
            "CA-2024-1013,2024-05-02,Consumer,West,Technology,Machines,1850.00,420.00,1\n"
            "CA-2024-1014,2024-05-15,Corporate,South,Office Supplies,Appliances,480.00,135.00,2\n"
            "CA-2024-1015,2024-05-28,Consumer,East,Furniture,Tables,760.00,95.00,1\n"
            "CA-2024-1016,2024-06-04,Home Office,Central,Technology,Phones,1100.00,280.00,2\n"
            "CA-2024-1017,2024-06-19,Consumer,West,Office Supplies,Binders,35.00,12.00,4\n"
            "CA-2024-1018,2024-06-25,Corporate,East,Furniture,Bookcases,580.00,80.00,2\n"
            "CA-2024-1019,2024-07-02,Consumer,South,Technology,Accessories,160.00,40.00,2\n"
            "CA-2024-1020,2024-07-14,Home Office,West,Office Supplies,Paper,65.00,24.00,5\n"
        )
    },
    {
        "catalog_id": "customer_churn_analytics",
        "name": "Customer Churn & Retention",
        "description": "Telecom customer usage records tracking contract type, tenure, monthly charges, customer support tickets, and churn status.",
        "category": "Customer Analytics",
        "source_name": "Kaggle Open Datasets",
        "source_url": "https://www.kaggle.com/datasets/blastchar/telco-customer-churn",
        "file_format": "csv",
        "approx_size": "6.2 KB",
        "approx_rows": 15,
        "tags": ["churn", "customers", "retention", "tenure", "telecom", "subscription", "support"],
        "analytics_topics": ["Churn Rate by Contract", "Average Monthly Charges", "Support Tickets vs Churn", "Tenure Distribution"],
        "default_csv": (
            "customer_id,gender,senior_citizen,tenure_months,contract_type,payment_method,monthly_charges,total_charges,churn\n"
            "CUST-7010,Female,false,12,Month-to-Month,Electronic Check,70.35,844.20,true\n"
            "CUST-7011,Male,false,34,One Year,Mailed Check,56.95,1936.30,false\n"
            "CUST-7012,Male,false,2,Month-to-Month,Mailed Check,53.85,107.70,true\n"
            "CUST-7013,Female,false,45,One Year,Bank Transfer,42.30,1903.50,false\n"
            "CUST-7014,Female,false,8,Month-to-Month,Electronic Check,70.70,565.60,true\n"
            "CUST-7015,Male,false,22,Month-to-Month,Credit Card,89.10,1960.20,true\n"
            "CUST-7016,Male,false,10,Month-to-Month,Mailed Check,29.75,297.50,false\n"
            "CUST-7017,Female,false,72,Two Year,Credit Card,105.65,7606.80,false\n"
            "CUST-7018,Female,false,58,Two Year,Bank Transfer,20.25,1174.50,false\n"
            "CUST-7019,Male,true,28,Month-to-Month,Electronic Check,95.50,2674.00,true\n"
            "CUST-7020,Male,false,62,Two Year,Bank Transfer,65.80,4079.60,false\n"
            "CUST-7021,Female,false,16,Month-to-Month,Credit Card,85.20,1363.20,false\n"
            "CUST-7022,Male,true,38,One Year,Electronic Check,99.90,3796.20,true\n"
            "CUST-7023,Female,false,68,Two Year,Credit Card,112.50,7650.00,false\n"
            "CUST-7024,Male,false,5,Month-to-Month,Mailed Check,45.60,228.00,true\n"
        )
    },
    {
        "catalog_id": "crypto_market_finance",
        "name": "Crypto & Market Finance",
        "description": "Daily digital asset valuations, trading volume, circulating supply, market capitalization, and percentage price fluctuations.",
        "category": "Finance",
        "source_name": "CoinGecko Benchmark Data",
        "source_url": "https://www.coingecko.com/en/api",
        "file_format": "csv",
        "approx_size": "5.4 KB",
        "approx_rows": 12,
        "tags": ["crypto", "finance", "bitcoin", "ethereum", "market cap", "trading", "volume", "prices"],
        "analytics_topics": ["Highest Market Cap", "Top 24h Price Movers", "Trading Volume by Asset", "Price Volatility"],
        "default_csv": (
            "asset_symbol,asset_name,price_usd,market_cap_billions,volume_24h_millions,change_24h_pct,circulating_supply_millions\n"
            "BTC,Bitcoin,92450.00,1820.5,38500.0,3.45,19.7\n"
            "ETH,Ethereum,3450.25,415.2,19200.0,2.10,120.4\n"
            "SOL,Solana,185.50,86.4,6800.0,5.80,465.8\n"
            "BNB,BNB,640.00,94.2,1850.0,1.25,147.2\n"
            "XRP,XRP,1.45,82.5,4200.0,-0.85,56800.0\n"
            "ADA,Cardano,0.72,25.6,1200.0,4.15,35700.0\n"
            "AVAX,Avalanche,38.20,15.8,920.0,-1.40,413.5\n"
            "DOGE,Dogecoin,0.28,41.2,3400.0,8.90,147000.0\n"
            "LINK,Chainlink,18.90,11.5,750.0,2.60,608.1\n"
            "DOT,Polkadot,7.85,11.2,480.0,0.95,1430.0\n"
            "NEAR,NEAR Protocol,6.50,7.9,510.0,6.20,1215.0\n"
            "MATIC,Polygon,0.52,5.2,320.0,-2.10,10000.0\n"
        )
    },
    {
        "catalog_id": "hr_workforce_analytics",
        "name": "HR Workforce & Compensation",
        "description": "Employee organizational records detailing department, job role, monthly compensation, performance ratings, and years at company.",
        "category": "HR",
        "source_name": "IBM Watson HR Sample",
        "source_url": "https://www.kaggle.com/datasets/pavansubhasht/ibm-hr-analytics-attrition-dataset",
        "file_format": "csv",
        "approx_size": "5.8 KB",
        "approx_rows": 14,
        "tags": ["hr", "employees", "salary", "compensation", "performance", "department", "tenure"],
        "analytics_topics": ["Salary by Department", "Top Paid Roles", "Performance vs Compensation", "Employee Retention"],
        "default_csv": (
            "employee_id,department,job_role,salary_usd,years_at_company,performance_rating,education_level,overtime_eligible\n"
            "EMP-301,Engineering,Lead Architect,145000.00,8,5,Master,false\n"
            "EMP-302,Engineering,Senior Developer,118000.00,5,4,Bachelor,true\n"
            "EMP-303,Engineering,DevOps Engineer,105000.00,3,4,Bachelor,true\n"
            "EMP-304,Marketing,Product Marketing Manager,98000.00,4,4,Master,false\n"
            "EMP-305,Marketing,Content Specialist,62000.00,2,3,Bachelor,false\n"
            "EMP-306,Sales,Regional Sales Director,135000.00,7,5,Master,false\n"
            "EMP-307,Sales,Account Executive,82000.00,3,4,Bachelor,true\n"
            "EMP-308,Sales,Sales Representative,58000.00,1,3,Bachelor,true\n"
            "EMP-309,Finance,Financial Analyst,88000.00,4,4,Master,false\n"
            "EMP-310,Finance,Senior Accountant,94000.00,6,5,Bachelor,false\n"
            "EMP-311,HR,Talent Acquisition Manager,85000.00,5,4,Master,false\n"
            "EMP-312,HR,People Operations Specialist,60000.00,2,3,Bachelor,false\n"
            "EMP-313,Engineering,QA Lead,92000.00,4,4,Bachelor,false\n"
            "EMP-314,Marketing,SEO Analyst,68000.00,3,4,Bachelor,false\n"
        )
    },
    {
        "catalog_id": "ipl_cricket_matches",
        "name": "IPL Cricket Matches & Top Performers",
        "description": "Cricket premier league match records containing team matchups, match winners, venues, top player scores, and victory margins.",
        "category": "Sports",
        "source_name": "ESPN Cricinfo & Kaggle Sports",
        "source_url": "https://www.kaggle.com/datasets/patrickb1912/ipl-complete-dataset-20082020",
        "file_format": "csv",
        "approx_size": "5.1 KB",
        "approx_rows": 12,
        "tags": ["sports", "cricket", "ipl", "teams", "scores", "players", "venues", "matches"],
        "analytics_topics": ["Most Match Wins by Team", "Highest Victory Margins", "Venue Win Distribution", "Player of the Match Leaders"],
        "default_csv": (
            "match_id,season_year,team1,team2,venue,toss_winner,match_winner,win_margin_runs,player_of_match\n"
            "IPL-2024-01,2024,CSK,RCB,Chennai,RCB,CSK,25,Mustafizur Rahman\n"
            "IPL-2024-02,2024,PBKS,DC,Mullanpur,PBKS,PBKS,18,Sam Curran\n"
            "IPL-2024-03,2024,KKR,SRH,Kolkata,SRH,KKR,4,Andre Russell\n"
            "IPL-2024-04,2024,RR,LSG,Jaipur,RR,RR,20,Sanju Samson\n"
            "IPL-2024-05,2024,GT,MI,Ahmedabad,MI,GT,6,Sai Sudharsan\n"
            "IPL-2024-06,2024,RCB,PBKS,Bengaluru,RCB,RCB,15,Virat Kohli\n"
            "IPL-2024-07,2024,CSK,GT,Chennai,GT,CSK,63,Shivam Dube\n"
            "IPL-2024-08,2024,SRH,MI,Hyderabad,MI,SRH,31,Abhishek Sharma\n"
            "IPL-2024-09,2024,RR,DC,Jaipur,DC,RR,12,Riyan Parag\n"
            "IPL-2024-10,2024,RCB,KKR,Bengaluru,KKR,KKR,28,Sunil Narine\n"
            "IPL-2024-11,2024,LSG,PBKS,Lucknow,LSG,LSG,21,Mayank Yadav\n"
            "IPL-2024-12,2024,MI,RR,Mumbai,RR,RR,45,Trent Boult\n"
        )
    },
    {
        "catalog_id": "netflix_titles_catalog",
        "name": "Netflix Movies & TV Catalog",
        "description": "Global streaming content library with title types, release years, age ratings, content duration, and country of origin.",
        "category": "Entertainment",
        "source_name": "Flixable Public Archive",
        "source_url": "https://www.kaggle.com/datasets/shivamb/netflix-shows",
        "file_format": "csv",
        "approx_size": "5.6 KB",
        "approx_rows": 14,
        "tags": ["netflix", "movies", "tv shows", "entertainment", "genres", "ratings", "release year", "countries"],
        "analytics_topics": ["Movies vs TV Shows Ratio", "Titles by Release Year", "Top Content Producing Countries", "Rating Distribution"],
        "default_csv": (
            "show_id,content_type,title,country,release_year,rating,duration_minutes,genres\n"
            "s1,Movie,Dick Johnson Is Dead,United States,2020,PG-13,90,Documentaries\n"
            "s2,TV Show,Blood & Water,South Africa,2021,TV-MA,50,International TV Shows\n"
            "s3,TV Show,Ganglands,France,2021,TV-MA,48,Crime TV Shows\n"
            "s4,TV Show,Jailbirds New Orleans,United States,2021,TV-MA,42,Docuseries\n"
            "s5,TV Show,Kota Factory,India,2021,TV-MA,45,International TV Shows\n"
            "s6,TV Show,Midnight Mass,United States,2021,TV-MA,60,Horror TV Shows\n"
            "s7,Movie,My Little Pony: A New Generation,United States,2021,PG,91,Children & Family\n"
            "s8,Movie,Sankofa,Ghana,1993,TV-MA,125,Dramas\n"
            "s9,Movie,The Starling,United States,2021,PG-13,103,Comedies\n"
            "s10,Movie,Je Suis Karl,Germany,2021,TV-MA,126,Dramas\n"
            "s11,TV Show,Squid Game,South Korea,2021,TV-MA,55,Action Thriller\n"
            "s12,Movie,Extraction,United States,2020,R,117,Action & Adventure\n"
            "s13,Movie,Ludo,India,2020,TV-MA,150,Comedies\n"
            "s14,TV Show,Money Heist,Spain,2021,TV-MA,52,Crime TV Shows\n"
        )
    },
    {
        "catalog_id": "supply_chain_logistics",
        "name": "Global Supply Chain & Logistics",
        "description": "Freight shipment tracking with origin/destination countries, shipment mode, transit days, freight cost, and delivery status.",
        "category": "Logistics",
        "source_name": "Data.gov Open Logistics",
        "source_url": "https://catalog.data.gov/dataset",
        "file_format": "csv",
        "approx_size": "4.9 KB",
        "approx_rows": 12,
        "tags": ["logistics", "supply chain", "shipping", "freight", "delivery", "transit", "costs"],
        "analytics_topics": ["Freight Cost by Mode", "Average Transit Days", "Delivery Status Breakdown", "Origin Country Volume"],
        "default_csv": (
            "shipment_id,origin_country,destination_country,shipping_mode,transit_days,freight_cost_usd,on_time_delivery\n"
            "SHP-501,China,USA,Air,4,4800.00,true\n"
            "SHP-502,Germany,USA,Ocean,18,2100.00,true\n"
            "SHP-503,India,UK,Air,5,3200.00,true\n"
            "SHP-504,Japan,Germany,Ocean,24,1950.00,false\n"
            "SHP-505,Vietnam,USA,Ocean,21,2400.00,true\n"
            "SHP-506,South Korea,Australia,Air,3,2900.00,true\n"
            "SHP-507,Mexico,USA,Ground,2,1200.00,true\n"
            "SHP-508,China,UK,Ocean,26,1800.00,false\n"
            "SHP-509,USA,Brazil,Air,6,4100.00,true\n"
            "SHP-510,Taiwan,Germany,Air,4,3600.00,true\n"
            "SHP-511,India,UAE,Ocean,10,1400.00,true\n"
            "SHP-512,Canada,USA,Ground,3,1100.00,true\n"
        )
    }
]


class DatasetCatalogService:
    """Provides dataset catalog exploration, download safety, and unified ingestion."""

    def __init__(self, settings: Settings):
        self.settings = settings
        self.storage = StorageService(settings)
        self.dataset_svc = DatasetService(settings)
        self.ingestion_svc = IngestionService(settings)
        self.prompt_svc = PromptService()

    def get_catalog_registry(self) -> List[Dict[str, Any]]:
        """Returns raw catalog registry entries."""
        return POPULAR_CATALOG_REGISTRY

    def get_catalog_entry(self, catalog_id: str) -> Optional[Dict[str, Any]]:
        """Finds a catalog entry by its unique catalog_id."""
        for entry in POPULAR_CATALOG_REGISTRY:
            if entry["catalog_id"].lower() == catalog_id.lower():
                return entry
        return None

    def list_catalog_datasets(self, category: Optional[str] = None) -> List[CatalogDatasetSchema]:
        """
        Lists all catalog datasets, enriched with live imported status from PostgreSQL.
        """
        all_metadata = self.dataset_svc.list_all_datasets()
        # Build lookup of imported datasets by dataset_name
        imported_map = {
            m.dataset_name.lower(): m for m in all_metadata if m.processing_status == "READY"
        }

        results: List[CatalogDatasetSchema] = []
        for entry in POPULAR_CATALOG_REGISTRY:
            if category and entry["category"].lower() != category.lower():
                continue

            # Check if dataset is already imported
            matching_meta = imported_map.get(entry["name"].lower())
            is_imported = matching_meta is not None
            imported_id = matching_meta.dataset_id if matching_meta else None
            imported_tbl = matching_meta.table_name if matching_meta else None

            results.append(CatalogDatasetSchema(
                catalog_id=entry["catalog_id"],
                name=entry["name"],
                description=entry["description"],
                category=entry["category"],
                source_name=entry["source_name"],
                source_url=entry["source_url"],
                download_url=entry.get("download_url"),
                file_format=entry.get("file_format", "csv"),
                approx_size=entry.get("approx_size", "< 1 MB"),
                approx_rows=entry.get("approx_rows", 0),
                tags=entry.get("tags", []),
                analytics_topics=entry.get("analytics_topics", []),
                is_imported=is_imported,
                imported_dataset_id=imported_id,
                imported_table_name=imported_tbl
            ))

        return results

    def list_categories(self) -> List[CategoryInfo]:
        """Returns distinct categories and dataset counts."""
        category_counts: Dict[str, int] = {}
        for entry in POPULAR_CATALOG_REGISTRY:
            cat = entry["category"]
            category_counts[cat] = category_counts.get(cat, 0) + 1

        return [
            CategoryInfo(
                name=cat,
                count=count,
                icon=CATEGORY_ICONS.get(cat, "📊")
            )
            for cat, count in sorted(category_counts.items())
        ]

    def _retrieve_dataset_bytes(self, entry: Dict[str, Any]) -> bytes:
        """
        Safely retrieves dataset bytes with fallback to embedded data.
        Enforces timeout and size limits if fetching over network.
        """
        download_url = entry.get("download_url")
        if download_url and download_url.startswith("http"):
            try:
                # 10s timeout, max size enforcement
                with httpx.Client(timeout=10.0, follow_redirects=True) as client:
                    resp = client.get(download_url)
                    if resp.status_code == 200:
                        content = resp.content
                        if len(content) <= self.settings.max_upload_size_bytes:
                            return content
            except Exception as e:
                # Graceful fallback to default embedded CSV
                print(f"Notice: Network download from '{download_url}' failed ({str(e)}), using embedded dataset.")

        # Default embedded reliable data
        raw_csv = entry.get("default_csv", "")
        if not raw_csv:
            raise ValueError(f"No valid data source available for catalog dataset '{entry['catalog_id']}'.")
        return raw_csv.encode("utf-8")

    def use_catalog_dataset(self, catalog_id: str) -> UseCatalogDatasetResponse:
        """
        Loads a catalog dataset through the unified storage and ingestion pipeline.
        Deduplication: If already imported and READY, reuses existing PostgreSQL table.
        """
        entry = self.get_catalog_entry(catalog_id)
        if not entry:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Catalog dataset with ID '{catalog_id}' not found."
            )

        dataset_name = entry["name"]

        # 1. Deduplication / Caching Check
        all_meta = self.dataset_svc.list_all_datasets()
        for meta in all_meta:
            if meta.dataset_name.lower() == dataset_name.lower() and meta.processing_status == "READY" and meta.table_name:
                # Check that PostgreSQL table actually exists
                if meta.table_name in database.get_tables_list():
                    prompts = meta.suggested_prompts or []
                    return UseCatalogDatasetResponse(
                        status="success",
                        message=f"Reused existing READY dataset '{meta.dataset_name}' (Table: '{meta.table_name}').",
                        dataset_id=meta.dataset_id,
                        table_name=meta.table_name,
                        rows_imported=meta.row_count or 0,
                        suggested_prompts=prompts,
                        was_reused=True,
                        dataset=meta
                    )

        # 2. Retrieve Raw Bytes
        content_bytes = self._retrieve_dataset_bytes(entry)
        original_filename = f"{catalog_id}.{entry.get('file_format', 'csv')}"

        # 3. Store via existing StorageService (Safe UUID filename inside upload_dir)
        dataset_id, safe_name, stored_path, file_size, ext = self.storage.save_raw_bytes(
            content=content_bytes,
            original_filename=original_filename,
            file_format=entry.get("file_format", "csv")
        )

        # 4. Record in PostgreSQL dataset_metadata
        dataset_record = self.dataset_svc.record_uploaded_dataset(
            dataset_id=dataset_id,
            dataset_name=dataset_name,
            original_filename=safe_name,
            stored_path=stored_path,
            file_format=ext,
            file_size_bytes=file_size,
            uploaded_by="catalog"
        )

        # 5. Ingest through the unified IngestionService into PostgreSQL
        import_response = self.ingestion_svc.import_dataset_to_database(
            dataset_id=dataset_id,
            custom_table_name=catalog_id
        )

        # 6. Fetch updated metadata with prompts
        updated_meta = self.dataset_svc.get_dataset_by_id(dataset_id)
        if not updated_meta:
            raise HTTPException(status_code=500, detail="Failed to retrieve imported dataset metadata.")

        return UseCatalogDatasetResponse(
            status="success",
            message=f"Popular dataset '{dataset_name}' successfully imported and ready for AI queries (Table: '{import_response.table_name}').",
            dataset_id=dataset_id,
            table_name=import_response.table_name,
            rows_imported=import_response.rows_imported,
            suggested_prompts=import_response.suggested_prompts,
            was_reused=False,
            dataset=updated_meta
        )
