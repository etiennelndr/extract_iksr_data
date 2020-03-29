import pathlib

from . import extractor

if __name__ == "__main__":
    url = ("http://iksr.bafg.de/iksr/dl_zippen.asp?S=1&JA={year}&ME=Bimm,EmLo,"
           "Emme,Gori,Hage,Kamp,Kemb,KoBr,KoMo,KoRh,LaKa,Laut,Lobi,Maas,Reki,"
           "SeLa,Selz,StRh,ViNe,Vree,Vure,Weil&KG={parameter}")
    folder = pathlib.Path(r"./data")
    extractor = extractor.HTTPExtractor(url, 1978, 2018, folder)
    extractor.run()
