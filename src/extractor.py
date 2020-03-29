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
