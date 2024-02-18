
import os 
import json
import requests

from datetime import datetime

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
firebase_admin.initialize_app(credentials.Certificate(service_account_info), {'databaseURL': 'https://momoheya-f67bc-default-rtdb.asia-southeast1.firebasedatabase.app/'})

# link to Slack webhook URL
webhook_url = os.getenv('SLACK_WEBHOOK_URL')



app = Flask(__name__)
app.logger.setLevel(logging.ERROR)



def notify_addTask():
    # set the message
    message = f"任務加好了!"

    # convert to slack message
    slack_data = {'text': message}

    # post to Slack webhook URL
    response = requests.post(webhook_url, json=slack_data, headers={'Content-Type': 'application/json'})

def notify_editTask():
    # set the message
    message = f"任務改好了!"

    # convert to slack message
    slack_data = {'text': message}

    # post to Slack webhook URL
    response = requests.post(webhook_url, json=slack_data, headers={'Content-Type': 'application/json'})   

    if response.status_code != 200:
        raise ValueError(f"Request to slack returned an error {response.status_code}, the response is:\n{response.text}")

def notify_deleteTask():
    # set the message
    message = f"任務已刪除了!"

    # convert to slack message
    slack_data = {'text': message}

    # post to Slack webhook URL
    response = requests.post(webhook_url, json=slack_data, headers={'Content-Type': 'application/json'})

def post_message(role, parts, message_id, firebase_url):
    # 獲取當前的時間截並格式化。
    timestamp = datetime.utcnow().isoformat(timespec='seconds') + '+08:00'
    # 構建訊息字典。
    message = {
        "id": message_id,
        "role": role,
        "parts": parts,
        "timestamp": timestamp
    }

 

    # 將訊息發送到Firebase。
    response = requests.post(firebase_url, json=message)

    return response



if __name__ == "__main__":
      app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080))) #for deploy on vercel

@app.route("/main", methods=['GET'])
def get_chat():
    ref = db.reference("/")
    if request.method == 'GET':
        # Read from Firebase
        chat_log = ref.get()
        return jsonify(chat_log)
    
@app.route("/main", methods=['POST'])
def post_chat():
    try:
        global last_message_id, message_id
        # 從 HTTP 請求的 body 中解析 JSON。
        chat_data = request.json
        firebase_url = "https://momoheya.vercel.app/main"
        ref = db.reference("/")

        # 確定 chat_data 是否包含所需的鍵
        if chat_data is None or 'user_prompt' not in chat_data or 'model_reply' not in chat_data:
            # 紀錄錯誤信息和收到的 chat_data，以便排查問題
            print("Error: 'user_prompt' or 'model_reply' missing in received data.", chat_data)
            return jsonify({"error": "Missing data in request"}), 400


        if chat_data:
            # Get the last message id from Firebase and increment it
            last_message_id = ref.child("last_message_id").get() or 0
            last_message_id += 1
            return jsonify(chat_data)


        # 從請求體中提取用戶訊息和模型回應，以及消息 ID。
        user_prompt = chat_data["user_prompt"]
        model_response = chat_data["model_reply"]
        message_id = last_message_id  # 使用更新後的 last_message_id 作為當前消息的 ID。


        # 分別發送用戶訊息和模型回應到 Firebase。
        resp1 = post_message("user", user_prompt, message_id, firebase_url)
        resp2 = post_message("model", model_response, message_id, firebase_url)

        # Update the last message id 
        ref.child("last_message_id").set(last_message_id)



        # 返回一個 JSON 響應，包含了發送結果。
        return jsonify({"user_message_status": resp1.status_code, "model_message_status": resp2.status_code})
    
    except Exception as e:
        # 在實際部署時，應該要有更好的錯誤處理機制
        return jsonify({"error": str(e)}), 500
    




@app.route("/main", methods=['PUT', 'DELETE'])
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
            notify_editTask() # send notify to webhook URL
            return jsonify({'message': 'Task updated'}), 200
        else:
            return jsonify({'message': 'Task not found'}), 404

    elif request.method == 'DELETE':
        # 根据task_id找到对应的任务引用
        task_ref = db.reference(f"/{task_id}")

        # 尝试获取这个引用指向的任务
        task = task_ref.get()
        
        if task:
            # 如果找到了任务，则删除这个任务
            task_ref.delete()
            notify_deleteTask() # send notify to webhook URL
            
            # 如果您需要的话，在这里可以更新current_task_id
            # 但是请注意，`ref.get()`不是用来获取所有任务的。
            # 您需要重新获取所有任务的引用，来找到新的最大ID。
            all_tasks_ref = db.reference("/") # 这是所有任务的引用
            all_tasks = all_tasks_ref.get() # 获取所有任务
            if all_tasks:
                task_ids = [int(task_id) for task_id in all_tasks.keys() if task_id != "current_task_id"]
                max_id = max(task_ids) if task_ids else 0 # 根据您的业务逻辑，这里可以是-1或0
                current_task_id_ref = db.reference("/current_task_id")
                current_task_id_ref.set(max_id) # 更新current_task_id

            return jsonify({'message': 'Task deleted'}), 200
        else:
            return jsonify({'message': 'Task not found'}), 404
                     
       


