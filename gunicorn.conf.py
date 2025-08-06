# deploy/django/gunicorn.conf.py
bind = "0.0.0.0:8000"
workers = 3
accesslog = "-"
errorlog = "-"