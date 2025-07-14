import json
from pathlib import Path

class Authenticator:
    def __init__(self, db_path="clients.json"):
        self.db_path = Path(__file__).parent / db_path
        
    def validate(self, client_id: str, password: str) -> bool:
        auth = Authenticator()
        
        try:
            
            with open(auth.db_path) as f:
                print(f'-------------') 
                clients = json.load(f)["clients"]
                return clients.get(client_id) == password
        except Exception as e:
            print(f"Auth error: {e}")
            return False