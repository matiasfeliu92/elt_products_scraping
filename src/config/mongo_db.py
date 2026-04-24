from pymongo import MongoClient
from pymongo.errors import ConnectionFailure

class MongoDB:
    def __init__(self):
        self.client = None
        self.db = None

    def connect(self, mongo_db_uri, db_name: str):
        """Conecta a MongoDB Atlas usando la URI configurada"""
        try:
            self.client = MongoClient(mongo_db_uri)
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
    
mongo_db = MongoDB()