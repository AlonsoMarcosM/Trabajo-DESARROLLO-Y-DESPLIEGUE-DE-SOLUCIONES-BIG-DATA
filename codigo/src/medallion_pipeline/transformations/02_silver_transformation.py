"""
Silver Layer — Telco Churn (Medallion Architecture)
=====================================================
Reads from Bronze Delta tables, applies quality rules (expectations),
routes invalid records to quarantine (Dead Letter Queue), applies
SCD Type-2 via AUTO CDC for customer master data, and produces a
unified stream-stream joined fact table of usage + churn labels.

Tables produced
---------------
silver_customers_quarantine  | DLQ for invalid customer records
silver_customers             | SCD-2 historical customer master (AUTO CDC)
silver_usage_quarantine      | DLQ for invalid usage records
silver_usage                 | Clean usage events (append-only)
silver_labels_quarantine     | DLQ for invalid label records
silver_labels                | Clean churn labels (append-only)
silver_interactions_quarantine | DLQ for invalid interaction records
silver_interactions          | Clean interaction events (append-only)
silver_usage_with_labels     | Unified fact: usage enriched with churn labels
                               (stream-stream join with watermark)
"""

###############################################################################
# Imports
###############################################################################

import pyspark.pipelines as dp
from pyspark.sql.functions import col, current_timestamp, expr, lit
from pyspark.sql.types import BooleanType
from functools import reduce

from rules import (
    get_customer_rules,
    get_usage_rules,
    get_label_rules,
    get_interaction_rules,
)

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


# Audit columns added by Bronze — must be excluded from CDC to avoid
# spurious SCD-2 versions on metadata changes.
BRONZE_AUDIT_COLS = ["ingestion_timestamp", "source_file", "_rescued_data"]


###############################################################################
# 1. CUSTOMERS — SCD Type-2 via AUTO CDC
###############################################################################

# 1a. Quarantine table (DLQ)
@dp.create_streaming_table(name="silver_customers_quarantine")
def silver_customers_quarantine():
    pass


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


# 1e. SCD-2 target table
@dp.create_streaming_table(name="silver_customers")
def silver_customers():
    pass


# 1f. AUTO CDC flow — maintains __START_AT / __END_AT automatically
dp.create_auto_cdc_flow(
    name             = "silver_customers_cdc",
    target           = "silver_customers",
    source           = "silver_customers_valid",
    keys             = ["customer_id"],
    sequence_by      = "customer_updated_at",
    except_column_list = BRONZE_AUDIT_COLS,
)


###############################################################################
# 2. USAGE — quarantine + clean append
###############################################################################

@dp.create_streaming_table(name="silver_usage_quarantine")
def silver_usage_quarantine():
    pass


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


@dp.create_streaming_table(name="silver_usage")
def silver_usage():
    pass


@dp.append_flow(target="silver_usage")
def usage_to_silver():
    return spark.readStream.table("silver_usage_valid")


###############################################################################
# 3. LABELS — quarantine + clean append
###############################################################################

@dp.create_streaming_table(name="silver_labels_quarantine")
def silver_labels_quarantine():
    pass


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


@dp.create_streaming_table(name="silver_labels")
def silver_labels():
    pass


@dp.append_flow(target="silver_labels")
def labels_to_silver():
    return spark.readStream.table("silver_labels_valid")


###############################################################################
# 4. INTERACTIONS — quarantine + clean append
###############################################################################

@dp.create_streaming_table(name="silver_interactions_quarantine")
def silver_interactions_quarantine():
    pass


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


@dp.create_streaming_table(name="silver_interactions")
def silver_interactions():
    pass


@dp.append_flow(target="silver_interactions")
def interactions_to_silver():
    return spark.readStream.table("silver_interactions_valid")


###############################################################################
# 5. UNIFIED FACT TABLE — stream-stream join with watermark
#    usage LEFT JOIN labels ON customer_id + year_month
#    Watermark: 60 days on label_available_date to handle delayed feedback
###############################################################################

@dp.create_streaming_table(
    name    = "silver_usage_with_labels",
    comment = """
    **Silver layer** — unified fact table.

    Joins clean usage events with churn labels using a stream-stream join
    with watermarks to handle delayed label feedback (up to 60 days).

    Key columns
    -----------
    customer_id         : FK -> silver_customers
    year_month          : billing period
    churn_date          : NULL if customer retained that month
    label_available_date: point-in-time boundary for safe ML feature extraction
    """,
)
def silver_usage_with_labels():
    pass


@dp.append_flow(target="silver_usage_with_labels")
def usage_with_labels_flow():
    usage = (
        spark.readStream
             .table("silver_usage")
             .withWatermark("ingestion_timestamp", "60 days")
    )

    labels = (
        spark.readStream
             .table("silver_labels")
             .withWatermark("label_available_date", "60 days")
    )

    return (
        usage.join(
            labels,
            on  = ["customer_id", "year_month"],
            how = "left",
        )
        .withColumn("silver_ingestion_timestamp", current_timestamp())
    )