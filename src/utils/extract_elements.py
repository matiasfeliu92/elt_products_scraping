from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, StaleElementReferenceException, ElementNotVisibleException, ElementNotInteractableException

from src.config.mongo_db import MongoDB
from src.config.logger import LoggerConfig
from src.utils.load_errors import LoadErrors

class ExtractElements:
    error_logs_collection = None
    def __init__(self, __driver__):
        self.driver = __driver__
        self.logger = LoggerConfig.get_logger(self.__class__.__name__)
        self.load_errors = LoadErrors()

    def safe_find_elements(self, by, path, field=None, product_id=None, retailer=None, multiple=False, timeout=20):
        try:
            wait = WebDriverWait(self.driver, timeout)
            wait.until(EC.visibility_of_element_located((by, path)))
            if multiple:
                self.logger.info("MULTIPLE")
                elements = self.driver.find_elements(by, path)
                return elements if elements else []
            else:
                self.logger.info("ELEMENT")
                element = self.driver.find_element(by, path)
                return element if element else None
        except TimeoutException as e:
            self.logger.error( f"[TimeoutException] {str(e)} | field={field} | by={by} | path={path} | product_id={product_id} | retailer={retailer}" )
            self.load_errors.load(
                product_id=product_id,
                retailer=retailer,
                error_type="TimeoutException",
                message=str(e),
                by=by,
                path=path,
                field=field
            )
            return None
        except NoSuchElementException as e:
            self.logger.error( f"[NoSuchElementException] {str(e)} | field={field} | by={by} | path={path} | product_id={product_id} | retailer={retailer}" )
            self.load_errors.load(
                product_id=product_id,
                retailer=retailer,
                error_type="NoSuchElementException",
                message=str(e),
                by=by,
                path=path,
                field=field
            )
            return None
        except StaleElementReferenceException as e:
            self.logger.error( f"[StaleElementReferenceException] {str(e)} | field={field} | by={by} | path={path} | product_id={product_id} | retailer={retailer}" )
            self.load_errors.load(
                product_id=product_id,
                retailer=retailer,
                error_type="StaleElementReferenceException",
                message=str(e),
                by=by,
                path=path,
                field=field
            )
            return None
        except ElementNotVisibleException as e:
            self.logger.error( f"[ElementNotVisibleException] {str(e)} | field={field} | by={by} | path={path} | product_id={product_id} | retailer={retailer}" )
            self.load_errors.load(
                product_id=product_id,
                retailer=retailer,
                error_type="ElementNotVisibleException",
                message=str(e),
                by=by,
                path=path,
                field=field
            )
            return None
        except ElementNotInteractableException as e:
            self.logger.error( f"[ElementNotInteractableException] {str(e)} | field={field} | by={by} | path={path} | product_id={product_id} | retailer={retailer}" )
            self.load_errors.load(
                product_id=product_id,
                retailer=retailer,
                error_type="ElementNotInteractableException",
                message=str(e),
                by=by,
                path=path,
                field=field
            )
            return None
        except Exception as e:
            self.logger.error( f"[Exception] {str(e)} | field={field} | by={by} | path={path} | product_id={product_id} | retailer={retailer}" )
            self.load_errors.load(
                product_id=product_id,
                retailer=retailer,
                error_type="Exception",
                message=str(e),
                by=by,
                path=path,
                field=field
            )
            return None