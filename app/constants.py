ADMIN = 0
STAFF = 1
USER = 2
COURSEUSER = 3
SUPERUSER = 4
ROLE = {
  ADMIN: 'admin',
  STAFF: 'staff',
  USER: 'user',
  COURSEUSER: 'courseuser',
  SUPERUSER: 'superuser'
}

class BadRequestError(ValueError):
    pass
