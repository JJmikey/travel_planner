
import os 
import json
import requests

from datetime import datetime, timedelta
import pytz

from flask import Flask, jsonify, request
import logging

import firebase_admin
from firebase_admin import credentials, db, storage


# Load the credentials from environment variable
firebase_service_account = os.getenv('FIREBASE_SERVICE_ACCOUNT')
if firebase_service_account is not None:
    service_account_info = json.loads(firebase_service_account)
else:
    print("'FIREBASE_SERVICE_ACCOUNT' is not set or empty")
    # handle this error appropriately...

# Assuming service_account_info is loaded from an environment variable or a file
cred = credentials.Certificate(service_account_info)

# 在初始化之前先檢查Firebase應用是否已經初始化
try:
    firebase_admin.get_app()
except ValueError as e:
    # 如果沒有初始化，則進行初始化
    # Initialize the Firebase application with Firebase URL
    firebase_admin.initialize_app(cred, {
        'databaseURL': 'https://travel-planner-3ccb3-default-rtdb.asia-southeast1.firebasedatabase.app//',
        'storageBucket': 'momoheya-f67bc.appspot.com'
    })
    # Now, you can use the db and storage modules from firebase_admin to interact with the database and storage.




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

def store_image_to_firebase(image_url):
    
    
    # 使用 requests 库下载图像
    response = requests.get(image_url)

    if response.status_code == 200:
        # 将响应内容作为图像存储到内存缓冲区
        from io import BytesIO
        image_blob = BytesIO(response.content)
        
        # 定义在 Firebase Storage 中的文件路径，使用圖像上傳時的時間戳作為文件名
        file_path = f"images/{datetime.now().strftime('%Y%m%d%H%M%S')}.png"

        # 上传图像到 Firebase Storage
        bucket = storage.bucket()
        blob = bucket.blob(file_path)
        
        # 从内存流上传图像
        blob.upload_from_file(image_blob, content_type='image/png')
        
        # 這裡直接呼叫 blob 的 make_public 方法
        blob.make_public()

        print(
        f"Blob {blob.name} is publicly accessible at {blob.public_url}"
        )

        # 获取下载 URL
        return blob.public_url

def check_missing_variables(request_data, required_fields):
    missing_fields = []
    for field in required_fields:
        # 使用 has_key() 函式來檢查鍵是否存在，這適用於布爾值的檢查
        if field not in request_data:
            missing_fields.append(field)
    return missing_fields





if __name__ == "__main__":
      app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080))) #for deploy on vercel

@app.route("/main", methods=['GET', 'POST'])
def trip_info():
    ref = db.reference("/info")
    if request.method == 'GET':
        # 讀取 Firebase 的 '/info' 節點
        chat_data = ref.get()  # 不指定子節點，直接讀取 'chat' 節點下所有數據
        if chat_data:
            return jsonify(chat_data), 200
        else:
            return jsonify({"error": "No data found."}), 404
    
    elif request.method == 'POST':
        # 定義必須的字段列表
        required_fields = ['destination', 'arrive_date', 'arrive_time', 'no_of_stayed_days', 'step1_completed', 'leave_time']
        # 檢查缺失的字段
        missing_fields = check_missing_variables(request.json, required_fields)
        if missing_fields:
            # 打印出缺失的字段名稱
            print(f"缺失的必須字段：{', '.join(missing_fields)}")
            # 可以在這裡添加代碼來處理缺失字段的情況，比如返回一個錯誤響應
            return jsonify(error=f"Missing required fields: {', '.join(missing_fields)}"), 400

        # 提取並檢查 no_of_stayed_days 字段
        no_of_stayed_days_str = request.json.get('no_of_stayed_days', None)
        if no_of_stayed_days_str is None:
            print("缺失的必須字段：no_of_stayed_days")
            return jsonify(error="Missing required field: no_of_stayed_days"), 400
        try:
            no_of_stayed_days = int(no_of_stayed_days_str)
        except ValueError:
            print("no_of_stayed_days 必須是一個整數")
            return jsonify(error="no_of_stayed_days must be an integer"), 400

        # 提取並檢查 arrive_date 字段
        arrive_date_str = request.json.get('arrive_date', '')
        try:
            arrival_date = datetime.strptime(arrive_date_str, '%Y-%m-%d')
        except ValueError as e:
            print(f"提供的日期格式不正確: {e}")
            return jsonify(error=f"Incorrect date format: {e}"), 400

        #設置逗留的天數
        stay_duration = timedelta(days=no_of_stayed_days)

        # 計算離開日本的日期
        departure_date = arrival_date + stay_duration

        # 輸出結果
        print(f"離開日本的日期是：{departure_date.strftime('%Y-%m-%d')}")


        # Get last_user_id from Firebase and increment it
        last_user_id = ref.child("last_user_id").get()
        if last_user_id is None:
            # If it doesn't exist, start it at 1
            last_user_id = 1
        else:
            last_user_id += 1
                  
                     
        #get current time
        hongkong_timezone = pytz.timezone('Asia/Hong_Kong')
        timestamp = datetime.now(hongkong_timezone).isoformat()
        
        # 如果 step1_completed 為 True，則 'leave_time' 需要存在
        if request.json.get('step1_completed'):
            required_fields.append('leave_time')

        # 构建用户的图像
        trip_info = {
            'id': last_user_id,
            'destination': request.json.get('destination', ''),
            'arrive_time': request.json.get('arrive_time', ''),
            'no_of_stayed_days': no_of_stayed_days,
            # 其他字段也相應地從request.json中獲取
        }

        # 特殊情況：arrival_date 和 departure_date 需要格式化
        trip_info['arrival_date'] = arrival_date.strftime('%Y-%m-%d') if arrival_date else ''
        trip_info['departure_date'] = departure_date.strftime('%Y-%m-%d') if departure_date else ''
        trip_info['leave_time'] = request.json.get('leave_time', '')  # 刪除尾巴上的空白並設定 leave_time
        trip_info["timestamp"] = timestamp  # 現在時間戳記


        # 写入数据到 Firebase
        ref.child(f"log/{last_user_id}").set(trip_info)  # 这里使用了 f-string 格式化
        ref.child("last_user_id").set(last_user_id)

        # 返回成功信息和數據
        return jsonify({
            'message': 'Trip information successfully recorded.',
            'data': trip_info
        }), 200



   
       
       
     



@app.route("/character", methods=['POST'])
def manage_character():    
    if request.method == 'POST':
        # 收集图像链接
        generated_image_url = request.json.get('img_url', '')     
        
        # 调用之前定义的函数来存储图像并获得图像的公开URL
        image_public_url = store_image_to_firebase(generated_image_url)

        return jsonify({'image_url': image_public_url}), 200

    # 如果不是 POST 請求
    return "Invalid Method", 405


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
                     
@app.route("/test1", methods=['GET'])
def test1():
    return 'Test successful!', 200


