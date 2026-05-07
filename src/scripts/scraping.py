import json
import random
import time
from selenium.webdriver.common.by import By

from src.config.logger import LoggerConfig
from src.config.scraping_settings import ScrapingSettings
from src.utils.extract_elements import ExtractElements
from src.utils.get_api_data import GetApiData
from src.utils.load_errors import LoadErrors


class Scraping:
    megatone_product_resume = None
    stock_megatone = None
    descripcion_megatone = None
    rating_product_megatone = None
    fravega_specifications = None
    megatone_specifications = None
    naldo_especifications = None
    cetrogar_specifications = None
    def __init__(self, __link__:str, __product_id__, __retailer__):
        self.link = __link__
        self.product_id = __product_id__
        self.retailer = __retailer__
        self.logger = LoggerConfig.get_logger(self.__class__.__name__)
        self.scraping_settings = ScrapingSettings()
        self.get_api_data = GetApiData()
        self.load_errors = LoadErrors()
        self.driver = self.scraping_settings.get_chrome_driver()
        self.extract_elements = ExtractElements(self.driver)
        self.product_data = {}

    def _store_error(self, error, field, path=None, by="SCRAPING"):
        self.load_errors.load(
            product_id=self.product_id,
            retailer=self.retailer,
            error_type=type(error).__name__,
            message=str(error),
            by=by,
            path=path or self.link,
            field=field
        )

    def run(self):
        if self.link is not None and "megatone.net" in self.link:
            self.logger.info("Iniciando extraccion para Megatone")
            self.logger.info(f"Accediendo al enlace: {self.link}")
            self.driver.get(self.link)
            time.sleep(random.uniform(2, 5))

            try:
                self.megatone_product_resume = self.driver.execute_script("return productoResumen")
            except Exception as e:
                self.logger.error(f"No se pudo obtener productoResumen: {e}")
                self._store_error(e, field="productoResumen", by="EXECUTE_SCRIPT")

            self.logger.info(f"productoResumen: {self.megatone_product_resume}")

            json_data_scripts = self.extract_elements.safe_find_elements(By.XPATH, self.scraping_settings.MEGATONE_SELECTORS["JSON_DATA"], "json_ld", self.product_id, self.retailer, multiple=True)
            for script in json_data_scripts:
                type_ = script.get_attribute("type") or ""
                if type_ == "application/ld+json":
                    try:
                        content = script.get_attribute("innerHTML")
                        data = json.loads(content)  # convertir string a dict

                        if "InStock" in content or "description" in content or "aggregateRating" in content:
                            self.logger.info(f"JSON-LD: {data}")
                            self.stock_megatone = True
                            self.descripcion_megatone = data.get("description", "")
                            self.logger.info(f"Descripción extraída del JSON-LD: {self.descripcion_megatone}")
                            self.rating_product_megatone = data.get("aggregateRating", {})
                            self.logger.info(f"Rating extraído del JSON-LD: {self.rating_product_megatone}")
                            specifications = data.get("additionalProperty", [])
                            # self.megatone_specifications = {
                            #     attr["name"]: attr["value"]
                            #     for attr in specifications````
                            # }
                            self.megatone_specifications = {}
                            for attr in specifications:
                                self.logger.info({"name": attr.get("name", ""), "value": attr.get("value", "")})
                                if "ancho" in attr.get("name", "") or "Ancho" in attr.get("name", ""):
                                    self.megatone_specifications[f"""__{attr.get("name", "")}"""] = attr.get("value", "")
                                else:
                                    self.megatone_specifications[attr.get("name", "")] = attr.get("value", "")
                            self.logger.info(f"Especificaciones formateadas: {self.megatone_specifications}")
                    except Exception as e:
                        self.logger.error(f"Error parseando JSON-LD: {e}")
                        self._store_error(e, field="json_ld", by="PARSE_JSON")


            product_title = self.megatone_product_resume.get("nombre", "") if self.megatone_product_resume else ""
            self.logger.info(f"PRODUCT TITLE EXTRAIDO DEL productoResumen: {product_title}")
            product_sku = self.megatone_product_resume.get("sku", "") if self.megatone_product_resume else ""
            self.logger.info(f"PRODUCT SKU EXTRAIDO DEL productoResumen: {product_sku}")
            brand = self.megatone_product_resume.get("marca", {}).get("descripcion", "") if self.megatone_product_resume else ""
            self.logger.info(f"BRAND EXTRAIDO DEL productoResumen: {brand}")
            self.logger.info(f"""CATEGORIAS EXTRAIDAS DEL productoResumen: {self.megatone_product_resume.get("categorias", [])}""")
            main_category = self.megatone_product_resume.get("categorias", [])[0].get("nombre", "") if len(self.megatone_product_resume.get("categorias", [])) > 0 else ""
            self.logger.info(f"MAIN CATEGORY EXTRAIDO DEL productoResumen: {main_category if main_category else 'No se pudo extraer la categoría principal'}")
            sub_category = self.megatone_product_resume.get("categorias", [])[1].get("nombre", "") if len(self.megatone_product_resume.get("categorias", [])) > 1 else ""
            self.logger.info(f"SUB CATEGORY EXTRAIDO DEL productoResumen: {sub_category if sub_category else 'No se pudo extraer la categoría secundaria'}")
            list_price = self.megatone_product_resume.get("precios", {}).get("web", {}).get("lista", None) if self.megatone_product_resume else None
            cash_price = self.megatone_product_resume.get("precios", {}).get("web", {}).get("promocional", None) if self.megatone_product_resume else None
            installments = self.megatone_product_resume.get("planes", {}).get("cuotasDestacadas", [])

            seen = set()
            installments_dict = {}

            if installments:
                for i, inst in enumerate(installments):
                    key_tuple = (
                        inst.get("cantidad", ""),
                        inst.get("leyenda", "")
                    )
                    if key_tuple not in seen:
                        seen.add(key_tuple)
                        installments_dict[f"Opcion {len(seen)}"] = {
                            "numberOfInstallments": key_tuple[0],
                            "interestRate": key_tuple[1]
                        }

            self.product_data["name"] = product_title
            self.product_data["sku"] = product_sku
            self.product_data["brand"] = brand
            self.product_data["main_category"] = main_category if main_category else ""
            self.product_data["sub_category"] = sub_category if sub_category else ""
            self.product_data["list_price"] = list_price if list_price else ""
            self.product_data["cash_price"] = cash_price if list_price != cash_price else ""
            self.product_data["installments"] = installments_dict
            self.product_data["stock"] = self.stock_megatone if self.stock_megatone is not None else None
            self.product_data["description"] = self.descripcion_megatone if self.descripcion_megatone else ""
            self.product_data["specifications"] = self.megatone_specifications if self.megatone_specifications else {}
            self.product_data["rating"] = self.rating_product_megatone if self.rating_product_megatone else {}
            self.product_data["store"] = "Megatone"
            self.product_data["link"] = self.link
            self.logger.info(f"------------PRODUCT DATA------------>{self.product_data}")
            self.logger.info(
                "---------------------------------------------------------------------------------------------------"
            )
            self.logger.info("")
            self.logger.info("")
            self.driver.quit()
            return self.product_data
        
        elif self.link is not None and "fravega.com" in self.link: ## GET a https://www.fravega.com/api/catalog_system/pub/products/search?fq=skuId:160752
            self.logger.info("Iniciando extraccion para Fravega")
            self.logger.info(f"Accediendo al enlace: {self.link}")
            self.driver.get(self.link)
            time.sleep(random.uniform(2, 5))

            splited_link = self.link.split("-")
            sku = splited_link[-1].replace("/", "") if len(splited_link)>1 else ""
            self.logger.info(f"SKU EXTRAIDO DEL LINK: {sku}")

            data = self.get_api_data.get(self.scraping_settings.FRAVEGA_API_URL.format(sku=sku))

            __next_data_script = self.extract_elements.safe_find_elements(By.XPATH, self.scraping_settings.FRAVEGA_SELECTORS["JSON_DATA"], "json_data_script", self.product_id, self.retailer)

            try:
                content = __next_data_script.get_attribute("innerHTML")
                self.logger.info(f"Contenido del script __NEXT_DATA__: {content[:500]}...")
                json_data = json.loads(content)
                root = json_data.get("props", {}).get("pageProps", {}).get("__APOLLO_STATE__", {})
                sku_key = f'sku({{"code":"{sku}"}})'
                self.fravega_specifications = {}
                specifications = (
                    root.get("ROOT_QUERY", {})
                        .get(sku_key, {})
                        .get("item", {})
                        .get('specifications({"tagged":["detailed"]})', [])
                )
                self.logger.info(f"Especificaciones extraídas del __NEXT_DATA__: {specifications}")
                for attr in specifications:
                    name = attr.get("name", "")
                    value = attr.get("value", "")
                    self.logger.info({"name": name, "value": value})
                    self.logger.info(f"ANTES DE ASIGNAR A DICCIONARIO")
                    key = f"__{name}" if "ancho" in name.lower() else name
                    self.logger.info(f"ANTES DE ASIGNAR A DICCIONARIO")
                    self.fravega_specifications[key] = value if value else ""
                    self.logger.info(f"DESPUÉS DE ASIGNAR A DICCIONARIO")
            except Exception as e:
                self.logger.error(f"Error parseando __NEXT_DATA__: {e}")
                self._store_error(e, field="__NEXT_DATA__", by="PARSE_JSON")

            product_title = data.get("productName", "") if data else ""
            self.logger.info(f"PRODUCT TITLE EXTRAIDO DEL JSON: {product_title}")
            product_sku = data.get("productId", "") if data else ""
            self.logger.info(f"PRODUCT SKU EXTRAIDO DEL JSON: {product_sku}")
            brand = data.get("brand", "") if data else ""
            self.logger.info(f"BRAND EXTRAIDO DEL JSON: {brand}")
            categories = data.get("categories", [])[0].split("/") if data and data.get("categories", []) else []
            main_category = categories[1] if len(categories)>1 else ""
            sub_category = categories[2] if len(categories)>2 else ""
            prices = data.get("items", [])[0].get("sellers", [])[0] if data and data.get("items", []) and data.get("items", [])[0].get("sellers", []) else {}
            list_price = prices.get("commertialOffer", {}).get("ListPrice", "") if prices else ""
            cash_price = prices.get("commertialOffer", {}).get("Price", "") if prices else ""
            stock = prices.get("commertialOffer", {}).get("IsAvailable", "") if prices else ""
            description = data.get("description", "") if data else ""
            self.logger.info("STOCK EXTRAIDO DEL JSON: {}".format(stock))
            installments = prices.get("commertialOffer", {}).get("Installments", []) if prices else []
            seen = set()
            installments_dict = {}

            if installments:
                for i, inst in enumerate(installments):
                    key_tuple = (
                        inst.get("NumberOfInstallments", ""),
                        inst.get("InterestRate", "")
                    )
                    if key_tuple not in seen:
                        seen.add(key_tuple)
                        installments_dict[f"Opcion {len(seen)}"] = {
                            "numberOfInstallments": key_tuple[0],
                            "interestRate": key_tuple[1]
                        }

            self.product_data["title"] = product_title if product_title else ""
            self.product_data["sku"] = product_sku if product_sku else ""
            self.product_data["brand"] = brand if brand else ""
            self.product_data["main_category"] = main_category if main_category else ""
            self.product_data["sub_category"] = sub_category if sub_category else ""
            self.product_data["list_price"] = list_price if list_price else ""
            self.product_data["cash_price"] = cash_price if list_price != cash_price else ""
            self.product_data["installments"] = installments_dict if installments_dict else {}
            self.product_data["stock"] = True if stock == "True" else False
            self.product_data["description"] = description if description else ""
            self.product_data["specifications"] = self.fravega_specifications if self.fravega_specifications else {}
            self.product_data["rating"] = {}
            self.product_data["store"] = "Fravega"
            self.product_data["link"] = self.link
            self.logger.info(f"------------PRODUCT DATA------------>{self.product_data}")
            self.logger.info(
                "---------------------------------------------------------------------------------------------------"
            )
            self.logger.info("")
            self.logger.info("")
            self.driver.quit()
            return self.product_data

        elif self.link is not None and "musimundo.com" in self.link:
            self.logger.info("Iniciando extraccion para Musimundo")
            self.logger.info(f"Accediendo al enlace: {self.link}")
            self.driver.get(self.link)
            time.sleep(random.uniform(2, 5))
            list_price = None
            cash_price = None
            stock = None
            installments_dict = None
            product_title = self.extract_elements.safe_find_elements(By.XPATH, self.scraping_settings.MUSIMUNDO_SELECTORS["PRODUCT_TITLE"], "product_title", self.product_id, self.retailer)
            product_sku = self.extract_elements.safe_find_elements(By.XPATH, self.scraping_settings.MUSIMUNDO_SELECTORS["SKU"], "product_sku", self.product_id, self.retailer)
            brand = self.extract_elements.safe_find_elements(By.XPATH, self.scraping_settings.MUSIMUNDO_SELECTORS["BRAND"], "product_brand",self.product_id, self.retailer)
            category_path_nav = self.extract_elements.safe_find_elements(By.CSS_SELECTOR, self.scraping_settings.MUSIMUNDO_SELECTORS["CATEGORY_PATH"], "category_paths", self.product_id, self.retailer, multiple=True)
            price_mostrado = self.extract_elements.safe_find_elements(By.CSS_SELECTOR, self.scraping_settings.MUSIMUNDO_SELECTORS["PRICE_MOSTRADO"], "price_mostrado", self.product_id, self.retailer)
            price_tachado = self.extract_elements.safe_find_elements(By.CSS_SELECTOR, self.scraping_settings.MUSIMUNDO_SELECTORS["PRICE_TACHADO"], "price_tachado", self.product_id, self.retailer)
            installments = self.extract_elements.safe_find_elements(By.CSS_SELECTOR, self.scraping_settings.MUSIMUNDO_SELECTORS["INSTALLMENTS"], "installments", self.product_id, self.retailer, multiple=True)
            button_ad_to_cart = self.extract_elements.safe_find_elements(By.ID, self.scraping_settings.MUSIMUNDO_SELECTORS["BUTTON_ADD_TO_CART"], self.product_id, self.retailer)
            
            category_path_links_text = [link.find_element(By.TAG_NAME, "a").text for link in category_path_nav if link.get_attribute("data-test-breadcrumbs") == "breadcrumb"] if category_path_nav and len(category_path_nav) else []

            if price_tachado and price_mostrado:
                list_price = price_tachado
                cash_price = price_mostrado
            elif price_mostrado and not price_tachado:
                list_price = price_mostrado
                cash_price = None

            if installments:
                installment_text = [installment.text for installment in installments if "cuotas" in installment.text]
                installments_dict = {f"Opcion {i+1}": cuota for i, cuota in enumerate(installment_text)}

            if button_ad_to_cart:
                stock = True
            else:
                stock = False

            self.product_data["name"] = product_title.text if product_title else ""
            self.product_data["sku"] = product_sku.text if product_sku else ""
            self.product_data["brand"] = brand.text if brand else ""
            self.product_data["main_category"] = category_path_links_text[0] if len(category_path_links_text)>0 else ""
            self.product_data["sub_category"] = category_path_links_text[1] if len(category_path_links_text)>1 else ""
            self.product_data["list_price"] = list_price.text if list_price else ""
            self.product_data["cash_price"] = cash_price.text if cash_price else ""
            self.product_data["installments"] = installments_dict
            self.product_data["stock"] = stock
            self.product_data["store"] = "Musimundo"
            self.product_data["link"] = self.link
            self.logger.info(f"------------PRODUCT DATA------------>{self.product_data}")
            self.logger.info(
                "---------------------------------------------------------------------------------------------------"
            )
            self.logger.info("")
            self.logger.info("")
            return self.product_data
        
        elif self.link is not None and "naldo.com.ar" in self.link: ## GET a https://www.naldo.com.ar/api/catalog_system/pub/products/search?fq=skuId:{sku}
            self.logger.info("Iniciando extraccion para Naldo")

            sku_ = self.link.split("/")
            self.logger.info(f"SKU SPLITEADO EXTRAIDO DEL LINK: {sku_}")
            sku = sku_[-1].split('=')[-1]
            self.logger.info(f"SKU EXTRAIDO DEL LINK: {sku}")
            api_link = self.scraping_settings.NALDO_API_URL.format(sku=sku)
            self.logger.info(f"API LINK GENERADO: {api_link}")
            data = self.get_api_data.get(api_link)

            product_title = data.get("productName", "") if data else ""
            self.logger.info(f"PRODUCT TITLE EXTRAIDO DEL JSON: {product_title}")
            product_sku = data.get("productId", "") if data else ""
            self.logger.info(f"PRODUCT SKU EXTRAIDO DEL JSON: {product_sku}")
            brand = data.get("brand", "") if data else ""
            self.logger.info(f"BRAND EXTRAIDO DEL JSON: {brand}")
            categories = data.get("categories", [])[0].split("/") if data and data.get("categories", []) else []
            self.logger.info(f"CATEGORIES: {categories}")
            main_category = categories[1] if len(categories)>1 else ""
            self.logger.info(f"MAIN CATEGORY EXTRAIDO DEL JSON: {main_category}")
            sub_category = categories[2] if len(categories)>2 else ""
            self.logger.info(f"SUB CATEGORY EXTRAIDO DEL JSON: {sub_category}")
            prices = data.get("items", [])[0].get("sellers", [])[0] if data and data.get("items", []) and data.get("items", [])[0].get("sellers", []) else {}
            self.logger.info(f"PRICES: {prices}")
            list_price = prices.get("commertialOffer", {}).get("ListPrice", "") if prices else ""
            self.logger.info(f"LIST PRICE EXTRAIDO DEL JSON: {list_price}")
            cash_price = prices.get("commertialOffer", {}).get("Price", "") if prices else ""
            self.logger.info(f"CASH PRICE EXTRAIDO DEL JSON: {cash_price}")
            stock = prices.get("commertialOffer", {}).get("IsAvailable", "") if prices else ""
            self.logger.info("STOCK EXTRAIDO DEL JSON: {}".format(stock))
            description = data.get("description", "") if data else ""
            self.logger.info(f"DESCRIPTION EXTRAIDO DEL JSON: {description}")
            specifications = data.get("Especificaciones de Producto", []) if data.get("Especificaciones de Producto", []) else []
            self.logger.info(f"ESPECIFICACIONES DE PRODUCTO EXTRAIDO DEL JSON: {specifications}")
            self.logger.info(f"LISTA DE LAS ESPECIFICACIONES DEL PRODUCTO EXTRAIDO DEL JSON: {specifications}")
            self.naldo_especifications = {}
            if len(specifications) > 0:
                for spec in specifications:
                    self.logger.info({"name": spec, "value": data.get(spec, [])})
                    if "ancho" in spec or "Ancho" in spec:
                        self.naldo_especifications[f"__{spec}"] = data.get(spec, [])[0] if data.get(spec, []) else ""
                    else:
                        self.naldo_especifications[spec] = data.get(spec, [])[0] if data.get(spec, []) else ""
            self.logger.info(f"Especificaciones formateadas: {self.naldo_especifications}")
            installments = prices.get("commertialOffer", {}).get("Installments", []) if prices else []
            seen = set()
            installments_dict = {}

            if installments:
                for i, inst in enumerate(installments):
                    key_tuple = (
                        inst.get("NumberOfInstallments", ""),
                        inst.get("InterestRate", "")
                    )
                    if key_tuple not in seen:
                        seen.add(key_tuple)
                        installments_dict[f"Opcion {len(seen)}"] = {
                            "numberOfInstallments": key_tuple[0],
                            "interestRate": key_tuple[1]
                        }

            self.product_data["name"] = product_title
            self.product_data["sku"] = product_sku
            self.product_data["brand"] = brand
            self.product_data["main_category"] = main_category
            self.product_data["sub_category"] = sub_category
            self.product_data["list_price"] = list_price
            self.product_data["cash_price"] = cash_price if list_price != cash_price else ""
            self.product_data["installments"] = installments_dict if installments_dict else {}
            self.product_data["stock"] = True if stock == True else False
            self.product_data["description"] = description if description else ""
            self.product_data["specifications"] = self.naldo_especifications if self.naldo_especifications else {}
            self.product_data["rating"] = {}
            self.product_data["store"] = "Naldo"
            self.product_data["link"] = self.link
            self.logger.info(f"------------PRODUCT DATA------------>{self.product_data}")
            self.logger.info(
                "---------------------------------------------------------------------------------------------------"
            )
            self.logger.info("")
            self.logger.info("")
            self.driver.quit()
            return self.product_data

        elif self.link is not None and "cetrogar.com.ar" in self.link: ## GET a https://www.cetrogar.com.ar/api/catalog_system/pub/products/search?fq=skuId:1958
            self.logger.info("Iniciando extraccion para Cetrogar")
            self.logger.info(f"Accediendo al enlace: {self.link}")
            sku = self.link.split("-")
            self.logger.info(f"SKU SPLITEADO EXTRAIDO DEL LINK: {sku[-1]}")
            sku = sku[-1].split('=')[-1].replace("/p", "") if len(sku)>1 else ""
            self.logger.info(f"SKU EXTRAIDO DEL LINK: {sku}")
            api_link = self.scraping_settings.CETROGAR_API_URL.format(sku=sku)
            self.logger.info(f"API LINK GENERADO: {api_link}")
            data = self.get_api_data.get(api_link)

            product_title = data.get("productName", "") if data else ""
            self.logger.info(f"PRODUCT TITLE EXTRAIDO DEL JSON: {product_title}")
            product_sku = data.get("productId", "") if data else ""
            self.logger.info(f"PRODUCT SKU EXTRAIDO DEL JSON: {product_sku}")
            brand = data.get("brand", "") if data else ""
            self.logger.info(f"BRAND EXTRAIDO DEL JSON: {brand}")
            categories = data.get("categories", [])[0].split("/") if data and data.get("categories", []) else []
            self.logger.info(f"CATEGORIES: {categories}")
            main_category = categories[1] if len(categories)>1 else ""
            self.logger.info(f"MAIN CATEGORY EXTRAIDO DEL JSON: {main_category}")
            sub_category = categories[2] if len(categories)>2 else ""
            self.logger.info(f"SUB CATEGORY EXTRAIDO DEL JSON: {sub_category}")
            prices = data.get("items", [])[0].get("sellers", [])[0] if data and data.get("items", []) and data.get("items", [])[0].get("sellers", []) else {}
            list_price = prices.get("commertialOffer", {}).get("ListPrice", "") if prices else ""
            self.logger.info(f"LIST PRICE EXTRAIDO DEL JSON: {list_price}")
            cash_price = prices.get("commertialOffer", {}).get("Price", "") if prices else ""
            self.logger.info(f"CASH PRICE EXTRAIDO DEL JSON: {cash_price}")
            stock = prices.get("commertialOffer", {}).get("IsAvailable", "") if prices else ""
            self.logger.info(f"STOCK EXTRAIDO DEL JSON: {stock}")
            description = data.get("description", "") if data else ""
            self.logger.info(f"DESCRIPTION EXTRAIDO DEL JSON: {description}")
            specifications = data.get("Características generales", [])+data.get("Especificaciones técnicas", []) if data.get("Características generales", []) and data.get("Especificaciones técnicas", []) else []
            self.logger.info(f"LISTA DE LAS ESPECIFICACIONES DEL PRODUCTO EXTRAIDO DEL JSON: {specifications}")
            self.cetrogar_specifications = {}
            if len(specifications) > 0:
                for spec in specifications:
                    self.logger.info({"name": spec, "value": data.get(spec, [])})
                    if "ancho" in spec or "Ancho" in spec:
                        self.cetrogar_specifications[f"__{spec}"] = data.get(spec, [])[0] if data.get(spec, []) else ""
                    else:
                        self.cetrogar_specifications[spec] = data.get(spec, [])[0] if data.get(spec, []) else ""
            self.logger.info(f"Especificaciones formateadas: {self.cetrogar_specifications}")
            self.logger.info("STOCK EXTRAIDO DEL JSON: {}".format(stock))
            installments = prices.get("commertialOffer", {}).get("Installments", []) if prices else []
            seen = set()
            installments_dict = {}

            if installments:
                for i, inst in enumerate(installments):
                    key_tuple = (
                        inst.get("NumberOfInstallments", ""),
                        inst.get("InterestRate", "")
                    )
                    if key_tuple not in seen:
                        seen.add(key_tuple)
                        installments_dict[f"Opcion {len(seen)}"] = {
                            "numberOfInstallments": key_tuple[0],
                            "interestRate": key_tuple[1]
                        }

            self.product_data["name"] = product_title
            self.product_data["sku"] = product_sku
            self.product_data["brand"] = brand
            self.product_data["main_category"] = main_category
            self.product_data["sub_category"] = sub_category
            self.product_data["main_category"] = main_category
            self.product_data["sub_category"] = sub_category
            self.product_data["list_price"] = list_price
            self.product_data["cash_price"] = cash_price if list_price != cash_price else ""
            self.product_data["installments"] = installments_dict if installments_dict else {}
            self.product_data["stock"] = True if stock == True else False
            self.product_data["description"] = description if description else ""
            self.product_data["specifications"] = self.cetrogar_specifications if self.cetrogar_specifications else {}
            self.product_data["rating"] = {}
            self.product_data["store"] = "Cetrogar"
            self.product_data["link"] = self.link
            self.logger.info(f"------------PRODUCT DATA------------>{self.product_data}")
            self.logger.info(
                "---------------------------------------------------------------------------------------------------"
            )
            self.logger.info("")
            self.logger.info("")
            self.driver.quit()
            return self.product_data

        else:
            return {}