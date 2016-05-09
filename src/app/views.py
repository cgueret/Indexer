# coding=utf8
import os

from app import application, proxy_store
from flask import render_template, send_from_directory, request, redirect
from rdflib.namespace import Namespace

OLO = Namespace("http://purl.org/ontology/olo/core#")
MRSS = Namespace("http://search.yahoo.com/mrss/")
SCHEMA = Namespace("http://schema.org/")

# Test queries
# http://acropolis.org.uk/?uri=http://dbpedia.org/resource/Venus_and_Adonis_(Shakespeare_poem)

@application.route('/')
def home():
    '''
    Route to the home page
    '''
    # If there are some parameters to the GET issue a search
    if len(request.args) != 0:
        if 'uri' in request.args:
            # This is a look-up request, try to find a proxy
            uri = proxy_store.lookup(request.args.get('uri'))
            if uri != None:
                return redirect(uri, code=302)
        else:
            # Any other kind of search
            results = proxy_store.search(request.args)
            return render_template('search_results.html', results=results)
        
    return render_template('index.html')

@application.route('/<identifier>', methods=['GET'])
def getResource(identifier):
    '''
    Route to get a specific identifier. This identifier may be proxy or
    a collection
    '''
    # If there are some parameters to the GET and if the requested
    # resource is a collection issue a search within the collection
    if len(request.args) != 0:
        if proxy_store.contains_collection(identifier):
            request.args.set('collection', identifier)
            results = proxy_store.search(request.args)
            return render_template('search_results.html', results)
    
    # Render the resource
    graph = proxy_store.get_proxy(request.base_url + "#id")
    
    # Turn the graph into something easier to process in the template
    data = []
    for (_, predicate, obj) in graph:
        data.append((predicate.toPython(), obj.toPython()))
    return render_template('resource.html', data=data)
        
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
    mimetypes = {
        ".css": "text/css",
        ".html": "text/html",
        ".js": "application/javascript",
        ".ico": "image/vnd.microsoft.icon",
        ".woff": "application/x-font-woff",
        ".ttf": "font/ttf"
    }
    mimetype = mimetypes.get(os.path.splitext(path)[1], "text/html")
    root = os.path.abspath(os.path.dirname(__file__))
    complete_path = os.path.join(os.path.join(root, 'assets'), path)
    (head, tail) = os.path.split(complete_path)
    return send_from_directory(head, tail, mimetype=mimetype)
