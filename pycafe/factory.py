import os
from flask import Flask
from . import db
from . import staff
from . import cashdesk
from . import admin
from pathlib import Path

def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__)
    app.config.from_mapping(
        SECRET_KEY='dev',
        DATABASE=os.path.join(app.root_path, 'pycafe.sqlite3'),
    )

    if test_config is None:
        # load PyCafe application settings from 'config/*.py' files, when not testing
        settings_files = sorted(Path(os.path.join(app.root_path, 'config')).glob('**/*.py'))
        print("Applying application settings from files:")
        for file in settings_files:
            print("  "+str(file))
            app.config.from_pyfile(file)
    else:
        # load the test config if passed in
        app.config.from_mapping(test_config)


    db.init_app(app)
    admin.init_app(app)
    app.register_blueprint(staff.bp)
    app.register_blueprint(cashdesk.bp)
    app.register_blueprint(admin.bp)
    app.add_url_rule('/', endpoint='cashdesk.main_page')

    return app
