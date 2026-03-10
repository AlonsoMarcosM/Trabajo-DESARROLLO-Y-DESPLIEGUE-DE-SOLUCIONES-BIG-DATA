"""
Gold Layer - Telco Churn (Medallion Architecture)
=================================================
Builds model-ready feature tables from Silver entities.

Tables produced
---------------
gold_churn_features         | Feature table with behavior + profile features
gold_churn_training_dataset | Feature table plus binary churn label
"""

import pyspark.pipelines as dp
from pyspark.sql import functions as F
from pyspark.sql.window import Window


@dp.table(
    name="gold_churn_features",
    comment="""
    Gold feature table for churn modeling.

    Includes:
    - recent behavior features from usage (3 and 6 months windows)
    - interaction intensity signals
    - stable profile features from customer master data
    """,
)
def gold_churn_features():
    usage = (
        spark.read
             .table("silver_usage_with_labels_batch")
             .withColumn("period_date", F.to_date(F.concat(F.col("year_month"), F.lit("-01"))))
    )

    interactions_monthly = (
        spark.read
             .table("silver_interactions")
             .withColumn("year_month", F.date_format(F.to_timestamp("timestamp"), "yyyy-MM"))
             .groupBy("customer_id", "year_month")
             .agg(
                 F.count("*").alias("interactions_count_m"),
                 F.sum(
                     F.when(F.col("interaction_type").isin(
                         "call_center_complaint",
                         "billing_dispute",
                         "cancellation_request",
                         "port_out_request",
                     ), F.lit(1)).otherwise(F.lit(0))
                 ).alias("negative_interactions_m"),
                 F.avg("satisfaction_score").alias("avg_interaction_satisfaction_m"),
             )
    )

    customers = (
        spark.read
             .table("silver_customers")
             .select(
                 "customer_id",
                 "age",
                 "gender",
                 "contract_type",
                 "region_type",
                 "monthly_fee",
                 "num_lines",
                 "signup_date",
                 "has_tv_bundle",
                 "has_fiber",
                 "has_roaming",
                 "paperless_billing",
                 "autopay",
                 "nps_score_at_start",
             )
             .dropDuplicates(["customer_id"])
    )

    base = (
        usage.alias("u")
             .join(interactions_monthly.alias("i"), on=["customer_id", "year_month"], how="left")
             .join(customers.alias("c"), on=["customer_id"], how="left")
             .fillna(
                 {
                     "interactions_count_m": 0,
                     "negative_interactions_m": 0,
                     "avg_interaction_satisfaction_m": 0.0,
                 }
             )
    )

    w3 = Window.partitionBy("customer_id").orderBy("period_date").rowsBetween(-2, 0)
    w6 = Window.partitionBy("customer_id").orderBy("period_date").rowsBetween(-5, 0)

    return (
        base.withColumn("age_group", F.when(F.col("age") <= 45, F.lit("young")).otherwise(F.lit("senior")))
            .withColumn("tenure_months", F.floor(F.months_between(F.col("period_date"), F.to_date("signup_date"))))
            .withColumn("avg_data_gb_3m", F.avg("data_consumed_gb").over(w3))
            .withColumn("avg_calls_3m", F.avg("call_minutes").over(w3))
            .withColumn("avg_sms_3m", F.avg("sms_count").over(w3))
            .withColumn("avg_bill_3m", F.avg("bill_amount").over(w3))
            .withColumn("avg_late_days_3m", F.avg("days_payment_late").over(w3))
            .withColumn("avg_nps_3m", F.avg("nps_score").over(w3))
            .withColumn("avg_interactions_3m", F.avg("interactions_count_m").over(w3))
            .withColumn("avg_negative_interactions_3m", F.avg("negative_interactions_m").over(w3))
            .withColumn("volatility_data_gb_6m", F.stddev_pop("data_consumed_gb").over(w6))
            .withColumn("volatility_nps_6m", F.stddev_pop("nps_score").over(w6))
    )


@dp.table(
    name="gold_churn_training_dataset",
    comment="""
    Final training dataset for Hito 3.

    Adds `label_will_churn` to the Gold feature table:
      1 -> churn_date is not null for that year_month
      0 -> churn_date is null
    """,
)
def gold_churn_training_dataset():
    return (
        spark.read
             .table("gold_churn_features")
             .withColumn(
                 "label_will_churn",
                 F.when(F.col("churn_date").isNotNull(), F.lit(1)).otherwise(F.lit(0))
             )
    )
