UNIT_MAP: dict[str, str] = {
    # Weight
    "milligrams": "mg",
    "milligram": "mg",
    "mg": "mg",
    "grams": "g",
    "gram": "g",
    "g": "g",
    "micrograms": "µg",
    "microgram": "µg",
    "mcg": "µg",        # mcg → µg  (per spec)
    "ug": "µg",
    "µg": "µg",
    "μg": "µg",
    "kilograms": "kg",
    "kg": "kg",

    # Energy
    "kcal": "kcal",
    "calories": "kcal",
    "calorie": "kcal",
    "cal": "kcal",
    "kj": "kJ",
    "kilojoules": "kJ",
    "kilojoule": "kJ",

    # Volume
    "ml": "ml",
    "milliliters": "ml",
    "millilitres": "ml",

    # Other
    "iu": "IU",
    "international units": "IU",
    "%": "%",
    "percent": "%",
}