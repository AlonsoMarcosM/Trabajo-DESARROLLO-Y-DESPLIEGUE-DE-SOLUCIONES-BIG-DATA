"""
Silver Layer — Telco Churn (Medallion Architecture)
=====================================================
Reads from Bronze Delta tables, applies quality rules (expectations),
routes invalid records to quarantine (Dead Letter Queue), and produces
clean Silver tables plus a unified usage+label fact stream.

Tables produced
---------------
silver_customers_quarantine    | DLQ for invalid customer records
silver_customers               | Clean customer stream (append-only)
silver_usage_quarantine        | DLQ for invalid usage records
silver_usage                   | Clean usage events (append-only)
silver_labels_quarantine       | DLQ for invalid label records
silver_labels                  | Clean churn labels (append-only)
silver_interactions_quarantine | DLQ for invalid interaction records
silver_interactions            | Clean interaction events (append-only)
silver_usage_with_labels       | Unified fact: usage enriched with churn labels
                                 (stream-stream join with watermark)
"""

###############################################################################
# Imports
###############################################################################

import pyspark.pipelines as dp
from pyspark.sql.functions import col, current_timestamp, expr, to_timestamp
from pyspark.sql.types import BooleanType
from functools import reduce

try:
    from rules import (
        get_customer_rules,
        get_usage_rules,
        get_label_rules,
        get_interaction_rules,
    )
except Exception:
    # Lakeflow scripts may run without local package resolution;
    # keep an inline fallback so the pipeline remains executable.
    def get_customer_rules():
        return {
            "valid_customer_id":    "customer_id IS NOT NULL",
            "valid_age":            "age > 0 AND age < 120",
            "valid_contract_type":  "contract_type IN ('monthly', 'annual')",
            "valid_monthly_fee":    "monthly_fee >= 0",
        }


    def get_usage_rules():
        return {
            "valid_customer_id":        "customer_id IS NOT NULL",
            "valid_year_month":         "year_month IS NOT NULL",
            "valid_data_consumed":      "data_consumed_gb >= 0",
            "valid_call_minutes":       "call_minutes >= 0",
            "valid_bill_amount":        "bill_amount >= 0",
        }


    def get_label_rules():
        return {
            "valid_customer_id":        "customer_id IS NOT NULL",
            "valid_year_month":         "year_month IS NOT NULL",
        }


    def get_interaction_rules():
        return {
            "valid_customer_id":        "customer_id IS NOT NULL",
            "valid_timestamp":          "timestamp IS NOT NULL",
            "valid_interaction_type":   (
                "interaction_type IN ("
                "'call_center_inquiry', 'call_center_complaint', 'online_chat',"
                "'store_visit', 'plan_upgrade', 'plan_downgrade', 'plan_renewal',"
                "'technical_support', 'billing_dispute', 'cancellation_request',"
                "'loyalty_offer_accepted', 'loyalty_offer_rejected', 'port_out_request'"
                ")"
            ),
        }

###############################################################################
# Helpers
###############################################################################

def build_quarantine_flag(rules: dict):
    """
    Returns a Spark Column that evaluates to True when ANY rule is violated.
    Dynamically combines all rule expressions with AND, then negates.
    """
    combined = reduce(
        lambda a, b: a & b,
        [expr(condition) for condition in rules.values()]
    )
    return (~combined).cast(BooleanType()).alias("is_quarantined")


###############################################################################
# 1. CUSTOMERS — quarantine + clean append
###############################################################################

# 1a. Quarantine table (DLQ)
dp.create_streaming_table(name="silver_customers_quarantine")


# 1b. Routing hub — temporary table, not persisted to disk
@dp.table(
    name      = "bronze_customers_hub",
    temporary = True,
)
@dp.expect_all(get_customer_rules())
def bronze_customers_hub():
    rules = get_customer_rules()
    return (
        spark.readStream
             .format("delta")
             .option("skipChangeCommits", "true")
             .table("bronze_customers")
             .withColumn("is_quarantined", build_quarantine_flag(rules))
    )


# 1c. Invalid records → quarantine
@dp.append_flow(target="silver_customers_quarantine")
def customers_to_quarantine():
    return (
        spark.readStream
             .table("bronze_customers_hub")
             .filter(col("is_quarantined") == True)
             .drop("is_quarantined")
    )


# 1d. Valid records → clean view (no extra materialisation)
@dp.view(name="silver_customers_valid")
def silver_customers_valid():
    return (
        spark.readStream
             .table("bronze_customers_hub")
             .filter(col("is_quarantined") == False)
             .drop("is_quarantined")
    )


