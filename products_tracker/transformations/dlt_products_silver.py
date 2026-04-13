import dlt
from pyspark.sql.functions import col, expr, when, lower, regexp_replace, concat, lit, round, array_max, transform, regexp_extract_all

@dlt.table(
    name="silver_products",
    comment="Capa Silver: Limpieza de precios, validación de stock y normalización de cuotas.",
    table_properties={"quality": "silver"}
)
def silver_products():
    # 1. Lectura de las tablas Bronze (Streaming o Live)
    # Usamos dlt.read para que el pipeline entienda las dependencias
    scrap = dlt.read("bronze_scraped_products")
    catal = dlt.read("catalog")
    
    # 2. Paso Intermedio: Join y Limpieza inicial de Precios
    # Reemplazamos los REPLACE anidados de SQL por regexp_replace
    enriched_df = scrap.alias("scrap").join(
        catal.alias("catal"),
        (col("scrap.product_id") == col("catal.product_id")) & 
        (col("scrap.retailer") == col("catal.retailer")),
        "inner"
    ).select(
        col("catal.product_id"),
        col("catal.brand").alias("brand"),
        col("scrap.sku"),
        col("scrap.name"),
        col("catal.retailer"),
        col("catal.main_category"),
        col("catal.sub_category"),
        # Limpieza de precios: eliminamos $ y . antes de castear
        expr("TRY_CAST(REGEXP_REPLACE(scrap.list_price, '[\\\\$.]', '') AS DOUBLE)").alias("list_price"),
        expr("TRY_CAST(REGEXP_REPLACE(scrap.cash_price, '[\\\\$.]', '') AS DOUBLE)").alias("cash_price"),
        col("scrap.scraped_at").cast("date").alias("scraped_at"),
        col("catal.link"),
        col("scrap.installments")
    )

    # 3. Aplicación de Lógica de Negocio y Flags
    return enriched_df.select(
        "*",
        # Disponibilidad
        when(
            (col("sku").isNotNull()) & 
            ((col("list_price").isNotNull()) | (col("cash_price").isNotNull())), 
            True
        ).otherwise(False).alias("is_available"),
        
        # Validación de Nombre
        when((col("name").isNotNull()) & (col("name") != ""), True).otherwise(False).alias("is_valid_name"),
        
        # Validación de Precios Lógicos
        when(
            (col("list_price").isNull() & col("cash_price").isNull()) |
            ((col("list_price") > 10000000) & (col("cash_price") > 10000000)) |
            ((col("list_price") < 0) & (col("cash_price") < 0)),
            False
        ).otherwise(True).alias("is_valid_price"),
        
        # Descuentos (Int y Str)
        round((1 - (col("cash_price") / col("list_price"))) * 100, 2).alias("discount_applied_int"),
        
        # Lógica de Cuotas (has_installments)
        expr("""
            CASE 
                WHEN (LOWER(installments) LIKE '%sin interés%' OR LOWER(installments) LIKE '%cuotas fijas%') THEN TRUE
                WHEN ARRAY_MAX(
                       TRANSFORM(
                         REGEXP_EXTRACT_ALL(installments, ':\\\\s*"*(\\\\d+)', 1), 
                         x -> CAST(x AS INT)
                       )
                     ) > 1 THEN TRUE
                ELSE FALSE 
            END
        """).alias("has_installments")
    ).orderBy(col("scraped_at").desc())