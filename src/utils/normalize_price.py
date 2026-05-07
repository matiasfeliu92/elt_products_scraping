import re
import pandas as pd

class NormalizePrice:
    @staticmethod
    def execute(value):
        if value is None:
            return None

        if not isinstance(value, str) or isinstance(value, int) or isinstance(value, float):
            return value

        # Eliminar espacios
        value = value.strip()

        if value == "":
            return None

        if "$" in value:
            # Quitar símbolo $
            value = value.replace("$", "")

        if "." in value:
            # Quitar separadores de miles (.)
            value = value.replace(".", "")

        if "," in value:
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