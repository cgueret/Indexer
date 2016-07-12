@when(u'I count the amount of relevant entities that are ingested')
def step_impl(context):
    raise NotImplementedError(u'STEP: When I count the amount of relevant entities that are ingested')

@when(u'a proxy exists for "{target}"')
def step_impl(context):
    raise NotImplementedError(u'STEP: When a proxy exists for "{target}"')

@then(u'the number of relevant entities in the collection should be the same')
def step_impl(context):
    raise NotImplementedError(u'STEP: Then the number of relevant entities in the collection should be the same')

@when(u'the proxy is associated with "{target}"\'s proxy')
def step_impl(context):
    raise NotImplementedError(u'STEP: When the proxy is associated with "{target}"\'s proxy')

@when(u'the proxy is listed in the graph of "{target}"\'s proxy')
def step_impl(context, target):
    raise NotImplementedError(u'STEP: When the proxy is listed in the graph of "{target}"\'s proxy')

@when(u'I search for media for "{audience}"')
def step_impl(context, audience):
    raise NotImplementedError(u'STEP: When I search for media for "http://shakespeare.acropolis.org.uk/#members"')

@then(u'the proxy is listed in the search results')
def step_impl(context):
    raise NotImplementedError(u'STEP: Then the proxy is listed in the search results')