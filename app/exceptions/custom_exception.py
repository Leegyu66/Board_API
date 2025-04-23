class NotFoundError(Exception):
    pass

class BadRequestError(Exception):
    pass

class Forbidden(Exception):
    pass

class UnAuthorized(Exception):
    pass

class ServerError(Exception):
    pass