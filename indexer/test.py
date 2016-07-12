'''
Created on 20 May 2016

@author: guerec01
'''
from util.config import Config

import logging
LOG_FORMAT = "%(asctime)-15s [%(levelname)-7s] %(name)s : %(message)s"
logging.basicConfig(format=LOG_FORMAT, level=logging.DEBUG)
logging.getLogger("requests").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

if __name__ == '__main__':
    e = Config('config.cfg')
    print (e.stardog())