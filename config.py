import firebase_admin
from firebase_admin import credentials, db
import os

print(os.getcwd())
cred = credentials.Certificate('c:\\Users\\prend\\Desktop\\CSSC_Antenas\\CSSC_Antenas\\cssc-antenas-firebase-adminsdk-fbsvc-699491abe5.json')
firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://cssc-antenas-default-rtdb.firebaseio.com/'
})