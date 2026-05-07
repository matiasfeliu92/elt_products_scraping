import os
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

from src.config.logger import LoggerConfig
from src.utils.load_errors import LoadErrors

class GoogleSheetsHandler:
    product_catalog_gsheet = None
    def __init__(self):
        self.logger = LoggerConfig.get_logger(self.__class__.__name__)
        self.load_errors = LoadErrors()

    def _store_error(self, error, field, path=None):
        self.load_errors.load(
            product_id=None,
            retailer=None,
            error_type=type(error).__name__,
            message=str(error),
            by="GOOGLE_SHEETS",
            path=path,
            field=field
        )

    def read(self, google_sheet_credentials, google_scopes): 
        sheet_url = "https://docs.google.com/spreadsheets/d/1HWSNVwLffxLLnYf45-2QqF8br_qzkkzupd56h3RIMnU/edit"
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
            spreadsheet = client.open_by_url(sheet_url) 
            worksheet = spreadsheet.sheet1 
            data = worksheet.get_all_records() 
            self.product_catalog_gsheet = pd.DataFrame(data)
            self.logger.info("Product Catalog was load succesfully")
            return self.product_catalog_gsheet 
        except FileNotFoundError as e: 
            self.logger.error(f"Credenciales no encontradas: {e}") 
            self._store_error(e, field="google_credentials", path=os.fspath(google_sheet_credentials))
        except gspread.exceptions.SpreadsheetNotFound as e: 
            self.logger.error(f"No se encontró la hoja de cálculo: {e}") 
            self._store_error(e, field="google_spreadsheet", path=sheet_url)
        except Exception as e: 
            self.logger.error(f"Error inesperado al leer Google Sheets: {e}") 
            self._store_error(e, field="google_sheet_read", path=sheet_url)
        return None

    
google_sheets_handler = GoogleSheetsHandler()