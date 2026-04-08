from pydantic import BaseModel
from typing import List, Optional

class PullRequest(BaseModel):
    title: str
    description: str

class Comment(BaseModel):
    filename: str
    line_number: int
    text: str

class Observation(BaseModel):
    pr_details: PullRequest
    files: List[str]
    current_file_content: Optional[str] = ""
    current_file_name: Optional[str] = ""
    comments: Optional[List[Comment]] = []
    message: Optional[str] = ""
    error_log: Optional[str] = ""
    code_output: Optional[str] = ""

class Action(BaseModel):
    command: str  # read_file, add_comment, request_changes, approve, submit
    filename: Optional[str] = None
    content: Optional[str] = None
    line_number: Optional[int] = None

class StepResponse(BaseModel):
    observation: Observation
    reward: float
    done: bool
    info: dict
