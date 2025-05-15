from sqlmodel import SQLModel


class Message(SQLModel):
    detail: str = "Error message"


responses = {400: {"model": Message}, 404: {"model": Message}}
