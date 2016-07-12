from flask import Flask
from flask_bootstrap import Bootstrap
from logging import Formatter, FileHandler
from indexer.util.config import Config

# Instantiate the configuration file
configuration = Config('config.cfg')

# Instantiate the application
application = Flask(__name__, template_folder='templates', static_folder='assets')
Bootstrap(application)
application.jinja_env.trim_blocks = True
application.jinja_env.lstrip_blocks = True
application.debug = True
application.config.from_object(__name__)

# Tweak logging
formatter = Formatter(
    '%(asctime)s %(levelname)s: %(message)s '
    '[in %(module)s:%(lineno)d]'
)
for handler in application.logger.handlers:
    handler.setFormatter(formatter)

# Import the viewsindexerclifrom . import views
