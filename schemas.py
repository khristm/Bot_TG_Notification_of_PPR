from pydantic import BaseModel
from datetime import datetime

class UserSchema(BaseModel):
    tg_id: int
    chat_id: int|None=None
    phone_number: str|None=None

class AIParsingTaskSchema(BaseModel):
    address: str
    month: str
    date_time: datetime
    number: int
    workers: str
    type: str

class TaskSchema(BaseModel):
    address: str | None
    month:str|None
    date_time:datetime
    number:int|None
    workers:str|None
    type:str|None

class WorkersSchema(BaseModel):
    name: str
    nickname: str


