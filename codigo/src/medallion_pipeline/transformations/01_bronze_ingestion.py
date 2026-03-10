"""
Bronze Layer — Telco Churn (Medallion Architecture)
=====================================================
Ingests the three raw file types produced by the synthetic Telco Churn
generator into managed Delta tables using Databricks Lakeflow Declarative
Pipelines.

Landing zone structure (output of the generator):
  context/
    customers.csv                    <- master data, batch / full-refresh

  events/
    usage/YYYY/MM/data.json          <- one row per active customer per month
    labels/YYYY/MM/data.json         <- churn labels, available end-of-month
    interactions/YYYY/MM/data.json   <- variable-volume customer interactions

Ingestion strategy:
  bronze_customers    | Batch full-refresh | spark.read (CSV snapshot)
  bronze_usage        | Streaming          | Auto Loader (JSON, append-only)
  bronze_labels       | Streaming          | Auto Loader (JSON, append-only)
  bronze_interactions | Streaming          | Auto Loader (JSON, append-only)

Decorators used
---------------
@dp.table              -> batch or streaming table (full-refresh for batch, streaming for streaming)
"""

###############################################################################
# Imports
###############################################################################

from pathlib import Path

import pyspark.pipelines as dp
from pyspark.sql.functions import col, current_timestamp, to_timestamp

###############################################################################
# Configuration
# ----------------------------------------------------------------------------
# Landing zone root can be provided from the pipeline configuration in
# pipeline.yml as `landing_volume_path`. Fallback keeps previous default.
# Example: /Volumes/<catalog>/<schema>/<volume_name>
###############################################################################

vol_landing_zone = Path(
    spark.conf.get("landing_volume_path", "/Volumes/workspace/default/landing_zone")
)

path_context      = vol_landing_zone / "context"
path_usage        = vol_landing_zone / "events" / "usage"
path_labels       = vol_landing_zone / "events" / "labels"
path_interactions = vol_landing_zone / "events" / "interactions"

###############################################################################
# 1. Customers — batch ingestion (full refresh)
###############################################################################

@dp.table(
    name    = "bronze_customers",
    comment = """
    **Bronze layer** — raw customer master data (context).

    Source   : context/customers.csv
    Strategy : Batch full-refresh. Overwritten on every pipeline run.

    Audit columns
    -------------
    ingestion_timestamp : instant the row entered the analytical ecosystem
    source_file         : absolute path of the source CSV (lineage/audit)
    _rescued_data       : schema-mismatch fields captured without stopping ingest

    Business columns
    ----------------
    customer_id         : hashed unique identifier (prefix CL)
    customer_updated_at : timestamp of last status change (e.g. churn event)
    age                 : customer age in years
    gender              : M | F | O  — protected attribute
    contract_type       : monthly | annual  — primary churn driver
    region              : specific city or rural zone name
    region_type         : urban | rural  — churn driver
    tariff_plan         : active plan at snapshot time
    monthly_fee         : contractual monthly charge (EUR)
    num_lines           : number of SIM lines on the account
    device_type         : android_low | android_mid | android_high | iphone | other
    acquisition_channel : online | store | telesales | referral | promotion
    payment_method      : direct_debit | credit_card | bank_transfer | digital_wallet
    signup_date         : date the customer originally signed a contract
    has_tv_bundle       : 1 if TV bundle add-on is active
    has_fiber           : 1 if fiber broadband is active
    has_roaming         : 1 if international roaming add-on is active
    paperless_billing   : 1 if customer opted for paperless billing
    autopay             : 1 if automatic payment is enabled (direct debit)
    nps_score_at_start  : Net Promoter Score proxy at start of data window
    is_active           : 1 = active customer, 0 = churned
    """,
)
def bronze_customers():
    return (
        spark.read
             .format("csv")
             .option("header",      "true")
             .option("inferSchema", "true")
             .load(str(path_context))
             # Keep schema stable across reruns with different input volumes.
             .withColumn("customer_updated_at", col("customer_updated_at").cast("string"))
             .withColumn("ingestion_timestamp", current_timestamp())
             .withColumn("source_file",         col("_metadata.file_path"))
    )

###############################################################################
# 2. Usage — streaming ingestion via Auto Loader
###############################################################################

