from pydantic import BaseModel

class Message(BaseModel):
    s: str   # sender (S or F)
    r: str   # receiver
    m: str   # message