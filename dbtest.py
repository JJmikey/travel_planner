# app.py
import os 
import json

# Load the credentials from environment variable
firebase_service_account = os.getenv('FIREBASE_SERVICE_ACCOUNT')
if firebase_service_account is not None:
    service_account_info = json.loads(firebase_service_account)
else:
    print("'FIREBASE_SERVICE_ACCOUNT' is not set or empty")
    # handle this error appropriately...


from flask import Flask, jsonify, request
import logging

import firebase_admin
from firebase_admin import credentials, db



# Initialize the Firebase application with Firebase database URL
firebase_admin.initialize_app(credentials.Certificate(service_account_info), {'databaseURL': 'https://todoapi-939ac-default-rtdb.asia-southeast1.firebasedatabase.app/'})

app = Flask(__name__)
app.logger.setLevel(logging.ERROR)

@app.route("/", methods=['GET', 'POST'])
def manage_tasks():
    ref = db.reference("/")
    if request.method == 'GET':
        # Read from Firebase
        todo_tasks = ref.get()
        return jsonify(todo_tasks)
    elif request.method == 'POST':
        task = request.json.get('task', '')
        if task:
            # Get current_task_id from Firebase and increment it
            current_task_id = ref.child("current_task_id").get()
            if current_task_id is None:
                # If it doesn't exist, start it at 1
                current_task_id = 1
            else:
                current_task_id += 1
            # Write to Firebase
            ref.child("-{}".format(current_task_id)).set({'id': current_task_id, 'task': task, 'status': 'pending'})
            ref.child("current_task_id").set(current_task_id)
            return jsonify({'message': 'Task added', 'id': current_task_id}), 201
        else:
            return jsonify({'message': 'Task is required'}), 400

@app.route("/<int:id>", methods=['PUT', 'DELETE'])
def manage_specific_task(id):
    ref = db.reference("/")
    task = ref.get()  # Fetch all tasks
    
    if task is not None:
        for task_ref in tasks.keys(): 

            task = tasks[task_ref]
            if task_ref == "current_task_id": # Skip the non-task property
                continue

            if task['id'] == id:         
                ref_task = db.reference("/" + task_ref) # Point to the specific task with its reference
                app.logger.info('Referencing: %s', "/" + task_ref) # Log the reference
                if request.method == 'PUT':
                    task_data = {
                        'id': id,
                        'task': request.json.get('task', task['task']),
                        'status': request.json.get('status', task['status'])
                    }

                    ref_task.update(task_data) # Update the task

                    return jsonify({'message': 'Task updated'}), 200

                elif request.method == 'DELETE':
                    try:
                        ref_task.delete() # Delete the task
                        app.logger.error('Task deletion successful.')  
                    except Exception as e:
                        app.logger.error('Task deletion failed. Error: %s', e)
                        return str(e), 500

                    return jsonify({'message': 'Task deleted'}), 200

    return jsonify({'message': 'Task not found'}), 404 # Task was not found if we reach here

        
       

if __name__ == "__main__":
      app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080))) #for deploy on vercel
