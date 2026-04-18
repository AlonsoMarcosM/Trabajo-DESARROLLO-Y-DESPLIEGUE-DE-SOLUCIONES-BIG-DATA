# Databricks notebook source
# MAGIC %md
# MAGIC # 04 - Feature Store Registration (Simulado en Free Edition)
# MAGIC
# MAGIC Este notebook se ejecuta despues del pipeline Medallion.
# MAGIC En Free Edition no se puede desplegar Online Feature Store/Lakebase,
# MAGIC asi que aqui se deja una simulacion ejecutable y el codigo real comentado.

# COMMAND ----------

dbutils.widgets.text("catalog", "workspace")
dbutils.widgets.text("schema", "telco_churn")

catalog = dbutils.widgets.get("catalog")
schema = dbutils.widgets.get("schema")

full_profile_table = f"{catalog}.{schema}.gold_customer_profile"
full_aggregations_table = f"{catalog}.{schema}.gold_customer_aggregations"

print("== Contexto de ejecucion ==")
print(f"Catalog: {catalog}")
print(f"Schema: {schema}")
print(f"Profile table: {full_profile_table}")
print(f"Aggregations table: {full_aggregations_table}")

# COMMAND ----------

profile_exists = spark.catalog.tableExists(full_profile_table)
aggregations_exists = spark.catalog.tableExists(full_aggregations_table)

if not profile_exists or not aggregations_exists:
    missing = []
    if not profile_exists:
        missing.append(full_profile_table)
    if not aggregations_exists:
        missing.append(full_aggregations_table)
    raise Exception("Faltan tablas Gold para simulacion Feature Store: " + ", ".join(missing))

profile_count = spark.sql(f"SELECT COUNT(*) AS n FROM {full_profile_table}").collect()[0]["n"]
aggregations_count = spark.sql(f"SELECT COUNT(*) AS n FROM {full_aggregations_table}").collect()[0]["n"]

print("== Validacion de tablas Gold ==")
print(f"{full_profile_table}: {profile_count} filas")
print(f"{full_aggregations_table}: {aggregations_count} filas")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Simulacion de registro/publicacion en Feature Store
# MAGIC
# MAGIC El codigo real queda como referencia para cuando haya licencia completa.

# COMMAND ----------

online_store_name = "telco_churn_online_store"
online_profile_table = f"{catalog}.{schema}.online_customer_profile"
online_aggregations_table = f"{catalog}.{schema}.online_customer_aggregations"

print("== Simulacion Feature Store (Free Edition) ==")
print("Online store (simulado):", online_store_name)
print("Publicacion simulada de:")
print(" -", full_profile_table, "->", online_profile_table)
print(" -", full_aggregations_table, "->", online_aggregations_table)

# Referencia de codigo real (no ejecutable en Free Edition):
# from databricks.feature_engineering import FeatureEngineeringClient
# fe = FeatureEngineeringClient()
# fe.create_online_store(name=online_store_name, capacity="CU_1")
# fe.publish_table(
#     online_store=online_store_name,
#     source_table_name=full_profile_table,
#     online_table_name=online_profile_table,
#     publish_mode="TRIGGERED",
# )
# fe.publish_table(
#     online_store=online_store_name,
#     source_table_name=full_aggregations_table,
#     online_table_name=online_aggregations_table,
#     publish_mode="TRIGGERED",
# )

# COMMAND ----------

print("Notebook completado correctamente (modo simulacion).")
