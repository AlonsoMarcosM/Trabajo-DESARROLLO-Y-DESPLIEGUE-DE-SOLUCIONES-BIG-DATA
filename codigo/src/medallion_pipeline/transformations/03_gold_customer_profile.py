"""
Gold customer profile for Telco Churn.

SCD2 customer profile table derived from silver_customers_history.
"""

import pyspark.pipelines as dp
from pyspark.sql.functions import col, when


gold_profile_table_name = "gold_customer_profile"
gold_profile_flow_name = "flow_gold_customer_profile"
silver_customers_source = "silver_customers_history"

gold_profile_comment = "SCD2 customer profile feature table for churn use case."

gold_profile_table_properties = {"delta.enableChangeDataFeed": "true"}

gold_profile_schema = """
    customer_id STRING NOT NULL,
    age INT,
    gender STRING,
    contract_type STRING,
    region STRING,
    region_type STRING,
    tariff_plan STRING,
    monthly_fee DOUBLE,
    num_lines INT,
    device_type STRING,
    acquisition_channel STRING,
    payment_method STRING,
    signup_date DATE,
    has_tv_bundle INT,
    has_fiber INT,
    has_roaming INT,
    paperless_billing INT,
    autopay INT,
    nps_score_at_start DOUBLE,
    is_active INT,
    __START_AT TIMESTAMP NOT NULL,
    __END_AT TIMESTAMP,
    age_group STRING NOT NULL,
    contract_risk_group STRING NOT NULL,
    CONSTRAINT gold_customer_profile_pk PRIMARY KEY (customer_id, __START_AT TIMESERIES)
"""

dp.create_streaming_table(
    name=gold_profile_table_name,
    comment=gold_profile_comment,
    table_properties=gold_profile_table_properties,
    schema=gold_profile_schema,
)


@dp.append_flow(target=gold_profile_table_name, name=gold_profile_flow_name)
def gold_customer_profile():
    df_customers = spark.readStream.table(silver_customers_source)

    return df_customers.select(
        col("customer_id"),
        col("age"),
        col("gender"),
        col("contract_type"),
        col("region"),
        col("region_type"),
        col("tariff_plan"),
        col("monthly_fee"),
        col("num_lines"),
        col("device_type"),
        col("acquisition_channel"),
        col("payment_method"),
        col("signup_date"),
        col("has_tv_bundle"),
        col("has_fiber"),
        col("has_roaming"),
        col("paperless_billing"),
        col("autopay"),
        col("nps_score_at_start"),
        col("is_active"),
        col("__START_AT"),
        col("__END_AT"),
        when(col("age") <= 45, "young").otherwise("senior").alias("age_group"),
        when(col("contract_type") == "monthly", "high_risk").otherwise("low_risk").alias("contract_risk_group"),
    )
