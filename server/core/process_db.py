from typing import Dict, List
import json

class ProcessDB:
    def __init__(self):
        self.db: Dict[str, List[dict]] = {}  # {client_id: [processes]}

    def update(self, client_id: str, processes: List[dict]):
        self.db[client_id] = processes

    def get_all(self) -> Dict[str, List[dict]]:
        return self.db