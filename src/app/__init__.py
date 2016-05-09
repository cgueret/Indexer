from . import config
from flask import Flask
from logging import Formatter, FileHandler

application = Flask(__name__, template_folder='templates', static_folder='assets')
application.jinja_env.trim_blocks = True
application.jinja_env.lstrip_blocks = True

application.debug = True
if (hasattr(config, 'DEBUG')):
    application.debug = config.DEBUG

formatter = Formatter(
    '%(asctime)s %(levelname)s: %(message)s '
    '[in %(module)s:%(lineno)d]'
)
for handler in application.logger.handlers:
    handler.setFormatter(formatter)

from . import views

