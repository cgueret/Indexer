'''
Created on 1 Apr 2016

@author: guerec01
'''

class Filter(object):
    '''
    A Filter takes as an input a raw payload of data that may come from a
    Crawler or a direct py. This input gets filtered to remove all the
    data that will not be used by the indexer. The output then gets stored
    as a cache resource in the data store.
    '''


    def __init__(self, params):
        '''
        Constructor
        '''
        pass