# coding=utf-8
"""
Exposes a simple HTTP API to search a users Gists via a regular expression.

Github provides the Gist service as a pastebin analog for sharing code and
other develpment artifacts.  See http://gist.github.com for details.  This
module implements a Flask server exposing two endpoints: a simple ping
endpoint to verify the server is up and responding and a search endpoint
providing a search across all public Gists for a given Github account.
"""

import re
import requests
from flask import Flask, jsonify, request


# *The* app object
app = Flask(__name__)


@app.route("/ping")
def ping():
    """Provide a static response to a simple GET request."""
    return "pong"

def error_to_dict(response = None):
    """Generates an error response dict given a response with status code != 200"""
    # covers 404 and 500 from gists API
    if response and "message" in response:
        message = response["message"]
    else:
        message = "Unexpected error."
    return {
        "status": "error",
        "message": message
    }

def get_gist_body(gist_url):
    """Retrieves the plain text body of a gist given a url"""
    response = requests.get(gist_url)
    response.raise_for_status()

    return response.text

def gists_for_user(username, page_num = 1, results = []):
    """Provides the list of gist metadata for a given user.

    This abstracts the /users/:username/gist endpoint from the Github API.
    See https://developer.github.com/v3/gists/#list-a-users-gists for
    more information.

    Args:
        username (string): the user to query gists for

    Returns:
        The dict parsed from the json response from the Github API.  See
        the above URL for details of the expected structure.
    """
    gists_url = 'https://api.github.com/users/{username}/gists?page={page_num}'.format(
            username=username, page_num=page_num)

    response = requests.get(gists_url)
    # BONUS: What failures could happen?
    # Let's raise an exception for status != 200, so we can catch it and be DRY
    response.raise_for_status()
    
    # BONUS: Paging? How does this work for users with tons of gists?
    if "next" in response.links:
        # If we can keep going, we recurse on the next page and memoize
        return gists_for_user(username, page_num + 1, results + response.json())
    else:
        return results + response.json()


@app.route("/api/v1/search", methods=['POST'])
def search():
    """Provides matches for a single pattern across a single users gists.

    Pulls down a list of all gists for a given user and then searches
    each gist for a given regular expression.

    Returns:
        A Flask Response object of type application/json.  The result
        object contains the list of matches along with a 'status' key
        indicating any failure conditions.
    """
    post_data = request.get_json()
    # BONUS: Validate the arguments?
    username = post_data['username']
    # For now assume pattern is valid
    pattern = post_data['pattern']

    result = {}
    # BONUS: Handle invalid users?
    #   We're returning a Not Found (straight from gists API)
    try:
        gists = gists_for_user(username)
    except requests.RequestException, e:
        # Otherwise (RequestException encapsulates 
        #   Timeout, HTTPError and TooManyRedirects) we bail

        # NOTE: I'm assuming an always-200 API paradigm
        #   so the response code is always 200, but the status fields
        #   becomes 'error' w/ a message
        return jsonify(error_to_dict(e.response.json()))
    except Exception, e:
        print e
        return jsonify(error_to_dict())

    matches = []
    compiled_pattern = re.compile(pattern)

    # If we're here, we got a 200
    for gist in gists:
        gist_url = "https://gist.github.com/%s/%s" % (gist["owner"]["login"], gist["id"])
        
        for filename, gist_file in gist["files"].iteritems():
            # BONUS: What about huge gists?
            #   Two options:
            #   1. The `files` in the reponse has `truncated: True`
            #         -> Taken care of by using the raw_url
            #   2. The individual gist file is > 10mb
            #         -> a lot more painful, requires cloning the gist
            try:
                gist_body = get_gist_body(gist_file["raw_url"])
            except:
                return jsonify(error_to_dict())
            
            if compiled_pattern.search(gist_body) != None:
                matches.append(gist_url)
    
    # REQUIRED: Fetch each gist and check for the pattern
    
    # BONUS: Can we cache results in a datastore/db?
    #   Yes, we can query the API with only the records after a specific timestamp
    #   so check through the gists we have saved and only retrieve the new ones
    #   although I'm not sure if the endpoint would also return items modified after
    #   the timestamp

    result['status'] = 'success'
    result['username'] = username
    result['pattern'] = pattern
    result['matches'] = matches

    return jsonify(result)


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8000)
