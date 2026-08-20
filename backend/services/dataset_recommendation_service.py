"""
Dataset Recommendation Service
Analyzes user analytical intent and recommends matching catalog datasets
based on keyword relevance, domain categories, tags, and analytics topics.
"""

import re
from typing import List, Dict, Any, Optional
from backend.config import Settings
from backend.services.dataset_catalog_service import DatasetCatalogService
from backend.schemas.dataset import CatalogDatasetSchema, DatasetRecommendationResponse


class DatasetRecommendationService:
    """Provides keyword-weighted, domain-aware dataset recommendations from the catalog."""

    def __init__(self, settings: Settings):
        self.settings = settings
        self.catalog_svc = DatasetCatalogService(settings)

    def recommend_datasets(
        self,
        query: str,
        category: Optional[str] = None,
        limit: int = 5
    ) -> DatasetRecommendationResponse:
        """
        Ranks and returns the most relevant catalog datasets for the user's intent.
        Strictly constrained to the actual dataset catalog (zero hallucinations).
        """
        clean_query = query.strip().lower()
        query_tokens = set(re.findall(r'\w+', clean_query))

        catalog_datasets = self.catalog_svc.list_catalog_datasets(category=category)
        scored_datasets: List[Tuple[float, CatalogDatasetSchema, str]] = []

        for ds in catalog_datasets:
            score = 0.0
            matched_features = []

            # 1. Exact Category match
            if category and ds.category.lower() == category.lower():
                score += 5.0

            # 2. Category mention in query
            if ds.category.lower() in clean_query:
                score += 4.0
                matched_features.append(f"Category '{ds.category}'")

            # 3. Name token matches
            name_tokens = set(re.findall(r'\w+', ds.name.lower()))
            common_name = query_tokens.intersection(name_tokens)
            if common_name:
                score += len(common_name) * 3.0
                matched_features.append(f"title match ({', '.join(common_name)})")

            # 4. Tag matches
            for tag in ds.tags:
                tag_lower = tag.lower()
                if tag_lower in clean_query or tag_lower in query_tokens:
                    score += 3.5
                    matched_features.append(f"tag '{tag}'")

            # 5. Analytics topics matches
            for topic in ds.analytics_topics:
                topic_tokens = set(re.findall(r'\w+', topic.lower()))
                common_topic = query_tokens.intersection(topic_tokens)
                if common_topic:
                    score += len(common_topic) * 2.0
                    matched_features.append(f"topic '{topic}'")

            # 6. Description substring / token matches
            desc_tokens = set(re.findall(r'\w+', ds.description.lower()))
            common_desc = query_tokens.intersection(desc_tokens)
            if common_desc:
                score += len(common_desc) * 1.0

            # 7. Time-series / Date heuristic
            if ("time" in query_tokens or "series" in query_tokens or "trend" in query_tokens or "date" in query_tokens) and "time-series" in ds.tags:
                score += 4.0
                matched_features.append("supports time-series analysis")

            reason = f"Matched {', '.join(matched_features[:3])}" if matched_features else "Curated popular analytical dataset"
            scored_datasets.append((score, ds, reason))

        # Sort by score descending
        scored_datasets.sort(key=lambda x: x[0], reverse=True)

        top_results = scored_datasets[:limit]
        recommended_schemas = [item[1] for item in top_results]

        top_reasons = [f"{item[1].name}: {item[2]}" for item in top_results if item[0] > 0]
        reasoning_text = "; ".join(top_reasons) if top_reasons else "Showing top recommended datasets from the catalog."

        return DatasetRecommendationResponse(
            query=query,
            recommended_datasets=recommended_schemas,
            reasoning=reasoning_text
        )
