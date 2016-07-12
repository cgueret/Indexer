from negotiator import ContentNegotiator, AcceptParameters, ContentType

class Conneg:
    DEFAULT = AcceptParameters(ContentType('text/turtle'))
    
    ACCEPTABLE = [DEFAULT,
        AcceptParameters(ContentType('application/rdf+xml')),
        AcceptParameters(ContentType('text/n3')),
        AcceptParameters(ContentType('application/n-quads')),
        AcceptParameters(ContentType('application/n-triples')),
        AcceptParameters(ContentType('application/trix'))]

    NEGOTIATOR = ContentNegotiator(DEFAULT, ACCEPTABLE)

    CONTENT_TYPE2FORMAT= {
        'application/rdf+xml': 'pretty-xml',
        'text/turtle': 'turtle',
        'text/n3': 'n3',
        'application/n-quads': 'nquads',
        'application/n-triples': 'nt',
        'application/trix': 'trix'
    }

    @staticmethod
    def content_type(request):
        if request.headers.has_key('Accept'):
            acceptable = Conneg.NEGOTIATOR.negotiate(accept=request.headers['Accept'])
            if acceptable:
                return str(acceptable.content_type)
    return None
