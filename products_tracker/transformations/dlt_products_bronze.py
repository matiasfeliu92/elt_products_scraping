import dlt
from pyspark.sql.functions import col, get_json_object, desc

@dlt.table(
  name="bronze_scraped_products",
  comment="Bronze table with raw scraped products data",
  table_properties={
    "quality": "bronze",
  }
)

def bronze_products_scraped():
    # 1. Leemos de la tabla origen que llenaste desde Mongo
    # Usamos spark.read.table porque es una tabla externa al pipeline DLT
    df = spark.read.table("products.raw_scrapping_data")
    
    # 2. Aplicamos la lógica de extracción de JSON (equivalente a tu SELECT)
    bronze_df = df.select(
        col("scraped_at"),
        col("product_id"),
        col("retailer"),
        get_json_object(col("raw_data"), "$.sku").alias("sku"),
        get_json_object(col("raw_data"), "$.name").alias("name"),
        get_json_object(col("raw_data"), "$.brand").alias("brand"),
        get_json_object(col("raw_data"), "$.main_category").alias("main_category"),
        get_json_object(col("raw_data"), "$.sub_category").alias("sub_category"),
        get_json_object(col("raw_data"), "$.list_price").alias("list_price"),
        get_json_object(col("raw_data"), "$.cash_price").alias("cash_price"),
        get_json_object(col("raw_data"), "$.stock").alias("is_in_stock"),
        get_json_object(col("raw_data"), "$.installments").alias("installments")
    )
    
    return bronze_df