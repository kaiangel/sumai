from flask import Flask, request, jsonify, render_template
from flask_socketio import SocketIO, emit
from sumai import get_article_text, generate_summary
from flask_cors import CORS
import time

app = Flask(__name__)
CORS(app)
socketio = SocketIO(app, ping_timeout=120, cors_allowed_origins="*")

@app.route('/status')
def status():
    return "Server is running"

@app.route('/')
def home_page():
    return render_template('index.html')

# 错误处理函数
def handle_error(error_message, sid=None):
    print(f"An error occurred: {error_message}")
    if sid:
        emit('error', {'error': error_message}, room=sid)

# 状态消息函数
def send_status(message, sid):
    print(f"Status: {message}")
    emit('status', {'message': message}, room=sid)

'''
@app.route('/summary', methods=['POST'])
def summary():
    url = request.json.get('url', None)
    if not url:
        return jsonify({'error': 'No URL provided.'}), 400

    try:
        article_text = get_article_text(url)
    except Exception as e:
        return jsonify({'error': 'Failed to fetch the article text: ' + str(e)}), 500

    if not article_text:
        return jsonify({'error': 'No text found in the article.'}), 400

    try:
        summary = generate_summary(article_text)
    except Exception as e:
        return jsonify({'error': 'Failed to generate the summary: ' + str(e)}), 500

    if not summary:
        return jsonify({'error': 'No summary generated.'}), 400

    return jsonify({'summary': summary})
'''

@socketio.on('connect')
def test_connect():
    print('Client connected, SID:', request.sid)

@socketio.on('disconnect')
def test_disconnect():
    print('Client disconnected, SID:', request.sid)

@socketio.on('generate_summary')
def handle_summary(message):
    sid = request.sid  # 获取当前连接的Session ID
    print(f"Received request for summary generation from sid: {sid}")  # 输出当前连接的Session ID
    emit('status', {'message': '收到请求......'}, room=sid)  # 新增
    url = message.get('url', None)
    if not url:
        handle_error('No URL provided.', sid)
        return

    try:
        article_text = get_article_text(url, sid)
        if "error" in article_text:  # 或者你可以选择一个更明确的错误标志
            handle_error(article_text, sid)
            return
    except Exception as e:
        emit('error', {'error': 'Failed to fetch the article text: ' + str(e)})
        return

    if not article_text:
        emit('error', {'error': 'No text found in the article.'})
        return

    try:
        print("Generating summary...")
        emit('status', {'message': '已成功获取内容，魔法将大约在半分钟后诞生......'}, room=sid)
        print("Emitting status: 已成功获取内容，魔法将大约在半分钟后诞生......")  # 添加这行日志
        full_summary = generate_summary(article_text)  # 获取完整摘要

        # 打印即将发送的数据对象
        print("Sending the following data object to client:")
        print({"summary": full_summary[:30]})  # 仅显示摘要的前300个字符，以避免日志过长
        emit('status', {'message': '摘要生成中......'}, room=sid)

        emit('summary_complete', {'summary': full_summary})  # 发送完整摘要
    except Exception as e:
        emit('error', {'error': 'Failed to generate the summary: ' + str(e)})
        return

    print(f"Sent complete summary to client: {full_summary[:50]}...")  # 添加日志（只显示摘要的前50个字符）

if __name__ == "__main__":
    socketio.run(app, host='0.0.0.0', port=80, debug=True)