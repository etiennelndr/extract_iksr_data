from __future__ import annotations

import dataclasses
import datetime
import os
import pathlib
import shutil
import time
import typing
import webbrowser

import pandas as pd
import pyautogui
import pyscreeze
import win32clipboard
from loguru import logger

from .extractor import Extractor
from .extractor import _free_dir


def open_webbrowser(url):
    """
    Opens this :param:`url` in a webbroser.
    """
    webbrowser.open_new(url)


def get_sub_books(book: pathlib.Path) -> typing.List[pathlib.Path]:
    """
    Returns all subbooks of a :param:`book`.
    """
    return [b for b in book.iterdir() if b.is_file()]


def get_sub_book(books: typing.List[pathlib.Path], value: str) -> pathlib.Path:
    return next(filter(lambda b: value in b.name, books))


def find_img_on_screen(
    img: pathlib.Path, click: bool = True, on_loop: bool = False, retry: int = 0, max_retries: int = 5, **kwargs
) -> bool:
    # Default search time
    kwargs.setdefault("minSearchTime", 5)
    # Default confidence
    kwargs.setdefault("confidence", 0.8)
    # Default sleep time
    sleep_time = kwargs.pop("sleep_time", 0.5)

    try:
        x, y = pyautogui.locateCenterOnScreen(str(img), **kwargs)
        if not click:
            return True
        pyautogui.click(x, y)
    except TypeError as err:
        print(f"{img.name}: {err}")
        return False
    except pyscreeze.ImageNotFoundException as err:
        if on_loop:
            retry += 1
            if retry > max_retries:
                print(f"{img.name}: {err}")
                return False
            time.sleep(sleep_time)
            return find_img_on_screen(img, click, on_loop, retry, max_retries, **kwargs)
        print(f"{img.name}: {err}")
        return False
    return True


def find_imgs_on_screen(img: str, click: bool = True, **kwargs) -> typing.Iterable:
    # Default confidence
    kwargs.setdefault("confidence", 0.8)
    # Default sleep time
    local_kwargs = dict()
    local_kwargs["sleep_time"] = kwargs.pop("sleep_time", 0.5)

    results = pyautogui.locateAllOnScreen(img, **kwargs)
    if click:
        for result in results:
            x, y = pyautogui.center(result)
            pyautogui.click(x, y)
            time.sleep(local_kwargs["sleep_time"])
    return results


def find_one_sub_book(book: Book) -> bool:
    grey_book = book.grey_sub_book
    list_minus = book.minus_sub_book
    list_plus = book.plus_sub_book

    kwargs = {}
    if "bleu" not in str(book):
        kwargs["minSearchTime"] = 0.5
    else:
        kwargs["on_loop"] = True

    time.sleep(0.5)
    found_grey = find_img_on_screen(grey_book, **kwargs)
    found_plus = find_img_on_screen(list_plus, click=False, minSearchTime=0.5)
    found_minus = find_img_on_screen(list_minus, click=False, minSearchTime=0.5)

    return found_grey or found_plus or found_minus


class NoNewSheets(Exception):
    pass


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


class GUIExtractor(Extractor):
    def __init__(self, url: str, _min: int, _max: int, folder: pathlib.Path, delete_existing: bool = False):
        super().__init__(url, _min, _max, folder, delete_existing)

        self.urls: typing.List[Url] = [Url(url, str(year)) for year in self.all_years]
        self.urls.reverse()
        self.results = self.folder / "results"
        if self.delete_existing and self.results.exists():
            _free_dir(self.results)
        self.results.mkdir(parents=True, exist_ok=True)
        livres_folder = folder / "livres"
        self.books = [d for d in livres_folder.iterdir() if d.is_dir()]

        self.descendre_liste = livres_folder / "descendre_liste.png"
        self.monter_liste = livres_folder / "monter_liste.png"
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

        self.all_parameters = self.results / "all_parameters.txt"
        self.parameters: typing.List[str] = []
        self.all_params_file = open(str(self.all_parameters), "w")
        self.write_to_file = True

        current_time = str(datetime.datetime.now()).replace(" ", "_").replace(":", "-")
        logger.add(self.results / f"file_{current_time}.log")

        pyscreeze.USE_IMAGE_NOT_FOUND_EXCEPTION = True

    def run(self):
        for url in self.urls:
            logger.info(f"Current year is {url.year}.")
            open_webbrowser(url.url)

            url_folder = self.results / url.year
            url_folder.mkdir(parents=True, exist_ok=True)

            for _book in self.books:
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
            for _ in range(go_deeper_by):
                find_img_on_screen(self.descendre_liste, confidence=0.99)
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
        for _ in range(new_deep):
            find_img_on_screen(self.monter_liste, confidence=0.95)

    def save_sheet(self, book: Book, x_sheet: int, y_sheet: int, max_retries: int = 10):
        if not self.write_to_file:
            self._save_sheet(book, x_sheet, y_sheet, max_retries)
        else:
            self._save_all_parameters(x_sheet, y_sheet)

    def _save_sheet(self, book: Book, x_sheet: int, y_sheet: int, max_retries: int = 10):
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

        if not self.save_pipeline(on_loop=True, max_retries=3, minSearchTime=2, confidence=0.97):
            return
        self.save_archive(book)

        time.sleep(0.5)
        find_imgs_on_screen(str(self.close_window))

    def _save_all_parameters(self, x_sheet: int, y_sheet: int):
        # Try to find a `save` button.
        if not find_img_on_screen(self.save, minSearchTime=0.5, confidence=0.97):
            print(f"No save button for [{x_sheet}, {y_sheet}].")
            return
        # Ctrl+l to get URL
        pyautogui.hotkey('ctrl', 'l', interval=0.1)
        time.sleep(0.1)
        # Copy the URL to the clipboard.
        pyautogui.hotkey('ctrl', 'c', interval=0.1)
        time.sleep(0.1)

        win32clipboard.OpenClipboard()
        new_data = win32clipboard.GetClipboardData()
        win32clipboard.CloseClipboard()

        parameter = new_data.split("=")[-1]
        if parameter not in self.parameters:
            self.all_params_file.write(f"{parameter}\n")
            self.all_params_file.flush()
            self.parameters.append(parameter)
        else:
            logger.info(f"Parameter {parameter} already exists. URL is {new_data}.\n")

        time.sleep(0.25)
        find_imgs_on_screen(str(self.close_window))

    def save_pipeline(self, **kwargs) -> bool:
        time.sleep(0.5)
        find_img_on_screen(self.download_compressed, **kwargs)
        time.sleep(0.5)
        find_img_on_screen(self.click_download, **kwargs)
        time.sleep(0.5)
        kwargs["confidence"] = 0.98
        find_img_on_screen(self.save_ok, **kwargs)
        time.sleep(0.5)
        return find_img_on_screen(self.save_file, **kwargs)

    def save_archive(self, book: Book) -> None:
        time.sleep(2)
        zip_file = next(iter([e for e in self.folder.iterdir() if "zip" in e.suffix]), None)
        if not zip_file:
            print(f"Didn't find any zip file for {book.result_folder}")
            return

        shutil.unpack_archive(str(zip_file), str(self.folder))
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
