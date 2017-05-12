ADMIN = 0
STAFF = 1
USER = 2
ROLE = {
  ADMIN: 'admin',
  STAFF: 'staff',
  USER: 'user',
}

class BadRequestError(ValueError):
    pass
