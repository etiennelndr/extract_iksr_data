import pathlib

from . import extractor

if __name__ == "__main__":
    url = "http://iksr.bafg.de/iksr/tableauxIKSRF.asp?S=1&JA="
    folder = pathlib.Path(r"D:\eland\Documents\Programmation\Python\extraction_donnees_cassandra/data")
    extractor = extractor.Extractor(url, 1978, 2018, folder)
    extractor.run()
