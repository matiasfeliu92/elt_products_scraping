import os
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

from src.config.logger import LoggerConfig

class GoogleSheetsHandler:
    product_catalog_gsheet = None
    def __init__(self):
        self.logger = LoggerConfig.get_logger(self.__class__.__name__)

    def read(self, google_sheet_credentials, google_scopes): 
        try: 
            # Si google_sheet_credentials es un dict, usar from_service_account_info
            if isinstance(google_sheet_credentials, dict):
                creds = Credentials.from_service_account_info(
                    google_sheet_credentials, scopes=google_scopes
                )
            else:
                # Si es un path a archivo .json, usar from_service_account_file
                creds = Credentials.from_service_account_file(
                    google_sheet_credentials, scopes=google_scopes
                )
            client = gspread.authorize(creds) 
            sheet_url = "https://docs.google.com/spreadsheets/d/1HWSNVwLffxLLnYf45-2QqF8br_qzkkzupd56h3RIMnU/edit"
            spreadsheet = client.open_by_url(sheet_url) 
            worksheet = spreadsheet.sheet1 
            data = worksheet.get_all_records() 
            self.product_catalog_gsheet = pd.DataFrame(data)
            self.logger.info("Product Catalog was load succesfully")
            return self.product_catalog_gsheet 
        except FileNotFoundError as e: 
            self.logger.error(f"Credenciales no encontradas: {e}") 
        except gspread.exceptions.SpreadsheetNotFound as e: 
            self.logger.error(f"No se encontró la hoja de cálculo: {e}") 
        except Exception as e: 
            self.logger.error(f"Error inesperado al leer Google Sheets: {e}") 
        return None

    
google_sheets_handler = GoogleSheetsHandler()