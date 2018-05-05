#Author: Marti Kallas
#Description: Simple site that provides an example of OAuth 2 flow
#   for CS496
#Date: 5/5/2018

from google.appengine.ext import ndb
import webapp2
import json
import os
import string
import random
from google.appengine.ext.webapp import template
from google.appengine.api import urlfetch

secrets = json.load(open('secrets.json'))

clientid = str(secrets['clientid'])
clientsecret = str(secrets['clientsecret'])
GoogleAuthURI = "https://accounts.google.com/o/oauth2/v2/auth"
GoogleTokenURI = "https://www.googleapis.com/oauth2/v4/token"
GooglePlusURI = "https://www.googleapis.com/plus/v1/people/me"
redirectURI = "https://osu-cs496-oauth-demo.appspot.com/receiveCode"
state = "SomeKey123"
accessCode = ""
access_token = ""

#generate state
#source: https://stackoverflow.com/questions/2257441/random-string-generation-with-upper-case-letters-and-digits-in-python
def generateState():
    chars=string.digits + string.ascii_letters
    return ''.join(random.choice(chars) for _ in range(15))

class State(ndb.Model):
    value = ndb.StringProperty()
    #TODO: should probably have an expiration

# First OAuth call redirects here with the access code
#   This object then gets the access token to be able to access user information
class rcvCode(webapp2.RequestHandler):
    def get(self):
        #get info from OAuth redirect
        returnedState = self.request.get('state')
        uri = "State = " + returnedState 
        uri = uri + "  :  Code = " + self.request.get('code')
        #check if state matches recent state
        qry = State.query()
        stateMatches = False
        for state in qry:
            if state.value == returnedState:
                stateMatches = True
                state.key.delete()
                break;
        accessCode = self.request.get('code')
        if not stateMatches:
                template_values = {
                    'errorHeader': 'Error',
                    'details': 'State did not match between requests',
                }
                path = os.path.join(os.path.dirname(__file__), 'www/error.html')
                self.response.out.write(template.render(path, template_values))
        uri = GoogleTokenURI
        uri = uri + "?code=" + accessCode
        uri = uri + "&client_id=" + clientid
        uri = uri + "&client_secret=" + clientsecret
        uri = uri + "&redirect_uri=" + redirectURI
        uri = uri + "&grant_type=authorization_code"
        #source: https://cloud.google.com/appengine/docs/standard/python/issue-requests
        #Send post to OAuth to get access token
        try:
            result = urlfetch.fetch(
                    url=uri,
                    method=urlfetch.POST,
                    validate_certificate=True)
            #source: https://www.programcreek.com/python/example/60231/google.appengine.api.urlfetch.POST
            if result.status_code == 200:
                j = json.loads(result.content)
                access_token = j['access_token']
            else:
                details = 'Got code ' + result.status_code + ' trying to fetch token'
                template_values = {
                    'errorHeader': 'Error',
                    'details': details,
                }
                path = os.path.join(os.path.dirname(__file__), 'www/error.html')
                self.response.out.write(template.render(path, template_values))

        except urlfetch.Error:
            logging.exception('Caught exception fetching url')
            template_values = {
                    'errorHeader': 'Error',
                    'details': 'Exception in POST for access token',
            }
            path = os.path.join(os.path.dirname(__file__), 'www/error.html')
            self.response.out.write(template.render(path, template_values))

        #send GET to googleapis.com/plus/v1/me
        # Must use access token in a header: Authorization : Bearer <token>
        bearerToken = 'Bearer ' + access_token
        header = {'Authorization': bearerToken}
        result = urlfetch.fetch(
                url=GooglePlusURI,
                headers=header)
        if result.status_code == 200:
            j = json.loads(result.content)
            template_values = {
                    'firstname': j['name']['givenName'],
                    'lastname': j['name']['familyName'],
                    'url': j['url'],
                    'state': returnedState,
            }
            path = os.path.join(os.path.dirname(__file__), 'www/info.html')
            self.response.out.write(template.render(path, template_values))
        else:
            template_values = {
                    'errorHeader': 'Error',
                    'details': 'Could not retrieve user details',
            }
            path = os.path.join(os.path.dirname(__file__), 'www/error.html')
            self.response.out.write(template.render(path, template_values))

#Main page redirects here - This fills in info for authorizing account access
#   Redirects user to google page to authorize account access
#   Once account access is authorized, user is redirected to rcvCode
class OauthHandler(webapp2.RequestHandler):
    def get(self):
        uri = GoogleAuthURI + "?response_type=code"
        uri = uri + "&client_id=" + clientid
        uri = uri + "&redirect_uri=" + redirectURI
        uri = uri + "&scope=email"
        state = generateState()
        new_state = State(value=state)
        new_state.put()
        uri = uri + "&state=" + state
        template_values = {
                'greet': 'This should be Oauth',
                'uri': uri,
        }
        self.redirect(uri)

#Index page - contains description and button to begin OAuth process
class MainPage(webapp2.RequestHandler):
    def get(self):
        template_values = {
            'greet': 'Hello',
        }
        path = os.path.join(os.path.dirname(__file__), 'www/index.html')
        self.response.out.write(template.render(path, template_values))

app = webapp2.WSGIApplication([
    ('/', MainPage),
    ('/oauth', OauthHandler),
    ('/receiveCode', rcvCode)
], debug=True)
