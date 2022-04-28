import json
import uuid

from app.utils.constants import CARD_FACE_VALUE, PLAYER_STATUS_READY
from dataclasses import dataclass
from dataclasses_json import dataclass_json


@dataclass_json
@dataclass
class Players:
    def __init__(self, name, cards, is_bank, wallet, active):
        self.name = name
        self.id = str(uuid.uuid4())
        self.cards = cards
        self.is_bank = is_bank
        self.wallet = wallet
        self.active = active
        self.on_hold = 0
        self.status = PLAYER_STATUS_READY
        self.value = 0 if len(cards) == 0 else sum(CARD_FACE_VALUE[val.value] for val in cards)

    def describe(self):
        print("Player " + self.name + "\n Cards: " + self.cards + "\n" + self.is_bank +
              "\n Value: " + self.value+"\n On Hold: "+self.onn_hold)

    def toJSON(self):
        return json.dumps(self, default=lambda o: o.__dict__,
                          sort_keys=True, indent=4)
