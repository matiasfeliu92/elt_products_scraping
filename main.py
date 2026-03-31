import os
from shutil import rmtree

from src.config.settings import Settings
from src.scripts.extract_data import ExtractData
from src.config.logger import LoggerConfig
from src.utils.google_sheet import GoogleSheetsHandler
from src.utils.load_to_databricks_file_store import LoadToDatabricksFileStore

class Main:
    def __init__(self, retailer):
        self.logger = LoggerConfig.get_logger(self.__class__.__name__)
        self.google_sheets_handler = GoogleSheetsHandler()
        self.extract_data = ExtractData()
        self.settings = Settings()
        self.retailer = retailer

    def run(self):
        input_product_catalog = self.google_sheets_handler.read()
        self.logger.info("Product Catalog from Google Sheets:")
        self.logger.info(f"\n{input_product_catalog.head()}")
        self.logger.info(f"Total products loaded: {len(input_product_catalog)}")
        self.extract_data.extract(input_product_catalog, retailer=self.retailer)