from pydantic import BaseModel
from datetime import datetime

class UserSchema(BaseModel):
    tg_id: int
    chat_id: int|None=None
    phone_number: str|None=None

class TaskSchema(BaseModel):
    adress:str|None
    month:str|None
    date_time:datetime
    number:int|None
    workers:str|None
    type:str|None


