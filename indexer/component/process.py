'''
Created on 8 May 2016

@author: guerec01
'''
from indexer.component.processors.description import DescriptionExtractor
from indexer.storage.cache import CacheStore
from indexer.storage.index import IndexStore
from urllib.parse import urlparse
from rdflib.namespace import RDF, OWL
from rdflib.graph import Dataset, Graph
from indexer.util.namespaces import INDEXER, PROV
from rdflib.plugins.sparql.processor import prepareQuery
import hashlib

import logging
from rdflib.compare import sha256
from rdflib.term import URIRef
import uuid
logger = logging.getLogger(__name__)


class Process(object):
    '''
    This class provides the higher level interface to the cache store
    '''
    def __init__(self, config, clean=False):
        '''
        Constructor
        '''
        # Get the base for minting URIs
        self.base = config.base()
        
        # Load the rules
        self.rules = self._load_rules(config.rules())
        logger.info('Loaded {} rule(s)'.format(len(self.rules)))
        
        # Create an instance of the cache interface
        self.cache_store = CacheStore(config)
        
        # Create an instance of the proxies interface
        self.index_store = IndexStore(config)
        
        # If clean, reset the index DB
        if clean:
            self.index_store.reset_db()
        
    def process(self, uri):
        '''
        Process one entry from the cache
        '''
        logger.info('Processing {}'.format(uri))
    
        # Retrieve the graph
        input_graph = self.cache_store.retrieve(uri)
        
        # Initialise the data set that will be generated from processing
        # the graph
        dataset = Dataset()
        
        # We define a named graph with the hash of the source. This way
        # different versions of the same document will overwrite the triples
        # previously generated from it        
        hashed_uri = hashlib.sha256(uri.encode()).hexdigest()
        named_graph_uri = URIRef('{}{}'.format(self.base, hashed_uri))
        
        # Extract a data set from applying the rules
        self._apply_rules(dataset, input_graph, named_graph_uri)
        
        # Change the subjects to use proxy URI instead
        self._replace_subjects_by_proxies(dataset, named_graph_uri)
        
        # Change the objects to use proxy URIs instead (but only if existing)
        self._replace_objects_by_proxies(dataset)
        
        # Add some more information about the collections
        self._update_collections(dataset)
        
        # Add some provenance information
        prov_uri = named_graph_uri + '#prov'
        prov_graph = dataset.graph(prov_uri)
        for dataset_graph in dataset.graphs():
            prov_graph.add((dataset_graph, PROV.wasDerivedFrom, URIRef(uri)))
        
        # Display the graph
        #for g in dataset.graphs():
        #    logger.debug(g.identifier + '\n' + g.serialize(format="nt").decode())
        
        # Store the generated dataset in the index   
        # self.index_store.store(dataset)
        
    def _replace_subjects_by_proxies(self, dataset, named_graph_uri):
        # Get or create a proxy URI for each of the subject
        replacement = {}
        for subject in dataset.subjects():
            if self.index_store.has_proxy(subject):
                # There is already a proxy
                proxy_uri = self.get_proxy_uri(subject)
                logger.info("Found a proxy {}".format(proxy_uri))
            else:
                # Generate a new UUID
                proxy_uri = URIRef("{}{}#id".format(self.base, uuid.uuid1()))
                logger.info("Generating a new proxy {}".format(proxy_uri))
            replacement[subject] = proxy_uri
            
        # In all the graphs replace the subjects by the proxy URI
        for g in dataset.graphs():
            for (s, p, o) in g:
                if s in replacement:
                    g.remove((s, p, o))
                    g.add((replacement[s], p, o))
                    
        # In a separate named graph state that the source URI is part of that proxy
        proxy_named_graph = named_graph_uri + "#membership"
        graph = dataset.graph(proxy_named_graph)
        for (subject, proxy_uri) in replacement.items():
            graph.add((proxy_uri, OWL.sameAs, subject))
    
    def _replace_objects_by_proxies(self, dataset):
        '''
        Replace all the objects by the equivalent proxy URI in one exists.
        Contrary to what is done with the subjects we do not create a proxy
        if one does not already exist. Creating such proxy will eventually
        happen if the object can be crawled and indexed. In this case the
        replacement will be done when this happens.
        '''
        # Get a proxy URI for each of the object
        replacement = {}
        for obj in dataset.objects():
            if self.index_store.has_proxy(obj):
                proxy_uri = self.get_proxy_uri(obj)
                logger.info("Found a proxy {}".format(proxy_uri))
                replacement[object] = proxy_uri
            
        # In all the graphs replace the subjects by the proxy URI
        for g in dataset.graphs():
            for (s, p, o) in g:
                if o in replacement:
                    g.remove((s, p, o))
                    g.add((s, p, replacement[o]))
    
    def _update_collections(self, dataset):
        '''
        -> every proxy is partOf the document URI that provided it
        -> every proxy is partOf everything
        -> every proxy is partOf the specific collections that apply to it
        '''
        # Add to the collection 'everything'
        #self.collections.add_to_collection('everything', proxy_uri)
    
        # Add to the collection corresponding to its type
        #subject = [s for s in entity.subjects()][0]
        #proxy_type = entity.value(subject, RDF.type).toPython()
        #if proxy_type in self.collections.TYPE_COLLECTIONS:
        #    (name, label, description) = self.collections.TYPE_COLLECTIONS[proxy_type]
        #    if not self.collections.contains(name):
        #        self.collections.create(name, label, description)
        #    self.collections.add_to_collection(name, proxy_uri)
            
        # Add to the collection for this source domain
        #hostname = urlparse(uri).hostname
        #name = hostname.replace('.', '_')
        #label = hostname
        #description = 'Everything with data coming from {}'.format(hostname)
        #if not self.collections.contains(name):
        #    self.collections.create(name, label, description)
        #self.collections.add_to_collection(name, proxy_uri)
        pass
    
    def _load_rules(self, rules_file_name):
        # Rules are stored in hash map
        rules = {}
        
        # Load the rule base into memory
        logger.debug('Loading {}'.format(rules_file_name))
        g = Graph().parse(rules_file_name, format="turtle")
        
        # Extract the namespaces from the rule base
        r_ns = {}
        for (ns, uri) in g.namespaces():
            r_ns[ns] = uri
        
        # Compose and prepare the SPARQL queries
        for s in g.subjects(RDF.type):
            # Extract the type and see if it is a known one
            r_t = g.value(s, RDF.type)
            if r_t not in [INDEXER.DescriptionRule]:
                continue
            # Extract the components of the rule
            r_if = g.value(s, INDEXER['if']).toPython().replace('\t', '')
            r_then = g.value(s, INDEXER['then']).toPython().replace('\t', '')
            rule = 'CONSTRUCT {' + r_then + '} WHERE {' + r_if + '}'
            # Pre-load the rule
            rules[s.toPython()] = prepareQuery(rule, initNs=r_ns)
    
        return rules
    
    def _apply_rules(self, dataset, input_graph, named_graph_uri):
        '''
        Execute all the processing rules against the graph passed as parameter
        and return them as an array of graph.
        
        @param input_graph: the data graph to process in search for entities
        @param named_graph_uri: the URI of the named graph identifying the processing
        '''
        # Apply all the rules one by one
        for (name, rule) in self.rules.items():
            # Apply the rule
            graph = input_graph.query(rule).graph
            if len(graph) == 0:
                continue
            logger.debug('Found a match for {}'.format(name))
                
            # Defined a named graph corresponding to source+rule
            fragment = urlparse(name).fragment
            rule_named_graph = named_graph_uri + "#" + fragment
            
            # Add the graph statements in the named graph of the result data set
            g = dataset.graph(rule_named_graph)
            for st in graph:
                g.add(st)
                graph.remove(st)
            
        return dataset
    
