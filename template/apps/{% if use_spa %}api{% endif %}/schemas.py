from ninja import Schema


class MeOut(Schema):
    id: int
    email: str
    name: str


class ErrorOut(Schema):
    detail: str
