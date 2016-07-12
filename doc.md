http://docs.stardog.com/#_user_defined_rule_reasoning

# Harvester

The Harvester interact with the document store to see which of the RDF documents
need to be refreshed or fetched. Every document for which the last harvest date
is non existent of beyond the freshness threshold is harvested.

The harvesting process consists in:
* Fetching the RDF at the target URI
* Extract from the RDF some meta-data
* Enrich the meta-data with the current date as last harvest date
* Push the RDF payload to the document store as binary and attach the meta-data
* If that URI is ok for further exploration, add all the related documents (objectProperties)
to the document store - without payload - and mark those as not being ok for
further exploration


# Useful doc
https://lawlesst.github.io/notebook/rdflib-stardog.html
http://toolbelt.readthedocs.io/en/latest/uploading-data.html#streaming-multipart-data-encoder
