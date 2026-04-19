import pyspark.pipelines as dp
from pyspark.sql.functions import col, date_format, to_timestamp, when


gold_spine_table_name = "gold_churn_spine"
gold_spine_flow_name = "flow_gold_churn_spine"
gold_spine_comment = "Event-level churn spine built from silver_churn_events."

silver_events_source = "silver_churn_events"


dp.create_streaming_table(
    name=gold_spine_table_name,
    comment=gold_spine_comment,
)


@dp.append_flow(target=gold_spine_table_name, name=gold_spine_flow_name)
def gold_churn_spine():
    df_events = spark.readStream.table(silver_events_source)

    # Normalización de timestamp
    df_events = df_events.withColumn(
        "label_available_date",
        to_timestamp(
            date_format(col("label_available_date"), "yyyy-MM-dd HH:mm:ss.SSS")
        ),
    )

    return df_events.select(
        col("customer_id"),
        col("year_month"),
        col("usage_event_time"),
        col("label_available_date"),
        col("churn_date"),
        when(col("churn_date").isNotNull(), 1).otherwise(0).alias("label_will_churn"),
        col("roaming_gb"),
        col("sms_count"),
        col("bill_overage"),
        col("speed_mbps"),
        col("days_active"),
        #col("tariff_plan"),
        #col("data_consumed_gb"),
        #col("call_minutes"),
        #col("bill_amount"),
        #col("days_payment_late"),
        #col("coverage_score"),
        #col("nps_score"),
    )