@dp.table(
    name    = "bronze_usage",
    comment = """
    **Bronze layer** — raw monthly usage events (append-only).

    Source   : events/usage/YYYY/MM/data.json
    Strategy : Streaming via Auto Loader. Checkpoint ensures only new files
               are processed on each incremental run — no duplicates.

    Audit columns
    -------------
    ingestion_timestamp : instant the row entered the analytical ecosystem
    source_file         : absolute path of the source file (lineage/audit)
    _rescued_data       : schema-mismatch rows captured without stopping ingest

    Business columns
    ----------------
    customer_id         : FK -> bronze_customers
    year_month          : billing period (YYYY-MM)
    days_active         : days customer was active (pro-rated on churn month)
    tariff_plan         : plan active that month (2025 may show esim_only_20gb
                          or 5g_premium_unlimited — data drift)
    data_consumed_gb    : mobile data consumed in GB
    call_minutes        : outbound call minutes in the period
    sms_count           : SMS messages sent
    roaming_gb          : data consumed while roaming (0 if no roaming add-on)
    bill_amount         : total invoice for the period (EUR)
    bill_overage        : extra charges above plan allowance (EUR)
    days_payment_late   : days the invoice was paid late (rises pre-churn)
    coverage_score      : network coverage quality 1-10
    speed_mbps          : measured download speed in Mbps
    nps_score           : monthly NPS proxy (degrades before churn)
    digital_discount    : digital billing discount — NEW from 2025-02, NULL
                          for all 2023-2024 rows (data drift signal)
    """,
)
def bronze_usage():
    return (
        spark.readStream
             .format("cloudFiles")
             .option("cloudFiles.format",           "json")
             .option("cloudFiles.inferColumnTypes", "true")
             .load(str(path_usage))
             .withColumn("ingestion_timestamp", current_timestamp())
             .withColumn("source_file",         col("_metadata.file_path"))
    )

###############################################################################
# 3. Churn Labels — streaming ingestion via Auto Loader
###############################################################################

@dp.table(
    name    = "bronze_labels",
    comment = """
    **Bronze layer** — raw churn labels, delayed feedback (append-only).

    Source   : events/labels/YYYY/MM/data.json
    Strategy : Streaming via Auto Loader. Files land end-of-month and are
               ingested incrementally as they become available.

    Audit columns
    -------------
    ingestion_timestamp  : instant the row entered the analytical ecosystem
    source_file          : absolute path of the source file (lineage/audit)
    _rescued_data        : schema-mismatch rows captured without stopping ingest

    Business columns
    ----------------
    customer_id          : FK -> bronze_customers / bronze_usage
    year_month           : billing period the label refers to (YYYY-MM)
    churn_date           : exact date the customer churned (NULL = retained)
    label_available_date : end-of-month timestamp when label was generated
                           (safe point-in-time boundary for Silver joins)
    """,
)
def bronze_labels():
    return (
        spark.readStream
             .format("cloudFiles")
             .option("cloudFiles.format",           "json")
             .option("cloudFiles.inferColumnTypes", "true")
             .load(str(path_labels))
             .withColumn("label_available_date", to_timestamp(col("label_available_date")))
             .withColumn("ingestion_timestamp", current_timestamp())
             .withColumn("source_file",         col("_metadata.file_path"))
    )

###############################################################################
# 4. Interactions — streaming ingestion via Auto Loader
###############################################################################

@dp.table(
    name    = "bronze_interactions",
    comment = """
    **Bronze layer** — raw customer interaction events (append-only).

    Source   : events/interactions/YYYY/MM/data.json
    Strategy : Streaming via Auto Loader. Variable volume, high frequency.

    Audit columns
    -------------
    ingestion_timestamp : instant the row entered the analytical ecosystem
    source_file         : absolute path of the source file (lineage/audit)
    _rescued_data       : schema-mismatch rows captured without stopping ingest

    Business columns
    ----------------
    customer_id         : FK -> bronze_customers
    timestamp           : exact event timestamp (ISO 8601 UTC)
    interaction_type    : call_center_inquiry | call_center_complaint |
                          online_chat | store_visit | plan_upgrade |
                          plan_downgrade | plan_renewal | technical_support |
                          billing_dispute | cancellation_request |
                          loyalty_offer_accepted | loyalty_offer_rejected |
                          port_out_request
    channel             : phone | app | web | store
    duration_seconds    : call duration in seconds (NULL for non-call types)
    resolution          : resolved_first_contact | escalated | unresolved |
                          callback_scheduled  (NULL for non-complaint types)
    agent_id            : hashed identifier of the handling agent
    satisfaction_score  : post-interaction score 1-5 (drops sharply pre-churn)
    """,
)
def bronze_interactions():
    return (
        spark.readStream
             .format("cloudFiles")
             .option("cloudFiles.format",           "json")
             .option("cloudFiles.inferColumnTypes", "true")
             .load(str(path_interactions))
             .withColumn("ingestion_timestamp", current_timestamp())
             .withColumn("source_file",         col("_metadata.file_path"))
    )
