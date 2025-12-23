from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class NoteInfoRequest(BaseModel):
    note_name: str
    note_pwd: str = ""

class NoteSaveRequest(BaseModel):
    note_name: str
    note_id: str
    note_content: str
    note_token: str
    expire_time: int = 259200
    note_pwd: str = ""

class LogEntry(BaseModel):
    client: str
    ip: str
    location: str
    time: str

class NoteData(BaseModel):
    note_id: str
    note_name: str
    note_content: str
    note_token: str
    created_time: str
    updated_time: str
    read_count: int
    expire_time: int
    log_list: List[LogEntry]
    file_list: List = []
    last_read_time: str
    note_pwd: str = ""
    has_password: bool = False

class NoteInfoResponse(BaseModel):
    status: int
    data: Optional[NoteData] = None
    req_id: str
    error: Optional[str] = None

class NoteSaveResponse(BaseModel):
    status: int
    data: Optional[dict] = None
    error: Optional[str] = None
    req_id: str