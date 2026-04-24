import logging
import platform
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

class ScrapingSettings:
    def __init__(self):
        self.USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
        self.INPUTS_DIR = "C:\Documentos\data_projects\inputs_for_pipelines"
        self.MEGATONE_SELECTORS = {
            "PRODUCT_TITLE": "/html/body/main/section/div[1]/section[3]/h1",
            "SKU": "/html/body/main/section/div[1]/section[2]/div[1]",
            "BRAND": '/html/body/main/section/div[1]/section[1]/nav/a[5]',
            "CATEGORY_PATH": "/html/body/main/section/div[1]/section[1]/nav",
            "PRICE_MOSTRADO": "//div[contains(@class, 'Mostrado')]",
            "PRICE_TACHADO": "//div[contains(@class, 'Tachado')]",
            "PRICE_1_PAGO": "/html/body/main/section/div[1]/section[7]/div[3]/p/span[2]",
            "INSTALLMENTS": "div.DestacadasPlanes > div.destacadas > div.destacada",
            "SIN_STOCK": "//div[contains(@class, 'Agotado')]",
            "CON_STOCK": "//span[contains(@class, 'LeyendaStock')]",
            "DESCRIPTION": "//div[contains(@class, 'Descripcion')]//article//p"
        }
        self.FRAVEGA_SELECTORS = {
            "PRODUCTO_NO_DISPONIBLE": '//*[@id="__next"]/div[2]/div[2]/div[3]/div[2]/section/p/b',
            "PRODUCT_TITLE": '//*[@id="__next"]/div[2]/div[2]/div[3]/div[2]/div/div[2]/h1',
            "SKU": '//*[@id="__next"]/div[2]/div[2]/div[5]/div[1]/div/div[1]/div/p[2]',
            "BRAND": '//*[@id="__next"]/div[2]/div[2]/div[5]/div[1]/div/div[1]/div/a',
            "CATEGORY_PATH": "div li a span",
            "PRICE_MOSTRADO": '//*[@id="__next"]/div[2]/div[2]/div[3]/div[2]/div/div[2]/div[2]/span',
            "PRICE_TACHADO": '//*[@id="__next"]/div[2]/div[2]/div[3]/div[2]/div/div[2]/div[2]/div/div/span[1]',
            "INSTALLMENTS": "b[class*='sc-']",
            "SIN_STOCK": "",
            "CON_STOCK": "",
            "DESCRIPTION": ""
        }
        self.MUSIMUNDO_SELECTORS = {
            "PRODUCT_TITLE": "//p[contains(@class, 'product-details-panel__name')]",
            "SKU": "//p[contains(@class, 'product-details-panel__code')]",
            "BRAND": '//*[@id="product_brand"]/span',
            "CATEGORY_PATH": "ul.clearfix li",
            "PRICE_MOSTRADO": "div.product-price-panel-pdp__price",
            "PRICE_TACHADO": "div.product-price-panel-pdp__old-price",
            "INSTALLMENTS": "div.installment-value-pdp > span",
            "BUTTON_ADD_TO_CART": "addToCartButton",
            "DESCRIPTION": ""
        }
        self.NALDO_SELECTORS = {
            "PRODUCT_TITLE": "h1 span",
            "SKU": "span.vtex-product-identifier-0-x-product-identifier__value",
            "BRAND": "//span[contains(@class, 'productBrandName')]",
            "CATEGORY_PATH": "//span[contains(@class, 'breadcrumb')]//a",
            "PRICE_MOSTRADO": "//span[contains(@class, 'sellingPriceValue')]",
            "PRICE_TACHADO": "//span[contains(@class, 'listPriceValue')]", ##listPriceValue
            "INSTALLMENTS": "//p[contains(@class, 'cuotasNumber')]", ##cuotasNumber
            "BUTTON_ADD_TO_CART": "",
            "DESCRIPTION": ""
        }
        
    def get_chrome_driver(self):
        options = Options()
        options.add_argument("--headless")
        options.add_argument("--disable-gpu")
        options.add_argument("--window-size=1920,1080")
        options.add_argument(f"--user-agent={self.USER_AGENT}")

        if platform.system() == "Windows":
            service = Service(ChromeDriverManager().install())
            return webdriver.Chrome(service=service, options=options)

        options.binary_location = "/usr/bin/chromium"
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")

        service = Service("/usr/bin/chromedriver")
        return webdriver.Chrome(service=service, options=options)