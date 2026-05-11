from datetime import datetime
import json
import os
from dotenv import load_dotenv
import pandas as pd

from src.config.mongo_db import MongoDB
from src.config.settings import Settings
from src.config.logger import LoggerConfig
from src.utils.normalize_price import NormalizePrice
from src.utils.load_errors import LoadErrors

load_dotenv()

class LoadData:
    def __init__(self):
        self.logger = LoggerConfig.get_logger(self.__class__.__name__)
        self.normalize_price = NormalizePrice()
        self.settings = Settings()
        self.mongo_db = MongoDB()
        self.mongo_db_uri = self.settings.MONGO_DB_URI
        self.load_errors = LoadErrors()

    def _store_error(self, error, product_id=None, retailer=None, field="load_data", path="products.scraped_products"):
        self.load_errors.load(
            product_id=product_id,
            retailer=retailer,
            error_type=type(error).__name__,
            message=str(error),
            by="MONGO_LOAD",
            path=path,
            field=field
        )

    def load(self, __data__: dict):
        product_id = __data__.get("product_id") if __data__ else None
        retailer = __data__.get("retailer") if __data__ else None
        try:
            if not __data__:
                self.logger.warning("No hay datos para insertar, se omite la carga.")
                return

            __data__["raw_data"] = __data__.pop("data")
            product_id = __data__.get("product_id")
            retailer = __data__.get("retailer")
            raw_product_data = __data__.get("raw_data", {})

            list_price_raw = raw_product_data.get("list_price")
            cash_price_raw = raw_product_data.get("cash_price")
            self.logger.info({
                "product_id": product_id,
                "retailer": retailer,
                "list_price_raw": list_price_raw,
                "cash_price_raw": cash_price_raw,
                "step": "ANTES DE NORMALIZAR PRECIOS"
            })
            list_price_norm = self.normalize_price.execute(list_price_raw)
            cash_price_norm = self.normalize_price.execute(cash_price_raw)
            self.logger.info({
                "product_id": product_id,
                "retailer": retailer,
                "list_price_raw": list_price_norm,
                "cash_price_raw": cash_price_norm,
                "step": "DESPUÉS DE NORMALIZAR PRECIOS"
            })

            self.logger.info(f"DATA TO LOAD: {json.dumps(__data__, indent=2)}")

            self.mongo_db.connect(self.mongo_db_uri, db_name="products")
            scraped_products_collection = self.mongo_db.get_database()["scraped_products"]

            last_entry = scraped_products_collection.find_one(
                {"product_id": product_id, "retailer": retailer},
                sort=[("scraped_at", -1)]
            )

            if last_entry:
                last_raw = last_entry.get("raw_data", {})
                last_list_price_norm = self.normalize_price.execute(last_raw.get("list_price"))
                last_cash_price_norm = self.normalize_price.execute(last_raw.get("cash_price"))
                self.logger.info({
                    "current_list_price_norm": list_price_norm,
                    "current_cash_price_norm": cash_price_norm,
                    "last_list_price_norm": last_list_price_norm,
                    "last_cash_price_norm": last_cash_price_norm,
                })

                if (last_list_price_norm == list_price_norm and
                    last_cash_price_norm == cash_price_norm):
                    self.logger.info("No hubo cambios en precios, no se inserta.")
                    return

            __data__["scraped_at"] = datetime.utcnow().strftime("%Y-%m-%d")
            scraped_products_collection.insert_one(__data__)
            self.logger.info(f"Producto {product_id} de {retailer} insertado en MongoDB Atlas")

        except Exception as e:
            self.logger.error(f"Error al cargar producto {product_id} de {retailer}: {e}", exc_info=True)
            self._store_error(e, product_id=product_id, retailer=retailer)
        finally:
            try:
                self.mongo_db.disconnect()
            except Exception as e:
                self.logger.warning(f"Error al desconectar de MongoDB: {e}")