# 1e. Clean customers table (append-only in current runtime profile).
dp.create_streaming_table(name="silver_customers")


@dp.append_flow(target="silver_customers")
def customers_to_silver():
    return spark.readStream.table("silver_customers_valid")


###############################################################################
# 2. USAGE — quarantine + clean append
###############################################################################

dp.create_streaming_table(name="silver_usage_quarantine")


@dp.table(
    name      = "bronze_usage_hub",
    temporary = True,
)
@dp.expect_all(get_usage_rules())
def bronze_usage_hub():
    rules = get_usage_rules()
    return (
        spark.readStream
             .format("delta")
             .option("skipChangeCommits", "true")
             .table("bronze_usage")
             .withColumn("is_quarantined", build_quarantine_flag(rules))
    )


@dp.append_flow(target="silver_usage_quarantine")
def usage_to_quarantine():
    return (
        spark.readStream
             .table("bronze_usage_hub")
             .filter(col("is_quarantined") == True)
             .drop("is_quarantined")
    )


@dp.view(name="silver_usage_valid")
def silver_usage_valid():
    return (
        spark.readStream
             .table("bronze_usage_hub")
             .filter(col("is_quarantined") == False)
             .drop("is_quarantined")
    )


dp.create_streaming_table(name="silver_usage")


@dp.append_flow(target="silver_usage")
def usage_to_silver():
    return spark.readStream.table("silver_usage_valid")


###############################################################################
# 3. LABELS — quarantine + clean append
###############################################################################

dp.create_streaming_table(name="silver_labels_quarantine")


@dp.table(
    name      = "bronze_labels_hub",
    temporary = True,
)
@dp.expect_all(get_label_rules())
def bronze_labels_hub():
    rules = get_label_rules()
    return (
        spark.readStream
             .format("delta")
             .option("skipChangeCommits", "true")
             .table("bronze_labels")
             .withColumn("is_quarantined", build_quarantine_flag(rules))
    )


@dp.append_flow(target="silver_labels_quarantine")
def labels_to_quarantine():
    return (
        spark.readStream
             .table("bronze_labels_hub")
             .filter(col("is_quarantined") == True)
             .drop("is_quarantined")
    )


@dp.view(name="silver_labels_valid")
def silver_labels_valid():
    return (
        spark.readStream
             .table("bronze_labels_hub")
             .filter(col("is_quarantined") == False)
             .drop("is_quarantined")
    )


dp.create_streaming_table(name="silver_labels")


@dp.append_flow(target="silver_labels")
def labels_to_silver():
    return spark.readStream.table("silver_labels_valid")


###############################################################################
# 4. INTERACTIONS — quarantine + clean append
###############################################################################

dp.create_streaming_table(name="silver_interactions_quarantine")


@dp.table(
    name      = "bronze_interactions_hub",
    temporary = True,
)
@dp.expect_all(get_interaction_rules())
def bronze_interactions_hub():
    rules = get_interaction_rules()
    return (
        spark.readStream
             .format("delta")
             .option("skipChangeCommits", "true")
             .table("bronze_interactions")
             .withColumn("is_quarantined", build_quarantine_flag(rules))
    )


@dp.append_flow(target="silver_interactions_quarantine")
def interactions_to_quarantine():
    return (
        spark.readStream
             .table("bronze_interactions_hub")
             .filter(col("is_quarantined") == True)
             .drop("is_quarantined")
    )


@dp.view(name="silver_interactions_valid")
def silver_interactions_valid():
    return (
        spark.readStream
             .table("bronze_interactions_hub")
             .filter(col("is_quarantined") == False)
             .drop("is_quarantined")
    )


dp.create_streaming_table(name="silver_interactions")


@dp.append_flow(target="silver_interactions")
def interactions_to_silver():
    return spark.readStream.table("silver_interactions_valid")


###############################################################################
# 5. UNIFIED FACT TABLE (batch)
#    usage LEFT JOIN labels ON customer_id + year_month
###############################################################################

@dp.table(
    name    = "silver_usage_with_labels_batch",
    comment = """
    **Silver layer** - unified fact table.

    Batch join between clean usage rows and labels.
    This avoids stream-stream join constraints in triggered updates.
    """,
)
def silver_usage_with_labels_batch():
    usage = spark.read.table("silver_usage")

    labels = (
        spark.read
             .table("silver_labels")
             .select("customer_id", "year_month", "churn_date", "label_available_date")
             .withColumn("label_available_date", to_timestamp(col("label_available_date")))
    )

    return (
        usage.join(
            labels,
            on  = ["customer_id", "year_month"],
            how = "left",
        )
        .withColumn("silver_ingestion_timestamp", current_timestamp())
    )
