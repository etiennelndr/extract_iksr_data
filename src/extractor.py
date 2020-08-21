import abc
import datetime
import pathlib
import re
import typing

import loguru


class Extractor(abc.ABC):
    def __init__(self, url: str, _min: int, _max: int, folder: pathlib.Path, delete_existing: bool = False):
        self.default_url = url
        self.all_years = list(range(_min, _max + 1))
        self.folder = folder
        self.results = self.folder / "results"
        self.delete_existing = delete_existing

        if self.delete_existing and self.results.exists():
            _free_dir(self.results)
        self.results.mkdir(parents=True, exist_ok=True)

        current_time = str(datetime.datetime.now())
        current_time = replace_in_string(current_time, {" ": "_", ":": "-"})
        loguru.logger.add(self.results / f"file_{current_time}.log")

    @abc.abstractmethod
    def run(self):
        pass


def replace_in_string(text: str, values: typing.Dict[str, str]) -> str:
    """
    See https://stackoverflow.com/a/6117124/11114701 for reference.
    """
    values = dict((re.escape(k), v) for k, v in values.items())
    pattern = re.compile("|".join(values.keys()))
    return pattern.sub(lambda m: values[re.escape(m.group(0))], text)


def _free_dir(_dir: pathlib.Path) -> None:
    # This directory/file may have already been deleted, so we need to verify
    # its existence.
    if not _dir.exists():
        return
    if _dir.is_file():
        _dir.unlink()
    elif _dir.is_dir():
        for element in _dir.iterdir():
            _free_dir(element)
        _dir.rmdir()
    else:
        return


@dataclasses.dataclass
class Url:
    root: str
    year: str

    @property
    def url(self) -> str:
        return self.root + self.year


@dataclasses.dataclass
class Book:
    url: Url
    url_folder: pathlib.Path
    folder: pathlib.Path

    def __post_init__(self):
        self.result_folder = self.url_folder / self.folder.name
        self.result_folder.mkdir(parents=True, exist_ok=True)

    @property
    def type(self) -> str:
        return self.folder.name

    @property
    def sub_books(self) -> typing.List[pathlib.Path]:
        return get_sub_books(self.folder)

    @property
    def grey_sub_book(self) -> pathlib.Path:
        grey_sub_book = self.get_sub_book("gris")
        assert grey_sub_book.exists(), f"{grey_sub_book} doesn't exist."
        return grey_sub_book

    @property
    def minus_sub_book(self) -> pathlib.Path:
        minus_sub_book = self.get_sub_book("liste_moins")
        assert minus_sub_book.exists(), f"{minus_sub_book} doesn't exist."
        return minus_sub_book

    @property
    def plus_sub_book(self) -> pathlib.Path:
        plus_sub_book = self.get_sub_book("liste_plus")
        assert plus_sub_book.exists(), f"{plus_sub_book} doesn't exist."
        return plus_sub_book

    def get_sub_book(self, value: str) -> pathlib.Path:
        return next(filter(lambda b: value in b.name, self.sub_books))


