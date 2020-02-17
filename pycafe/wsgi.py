# wsgi.py - required to run the app with 'uwsgi' Application Server
# Callable name is 'pycafe.wsgi:app'
# Basic command line to start PyCafe is (executed in Project root folder):
# uwsgi --http-socket 0.0.0.0:5000 --manage-script-name --mount /=pycafe.wsgi:app

from .factory import create_app

app = create_app()
