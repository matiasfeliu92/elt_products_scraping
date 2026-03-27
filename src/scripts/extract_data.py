from datetime import datetime

from src.config.logger import LoggerConfig
from src.scripts.scraping import Scraping
from src.config.settings import Settings

class ExtractData:
    engine = None
    product_catalog_query = None
    product_catalog_links = None
    def __init__(self):
        self.settings = Settings()
        self.logger = LoggerConfig.get_logger(self.__class__.__name__)
        self.all_products_data = []
        self.retailers = self.settings.RETAILERS

    def extract(self, input_product_catalog, retailer):
        try:         
            self.logger.info(f"Scraping process for retailer {retailer} will start now")
            input_product_catalog = input_product_catalog[input_product_catalog["retailer"] == retailer] if retailer else input_product_catalog
            for _, row in input_product_catalog.iterrows():
                try:
                    scraped_at = datetime.now().strftime('%Y-%m-%d')
                    product_id = row["product_id"]
                    retailer = row["retailer"]
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
                    self.logger.info("Scraping process run successfuly")
                except Exception as e:
                    self.logger.error(f"Error scraping product {product_id}: {str(e)}")
                    continue
        except Exception as e:
            self.logger.error(f"Error in extract method: {str(e)}")
            raise