from google.appengine.ext import ndb
import webapp2
import json
import os
from google.appengine.ext.webapp import template
from google.appengine.api import urlfetch

secrets = json.load(open('secrets.json'))

clientid = str(secrets['clientid'])
clientsecret = str(secrets['clientsecret'])
GoogleAuthURI = "https://accounts.google.com/o/oauth2/v2/auth"
GoogleTokenURI = "https://www.googleapis.com/oauth2/v4/token"
redirectURI = "http://localhost:8080/receiveCode"
state = "SomeKey123"
accessCode = ""
access_token = ""

class rcvCode(webapp2.RequestHandler):
    def get(self):
        uri = "State = " + self.request.get('state')
        uri = uri + "  :  Code = " + self.request.get('code')
        accessCode = self.request.get('code')
        if state != self.request.get('state'):
            #TODO:
            a = 1
        uri = GoogleTokenURI
        uri = uri + "?code=" + accessCode
        uri = uri + "&client_id=" + clientid
        uri = uri + "&client_secret=" + clientsecret
        uri = uri + "&redirect_uri=" + redirectURI
        uri = uri + "&grant_type=authorization_code"
        #source: https://cloud.google.com/appengine/docs/standard/python/issue-requests
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
                access_token = "Error"
        except urlfetch.Error:
            logging.exception('Caught exception fetching url')
        template_values = {
                'greet': 'This should be Oauth',
                'uri': access_token,
        }

        path = os.path.join(os.path.dirname(__file__), 'www/index.html')
        self.response.out.write(template.render(path, template_values))


class OauthHandler(webapp2.RequestHandler):
    def get(self):
        uri = GoogleAuthURI + "?response_type=code"
        uri = uri + "&client_id=" + clientid
        uri = uri + "&redirect_uri=" + redirectURI
        uri = uri + "&scope=email"
        #TODO: generate state
        uri = uri + "&state=" + state

        template_values = {
                'greet': 'This should be Oauth',
                'uri': uri,
        }
        self.redirect(uri)

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
