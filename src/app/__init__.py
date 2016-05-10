from . import config
from flask import Flask
from logging import Formatter, FileHandler
from storage.proxy import ProxyStore
from storage.collection import CollectionStore

formatter = Formatter(
    '%(asctime)s %(levelname)s: %(message)s '
    '[in %(module)s:%(lineno)d]'
)

# Instantiate the application
application = Flask(__name__, template_folder='templates', static_folder='assets')
application.jinja_env.trim_blocks = True
application.jinja_env.lstrip_blocks = True
application.debug = True
if (hasattr(config, 'DEBUG')):
    application.debug = config.DEBUG
for handler in application.logger.handlers:
    handler.setFormatter(formatter)

# Instantiate the proxy store
proxies = ProxyStore()

# Instantiate the collection store
collections = CollectionStore()

from . import views

