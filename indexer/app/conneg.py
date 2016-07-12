import os
from rdflib.term import URIRef
from rdflib.namespace import RDFS, RDF, DCTERMS
from indexer.util.namespaces import OLO
from flask.templating import render_template
from flask.helpers import make_response
from werkzeug.http import parse_accept_header

import logging
logger = logging.getLogger(__name__)

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

def graph_to_python(request, graph):
    '''
    Convert a graph representing search results into a python structure
    usable by the template engine
    '''
    # Prepare the map of data to pass on to the template
    base = request.base_url.split('.')[0]
    data = {'description': {}, 'related': {}, 'base': base}
        
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
