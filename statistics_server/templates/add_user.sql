insert into users (username, department, permission_admin, permission_forecast, permission_json, password) values
('{{ username }}', '{{ department }}', {{ permission_admin }}, {{ permission_forecast }}, {{ permission_json }}, '{{ password }}');
