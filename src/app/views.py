# coding=utf8
import os

from app import application, collections, proxies
from flask import render_template, send_from_directory, request, redirect
from rdflib.namespace import Namespace, RDF, RDFS, DCTERMS
from rdflib.graph import Graph
from rdflib.term import URIRef, BNode, Literal
from werkzeug.http import parse_accept_header
from flask.helpers import make_response, url_for

MRSS = Namespace("http://search.yahoo.com/mrss/")
SCHEMA = Namespace("http://schema.org/")

logger = application.logger

# Test queries
# http://acropolis.org.uk/?uri=http://dbpedia.org/resource/Venus_and_Adonis_(Shakespeare_poem)

SUFFIX_TO_MIME = {
    ".ttl":"text/turtle",
    ".nt":"application/n-triples",
    ".rdf": "application/rdf+xml",
    ".rj": "application/rdf+json",
    ".css": "text/css",
    ".html": "text/html",
    ".js": "application/javascript",
    ".ico": "image/vnd.microsoft.icon",
    ".woff": "application/x-font-woff",
    ".ttf": "font/ttf"
}

OLO = Namespace("http://purl.org/ontology/olo/core#")

def graph_to_python(request, graph):
    '''
    Convert a graph representing search results into a python structure
    usable by the template engine
    '''
    # Prepare the map of data to pass on to the template
    base = request.base_url.split('.')[0]
    data = {'description': {}, 'related':{}, 'base': base}
    
    logger.debug(graph.serialize(format="turtle").decode())
        
    # Extract basic properties from the graph
    subj = URIRef(base + "#id")
    try:
        data['description']['label'] = graph.value(subj, RDFS.label).toPython()
    except:
        data['description']['label'] = ''
        
    # Turn the OLO slots into a array of associated resources
    for slot in graph.subjects(RDF.type, OLO.Slot):
        index = graph.value(slot, OLO['index']).toPython()
        item = graph.value(slot, OLO.item).toPython()
        logger.debug(item)
        label = graph.value(URIRef(item), RDFS.label).toPython()
        description = graph.value(URIRef(item), DCTERMS.description).toPython()
        data['related'][index] = {'uri':item, 
                                  'label':label,
                                  'description':description}
    
    return data

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
    logger.debug('{}'.format(len(graph)))
        
    # Use the accept header if it was provided
    if 'Accept' in request.headers:
        mimetype = parse_accept_header(request.headers['Accept']).best
        logger.debug("Asked for {} in content neg".format(mimetype))

    # If a known suffix was asked use that instead of the accept header
    ext = os.path.splitext(request.base_url)[1]
    if ext in SUFFIX_TO_MIME:
        mimetype = SUFFIX_TO_MIME[ext]
        logger.debug("Asked for {} using {}".format(mimetype, ext))
    
    logger.debug("Will serve {}".format(mimetype))
    
    # Serve HTML
    if mimetype in ['text/html','application/xhtml_xml','*/*']:
        # Get data usable by the template engine
        data = graph_to_python(request, graph)
        
        # Render the requested template
        return render_template(html_template, data=data)
    # Serve Turtle
    elif mimetype in ['text/turtle', 'application/x-turtle']:
        logger.debug(graph.serialize(format='turtle'))
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
    

def do_search(request, params):
    # Get the results for the search
    graph = proxies.search(request.url, params)
        
    # Negotiate the output
    return negotiate(graph, 'search_results.html', request)
    
@application.route('/', methods=['GET'])
def home():
    '''
    Route to the home page
    '''
    args = request.args
    redirect_url = url_for('index', **args)

    response = make_response('Moved permanently',303)
    response.headers['Location'] = redirect_url
    response.headers['Accept'] = request.headers['Accept']
    return response

@application.route('/index', methods=['GET'])
def index():
    '''
    Show the index of the dataset or search in it
    '''
    # If there are some parameters to the GET issue a search
    if len(request.args) != 0:
        if 'uri' in request.args:
            # This is a look-up request, try to find a proxy
            uri = proxies.lookup(request.args.get('uri'))
            if uri != None:
                return redirect(uri, code=302)
        else:
            # Do the search
            return do_search(request, request.args)

    # TODO Query for the list of collection and render the corresponding VoID        
    data = {'base': request.base_url.split('.')[0]}
    return render_template('index.html', data=data)
    
@application.route('/<identifier>', methods=['GET'])
def get_resource(identifier):
    '''
    Route to get a specific identifier. This identifier may be proxy or
    a collection
    '''
    # If there are some parameters to the GET and if the requested
    # resource is a collection issue a search within the collection
    if len(request.args) != 0:
        if collections.contains(identifier):
            # Add the collection to the target arguments
            request.args.set('collection', identifier)
            # Do the search
            return do_search(request, request.args)
    
    # Get the data
    graph = proxies.get_proxy(request.base_url.split('.')[0] + "#id")

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
