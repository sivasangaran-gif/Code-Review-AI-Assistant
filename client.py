import requests
import os

class CodeReviewClient:
    def __init__(self, base_url=None):
        self.base_url = base_url or os.getenv("OPENENV_SERVER_URL", "http://localhost:7860")
    
    def reset(self, task_id="task_1"):
        """Resets the environment for a specific task."""
        response = requests.post(f"{self.base_url}/reset?task_id={task_id}")
        response.raise_for_status()
        return response.json()
    
    def step(self, command, filename=None, content=None, line_number=None):
        """Executes an action in the environment."""
        payload = {
            "command": command,
            "filename": filename,
            "content": content,
            "line_number": line_number
        }
        response = requests.post(f"{self.base_url}/step", json=payload)
        response.raise_for_status()
        return response.json()
    
    def state(self):
        """Returns the current observation state."""
        response = requests.get(f"{self.base_url}/state")
        response.raise_for_status()
        return response.json()

# Entry point for OpenEnv SDK
def get_client(base_url=None):
    return CodeReviewClient(base_url)
