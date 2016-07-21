import os
import json
import tempfile

import pytest

import gistapi


@pytest.fixture
def client(request):
    #db_fd, gistapi.app.config['DATABASE'] = tempfile.mkstemp()
    gistapi.app.config['TESTING'] = True
    client = gistapi.app.test_client()

    #with gistapi.app.app_context():
    #    gistapi.init_db()
    
    #def teardown():
    #    os.close(db_fd)
    #    os.unlink(flaskr.app.config['DATABASE'])
    #request.addfinalizer(teardown)

    return client

def issue_request(client, username, pattern):
    post_data = {'username': username, 'pattern': pattern}
    rv = client.post('/api/v1/search', 
                     data=json.dumps(post_data),
                     headers={'content-type':'application/json'})
    result_dict = json.loads(rv.data.decode('utf-8'))

    return result_dict

def test_ping(client):
    """Start with a sanity check."""
    rv = client.get('/ping')
    assert b'pong' in rv.data


def test_search(client):
    """Start with a passing test."""
    result_dict = issue_request(client, 'justdionysus', 'TerbiumLabsChallenge_[0-9]+')
    expected_dict = {'status': 'success', 
                     'username': 'justdionysus',
                     'pattern': 'TerbiumLabsChallenge_[0-9]+',
                     'matches': ['https://gist.github.com/justdionysus/6b2972aa971dd605f524']}
    assert result_dict == expected_dict

def test_search_not_found(client):
    """Checks for a non existing user."""
    result_dict = issue_request(client, 'justdionysus_doesnt_exist_guys_sorry', 'TerbiumLabsChallenge_[0-9]+')
    expected_dict = {'status': 'error', 
                     'message': 'Not Found'}
    assert result_dict == expected_dict

def test_search_invalid_username(client):
    """Checks for an invalid username."""
    result_dict = issue_request(client, 665743, 'TerbiumLabsChallenge_[0-9]+')
    expected_dict = {'status': 'error', 
                     'message': 'Username must be a string.'}
    assert result_dict == expected_dict

def test_search_invalid_pattern(client):
    """Checks for an invalid regexps."""
    result_dict = issue_request(client, 'justdionysus', '(')
    expected_dict = {'status': 'error', 
                     'message': 'Pattern must be a valid regular expression.'}
    assert result_dict == expected_dict
