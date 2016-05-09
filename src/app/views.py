# coding=utf8
import os

from app import application, proxy_store
from flask import render_template, send_from_directory, request, redirect
from rdflib.namespace import Namespace, RDF, RDFS
from rdflib.graph import Graph
from rdflib.term import URIRef, BNode, Literal
from werkzeug.http import parse_accept_header
from flask.helpers import make_response, url_for

OLO = Namespace("http://purl.org/ontology/olo/core#")
MRSS = Namespace("http://search.yahoo.com/mrss/")
SCHEMA = Namespace("http://schema.org/")

logger = application.logger

# Test queries
# http://acropolis.org.uk/?uri=http://dbpedia.org/resource/Venus_and_Adonis_(Shakespeare_poem)

SUFFIX_TO_MIME = {
    ".ttl":"text/turtle",
    ".css": "text/css",
    ".html": "text/html",
    ".js": "application/javascript",
    ".ico": "image/vnd.microsoft.icon",
    ".woff": "application/x-font-woff",
    ".ttf": "font/ttf"
}

def negotiate(graph, html_template, request):
    '''
    Negotiate the response to return
    
    @param graph: the RDF graph containing the data to render
    @param html_template: the template to use for HTML responses
    @param headers: the request headers
    @param suffix: the suffix used for the query URL
    '''
    # Serve HTML by default
    mimetype = 'text/html'
        
    # Use the accept header if it was provided
    if 'Accept' in request.headers:
        mimetype = parse_accept_header(request.headers['Accept']).best
    
    # If a known suffix was asked use that instead of the accept header
    ext = os.path.splitext(request.url)[1]
    if ext in SUFFIX_TO_MIME:
        mimetype = SUFFIX_TO_MIME[ext]
    
    logger.debug("Will serve {}".format(mimetype))
    
    # Serve HTML
    if mimetype in ['text/html','application/xhtml_xml','*/*']:
        data = {'description': {}, 'related':{}}
        # Extract basic properties from the graph
        data['description']['label'] = graph.value(URIRef(request.url), RDFS.label).toPython()
        
        # Turn the OLO slots into a array of associated resources
        for slot in graph.subjects(RDF.type, OLO.Slot):
            index = graph.value(subject=slot, predicate=OLO['index']).toPython()
            item = graph.value(subject=slot, predicate=OLO.item).toPython()
            data['related'][index] = item

        # Render the requested template
        return render_template(html_template, data=data)
    # Serve Turtle
    elif mimetype in ['text/turtle', 'application/x-turtle']:
        response = make_response(graph.serialize(format='turtle'))
        response.headers['Content-Type'] = mimetype
        return response
    # Serve N-triples
    elif mimetype in ['application/n-triples']:
        response = make_response(graph.serialize(format='nt'))
        response.headers['Content-Type'] = mimetype
        return response
    # Serve RDF+XML :-(
    elif mimetype in ['application/rdf+xml']:
        response = make_response(graph.serialize(format='pretty-xml'))
        response.headers['Content-Type'] = mimetype
        return response
    
def array_to_olo(uri, array):
    '''
    Turns an array into an OLO based graph using some uri as the subject
    
    @param uri: the subject of the graph to create
    @param array: the array of results to convert
    '''
    graph = Graph()
    graph.namespace_manager.bind('olo', OLO)
    for index in range(0, len(array)):
        slot = BNode()
        graph.add((slot, RDF.type, OLO.Slot))
        graph.add((slot, RDFS.label, Literal("Result #{}".format(index+1))))
        graph.add((slot, OLO['index'], Literal(index+1)))
        graph.add((slot, OLO.item, URIRef(array[index])))
        graph.add((uri, OLO.slot, slot))
    return graph

def do_search(request, params):
    # Get the results for the search
    results = proxy_store.search(params)
    
    # Turn the result array into a OLO sorted graph
    search_uri = URIRef(request.url)
    graph = array_to_olo(search_uri, results)
    
    # Add some nice text
    title = Literal("Everything containing \"{}\"".format(params['q']))
    graph.add((search_uri, RDFS.label, title))
    
    # Negotiate the output
    return negotiate(graph, 'search_results.html', request)
    
@application.route('/', methods=['GET'])
def home():
    '''
    Route to the home page
    '''
    args = request.args
    redirect_url = url_for('get_index', **args)

    response = make_response('Moved permanently',303)
    response.headers['Location'] = redirect_url
    response.headers['Accept'] = request.headers['Accept']
    return response

@application.route('/index', methods=['GET'])
def get_index():
    '''
    Show the index of the dataset or search in it
    '''
    # If there are some parameters to the GET issue a search
    if len(request.args) != 0:
        if 'uri' in request.args:
            # This is a look-up request, try to find a proxy
            uri = proxy_store.lookup(request.args.get('uri'))
            if uri != None:
                return redirect(uri, code=302)
        else:
            # Do the search
            return do_search(request, request.args)

    # TODO Query for the list of collection and render the corresponding VoID        
    return render_template('index.html')
    
@application.route('/<identifier>', methods=['GET'])
def get_resource(identifier):
    '''
    Route to get a specific identifier. This identifier may be proxy or
    a collection
    '''
    # If there are some parameters to the GET and if the requested
    # resource is a collection issue a search within the collection
    if len(request.args) != 0:
        if proxy_store.contains_collection(identifier):
            # Add the collection to the target arguments
            request.args.set('collection', identifier)
            # Do the search
            return do_search(request, request.args)
    
    # Get the data
    graph = proxy_store.get_proxy(request.base_url.split('.')[0] + "#id")

    # Render the content
    return negotiate(graph, 'resource.html', request)

        
@application.route('/favicon.ico')
def favicon():
    '''
    Favicon
    '''
    return redirect('/assets/favicon.ico', code=303)

@application.errorhandler(404)
def page_not_found(error):
    '''
    404 handle
    '''
    return render_template('page_not_found.html'), 404

@application.route('/assets/<path:path>')
def get_asset(path):
    '''
    Assets
    '''
    mimetype = SUFFIX_TO_MIME.get(os.path.splitext(path)[1], "text/html")
    root = os.path.abspath(os.path.dirname(__file__))
    complete_path = os.path.join(os.path.join(root, 'assets'), path)
    (head, tail) = os.path.split(complete_path)
    return send_from_directory(head, tail, mimetype=mimetype)
