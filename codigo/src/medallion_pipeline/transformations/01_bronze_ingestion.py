"""
Bronze layer ingestion for Telco Churn.

Pattern aligned with professor example:
- batch snapshot for customer master data
- streaming ingestion with Auto Loader for event entities
"""

from pathlib import Path

import pyspark.pipelines as dp
from pyspark.sql.functions import col, current_timestamp

vol_landing_zone = Path(spark.conf.get("landing_volume_path", "/Volumes/workspace/default/landing_zone"))

path_context = vol_landing_zone / "context"
path_usage = vol_landing_zone / "events" / "usage"
path_labels = vol_landing_zone / "events" / "labels"
path_interactions = vol_landing_zone / "events" / "interactions"


@dp.table(
    name="bronze_customers",
    comment="""
    Raw customer master data from landing zone context.
    Full refresh is handled by the pipeline runtime.
    """,
)
def bronze_customers():
    return (
        spark.read
             .format("csv")
             .option("header", "true")
             .option("inferSchema", "true")
             .load(str(path_context))
             .withColumn("customer_updated_at", col("customer_updated_at").cast("string"))
             .withColumn("ingestion_timestamp", current_timestamp())
             .withColumn("source_file", col("_metadata.file_path"))
    )


usage_table_name = "bronze_usage"
usage_flow_name = "bronze_usage_ingest_flow"

dp.create_streaming_table(
    name=usage_table_name,
    comment="Raw monthly usage events ingested incrementally via Auto Loader.",
)


@dp.append_flow(target=usage_table_name, name=usage_flow_name)
def bronze_usage_flow():
    return (
        spark.readStream
             .format("cloudFiles")
             .option("cloudFiles.format", "json")
             .option("cloudFiles.inferColumnTypes", "true")
             .load(str(path_usage))
             .withColumn("ingestion_timestamp", current_timestamp())
             .withColumn("source_file", col("_metadata.file_path"))
    )


labels_table_name = "bronze_labels"
labels_flow_name = "bronze_labels_ingest_flow"

dp.create_streaming_table(
    name=labels_table_name,
    comment="Raw churn labels ingested incrementally via Auto Loader.",
)


@dp.append_flow(target=labels_table_name, name=labels_flow_name)
def bronze_labels_flow():
    return (
        spark.readStream
             .format("cloudFiles")
             .option("cloudFiles.format", "json")
             .option("cloudFiles.inferColumnTypes", "true")
             .load(str(path_labels))
             .withColumn("ingestion_timestamp", current_timestamp())
             .withColumn("source_file", col("_metadata.file_path"))
    )


interactions_table_name = "bronze_interactions"
interactions_flow_name = "bronze_interactions_ingest_flow"

dp.create_streaming_table(
    name=interactions_table_name,
    comment="Raw customer interactions ingested incrementally via Auto Loader.",
)


@dp.append_flow(target=interactions_table_name, name=interactions_flow_name)
def bronze_interactions_flow():
    return (
        spark.readStream
             .format("cloudFiles")
             .option("cloudFiles.format", "json")
             .option("cloudFiles.inferColumnTypes", "true")
             .load(str(path_interactions))
             .withColumn("ingestion_timestamp", current_timestamp())
             .withColumn("source_file", col("_metadata.file_path"))
    )
