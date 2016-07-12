'''
Created on 1 Apr 2016

Turn an entry from the cache into the common representation and then group
it into one of the proxy

* Load the cache data
* Process it through the set of IF/THEN rules to extract our representation
* For each subject returned
** skip if the domain of the subject does not match the domain of the source
** look if a proxy exist and create one if needed, then associate the subject 
to the proxy (ORE) and all its properties to it using the singleton modeling
to keep track of the provenance
** if a proxy was created: update all proxies that pointed to the subject to 
point now to the proxy URI (deal with cases when something is pointed to but
has not been ingested yet)

@author: guerec01
'''

class Indexer(object):
    '''
    classdocs
    '''


    def __init__(self, params):
        '''
        Constructor
        '''
        