import abc
import pathlib
import re
import typing


class Extractor(abc.ABC):
    def __init__(self, url: str, _min: int, _max: int, folder: pathlib.Path, delete_existing: bool = False):
        self.default_url = url
        self.all_years = list(range(_min, _max + 1))
        self.folder = folder
        self.delete_existing = delete_existing

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
