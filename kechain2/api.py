from kechain2.client import Client


client = Client()


def login(*args, **kwargs):
    return client.login(*args, **kwargs)


def parts(*args, **kwargs):
    return client.parts(*args, **kwargs)


def part(*args, **kwargs):
    return client.part(*args, **kwargs)


# def scopes(name=None, status='ACTIVE'):
#     r = client.session.get(api_url('scopes'), headers=HEADERS, params={
#         'name': name,
#         'status': status
#     })
#
#     assert r.status_code == 200, "Could not retrieve scopes"
#
#     data = r.json()
#
#     return [Scope(s) for s in data['results']]
#
#
# def scope(*args, **kwargs):
#     _scopes = scopes(*args, **kwargs)
#
#     assert len(_scopes) > 0, "No scope fits criteria"
#     assert len(_scopes) == 1, "Multiple scopes fit criteria"
#
#     return _scopes[0]
#
#
# def activities(name=None):
#     r = client.session.get(api_url('activities'), headers=HEADERS, params={
#         'name': name
#     })
#
#     assert r.status_code == 200, "Could not retrieve activities"
#
#     data = r.json()
#
#     return [Activity(a) for a in data['results']]
#
#
# def activity(*args, **kwargs):
#     _activities = activities(*args, **kwargs)
#
#     assert len(_activities) > 0, "No activity fits criteria"
#     assert len(_activities) == 1, "Multiple activities fit criteria"
#
#     return _activities[0]
#
#
# def part(*args, **kwargs):
#     _parts = parts(*args, **kwargs)
#
#     assert len(_parts) > 0, "No part fits criteria"
#     assert len(_parts) == 1, "Multiple parts fit criteria"
#
#     return _parts[0]
#
#
# def model(*args, **kwargs):
#     kwargs['category'] = 'MODEL'
#     _parts = parts(*args, **kwargs)
#
#     assert len(_parts) > 0, "No model fits criteria"
#     assert len(_parts) == 1, "Multiple models fit criteria"
#
#     return _parts[0]
#
#
# def properties(name=None, category='INSTANCE'):
#     r = client.session.get(api_url('properties'), headers=HEADERS, params={
#         'name': name,
#         'category': category
#     })
#
#     assert r.status_code == 200, "Could not retrieve properties"
#
#     data = r.json()
#
#     return [Property(p) for p in data['results']]
