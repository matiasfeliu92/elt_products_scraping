from datetime import datetime

from src.config.logger import LoggerConfig
from src.config.settings import Settings
from src.config.mongo_db import MongoDB

class LoadErrors:
    def __init__(self):
        self.logger = LoggerConfig.get_logger(self.__class__.__name__)
        self.settings = Settings()
        self.mongo_db = MongoDB()
        self.mongo_db_uri = self.settings.MONGO_DB_URI
    
    def load(self, product_id, retailer, error_type, message, by, path, field):
        try:
            error_log = {
                "product_id": product_id,
                "retailer": retailer,
                "error_type": error_type,
                "message": message,
                "by": by,
                "path": path,
                "field": field,
                "timestamp": datetime.now().strftime("%Y-%m-%d")
            }
            self.mongo_db.connect(self.mongo_db_uri, db_name="products")
            error_logs_collection = self.mongo_db.get_database()["error_logs"]
            error_logs_collection.insert_one(error_log)
        except Exception as e:
            self.logger.error(f"Error al cargar el log: {e}", exc_info=True)
        finally:
            try:
                self.mongo_db.disconnect()
            except Exception as e:
                self.logger.warning(f"Error al desconectar de MongoDB: {e}")