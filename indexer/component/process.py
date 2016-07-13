'''
Created on 8 May 2016

@author: guerec01
'''
from indexer.storage.cache import CacheStore
from indexer.storage.index import IndexStore
from urllib.parse import urlparse
from rdflib.namespace import RDF, OWL, FOAF, RDFS
from rdflib.graph import Dataset, Graph
from indexer.util.namespaces import INDEXER, PROV
from rdflib.plugins.sparql.processor import prepareQuery
import hashlib

import logging
from rdflib.term import URIRef, Literal, BNode
import uuid
import datetime
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

        # Keep track of the starting time
        start_time = Literal(datetime.datetime.now())
            
        # Retrieve the graph
        input_graph = self.cache_store.retrieve(uri)
        
        # We define a named graph with the hash of the source. This way
        # different versions of the same document will overwrite the triples
        # previously generated from it        
        hashed_uri = hashlib.sha256(uri.encode()).hexdigest()
        named_graph_base = URIRef('{}{}'.format(self.base, hashed_uri))
        
        # Defined a number of graph URIs
        named_graph_uri = named_graph_base + "#id"
        prov_uri = named_graph_base + "#prov"
        data_uri = named_graph_base + "#data"
        activity_uri = BNode()
        
        # Initialise the data set that will be generated from processing
        # the graph.
        dataset = Dataset()
        
        # Extract a data set from applying the rules
        self._apply_rules(dataset.graph(data_uri), input_graph)
        logger.debug('Generated {} triples using the rules'.format(len(dataset)))
        
        # Change the subjects and objects to use proxy URIs instead of the
        # subjects and objects currently used
        proxies_map = self._replace_subjects_by_proxies(dataset.graph(data_uri))
        self._replace_objects_by_proxies(dataset.graph(data_uri))
        
        # Add some more information about the collections
        self._update_collections(dataset.graph(data_uri))

        # Keep track of the end time
        end_time = Literal(datetime.datetime.now())
        
        # Add some provenance information
        prov_graph = dataset.graph(prov_uri)
        prov_graph.add((data_uri, RDF.type, PROV.Entity))
        prov_graph.add((data_uri, PROV.wasDerivedFrom, URIRef(uri)))
        prov_graph.add((data_uri, PROV.wasGeneratedBy, activity_uri))
        prov_graph.add((activity_uri, PROV.used, URIRef(uri)))
        prov_graph.add((activity_uri, PROV.startedAtTime, start_time))
        prov_graph.add((activity_uri, PROV.endedAtTime, end_time))
        
        # Describe the document we just created
        default_graph = dataset.graph(named_graph_base)
        default_graph.add((named_graph_base, RDF.type, FOAF.Document))
        default_graph.add((named_graph_base, RDFS.label, 
                           Literal("Outcome of the processing of <{}>".format(uri))))
        default_graph.add((named_graph_base, FOAF.primaryTopic, named_graph_uri))
        
        # Store the generated dataset in the index   
        ok = self.index_store.store(dataset)
        
        # If we managed to store that data we may need to change all the 
        # references made to the subjects we just created a new proxy for
        if ok:
            self.index_store.update_uris(proxies_map)
        
    def _replace_subjects_by_proxies(self, graph):
        '''
        Replace all the subjects by the equivalent proxy URI in one exists.
        Then update the set of sameAs relation to keep track of the appartenance
        of all those subjects to the proxy
        '''
        # Prepare a map of replacements
        replacement = {}
        for subj in graph.subjects():
            logger.debug("Dealing with {}".format(subj))
                        
            # If we already dealt with this subject move on
            # also skip everything that is not a URIRef
            if subj in replacement or not isinstance(subj, URIRef):
                continue

            # Get all the things this subject is a sameAs of either as a subject
            # or as an object. Combine that into a set of subjects all equivalent
            # to each other. That set only considers the data available in the
            # document being currently processed as passed on by "graph"
            sameAsO = set([o for o in graph.objects(subj, OWL.sameAs)])
            sameAsS = set([s for s in graph.subjects(OWL.sameAs, subj)])
            subjects = sameAsO | sameAsS | set([subj])
            logger.info("Looking for a proxy any of {}".format(subjects))
            
            # Try first to find a proxy we just created for one of the subjects
            proxy_uri = None 
            for subject in subjects:
                if subject in replacement:
                    proxy_uri = replacement[subject]
                    
            # Try to find a proxy already existing for one of the subjects
            if proxy_uri == None:
                for subject in subjects:
                    if self.index_store.has_proxy(subject):
                        proxy_uri = self.get_proxy_uri(subject)
                    
            # If we have not found any create a new one
            if proxy_uri == None:
                proxy_uri = URIRef("{}{}#id".format(self.base, uuid.uuid1()))
                logger.info("Created <{}>".format(proxy_uri))
            else:
                logger.info("Found <{}>".format(proxy_uri))
                
            # Save the mapping
            replacement[subj] = proxy_uri

            # Also add an RDF statement to state that equivalence
            graph.add((proxy_uri, OWL.sameAs, subj))
            
        # In all the graphs replace the subjects by their proxy URI
        for (s, p, o) in graph:
            if s in replacement:
                graph.remove((s, p, o))
                graph.add((replacement[s], p, o))
    
        # Return the replacement map
        return replacement
    
    def _replace_objects_by_proxies(self, graph):
        '''
        Replace all the objects by the equivalent proxy URI in one exists.
        Contrary to what is done with the subjects we do not create a proxy
        if one does not already exist. Creating such proxy will eventually
        happen if the object can be crawled and indexed. In this case the
        replacement will be done when this happens.
        '''
        # Get a proxy URI for each of the object
        replacement = {}
        for obj in graph.objects():
            # If we already dealt with this object move on
            # also skip everything that is not a URIRef
            if obj in replacement or not isinstance(obj, URIRef):
                continue
            
            # Get the proxy URI if there is one
            if self.index_store.has_proxy(obj):
                replacement[obj] = self.get_proxy_uri(obj)
            
        # In all the graphs replace the subjects by the proxy URI
        for (s, p, o) in graph:
            if o in replacement:
                graph.remove((s, p, o))
                graph.add((s, p, replacement[o]))
    
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
        for s in g.subjects(RDF.type, INDEXER.Rule):
            # Extract the components of the rule
            r_if = g.value(s, INDEXER['if']).toPython().replace('\t', '')
            r_then = g.value(s, INDEXER['then']).toPython().replace('\t', '')
            rule = 'CONSTRUCT {' + r_then + '} WHERE {' + r_if + '}'
            
            # Pre-load the rule
            rules[s.toPython()] = prepareQuery(rule, initNs=r_ns)
    
        return rules
    
    def _apply_rules(self, output_graph, input_graph):
        '''
        Execute all the processing rules against the graph passed as parameter
        and return them as an array of graph.
        
        @param output_graph: the target graph to put the result of the rules in
        @param input_graph: the data graph to process in search for entities
        '''
        # Apply all the rules one by one
        for (name, rule) in self.rules.items():
            # Apply the rule, the result is an RDF graph
            tmp_graph = input_graph.query(rule).graph
            if len(tmp_graph) == 0:
                continue
            logger.debug('Found a match for {}'.format(name))
                
            # Add the graph statements in the named graph
            for st in tmp_graph:
                output_graph.add(st)
                tmp_graph.remove(st)
        