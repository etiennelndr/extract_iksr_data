import pathlib

from . import http

if __name__ == "__main__":
    # url = "http://iksr.bafg.de/iksr/tableauxIKSRF.asp?S=1&JA="
    # folder = pathlib.Path(r"./data")
    # extractor = extractor.Extractor(url, 1978, 2015, folder)
    # extractor.run()
    #
    # with database.Database(pathlib.Path(r"C:/Users/cassandra/Documents/Qualité"
    #                                     r" Sédiments/GitHub/extract_iksr_data"
    #                                     r"/data/results/"),
    #                        1978,
    #                        2018) as db:
    #     db.run()

    url = (
        "http://iksr.bafg.de/iksr/dl_zippen.asp?S=1&JA={year}&ME=Bimm,EmLo,"
        "Emme,Gori,Hage,Kamp,Kemb,KoBr,KoMo,KoRh,LaKa,Laut,Lobi,Maas,Reki,"
        "SeLa,Selz,StRh,ViNe,Vree,Vure,Weil&KG={parameter}"
    )
    folder = pathlib.Path(r"./data")
    extractor = http.HTTPExtractor(url, 1978, 2018, folder)
    extractor.run()
