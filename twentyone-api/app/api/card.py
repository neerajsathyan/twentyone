import json
from dataclasses import dataclass
from dataclasses_json import dataclass_json

from app.utils.constants import CARD_FACE_VALUE


@dataclass_json
@dataclass
class Card:
    def __init__(self, kind, face_value):
        self.kind = kind
        self.face_value = face_value
        self.value = CARD_FACE_VALUE[face_value]

    def describe(self):
        print("Card Kind: " + self.kind)
        print("\nCard Face Value: " + self.face_value)

    def toJSON(self):
        return json.dumps(self, default=lambda o: o.__dict__,
                          sort_keys=True, indent=4)
