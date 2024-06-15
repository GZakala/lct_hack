select username, department, permission_admin, permission_forecast, permission_json, password
from users
where username = '{{ username }}'
