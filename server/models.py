from pydantic import BaseModel
from typing import List, Optional

class Action(BaseModel):
    command: str  # read_file, add_comment, request_changes, submit, approve
    filename: Optional[str] = None
    line_number: Optional[int] = 1
    content: Optional[str] = None

class Comment(BaseModel):
    filename: str
    line_number: int
    text: str

class PullRequest(BaseModel):
    title: str
    description: str

class Observation(BaseModel):
    pr_details: Optional[PullRequest] = None
    files: List[str] = []
    current_file_name: Optional[str] = ""
    current_file_content: Optional[str] = ""
    comments: List[Comment] = []
    message: str = ""
    error_log: str = ""
    code_output: Optional[str] = "" # For execution results

class Reward(BaseModel):
    score: float # Range 0.0 - 1.0

class StepResponse(BaseModel):
    observation: Observation
    reward: float
    done: bool
    info: dict