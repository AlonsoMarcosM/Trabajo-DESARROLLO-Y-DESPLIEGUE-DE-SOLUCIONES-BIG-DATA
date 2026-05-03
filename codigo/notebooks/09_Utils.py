"""
Shared utilities for the production churn inference and label enrichment pipeline.
"""


###############################################################################
# Imports
###############################################################################

from databricks.feature_engineering import FeatureEngineeringClient, FeatureLookup


###############################################################################
# Table configuration
###############################################################################

spine_table = f"{catalog}.{database}.gold_churn_spine"
customer_profile_table = f"{catalog}.{database}.gold_customer_profile"
customer_agg_table = f"{catalog}.{database}.gold_customer_aggregations"
inference_enriched_table = f"{catalog}.{database}.gold_churn_inference_enriched"
churn_labels_table = f"{catalog}.{database}.silver_churn_events"


###############################################################################
# Column configuration
###############################################################################

customer_id_column = "customer_id"
date_column = "year_month"
label_column = "label_will_churn"
prediction_column = "prediction"
prob_churn_column = "prob_churn"
model_version_col = "model_version"
inference_timestamp_col = "inference_timestamp"


###############################################################################
# Feature store configuration
###############################################################################

entity_key = "customer_id"
timestamp_key = "usage_event_time"

# Static or slowly-changing customer profile features (from gold_customer_profile).
# Must match exactly the feature_names used in 05_Training_Dataset_Generation
# to guarantee that the enrichment is identical to training.
profile_feature_names = [
    # Demographic
    "age",
    "age_group",
    "gender",
    # Contract & plan
    "contract_type",
    "contract_risk_group",
    "tariff_plan",
    "monthly_fee",
    "num_lines",
    # Product bundles
    "has_tv_bundle",
    "has_fiber",
    "has_roaming",
    # Device & channel
    "device_type",
    "acquisition_channel",
    "payment_method",
    "paperless_billing",
    "autopay",
    # Geography
    "region",
    "region_type",
    # Baseline satisfaction
    "nps_score_at_start",
    #
    "is_active",
    "signup_date",
]

# Monthly behavioral aggregations (from gold_customer_aggregations).
# Churn signals focus on usage trends, payment behaviour and satisfaction.
aggregation_feature_names = [
    # Usage
    "data_consumed_gb",
    "call_minutes",
    # Billing
    "bill_amount",
    "days_payment_late",
    "bill_vs_data_ratio",
    # Satisfaction & network
    "nps_score",
    "coverage_score",
]

profile_lookup = FeatureLookup(
    table_name = customer_profile_table,
    feature_names = profile_feature_names,
    lookup_key = entity_key,
    timestamp_lookup_key = timestamp_key
)

aggregations_lookup = FeatureLookup(
    table_name = customer_agg_table,
    feature_names = aggregation_feature_names,
    lookup_key = entity_key,
    timestamp_lookup_key = timestamp_key
)

feature_lookups = [profile_lookup, aggregations_lookup]

exclude_columns = ["churn_date"]

print(f"Profile features ({len(profile_feature_names)}): {profile_feature_names}")
print(f"Aggregation features ({len(aggregation_feature_names)}): {aggregation_feature_names}")
print(f"Total feature columns: {len(profile_feature_names) + len(aggregation_feature_names)}")
print()


print("09_Utils_churn.py script loaded successfully.")