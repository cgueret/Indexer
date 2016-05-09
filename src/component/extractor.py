'''
Created on 8 May 2016

@author: guerec01
'''
import os
import component
from rdflib.plugins.sparql.processor import prepareQuery

class EntityExtractor(object):
    '''
    The entity extractor uses a set of processing rules to extract recognised
    entities from an RDF graph. The rules are defined as a set of CONSTRUCT
    queries which are all executed in order to get a set of entities.
    '''

    def __init__(self):
        '''
        Constructor
        '''
        # An map of CONSTRUCT models to test against each graph
        self._models = {}
        
        # Load all the models
        path = os.path.join(component.__path__[0], 'models')
        for entry in os.listdir(path):
            full_path = os.path.join(path, entry)
            if os.path.isfile(full_path) and entry.split('.')[-1] == 'rq':
                print ('Loading {}'.format(entry))
                request = prepareQuery(open(full_path, 'r').read())
                self._models[entry] = request
        
    def extract_entities(self, graph):
        '''
        Execute all the processing rules against the graph passed as parameter
        and return them as an array of graph. Each graph is a potential new
        proxy
        '''
        results = []
        for (name, query) in self._models.items():
            res_graph = graph.query(query).graph
            if len(res_graph) > 0:
                print ('Found a match for {}'.format(name))
                results.append(res_graph)
                
        return results