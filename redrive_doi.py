#!/usr/bin/python

import getpass
import json
import string
import urllib2

def get_request(url, session=None):
    request = urllib2.Request(url)
    request.add_header('Accept', 'application/json')
    request.add_header('Content-Type', 'application/json')
    if session is not None:
        request.add_header('sessionToken', session)
    return request

def get_results(request, data=None, put=None):
    if put is not None:
        request.get_method = lambda: 'PUT'
    try:
        response = urllib2.urlopen(url=request, data=data)
        response_body = response.read()
        response.close()
        results = json.loads(response_body)
        return results
    except urllib2.HTTPError as e:
        print e.code, e.msg

def login(email, password):
    url = 'https://repo-staging.prod.sagebase.org/auth/v1/session'
    request = get_request(url)
    data = json.dumps({'email' : email, 'password' : password})
    results = get_results(request, data)
    return results['sessionToken']

def put_doi(session, entity_id, version=None):
    url = 'https://repo-staging.prod.sagebase.org/repo/v1/entity/' + entity_id
    if version is not None:
        url = url + '/version/' + version
    url = url + '/doi'
    request = get_request(url, session)
    results = get_results(request=request, put='put')
    return results

email = raw_input('Email: ')
password = getpass.getpass('Password: ')
session = login(email, password)
results = put_doi(session=session, entity_id='syn1856613')
print results
results = put_doi(session=session, entity_id='syn2320764')
print results
results = put_doi(session=session, entity_id='syn2344234')
print results
results = put_doi(session=session, entity_id='syn1876281', version='1')
print results
