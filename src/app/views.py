# coding=utf8
import os

from app import application
from flask import render_template, send_from_directory

from rdflib.namespace import Namespace

OLO = Namespace("http://purl.org/ontology/olo/core#")
MRSS = Namespace("http://search.yahoo.com/mrss/")
SCHEMA = Namespace("http://schema.org/")

@application.route('/')
def home():
    '''
    Route to the home page
    '''
    # TODO If there are some parameters to the GET issue a search
    return render_template('index.html')

@application.route('/<resource>', methods=['GET'])
def getResource():
    '''
    Route to get a specific resource. This resource may be proxy or
    a collection
    '''
    # TODO If there are some parameters to the GET and if the requested
    # resource is a collection issue a search    
    return render_template('resource.html')
        
@application.route('/favicon.ico')
def favicon():
    '''
    Favicon
    '''
    # TODO redirect to asset
    pass

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
    complete_path = os.path.join(os.path.join(root, 'static'), path)
    (head, tail) = os.path.split(complete_path)
    return send_from_directory(head, tail, mimetype=mimetype)
