# coding=utf8
import os

from flask import render_template, send_from_directory, request, redirect, g
from flask.helpers import make_response, url_for
from indexer.storage.proxy import ProxyStore
from indexer.storage.collection import CollectionStore
from indexer.app import application, configuration
from indexer.app.conneg import negotiate, SUFFIX_TO_MIME
from rdflib.graph import Graph

# Debug logging
DEBUG = True

logger = application.logger

def do_search(g, request, params, collection=None):
    # Get the results for the search
    logger.debug(request.base_url)
    graph = g.proxies.search(request.base_url + "#id", params, collection)
        
    # Negotiate the output
    return negotiate(graph, 'search_results.html', request)

def redirect_with_args(target, args):
    '''
    Convenience function to prepare a redirect response
    '''
    redirect_url = url_for('index', **args)
    response = make_response('See Other',303)
    response.headers['Location'] = redirect_url
    response.headers['Accept'] = request.headers['Accept']
    return response
    
@application.before_request
def before_request():
    # Instantiate the proxy store and collections store
    g.proxies = ProxyStore(base = configuration.base(), store = configuration.stardog())
    g.collections = CollectionStore(base = configuration.base(), store = configuration.stardog())

@application.teardown_request
def teardown_request(exception):
    g.proxies.close()
    g.collections.close()
    
@application.route('/', methods=['GET'])
def home():
    '''
    Route to the home page
    '''
    return redirect_with_args('index', request.args)

@application.route('/index', methods=['GET'])
def index():
    '''
    Show the index of the dataset or search in it
    '''
    # If there are some parameters to the GET redirect to 'everything' to
    # issue a search against all the collection
    if len(request.args) != 0:
        return redirect_with_args('everything', request.args)

    # TODO Query for the list of collection and render the corresponding VoID
    # compose all in a graph and return that graph for negotiation
    graph = Graph
    
    return negotiate(graph, 'content.html', request)
    
@application.route('/<identifier>', methods=['GET'])
def get_resource(identifier):
    '''
    Route to get a specific identifier. This identifier may be proxy or
    a collection
    '''
    # If there are some parameters to the GET and if the requested
    # resource is a collection issue a search within the collection
    if len(request.args) != 0:
        if 'uri' in request.args:
            # This is a look-up request, try to find a proxy
            uri = g.proxies.lookup(request.args.get('uri'))
            if uri != None:
                return redirect(uri, code=302)
        else:
            # Do the search
            return do_search(request, request.args)
        
        if g.collections.contains(identifier):
            # Do the search
            return do_search(g, request, request.args, identifier)
    
    # Get the data
    graph = g.proxies.get_proxy(request.base_url.split('.')[0] + "#id")

    # Render the content
    return negotiate(graph, 'content.html', request)

    
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
