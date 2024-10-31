from flask import Flask, jsonify
from flask_cors import CORS
from datetime import datetime
import os

app = Flask(__name__)
CORS(app)

# 添加错误处理
@app.errorhandler(404)
def not_found_error(error):
    return jsonify({"error": "Resource not found"}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({"error": "Internal server error"}), 500

@app.route('/')
def home():
    return jsonify({
        "status": "running",
        "message": "TLDR Newsletter Chinese API is running!",
        "version": "1.0.0"
    })

@app.route('/api/newsletter/<date>')
def get_newsletter_data(date):
    try:
        # 验证日期格式
        datetime.strptime(date, '%Y-%m-%d')
        
        # TODO: 实现实际的数据获取逻辑
        # 这里应该添加从数据源获取newsletter数据的代码
        
        return jsonify({
            "date": date,
            "content": [],  # 这里将来放实际的newsletter内容
            "status": "success"
        })
    except ValueError:
        return jsonify({
            "error": "Invalid date format. Please use YYYY-MM-DD"
        }), 400
    except Exception as e:
        return jsonify({
            "error": "An error occurred while processing your request"
        }), 500

if __name__ == '__main__':
    app.run(debug=os.getenv('FLASK_DEBUG', 'False') == 'True')