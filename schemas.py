from pydantic import BaseModel

class UserSchema(BaseModel):
    tg_id: str
    chat_id: str|None=None
    phone_number: str|None=None

class TaskSchema(BaseModel):
    adress:str
    month:str
    date_time:str
    number:int
    workers:str
    type:str