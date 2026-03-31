import re
import pandas as pd

class NormalizePrice:
    @staticmethod
    def execute(value):
        if value is None:
            return None

        if not isinstance(value, str):
            return None

        # Eliminar espacios
        value = value.strip()

        if value == "":
            return None

        # Quitar símbolo $
        value = value.replace("$", "")

        # Quitar separadores de miles (.)
        value = value.replace(".", "")

        # Reemplazar coma decimal por punto
        value = value.replace(",", ".")

        try:
            number = float(value)

            # Validación > 0
            if number > 0:
                return number
            else:
                return None
        except ValueError:
            return None