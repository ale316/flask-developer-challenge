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

def error_to_dict(response):
    """Generates an error response dict given a response with status code != 200"""
    # covers 404 and 500 from gists API
    if "message" in response:
        message = response["message"]
    else:
        message = "Unexpected error."
    return {
        "status": "error",
        "message": message
    }

def gists_for_user(username):
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
    gists_url = 'https://api.github.com/users/{username}/gists'.format(
            username=username)

    response = requests.get(gists_url)
    # BONUS: What failures could happen?
    # Let's raise an exception for status != 200, so we can catch it and be DRY
    response.raise_for_status()

    # BONUS: Paging? How does this work for users with tons of gists?

    return response.json()


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
    pattern = re.compile(post_data['pattern'])

    result = {}
    # BONUS: Handle invalid users?
    #   We're returning a Not Found (straight from gists API)
    try:
        gists = gists_for_user(username)
    except requests.RequestException, e:
        # Otherwise (RequestException encapsulates 
        #   Timeout, HTTPError and TooManyRedirects) we bail
        return jsonify(error_to_dict(e.response.json()))

    matches = []
    for gist in gists:
        # REQUIRED: Fetch each gist and check for the pattern
        print gist
        # if pattern.search(gist) != None:
        #     matches.append(gist)
        # BONUS: What about huge gists?
        # BONUS: Can we cache results in a datastore/db?

    result['status'] = 'success'
    result['username'] = username
    result['pattern'] = pattern
    result['matches'] = matches

    return jsonify(result)


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8000)
