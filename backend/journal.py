import json
import os

class AttackJournal:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(AttackJournal, cls).__new__(cls)
            cls._instance.entries = []
        return cls._instance

    def add_entry(self, attempt_number, vuln_type, payload, server_response_summary, gamma_critique, outcome):
        entry = {
            "attempt_number": attempt_number,
            "vuln_type": vuln_type,
            "payload": payload,
            "server_response_summary": server_response_summary,
            "gamma_critique": gamma_critique,
            "outcome": outcome
        }
        self.entries.append(entry)

    def get_context_string(self):
        if not self.entries:
            return "No previous attempts."
        
        context_parts = []
        for e in self.entries:
            part = f"ATTEMPT {e['attempt_number']}: Payload=`{e['payload']}`, Response=`{e['server_response_summary']}`, Critique=`{e['gamma_critique']}`, Outcome={e['outcome']}."
            context_parts.append(part)
        
        return " ".join(context_parts)

    def get_winning_payload(self):
        for e in self.entries:
            if e["outcome"] == "breached":
                return e["payload"]
        return None

    def reset(self):
        self.entries = []

    def to_file(self, path):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'w') as f:
            json.dump(self.entries, f, indent=4)
