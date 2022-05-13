'''
To use the script, please:
1. Install MongoDB and setup your database
2. pip install Authlib
3. pip install Flask-login
'''

from flask import Flask
import pymongo, json
from bson import ObjectId
from bson import json_util
import database_config as cfg
from user import User

from datetime import timedelta
from flask import Flask, render_template, url_for, redirect, request, session
from authlib.integrations.flask_client import OAuth
from flask_login import (
    LoginManager,
    current_user,
    login_required,
    login_user,
    logout_user,
)

'''
Required App, Oauth, Session Management Initializations
'''

app = Flask(_name_, static_url_path='',
                  static_folder='build',
                  template_folder='templates')

oauth = OAuth(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.needs_refresh_message = (u"Session timedout, please re-login")
login_manager.needs_refresh_message_category = "info"


'''
Read credentials from the configuration file
'''
app.config['SECRET_KEY'] = cfg.google_client_credentials['secret_key']
app.config['GOOGLE_CLIENT_ID'] = cfg.google_client_credentials['client_id']
app.config['GOOGLE_CLIENT_SECRET'] = cfg.google_client_credentials['client_secret']


'''
Initialize google oauth registration details
'''
google = oauth.register(
    name = 'google',
    client_id = app.config["GOOGLE_CLIENT_ID"],
    client_secret = app.config["GOOGLE_CLIENT_SECRET"],
    access_token_url = 'https://accounts.google.com/o/oauth2/token',
    access_token_params = None,
    authorize_url = 'https://accounts.google.com/o/oauth2/auth',
    authorize_params = None,
    api_base_url = 'https://www.googleapis.com/oauth2/v1/',
    userinfo_endpoint = 'https://openidconnect.googleapis.com/v1/userinfo',  # This is only needed if using openId to fetch user info
    client_kwargs = {'scope': 'openid email profile'},
)



@login_manager.user_loader
def loadUser(user_id):
    '''
    Load current user on the basis of the Unique ID
    '''
    return User.get(user_id)


@app.route("/logout")
@login_required
def logout():
    '''
    If the user clicks on the logout link
    '''
    logout_user()
    return redirect(url_for("index"))


@app.before_request
def beforeRequest():
    '''
    Setting logout time
    '''
    session.permanent = True
    app.permanent_session_lifetime = timedelta(minutes=5)
    
    
@app.route("/")
def index():
    '''
    Link to the homepage. This is what the UI will be calling.
    '''
    
    if current_user.is_authenticated:
        return render_template("index.html", name=current_user.name, email=current_user.email)
     
    else:
        return render_template("login.html")
    

@app.route('/login')
def googleLogin():
    '''
    Google login route
    '''
    
    google = oauth.create_client('google')
    redirected_url = url_for('googleAuthorize', _external=True)
    return google.authorize_redirect(redirected_url)


@app.route('/login/google/authorize')
def googleAuthorize():
    '''
    Google authorization route
    '''
    
    google = oauth.create_client('google')
    token = google.authorize_access_token()
    user_info = google.get('userinfo').json()
#     print (user_info['name'], user_info['email'])
    
    if user_info.get("verified_email"):
        unique_id = user_info["id"]
        user_email = user_info["email"]
        user_name = user_info["name"]
    else:
        return "User email not available or not verified by Google.", 400
    
    
    '''
    Check for user's existence in the database, insert one if not already in the database
    '''
    user = User.get(unique_id)
    
    if user is not None:
        login_user(user)
    else:
        user=User(unique_id, user_name, user_email, [])
        user_created = user.create(unique_id, user_name, user_email, [])
        if user_created == False:
            return "User creation in the database failed"

    print ("Google Login Successful")
    # Send user to the required page
    
    ## Return JSON response saying login is successful - Login email and name of the user
    return redirect(url_for("index"))


def createDatabaseConnection():
    '''
    Create MongoClient Connection and return the database
    '''
    
    mongo_client = pymongo.MongoClient(cfg.mongo_credentials['hostIP'])
    database = mongo_client[cfg.mongo_credentials['databaseName']]
    
    return database



@app.route("/getDatasetsList")
def fetchDatasetList():
    '''
    Create Database Connection and query the collection with dataset details and return the list of distinct datasets
    '''
    
    argus_database=createDatabaseConnection()                                    
    
    collection_of_datasets = database[cfg.mongo_credentials['datasetListCollection']]
    list_of_datasets = collection_of_datasets.distinct('dataset_name')
    
    return {"Dataset_List":list_of_datasets}



@app.route("/getDatasetDetails/<dataset_name>")
def fetchDatasetDetails(dataset_name):
    '''
    Create Database Connection and query the collection with responses, return as a list and the total count
    '''
    
    database = createDatabaseConnection()
    
    collection_of_responses = database[cfg.mongo_credentials['datasetDetailsCollection']]
    list_of_responses = collection_of_responses.find({'dataset_name':dataset_name})
    
    list_of_responses = list(list_of_responses)
    total_count = len(list_of_responses)
    
    return {"Total Images": str(total_count), "Responses_list":json.loads(json_util.dumps(list_of_responses))}



if __name__ == '__main__':
    app.run()