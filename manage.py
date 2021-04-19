import os
import re
from flask_script import Manager
from flask_migrate import Migrate, MigrateCommand

#import app 
from main.__init__ import db, app

app.config.from_object(os.environ['APP_SETTINGS'])


migrate = Migrate(app, db)

manager = Manager(app)
manager.add_command('db', MigrateCommand)


if __name__ == '__main__':
    manager.run()