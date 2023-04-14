import typing
import json
import tempfile
import os
import shutil
from typing import List
from dataclasses import dataclass
from character.lib import database_path


def list_to_json(rows, path) -> None:
    fd, temp_path = tempfile.mkstemp(".json")
    with os.fdopen(fd, "w") as file:
        data = [row.__dict__ for row in rows]
        json.dump(data, file, indent=2)

    if os.path.exists(path):
        shutil.move(path, path + ".bak")

    shutil.move(temp_path, path)


@dataclass
class FashionRow:
    name: str
    image: str
    model: str
    description: str


class FashionTable:
    def __init__(self):
        self.fashions = {}
        self.path = os.path.join(database_path, "fashions.json")
        self.reload()

    def reload(self):
        self.fashions.clear()

        if not os.path.exists(self.path):
            return

        try:
            with open(self.path, "r") as file:
                rows = json.load(file)
            self.fashions = [FashionRow(**row) for row in rows]
        except Exception:
            print(f"Error: Invalid JSON data in {self.path}")

    def save(self) -> None:
        list_to_json(self.fashions, self.path)


@dataclass
class PoseRow:
    name: str
    image: str
    model: str
    description: str

class PoseTable:
    def __init__(self):
        self.poses = {}
        self.path = os.path.join(database_path, "poses.json")
        self.reload()

    def reload(self):
        self.poses.clear()

        if not os.path.exists(self.path):
            return

        try:
            with open(self.path, "r") as file:
                rows = json.load(file)
            self.poses = [PoseRow(**row) for row in rows]
        except Exception:
            print(f"Error: Invalid JSON data in {self.path}")

    def save(self) -> None:
        list_to_json(self.poses, self.path)