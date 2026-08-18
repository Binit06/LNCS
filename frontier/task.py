from dataclasses import dataclass, field
from typing import Dict

import json

@dataclass
class Task:
    url: str
    site: str
    rate_limit: float = 1.0
    priority: int = 1
    retry_count: int = 0
    max_retries: int = 3
    headers: Dict[str, str] = field(default_factory=dict)

    def to_json(self):
        return json.dumps({
            "url": self.url,
            "site": self.site,
            "rate_limit": self.rate_limit,
            "priority": self.priority,
            "retry_count": self.retry_count,
            "max_retries": self.max_retries,
            "headers": self.headers
        })

    @classmethod
    def from_json(cls, data):
        return cls(**json.loads(data))