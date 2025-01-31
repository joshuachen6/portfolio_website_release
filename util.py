import atexit
import datetime
import multiprocessing
import os
import sqlite3
import shutil
import time
import yaml
import urllib.parse


def get_config(key):
    with open("config.yaml", "r") as config:
        return yaml.safe_load(config)[key]


def to_url(sys_path):
    url = urllib.parse.quote(sys_path.replace(os.sep, "/"))
    if url[0] != "/":
        url = "/" + url
    return url


def to_path(url):
    return urllib.parse.unquote(url).replace("/", os.sep)


def backup_database():
    while True:
        root = os.path.abspath(os.path.dirname(__file__))
        timestamp = datetime.datetime.strftime(
            datetime.datetime.now(), "%m-%d-%Y_%H-%M-%S"
        )
        backup_folder = os.path.join(root, "db_backups")
        os.makedirs(backup_folder, exist_ok=True)
        shutil.copy(
            os.path.join(root, "database.db"),
            os.path.join(backup_folder, f"{timestamp}.db"),
        )

        for backup in os.listdir(backup_folder):
            name, ext = os.path.splitext(backup)
            backup_time = datetime.datetime.strptime(name, "%m-%d-%Y_%H-%M-%S")
            if (datetime.datetime.now() - backup_time).days > get_config(
                "max_backup_days"
            ):
                os.remove(os.path.join(backup_folder, backup))
        time.sleep(get_config("backup_interval"))


class DataBase:
    __backup_process = None

    def __init__(self):
        curr_dir = os.path.abspath(os.path.dirname(__file__))
        self.connection = sqlite3.connect(
            os.path.join(curr_dir, "database.db"), check_same_thread=False
        )
        self.cursor = self.connection.cursor()

        # Create the tables on first run
        command_path = os.path.join(curr_dir, "create.sql")
        with open(command_path, "r") as file:
            command = file.read()
            self.cursor.executescript(command)
            self.connection.commit()

        if not os.path.exists("backup.lock") and get_config("backup_interval") > 0:
            DataBase.__backup_process = multiprocessing.Process(target=backup_database)
            DataBase.__backup_process.start()
            with open("backup.lock", "w"):
                pass

            def stop_backup():
                DataBase.__backup_process.terminate()
                os.remove("backup.lock")

            atexit.register(stop_backup)
