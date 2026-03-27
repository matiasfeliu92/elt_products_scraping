import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    BASE_DIR = os.getcwd()
    GOOGLE_CREDENTIALS = os.path.join(BASE_DIR, os.getenv("GOOGLE_CREDENTIALS"))
    GOOGLE_SCOPES = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    RETAILERS = ["Fravega", "Musimundo", "Megatone", "Naldo"]
    STOCK_CONFIG = {
        "Electrodomesticos": {
            "Lavarropas": (1, 8),   # Alta rotación, stock limitado
            "Heladeras": (1, 6),    # Stock crítico frecuente
            "Cocinas": (2, 10),
            "Microondas": (5, 15),
            "Aires Acondicionados": (2, 12)
        },
        "Tecnologia": {
            "Celulares": (10, 30),  # Mucho movimiento, stock más alto
            "Tv": (5, 20)           # Stock intermedio
        },
        "Audio": {
            "Parlantes": (8, 25)
        },
        "Cuidado Personal": {
            "Depiladoras": (15, 40) # Generalmente hay mucho stock
        }
    }

    @classmethod 
    def get_dir(cls, *args) -> str: 
        path = cls.BASE_DIR 
        for value in args: 
            path = os.path.join(path, value) 
        return path
    
    @classmethod
    def create_dir(cls, *args):
        print(f"DIR PATHS ----> {args}")
        base_dir = cls.BASE_DIR
        new_path = '\\'.join(args)
        new_dir = os.path.join(base_dir, new_path)
        print(f"NEW DIR ------> {new_dir}")
        os.makedirs(new_dir, exist_ok=True)
        return new_dir