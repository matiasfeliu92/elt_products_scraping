from pymongo import MongoClient
from pymongo.errors import ConnectionFailure

from src.config.settings import Settings

class MongoDB:
    def __init__(self):
        self.settings = Settings()
        self.mongo_db_uri = self.settings.MONGO_DB_URI
        self.client = None
        self.db = None

    def connect(self, db_name: str):
        """Conecta a MongoDB Atlas usando la URI configurada"""
        try:
            self.client = MongoClient(self.mongo_db_uri)
            self.client.admin.command('ping')
            self.db = self.client[db_name]
            print(f"Conectado a MongoDB Atlas - Base de datos: {db_name}")
            return self.db
        except ConnectionFailure as e:
            print(f"Error al conectar a MongoDB: {e}")
            raise

    def disconnect(self):
        """Desconecta de MongoDB"""
        if self.client:
            self.client.close()
            print("Desconectado de MongoDB")

    def get_database(self):
        """Retorna la base de datos actual"""
        return self.db