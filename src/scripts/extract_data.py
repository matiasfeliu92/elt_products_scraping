from datetime import datetime

from src.scripts.load_data import LoadData
from src.config.logger import LoggerConfig
from src.scripts.scraping import Scraping
from src.config.settings import Settings
from src.utils.load_errors import LoadErrors

class ExtractData:
    engine = None
    product_catalog_query = None
    product_catalog_links = None
    def __init__(self):
        self.settings = Settings()
        self.logger = LoggerConfig.get_logger(self.__class__.__name__)
        self.all_products_data = []
        self.retailers = self.settings.RETAILERS
        self.load_data = LoadData()
        self.load_errors = LoadErrors()

    def _store_error(self, error, retailer=None, product_id=None, field="extract_data", path=None, by="PIPELINE"):
        self.load_errors.load(
            product_id=product_id,
            retailer=retailer,
            error_type=type(error).__name__,
            message=str(error),
            by=by,
            path=path,
            field=field
        )

    def extract(self, input_product_catalog, retailer):
        current_product_id = None
        current_retailer = retailer
        self.logger.info(input_product_catalog.head())
        try:         
            self.logger.info(f"Extraction process for retailer {retailer} will start now")
            input_product_catalog = input_product_catalog[
                (input_product_catalog["retailer"] == retailer) &
                (input_product_catalog["is_active"].astype(str).str.upper() == "TRUE")
            ] if retailer else input_product_catalog[
                input_product_catalog["is_active"].astype(str).str.upper() == "TRUE"
            ]
            self.logger.info(f"Total products to extract: {len(input_product_catalog)}")
            for _, row in input_product_catalog.iterrows():
                try:
                    scraped_at = datetime.now().strftime('%Y-%m-%d')
                    product_id = row["product_id"]
                    retailer = row["retailer"]
                    current_product_id = product_id
                    current_retailer = retailer
                    link = row["link"]
                    scraper = Scraping(link, product_id, retailer)
                    product_data = scraper.run()
                    print(product_data)
                    product_data_formatted = {
                        "scraped_at": scraped_at,
                        "product_id": product_id,
                        "retailer": retailer,
                        "data": product_data
                    }
                    self.load_data.load(product_data_formatted)
                    self.logger.info("Extraction process run successfuly")
                except Exception as e:
                    self.logger.error(f"Error extracting product {product_id}: {str(e)}")
                    self._store_error(e, retailer=retailer, product_id=product_id, field="extracting_product", path=link, by="EXTRACTION")
                    continue
        except Exception as e:
            self.logger.error(f"Error in extract method: {str(e)}")
            self._store_error(e, retailer=current_retailer, product_id=current_product_id, field="extract_method", by="PIPELINE")
            raise