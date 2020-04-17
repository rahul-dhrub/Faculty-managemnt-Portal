from pymongo import MongoClient
from pprint import pprint
import os

class MongoDBHelper:
    def __init__(self):
        self.connect()

    def connect(self):
        self.client = MongoClient(os.environ.get('MONGO_HOST','localhost'), int(os.environ.get('MONGO_PORT', 27017)))
        db = self.client.faculty
        #test Database Connection
        serverStatusResult = db.command("serverStatus")
        pprint(serverStatusResult)
    
    def updateCV(self, emp_id, about_faculty, research_interests, publications, grants, 
                                    awards, teaching_experience):
        db = self.client.faculty

        if db.faculty_info.find({"emp_id" : emp_id}).count() > 0:

            try:
                db.faculty_info.update({'emp_id':emp_id},
                    {
                        'emp_id' : emp_id,
                        'about_faculty' : about_faculty,
                        'research_interests' : research_interests,
                        'publications' : publications,
                        'grants' : grants,
                        'awards' : awards,
                        'teaching_experience' : teaching_experience,
                    })
                return emp_id
            
            except Exception as e:
                print(e)
                return False
        else:
            document = {
                'emp_id' : emp_id,
                'about_faculty' : about_faculty,
                'research_interests' : research_interests,
                'publications' : publications,
                'grants' : grants,
                'awards' : awards,
                'teaching_experience' : teaching_experience,
            }
            pprint(document)
            error = False
            try:
                print('Trying to insert')
                insertion_id = db.faculty_info.insert_one(document)
                print('insertion Successful')
                return insertion_id
            except Exception as e:
                error = True
                print(e)
                print('Error in inserting')
                return error
    
    def getCV(self, emp_id):
        db = self.client.faculty
        cv = None
        try:
            cv = db.faculty_info.find_one({"emp_id" : str(emp_id)})
        except Exception as e:
            print(e)
            print("getCv !!")
        return cv

    # Leave Application

    def insertComment(self, application_no, comment = '', comment_by = None):
        db = self.client.faculty

        if db.comments.find({"application_no" : application_no}).count() > 0:
            document = db.comments.find_one({"application_no" : application_no})
            if comment_by == 'hod':
                document['hod'] = comment
            elif comment_by == 'dean':
                document['dean'] = comment
            elif comment_by == 'director':
                document['director'] = comment
            else:
                document['employee'] = comment
            
            try:
                print('Inserting Document: ')
                pprint(document)
                db.comments.update({"application_no" : application_no},
                {
                    'application_no' : document['application_no'],
                    'hod' : document['hod'],
                    'dean' : document['dean'],
                    'director' : document['director'],
                    'employee' : document['employee']
                })
            except Exception as e:
                print(e)

        else:
            document = {
                'application_no' : application_no,
                'hod': '',
                'dean': '',
                'director': '',
                'employee' : comment,
            }
            try:
                db.comments.insert_one(document)
            except Exception as e:
                print(e)
    
    def getComment(self, application_no):
        db = self.client.faculty
        print(application_no)
        comment = None
        try:
            comment = db.comments.find_one({'application_no' : application_no })
        except Exception as e:
            print(e)
            print("getComment !!")
        return comment

    
    def updateRoutes(self, faculty_route = "dean", hod_route = "dean", dean_route = "director"):
        db = self.client.faculty
        try:
            db.routes.update_one(
                {'position':'faculty'}, 
                {
                    '$set':{
                        'position':'faculty',
                        'route':faculty_route,
                    }
                },
                upsert=True
            )
            db.routes.update_one(
                {'position':'hod'}, 
                {
                    '$set':{
                        'position':'hod',
                        'route':hod_route,
                    }
                },
                upsert=True
            )
            db.routes.update_one(
                {'position':'dean'}, 
                {
                    '$set':{
                        'position':'dean',
                        'route':dean_route,
                    }
                },
                upsert=True
            )
        except Exception as e:
            print(e)

    def getRoute(self, position):
        db = self.client.faculty
        print(position)
        try:
            if db.routes.find({'position' : position}).count() > 0:
                print("FOUND")
                document = db.routes.find_one({'position' : position})
                print(document)
                return document['route']
        except Exception as e:
            print(e)
            return None