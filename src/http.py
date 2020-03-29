from __future__ import annotations

import datetime
import os
import pathlib
import shutil
import threading
import typing

import requests
from loguru import logger

from .extractor import Extractor
from .extractor import _free_dir
from .extractor import replace_in_string


NBR_MUTEX = 1
MUTEXES_GENERATE = [threading.Lock() for _ in range(NBR_MUTEX)]
MUTEXES_DOWNLOAD = [threading.Lock() for _ in range(NBR_MUTEX)]
MUTEX_LOGGER = threading.Lock()


def info(text: str):
    MUTEX_LOGGER.acquire()
    logger.info(text)
    MUTEX_LOGGER.release()


def error(text: str):
    MUTEX_LOGGER.acquire()
    logger.error(text)
    MUTEX_LOGGER.release()


class Work:
    """
    Thread safe work to extract HTTP content from CIPR/IKSR website.
    """
    def __init__(
        self,
        result_folder: pathlib.Path,
        url: str,
        year: str,
        parameters: typing.Dict[str, int],
        mutex_generate: threading.Lock,
        mutex_download: threading.Lock
    ):
        self.result_folder = (result_folder / "http") / year
        if not self.result_folder.exists():
            self.result_folder.mkdir(parents=True, exist_ok=True)
        self.url = url
        self.year = year
        self.parameters = parameters
        # Make a copy of the parameters' name
        self._parameters = list(parameters.keys())
        self.mutex_generate = mutex_generate
        self.mutex_download = mutex_download
        # Maximum of retry for each parameter
        self.max_retry: int = 5

    def get_url_for(self, parameter: str) -> str:
        return self.url.format(year=self.year, parameter=parameter)

    def run(self):
        for parameter in self._parameters:
            result_content = self.download_parameter(parameter)
            if result_content:
                self.save_parameter_result(parameter, result_content)

    def download_parameter(self, parameter: str) -> typing.Optional[bytes]:
        """
        Download an HTTP content for a given :param:`parameter.
        """
        response = self.get(self.get_url_for(parameter), parameter, self.mutex_generate, timeout=5)
        if not response:
            return
        response = response.decode(encoding="latin1")
        url = response.split("='")[-1].split("'")[0]
        return self.get(url, parameter, self.mutex_download)

    def retry(self, parameter: str) -> None:
        """
        If the number of retries for this :param:`parameter` is less than
        :attr:`Work.max_retry`, retry.
        """
        parameter_step = self.parameters[parameter] + 1
        if parameter_step <= self.max_retry:
            self._parameters.append(parameter)

    def get(self, url: str, parameter: str, mutex: threading.Lock, **kwargs) -> typing.Optional[bytes]:
        with mutex:
            try:
                response = requests.get(url, timeout=kwargs.get("timeout", 5))
            except requests.exceptions.ReadTimeout:
                return self.retry(parameter)
        if response.status_code != 200:
            error(f"[{self.year}, {parameter}]: ERROR, status: {response.status_code}")
            return self.retry(parameter)
        else:
            response_content = response.content
            info(f"[{self.year}, {parameter}]: OK. Result size is {len(response_content)}.")
            return response_content

    def save_parameter_result(self, parameter: str, result_content: bytes) -> None:
        """
        For a given :param:`parameter`, uncompresses its content
        :param:`result_content` and saves it.
        """
        # Create a zip file with the bytes from :param:`result_content` and
        # unzip it.
        zip_filename = self.result_folder / f"{parameter}.zip"
        with open(str(zip_filename), "wb") as zip_file:
            zip_file.write(result_content)
        shutil.unpack_archive(str(zip_filename), str(self.result_folder))
        if zip_filename.exists():
            zip_filename.unlink()

        # Rename CSV file with the :param:`parameter` in the filename.
        csv_file = next(iter([e for e in self.result_folder.iterdir() if "csv" in e.suffix]), None)
        result_filename = f"{parameter}_{csv_file.name}"
        os.replace(str(csv_file), str(self.result_folder / result_filename))


class HTTPExtractor(Extractor):
    def __init__(self, url: str, _min: int, _max: int, folder: pathlib.Path, delete_existing: bool = False):
        super().__init__(url, _min, _max, folder, delete_existing)

        self.results = self.folder / "results"
        if self.delete_existing and self.results.exists():
            _free_dir(self.results)
        self.results.mkdir(parents=True, exist_ok=True)

        all_parameters = self.results / "all_parameters.txt"
        parameters: typing.Dict[str, int] = {}
        with open(str(all_parameters), "r") as all_params_file:
            for parameter in all_params_file.readlines():
                parameter = parameter.replace("\n", "")
                parameters[parameter] = 0

        self.works: typing.List[Work] = []
        for i, year in enumerate(self.all_years):
            mutex_generate = MUTEXES_GENERATE[i % NBR_MUTEX]
            mutex_download = MUTEXES_DOWNLOAD[i % NBR_MUTEX]
            work = Work(self.results, url, str(year), parameters, mutex_generate, mutex_download)
            self.works.append(work)

        current_time = str(datetime.datetime.now())
        current_time = replace_in_string(current_time, {" ": "_", ":": "-"})
        logger.add(self.results / f"file_{current_time}.log")

    def run(self):
        threads: typing.List[threading.Thread] = []
        for work in self.works:
            thread = threading.Thread(target=work.run)
            thread.start()
            threads.append(thread)

        for thread in threads:
            thread.join()
