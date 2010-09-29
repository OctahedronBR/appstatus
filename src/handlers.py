'''
Created on 29/09/2010

@author: danilo
'''
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext import webapp
from model import modelFacade

model = modelFacade()

class RegisterApp(webapp.RequestHandler):
    def get(self):
        None # mandar pra template de registro
        
    def post(self):
        None # receber info e adicionar uma aplication

class ShowStatus(webapp.RequestHandler):
    def get(self):
        model.getAppStatus()


class Monitor(webapp.RequestHandler):
    def post(self):
        model.monitorApps(self.request.get("cursor"))
        self.redirect("/")
        

# Application entry point
application = webapp.WSGIApplication(
                                     [('/', ShowStatus), 
                                      ('/monitor', Monitor)], 
                                      debug=True)


def main():
    run_wsgi_app(application)

if __name__ == "__main__":
    main()