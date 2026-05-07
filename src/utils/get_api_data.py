import json
import requests

from src.config.logger import LoggerConfig
from src.utils.load_errors import LoadErrors

class GetApiData:
    def __init__(self):
        self.logger = LoggerConfig.get_logger(self.__class__.__name__)
        self.load_errors = LoadErrors()
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

    def _store_error(self, error, field, link=None, retailer=None):
        self.load_errors.load(
            product_id=None,
            retailer=retailer,
            error_type=type(error).__name__,
            message=str(error),
            by="API_REQUEST",
            path=link,
            field=field
        )

    def get(self, link=None):
        try:
            if not link:
                self.logger.error("No se proporcionó un enlace para obtener datos de la API.")
                return None
            # Timeout de 10 segundos para evitar que el script se cuelgue
            response = requests.get(link, headers=self.headers, timeout=10)
            
            # Lanza una excepción si el status_code es 4xx o 5xx
            response.raise_for_status()
            
            data = response.json()
            self.logger.info(f"TYPE OF DATA OBTAINED FROM API: {type(data)}")
            if not data:
                self.logger.error(f"No es posible obtener datos de la API para el enlace: {link}")
                return None
            # self.logger.info(f"DATA OBTAINED FROM API: {data}" if "cetrogar" in link else f"")
            if "naldo" in link or "cetrogar" in link or "fravega" in link:
                if isinstance(data, list) and len(data) > 0 and isinstance(data[0], dict):
                    data = data[0]
                else:
                    self.logger.error("Unexpected Naldo API response format")
                    return None
                # self.logger.info(f"DATA OBTAINED FROM NALDO API: {data}")
            return data

        except requests.exceptions.HTTPError as http_err:
            self.logger.error(f"Error HTTP ocurrido: {http_err}")
            self._store_error(http_err, field="api_http_error", link=link)
        except requests.exceptions.ConnectionError:
            error = requests.exceptions.ConnectionError("Verifica tu internet o si el sitio bloqueó la IP.")
            self.logger.error("Error de conexión: Verifica tu internet o si el sitio bloqueó la IP.")
            self._store_error(error, field="api_connection_error", link=link)
        except requests.exceptions.Timeout:
            error = requests.exceptions.Timeout("La petición excedió el tiempo de espera.")
            self.logger.error("Error: La petición excedió el tiempo de espera.")
            self._store_error(error, field="api_timeout", link=link)
        except json.JSONDecodeError:
            error = json.JSONDecodeError("La respuesta del servidor no es un JSON válido.", doc="", pos=0)
            self.logger.error("Error: La respuesta del servidor no es un JSON válido.")
            self._store_error(error, field="api_invalid_json", link=link)
        except Exception as err:
            self.logger.error(f"Ocurrió un error inesperado: {err}")
            self._store_error(err, field="api_unexpected_error", link=link)
        
        return None