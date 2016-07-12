#encoding: utf-8
'''
Created on 21 May 2016

@author: guerec01
'''
from configparser import ConfigParser

import logging
logger = logging.getLogger(__name__)

class Config(object):
    '''
    Interface around the configuration file
    '''
    def __init__(self, file_name):
        '''
        Constructor
        '''
        self.config = ConfigParser()
        self.config.read(file_name)
        logger.debug(self.config.sections())
        
    def base(self):
        '''
        Return the base namespace
        '''
        return self.config.get('indexer', 'base')
    
    def rules(self):
        return self.config.get('indexer', 'rules')
    
    def stardog_url(self):
        '''
        Get the location of StarDog
        '''
        return self._store_section('stardog', 'localhost', '5820')

    def stardog_db(self):
        '''
        Get the location of StarDog
        '''
        return self.config.get('stardog', 'db')
    
    def couchdb_url(self):
        '''
        Get the location of CouchDB
        '''
        return self._store_section('couchdb', 'localhost', '5984')
    
    def couchdb_db(self):
        '''
        Get the name of the DB for CouchDB
        '''
        return self.config.get('couchdb', 'db')
    
    def _store_section(self, store_name, hostname, port):    
        # Default values
        p = {}
        p['hostname'] = hostname
        p['port'] = port
        
        # See if some other values where specified
        for param in ['hostname', 'port']:
            if self.config.has_option(store_name, param):
                p[param] = self.config.get(store_name, param)
        
        # Return the value
        return "http://{}:{}/".format(p['hostname'], p['port'])
    
        