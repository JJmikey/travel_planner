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

@app.route("/task", methods=['GET', 'POST'])
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
            ref.child("{}".format(current_task_id)).set({'id': current_task_id, 'task': task, 'status': 'pending'})
            ref.child("current_task_id").set(current_task_id)
            return jsonify({'message': 'Task added', 'id': current_task_id}), 201
        else:
            return jsonify({'message': 'Task is required'}), 400

@app.route("/task", methods=['PUT', 'DELETE'])
def manage_specific_task():  # 不需要参数id
    data = request.get_json()
    if 'id' not in data:
        return jsonify({'message': 'Task ID required'}), 400

    task_id = data['id']
    ref = db.reference(f"/{task_id}")

    if request.method == 'PUT':
        task = ref.get()
        if task:
            task_data = {
                'id': task_id,
                'task': data.get('task', task['task']),
                'status': data.get('status', task['status'])
            }
            ref.update(task_data)
            return jsonify({'message': 'Task updated'}), 200
        else:
            return jsonify({'message': 'Task not found'}), 404

     elif request.method == 'DELETE':
        task = ref.get()
        if task:
            ref.delete()
            task = ref.get() # Fetch all tasks again after the delete
            task_ids = [int(task_id) for task_id in tasks.keys() if task_id != "current_task_id"]
            max_id = max(task_ids) if task_ids else 0 # -1 or 0, based on how you define task id
            ref = db.reference("/current_task_id")
            ref.set(max_id)
            return jsonify({'message': 'Task deleted'}), 200
        else:
            return jsonify({'message': 'Task not found'}), 404


          
       

if __name__ == "__main__":
      app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080))) #for deploy on vercel