class Extractor:
    def __init__(self, url: str, _min: int, _max: int, folder: pathlib.Path, delete_existing: bool = False):
        self.urls: typing.List[Url] = [Url(url, str(year)) for year in range(_min, _max + 1)]
        self.urls.reverse()
        self.folder = folder
        self.results = folder / "results"
        if delete_existing and self.results.exists():
            _free_dir(self.results)
        self.results.mkdir(parents=True, exist_ok=True)
        livres_folder = folder / "livres"
        self.books = [d for d in livres_folder.iterdir() if d.is_dir()]
        self.descendre_liste = livres_folder / "descendre_liste.png"
        self.descendre_liste_80 = livres_folder / "descendre_liste_80.png"
        self.monter_liste = livres_folder / "monter_liste.png"
        self.monter_liste_80 = livres_folder / "monter_liste_80.png"
        self.fiche = livres_folder / "fiche.png"
        self.close_tab = folder / "close_tab.png"
        self.save = livres_folder / "sauvegarde.png"
        self.click_download = livres_folder / "click_download.png"
        self.download_compressed = livres_folder / "download_compressed.png"
        self.no_data = livres_folder / "no_data.png"
        self.save_ok = livres_folder / "save_ok.png"
        self.save_file = livres_folder / "save_file.png"
        self.close_compressed = folder / "close_compressed.png"
        self.close_zipfile = folder / "close_zipfile.png"
        self.close_window = folder / "close_window.png"
        self.end_of_list = livres_folder / "fin_liste.png"

        current_time = str(datetime.datetime.now()).replace(" ", "_").replace(":", "-")
        logger.add(f"file_{current_time}.log")

        pyscreeze.USE_IMAGE_NOT_FOUND_EXCEPTION = True

    def run(self):
        for url in self.urls:
            logger.info(f"Current year is {url.year}.")
            open_webbrowser(url.url)

            url_folder = self.results / url.year
            url_folder.mkdir(parents=True, exist_ok=True)

            for _book in self.books:
                if url.year == "1995" and _book.name != "rouge":
                    time.sleep(5)
                    continue

                book = Book(url, url_folder, _book)

                list_minus = book.minus_sub_book
                list_plus = book.plus_sub_book

                if not find_one_sub_book(book):
                    print(f"{book.type}: Nothing to do.")
                    continue

                time.sleep(1)
                try:
                    find_imgs_on_screen(str(list_minus), confidence=0.95)
                except pyscreeze.ImageNotFoundException:
                    print("Nothing to close.")

                time.sleep(1)

                # Lower the confidence for red books.
                if "rouge" in book.type:
                    confidence = 0.955
                else:
                    confidence = 0.97
                positions = find_imgs_on_screen(str(list_plus), click=False, confidence=confidence)
                for pos in positions:
                    x, y = pyautogui.center(pos)
                    print(x, y)
                    pyautogui.click(x, y)
                    time.sleep(0.5)

                    self.loop_on_sheets(book)
                    time.sleep(0.5)

                    find_img_on_screen(list_minus, confidence=0.95)
                    time.sleep(0.5)
            find_img_on_screen(self.close_tab)

    def loop_on_sheets(self, book: Book, deep: int = 0, go_deeper_by: int = 2) -> int:
        time.sleep(0.5)
        if find_img_on_screen(self.fiche, click=False, minSearchTime=2, confidence=0.967):
            # Find each sheet
            sheet_positions = find_imgs_on_screen(str(self.fiche), click=False, confidence=0.967)

            x_sheet: int = 1
            y_sheet: int = 1
            for sheet_pos in sheet_positions:
                x_sheet, y_sheet = pyautogui.center(sheet_pos)
                print(x_sheet, y_sheet)
                pyautogui.click(x_sheet, y_sheet)
                time.sleep(0.5)

                self.save_sheet(book, x_sheet, y_sheet)
                time.sleep(0.5)
            pyautogui.click(x_sheet + 800, y_sheet)

        time.sleep(0.5)
        if find_img_on_screen(self.end_of_list, click=False, minSearchTime=1, confidence=0.97):
            raise NoNewSheets

        # Go down
        try:
            if int(book.url.year) <= 1989:
                descendre_liste = self.descendre_liste_80
            else:
                descendre_liste = self.descendre_liste
            for _ in range(go_deeper_by):
                find_img_on_screen(descendre_liste, confidence=0.99)
            new_deep = self.loop_on_sheets(book, deep=deep + go_deeper_by, go_deeper_by=go_deeper_by)
        except pyscreeze.ImageNotFoundException:
            print("Can't go deeper.")
            return deep + go_deeper_by
        except NoNewSheets:
            print("No new sheets.")
            if deep:
                return deep + go_deeper_by
            else:
                new_deep = deep + go_deeper_by

        if deep:
            return new_deep

        if int(book.url.year) <= 1989:
            monter_liste = self.monter_liste_80
        else:
            monter_liste = self.monter_liste
        for _ in range(new_deep):
            find_img_on_screen(monter_liste, confidence=0.95)

    def save_sheet(self, book: Book, x_sheet: int, y_sheet: int, max_retries: int = 10, retry: bool = True):
        # Try to a find a `save` button.
        if not find_img_on_screen(self.save, minSearchTime=1, confidence=0.97):
            print(f"No save button for [{x_sheet}, {y_sheet}].")
            return

        time.sleep(0.5)
        for _ in range(max_retries):
            if not find_img_on_screen(self.no_data, click=False, minSearchTime=1, confidence=0.97):
                break
            time.sleep(0.5)
        else:
            print(f"No data to save for [{x_sheet}, {y_sheet}].")
            return

        kwargs = {
            "on_loop": True,
            "max_retries": 3,
            "minSearchTime": 2,
            "confidence": 0.97
        }
        time.sleep(0.5)
        find_img_on_screen(self.download_compressed, **kwargs)
        time.sleep(0.5)
        find_img_on_screen(self.click_download, **kwargs)
        time.sleep(0.5)
        kwargs["confidence"] = 0.98
        find_img_on_screen(self.save_ok, **kwargs)
        time.sleep(0.5)
        for _ in range(max_retries):
            if find_img_on_screen(self.save_file, **kwargs):
                break
            time.sleep(0.5)
        else:
            print(f"No `save file` button for [{x_sheet}, {y_sheet}].")
            return

        time.sleep(2)
        zip_file = next(iter([e for e in self.folder.iterdir() if "zip" in e.suffix]), None)
        if not zip_file:
            print(f"Didn't find any zip file for {book.result_folder}")
            return

        # Create a ZipFile Object and load sample.zip in it
        try:
            with zipfile.ZipFile(str(zip_file), 'r') as zip_obj:
                # Extract all the contents of zip file in different directory
                zip_obj.extractall(str(self.folder))
            time.sleep(0.5)
        except zipfile.BadZipFile:
            if zip_file.exists():
                zip_file.unlink()
            time.sleep(0.5)
            find_imgs_on_screen(str(self.close_window))
            if retry:
                time.sleep(0.5)
                return self.save_sheet(book, x_sheet, y_sheet, max_retries, retry=False)
            else:
                tmp_filename = str(datetime.datetime.now()).replace(" ", "_").replace(":", "-")
                tmp_path = book.result_folder / f"{tmp_filename}.txt"
                logger.info(f"Could not download CSV file. Error file is {tmp_path}.")
                tmp_path.touch()
                return
            
        csv_file = next(iter([e for e in self.folder.iterdir() if "csv" in e.suffix]), None)

        df = pd.read_csv(str(csv_file), sep=";", encoding='latin1')
        param = next(iter([c for c in list(df.columns) if "param" in c]), None)
        if not param:
            param = ""
        else:
            param = str(df[param][0]).replace(" ", "_").replace(":", "-").replace("/", "").replace("\\", "")
            param += "_"
        result_filename = f"{param}_{csv_file.name}"
        os.replace(str(csv_file), str(book.result_folder / result_filename))
        if zip_file.exists():
            zip_file.unlink()

        time.sleep(0.5)
        find_imgs_on_screen(str(self.close_window))
