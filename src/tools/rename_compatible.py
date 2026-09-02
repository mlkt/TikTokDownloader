from shutil import copy2

from ..custom import get_volume


class RenameCompatible:
    @classmethod
    def old_db_file(cls):
        return get_volume().joinpath("TikTokDownloader.db")

    @classmethod
    def new_db_file(cls):
        return get_volume().joinpath("DouK-Downloader.db")

    @classmethod
    def migration_file(
        cls,
    ):
        old_file = cls.old_db_file()
        new_file = cls.new_db_file()
        if old_file.exists() and not new_file.exists():
            copy2(old_file.resolve(), new_file.resolve())
