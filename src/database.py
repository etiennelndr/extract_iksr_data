from __future__ import annotations

import datetime
import pathlib
import typing

import pandas as pd
import pyodbc


def split_parameter(value: str) -> typing.Tuple[str, str]:
    # Replace ` in ` into ` en `.
    value = value.replace(" in ", " en ")
    if "en" not in value:
        return value, ""
    splitted_value = value.split("en")
    parameter = "en".join(splitted_value[:-1]).strip()
    unit = splitted_value[-1].strip()
    return parameter, unit


class Database:
    def __init__(self, folder: pathlib.Path, _min: int, _max: int, free: bool = True):
        self.info = r"DRIVER={Microsoft Access Driver (*.mdb, *.accdb)};" \
                    r"DBQ=C:\Users\cassandra\Documents\Qualité Sédiments\IKSR\IKSR.accdb"
        self.cnxn: pyodbc.Connection = pyodbc.connect(self.info)
        self.cursor: pyodbc.Cursor = self.cnxn.cursor()
        self.query_iksr_data = "insert into iksr_data(station, fleuve, " \
                               "matrice, groupe, parameter, type_prelevement," \
                               " annee, periode, _date, caracteres_specifiques," \
                               " valeur) values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?," \
                               " ?)"
        self.query_parameters = r"insert into [C:\Users\cassandra\Documents" \
                                r"\Qualité Sédiments\IKSR\IKSR.accdb]." \
                                r"parameters(parameter, unit) values (?, ?)"

        if free:
            self.cursor.execute("delete * from iksr_data")
            self.cnxn.commit()
            self.cursor.execute(r"delete * from [C:\Users\cassandra\Documents"
                                r"\Qualité Sédiments\IKSR\IKSR.accdb]."
                                r"parameters")
            self.cnxn.commit()
            self.cursor.execute("alter table iksr_data ALTER COLUMN id COUNTER(1,1)")
            self.cnxn.commit()

        assert folder.exists(), f"{folder} doesn't exist."
        self.folder = folder
        self.years = [folder / str(year) for year in range(_min, _max + 1)]
        self._curr_year: str = str(_min)

    def __enter__(self) -> Database:
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cursor.close()
        self.cnxn.close()

    def run(self):
        for year in self.years:
            self._curr_year = year.name
            assert year.exists(), f"{year} doesn't exist."

            bleu = self.folder / f"{year}/bleu"
            jaune = self.folder / f"{year}/jaune"
            rouge = self.folder / f"{year}/rouge"

            files: typing.List[pathlib.Path] = []
            if bleu.exists():
                files.extend([f for f in bleu.iterdir() if "csv" in f.suffix])
            if jaune.exists():
                files.extend([f for f in jaune.iterdir() if "csv" in f.suffix])
            if rouge.exists():
                files.extend([f for f in rouge.iterdir() if "csv" in f.suffix])

            self.work(files)

    def work(self, files: typing.List[pathlib.Path]):
        print(f"{self._curr_year}: {len(files)}")
        for csv_file in files:
            self._work_on_file(csv_file)

    def _work_on_file(self, csv_file: pathlib.Path):
        df = pd.read_csv(str(csv_file), sep=";", encoding="latin1")
        assert list(df.columns) == [
            "Station de mesure",
            "fleuve",
            "matrice",
            "groupe",
            "paramètres",
            "type de prélèvement",
            "année",
            "période",
            "date",
            "caractères spécifiques",
            "valeur"
        ]
        for data in df.itertuples():
            values = list(data)[1:]
            valeur = values[-1]
            carac_spe = values[-2]
            parameter = values[4]
            if isinstance(valeur, str):
                values[-1] = float(valeur.replace(",", "."))
            if pd.isna(valeur):
                values[-1] = 0
            if pd.isna(carac_spe):
                values[-2] = ""
            values[-3] = datetime.datetime.strptime(values[-3], "%d.%m.%Y")
            parameter, unit = split_parameter(parameter)
            values[4] = parameter

            self._insert(self.query_iksr_data, values)
            self._insert(self.query_parameters, [parameter, unit])

    def _insert(self, query: str, values: typing.List):
        try:
            self.cursor.execute(query, values)
            self.cnxn.commit()
        except pyodbc.IntegrityError:
            pass
