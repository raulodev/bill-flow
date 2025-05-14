from fastapi import HTTPException


class NotFoundError(HTTPException):

    def __init__(self, status_code=404, detail="Not found", headers=None):
        super().__init__(status_code, detail, headers)


class BadRequestError(HTTPException):
    def __init__(self, status_code=400, detail="Bad Request", headers=None):
        super().__init__(status_code, detail, headers)
