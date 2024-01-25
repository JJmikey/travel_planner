# app.py
import os 
import json
from flask import Flask, jsonify, request
import firebase_admin
from firebase_admin import credentials, db

# Load the credentials from environment variable
service_account_info = json.loads(os.getenv('FIREBASE_SERVICE_ACCOUNT'))

# Initialize the Firebase application with Firebase database URL
firebase_admin.initialize_app(credentials.Certificate(service_account_info), {'databaseURL': 'https://todoapi-939ac-default-rtdb.asia-southeast1.firebasedatabase.app/'})

app = Flask(__name__)

current_task_id = 0

@app.route("/", methods=['GET', 'POST'])
def manage_tasks():
    global current_task_id
    if request.method == 'GET':
        # Read from Firebase
        todo_tasks = db.reference("/").get()
        return jsonify(todo_tasks)
    elif request.method == 'POST':
        task = request.json.get('task', '')
        if task:
            current_task_id += 1
            # Write to Firebase
            db.reference("/").push({'id': current_task_id, 'task': task, 'status': 'pending'})
            return jsonify({'message': 'Task added', 'id': current_task_id}), 201
        else:
            return jsonify({'message': 'Task is required'}), 400

@app.route("/<int:id>", methods=['PUT', 'DELETE'])
def modify_task(id):
    task = [t for t in todo_tasks if t['id'] == id]
    if len(task) == 0:
        return jsonify({'message': 'Task not found'}), 404
    if request.method == 'PUT':
        task[0]['task'] = request.json.get('task', task[0]['task'])
        task[0]['status'] = request.json.get('status', task[0]['status'])
        return jsonify({'message': 'Task updated'}), 200
    elif request.method == 'DELETE':
        todo_tasks.remove(task[0])
        return jsonify({'message': 'Task deleted'}), 200

# gunicorn command in start script
# gunicorn -w 4 -b 0.0.0.0:$PORT app:app



if __name__ == "__main__":
      app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080))) #for deploy on vercel
