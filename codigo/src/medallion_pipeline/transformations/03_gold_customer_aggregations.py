"""
Gold customer aggregations for Telco Churn.

Lightweight derived features from gold_churn_spine.
Kept as streaming table to preserve dataset type compatibility.
"""

import pyspark.pipelines as dp
from pyspark.sql.functions import (
    col,
    lit,
)


gold_spine_source = "gold_churn_spine"
gold_aggregations_table_name = "gold_customer_aggregations"
gold_aggregations_flow_name = "flow_gold_customer_aggregations"
gold_aggregations_comment = "Derived churn features per customer-month."
gold_aggregations_properties = {"delta.enableChangeDataFeed": "true"}
EPSILON = 1e-6

gold_aggregations_schema = """
    customer_id STRING NOT NULL,
    year_month STRING,
    window_end TIMESTAMP NOT NULL,
    label_available_date TIMESTAMP,
    label_will_churn INT,
    data_consumed_gb DOUBLE,
    call_minutes DOUBLE,
    bill_amount DOUBLE,
    days_payment_late INT,
    nps_score DOUBLE,
    coverage_score DOUBLE,
    bill_vs_data_ratio DOUBLE,
    CONSTRAINT gold_customer_aggregations_pk PRIMARY KEY (customer_id, window_end TIMESERIES)
"""


dp.create_streaming_table(
    name=gold_aggregations_table_name,
    comment=gold_aggregations_comment,
    table_properties=gold_aggregations_properties,
    schema=gold_aggregations_schema,
)


@dp.append_flow(target=gold_aggregations_table_name, name=gold_aggregations_flow_name)
def gold_customer_aggregations():
    df = spark.readStream.table(gold_spine_source)

    return (
        df.select(
            col("customer_id"),
            col("year_month"),
            col("usage_event_time").alias("window_end"),
            col("label_available_date"),
            col("label_will_churn"),
            col("data_consumed_gb"),
            col("call_minutes"),
            col("bill_amount"),
            col("days_payment_late"),
            col("nps_score"),
            col("coverage_score"),
            (col("bill_amount") / (col("data_consumed_gb") + lit(EPSILON))).alias("bill_vs_data_ratio"),
        )
    )
