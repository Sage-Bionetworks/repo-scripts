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
    url = 'https://auth-staging.prod.sagebase.org/auth/v1/session'
    request = get_request(url)
    data = json.dumps({'email' : email, 'password' : password})
    results = get_results(request, data)
    return results['sessionToken']

def get_user_group(session, group_name):
    url = 'https://repo-staging.prod.sagebase.org/repo/v1/userGroupHeaders?prefix='
    url = url + group_name
    request = get_request(url, session)
    results = get_results(request)
    for group in results['children']:
        if not group['isIndividual']:
            return int(group['ownerId'])
    return None

def get_eval_permissions(session, eval_id):
    url = 'https://repo-staging.prod.sagebase.org/repo/v1/evaluation/'
    url = url + eval_id
    url = url + '/permissions'
    request = get_request(url, session)
    permissions = get_results(request)
    return permissions

def get_eval(session, eval_id):
    url = 'https://repo-staging.prod.sagebase.org/repo/v1/evaluation/'
    url = url + eval_id
    request = get_request(url, session)
    return get_results(request)

def get_eval_acl(session, eval_id):
    url = 'https://repo-staging.prod.sagebase.org/repo/v1/evaluation/'
    url = url + eval_id
    url = url + '/acl'
    request = get_request(url, session)
    acl = get_results(request)
    return acl

def update_eval_acl(session, acl):
    url = 'https://repo-staging.prod.sagebase.org/repo/v1/evaluation/acl'
    request = get_request(url, session)
    data = json.dumps(acl)
    acl = get_results(request, data, 'PUT')
    return acl

def backfill_acl(acl, owner_id, public_id, auth_id):
    # Remove owner, public, authenticated from the access control list
    owner_ra = None
    public_ra = None
    auth_ra = None
    ra_list = acl['resourceAccess']
    for ra in ra_list:
        if owner_id == ra['principalId']:
            owner_ra = ra
        elif public_id == ra['principalId']:
            public_ra = ra
        elif auth_id == ra['principalId']:
            auth_ra = ra
    if owner_ra is not None:
        ra_list.remove(owner_ra)
    if public_ra is not None:
        ra_list.remove(public_ra)
    if auth_ra is not None:
        ra_list.remove(auth_ra)
    # Owner has everything
    access_list = [
            'READ',
            'PARTICIPATE',
            'UPDATE_SUBMISSION',
            'UPDATE',
            'CHANGE_PERMISSIONS',
            'SUBMIT',
            'READ_PRIVATE_SUBMISSION',
            'DELETE_SUBMISSION',
            'CREATE',
            'DELETE']
    owner_ra = {'accessType' : access_list, 'principalId' : owner_id}
    ra_list.append(owner_ra)
    # Authenticated users can READ, PARTICIATE, and SUBMIT
    access_list = [
            'READ',
            'PARTICIPATE',
            'SUBMIT']
    auth_ra = {'accessType' : access_list, 'principalId' : auth_id}
    ra_list.append(auth_ra)
    # Public can READ
    access_list = ['READ']
    public_ra = {'accessType' : access_list, 'principalId' : public_id}
    ra_list.append(public_ra)
    return acl

def validate_backfill(acl, owner_id, public_id, auth_id):
    has_owner = False
    has_public = False
    has_auth = False
    ra_list = acl['resourceAccess']
    for ra in ra_list:
        pid = ra['principalId']
        access = ra['accessType']
        access.sort()
        if owner_id == pid:
            has_owner = True
            if len(access) <> 10:
                return False
            if access[0] <> 'CHANGE_PERMISSIONS':
                return False
            if access[1] <> 'CREATE':
                return False
            if access[2] <> 'DELETE':
                return False
            if access[3] <> 'DELETE_SUBMISSION':
                return False
            if access[4] <> 'PARTICIPATE':
                return False
            if access[5] <> 'READ':
                return False
            if access[6] <> 'READ_PRIVATE_SUBMISSION':
                return False
            if access[7] <> 'SUBMIT':
                return False
            if access[8] <> 'UPDATE':
                return False
            if access[9] <> 'UPDATE_SUBMISSION':
                return False
        elif public_id == pid:
            has_public = True
            if len(access) <> 1:
                return False
            if access[0] <> 'READ':
                return False
        elif auth_id == pid:
            has_auth = True
            if len(access) <> 3:
                return False
            if access[0] <> 'PARTICIPATE':
                return False
            if access[1] <> 'READ':
                return False
            if access[2] <> 'SUBMIT':
                return False
    if not has_owner:
        return False
    if not has_public:
        return False
    if not has_auth:
        return False
    return True

email = raw_input('Email: ')
password = getpass.getpass('Password: ')
session = login(email, password)
print 'Session token: ', session
eval_file = raw_input('Eval File: ')
eval_list = open(eval_file).read().splitlines()
total = 0
success = 0
failure = 0
for eval_id in eval_list:
    if len(eval_id) == 0:
        continue
    total = total + 1
    print ''
    print 'Begin backfilling ', eval_id
    ev = get_eval(session, eval_id)
    owner_id = int(ev['ownerId'])
    public_id = get_user_group(session, 'PUBLIC')
    auth_id = get_user_group(session, 'AUTHENTICATED')
    acl = get_eval_acl(session, eval_id)
    acl = backfill_acl(acl, owner_id=owner_id, public_id=public_id, auth_id=auth_id)
    acl = update_eval_acl(session, acl)
    backfilled = validate_backfill(acl, owner_id=owner_id, public_id=public_id, auth_id=auth_id)
    if backfilled:
        success = success + 1
        print 'Backfilled ', acl['id']
    else:
        failure = failure + 1
        print '!!!FAILURE!!! Backfill failed for eval: ', eval_id
print 'Total: ', total
print 'Success: ', success
print 'Failure: ', failure

