from flask_login import UserMixin
import database_config as cfg
import pymongo


def createDatabaseConnection():
    '''
    Create MongoClient Connection and return the database
    '''
    
    mongo_client = pymongo.MongoClient(cfg.mongo_credentials['hostIP'])
    database = mongo_client[cfg.mongo_credentials['databaseName']]
    
    return database


class User(UserMixin):
    def __init__(self, id_, name, email, datasets=[]):
        self.id = id_
        self.name = name
        self.email = email
        self.datasets = datasets

    @staticmethod
    def get(user_id):
        database = createDatabaseConnection()
    
        collection_of_existing_users = database[cfg.mongo_credentials['usersCollection']]
        user = collection_of_existing_users.find_one({'id':user_id})
        
        return User(user['user_id'], user['name'], user['email'], user['datasets'])

    @staticmethod
    def create(id_, name, email, datasets=[]):
        try:
            database = createDatabaseConnection()

            collection_of_existing_users = database[cfg.mongo_credentials['usersCollection']]

            user_details={'user_id': id_, 'name':name, 'email':email, 'datasets':datasets}
            update_user_list = collection_of_existing_users.insert_one(user_details)
            
            return True
        
        except:
            return False

