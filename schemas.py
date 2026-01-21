from pydantic import BaseModel
from datetime import datetime

class UserSchema(BaseModel):
    tg_id: str
    chat_id: str|None=None
    phone_number: str|None=None

class TaskSchema(BaseModel):
    adress:str
    month:str
    date_time:datetime
    number:int
    workers:str
    type:str


