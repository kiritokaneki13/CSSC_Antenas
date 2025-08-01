import firebase_admin
from firebase_admin import credentials, db
import os

# Configura tu credencial de Firebase
print(os.getcwd())
cred = credentials.Certificate('c:\\Users\\prend\\Desktop\\CSSC_Antenas\\CSSC_Antenas\\cssc-antenas-firebase-adminsdk-fbsvc-0dec0716e7.json')
firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://cssc-antenas-default-rtdb.firebaseio.com/'
})