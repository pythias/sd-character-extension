import typing
import json
import tempfile
import os
import shutil
from typing import List, Optional
from dataclasses import dataclass
from character.lib import database_path, log, LogLevel

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
    description: str
    tags: str
    negative_prompt: Optional[str] = ""
    image: Optional[str] = ""


class FashionTable:
    def __init__(self):
        self.fashions = {}
        self.path = os.path.join(database_path, "fashions.json")
        self.reload()

    def get_fashion_tags(self, names: List[str]) -> str:
        prompts = []
        for name in names:
            if name not in self.fashions:
                continue
            prompts.append(self.fashions[name].tags)
        return ",".join(prompts)

    def get_fashion_negative_prompts(self, names: List[str]) -> str:
        prompts = []
        for name in names:
            if name not in self.fashions:
                continue
            if self.fashions[name].negative_prompt:
                prompts.append(self.fashions[name].negative_prompt)
        return ",".join(prompts)

    def reload(self):
        self.fashions.clear()

        if not os.path.exists(self.path):
            log("No fashion database found.", LogLevel.WARNING)
            return

        try:
            with open(self.path, "r") as file:
                rows = json.load(file)
            self.fashions = [FashionRow(**row) for row in rows]
            log(f"Loaded {len(self.fashions)} fashions from {self.path}", LogLevel.INFO)
        except Exception as e:
            log(f"Error: Invalid JSON data in {self.path}, error: {str(e)}", LogLevel.ERROR)

    def save(self) -> None:
        list_to_json(self.fashions, self.path)


@dataclass
class PoseRow:
    name: str
    description: str
    model: str
    image: Optional[str] = ""

class PoseTable:
    def __init__(self):
        self.poses = {}
        self.path = os.path.join(database_path, "poses.json")
        self.reload()

    def reload(self):
        self.poses.clear()

        if not os.path.exists(self.path):
            log("No pose database found.", level=LogLevel.WARNING)
            return

        try:
            with open(self.path, "r") as file:
                rows = json.load(file)
            self.poses = [PoseRow(**row) for row in rows]
            log(f"Loaded {len(self.poses)} poses from {self.path}", level=LogLevel.INFO)
        except Exception as e:
            log(f"Error: Invalid JSON data in {self.path}, error: {str(e)}", level=LogLevel.ERROR)

    def save(self) -> None:
        list_to_json(self.poses, self.path)

fashion_table = FashionTable()
pose_table = PoseTable()
