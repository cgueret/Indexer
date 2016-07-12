#encoding: utf-8
Feature: Collections and associated media

Scenario: Number of proxies in the collection
	When I count the amount of relevant entities that are ingested
	And a proxy exists for "http://shakespeare.acropolis.org.uk/#id"
	Then the number of relevant entities in the collection should be the same

Scenario: Associated media
	When a proxy exists for "http://shakespeare.acropolis.org.uk/images/6731510#id"
	And the proxy is associated with "http://dbpedia.org/resource/Judi_Dench"'s proxy
	And the proxy is listed in the graph of "http://dbpedia.org/resource/Judi_Dench"'s proxy

Scenario: Media correctly licensed
	When I search for media for "http://shakespeare.acropolis.org.uk/#members"
	And a proxy exists for "http://shakespeare.acropolis.org.uk/images/6731510#id"
	Then the proxy is listed in the search results