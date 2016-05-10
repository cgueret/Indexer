'''
Created on 8 May 2016

@author: guerec01
'''
from storage.config import BASE, SPARQL, SPARUL
from SPARQLWrapper import SPARQLWrapper, POST, JSON
from rdflib.graph import Graph
from rdflib.namespace import RDF, VOID, RDFS, DCTERMS, Namespace, FOAF
from rdflib.term import Literal, URIRef

import logging
logger = logging.getLogger(__name__)

SCHEMA = Namespace("http://schema.org/")
PO = Namespace("http://purl.org/ontology/po/")

class CollectionStore(object):
    '''
    Interface to the store containing the data about the collections
    '''
    TYPE_COLLECTIONS = {
        FOAF.Image : ('images', 'Images', 'All the images'),
        PO.TVContent : ('videos', 'Videos', 'All the TV content')
        }

    def __init__(self):
        '''
        Constructor
        '''        
        # Verify that we have the default collection 'Everything'
        if not self.contains('everything'):
            # Create it if needed
            self.create('everything', 'Everything', 'Everything in this database')
    
    def get_uri(self, name):
        '''
        Return the URI of a collection

        @param name: the name of the collection
        '''
        return BASE + name 
    
    def contains(self, name):
        '''
        Returns True if a collection with the given name exists in the
        collection store
        
        @param name: the name of the collection
        '''
        # Get the URI for this collection
        uri = self.get_uri(name)
        logger.debug('Check if the collection \"{}\" exists'.format(uri))
        
        # Prepare the query
        query = """
        PREFIX void: <http://rdfs.org/ns/void#>
        ASK { <__URI__> a void:Dataset. }
        """.replace("__URI__", uri)
        sparql = SPARQLWrapper(SPARQL)
        sparql.setQuery(query)
        sparql.setReturnFormat(JSON)
        
        # Execute it
        res = sparql.query().convert()["boolean"]
        return res

    def create(self, name, label, description):
        '''
        Create a new collection and return its URI
        
        @param name: the name of the collection
        @param label: a short label
        @param description: a longer blob of text describing the collection
        '''        
        # Get the URI for this collection
        uri = self.get_uri(name)
        logger.debug("Create collection {}".format(uri))
        
        # Create and populate the description of the collection
        graph = Graph()
        graph.add((URIRef(uri), RDF.type, VOID.Dataset))
        graph.add((URIRef(uri), RDFS.label, Literal(label)))
        graph.add((URIRef(uri), RDFS.comment, Literal(description)))
        data = graph.serialize(format="nt").decode()
        
        # Prepare the query
        query = """
        INSERT DATA {
            __PAYLOAD__
        }
        """.replace("__PAYLOAD__", data)
        sparql = SPARQLWrapper(SPARUL)
        sparql.setQuery(query)
        sparql.setMethod(POST)
        
        # Execute it
        sparql.query()

        # Return the uri of the collection        
        return uri
    
    def add_to_collection(self, name, uri):
        '''
        Add a URI has a member of a collection
        
        @param name: the name of the collection
        @param uri: the uri of the resource to add as a member
        '''
        # Get the URI for this collection
        collection_uri = self.get_uri(name)
        
        # Create and populate the description of the membership
        graph = Graph()
        graph.add((URIRef(uri), DCTERMS.isPartOf, URIRef(collection_uri)))
        data = graph.serialize(format="nt").decode()
        
        # Prepare the query
        query = """
        INSERT DATA {
            __PAYLOAD__
        }
        """.replace("__PAYLOAD__", data)
        sparql = SPARQLWrapper(SPARUL)
        sparql.setQuery(query)
        sparql.setMethod(POST)
        
        # Execute it
        sparql.query()
        