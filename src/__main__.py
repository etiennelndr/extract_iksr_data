import pathlib

from . import database
from . import extractor

if __name__ == "__main__":
    # url = "http://iksr.bafg.de/iksr/tableauxIKSRF.asp?S=1&JA="
    # folder = pathlib.Path(r"./data")
    # extractor = extractor.Extractor(url, 1978, 2015, folder)
    # extractor.run()

    with database.Database(pathlib.Path(r"C:/Users/cassandra/Documents/Qualité"
                                        r" Sédiments/GitHub/extract_iksr_data"
                                        r"/data/results/"),
                           1978,
                           2018) as db:
        db.run()
