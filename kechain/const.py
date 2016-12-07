

API_ROOT = 'http://0.0.0.0:8000/'

API_PATH = {
    'parts': 'api/parts.json',
    'property': 'api/properties/{property_id}.json'
}


def API(resource, **kwargs):
    return API_ROOT + API_PATH[resource].format(**kwargs)
