import io

import requests
import sys

from kechain.query import PartSet
from .globals import data
from .part import Part

api_parts_url = 'http://0.0.0.0:8000/api/parts.json'
api_property_url = 'http://0.0.0.0:8000/api/properties/{0}.json'

def set_activity(activity_id):
    data.activity_id = activity_id


def set_auth_token(token):
    data.api_headers['Authorization'] = 'Token ' + token


def retrieve_parts():
    old_part_ids = set(part.id for part in data.parts)

    r = requests.get(api_parts_url, headers=data.api_headers, params={
        'activity_id': data.activity_id
    })

    if not r.status_code == 200:
        print(r.json()["results"][0]["detail"], file=sys.stderr)
        return

    raw_data = r.json()

    data.parts[:] = [Part.from_dict(part_data)
                     for part_data
                     in raw_data['results']
                     if part_data['category'] == 'INSTANCE']

    new_part_ids = set(part.id for part in data.parts)

    refreshed_parts = len(old_part_ids & new_part_ids)
    if refreshed_parts:
        print("Refreshed {0} parts".format(refreshed_parts))

    retrieved_parts = len(new_part_ids - old_part_ids)
    if retrieved_parts:
        print("Retrieved {0} parts".format(retrieved_parts))

    removed_parts = len(old_part_ids - new_part_ids)
    if removed_parts:
        print("Removed {0} parts".format(removed_parts))


def update_properties():
    updated_properties = 0

    for part in data.parts:
        for prop in part.properties:
            if prop.dirty:

                r = requests.put(api_property_url.format(prop.id), headers=data.api_headers, json={
                    'value': prop.value
                })

                assert r.status_code == 200

                updated_properties += 1

            prop._dirty = False

    if updated_properties:
        print("Updated {0} properties".format(updated_properties))


def find_part(name):
    return next(part for part in data.parts if part.name == name)


def find_parts(name):
    return PartSet(part for part in data.parts if part.model['name'] == name)


def sync(push=True, pull=True):
    if push:
        update_properties()

    if pull:
        retrieve_parts()