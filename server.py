"""
健身房入会须知 - 后端服务
使用 Flask + SQLite 存储数据
"""

from flask import Flask, request, jsonify, send_from_directory, send_file
from flask_cors import CORS
import sqlite3
import os
import csv
import io
from datetime import datetime

app = Flask(__name__, static_folder='.', static_url_path='')
CORS(app)

# 数据库文件
DB_FILE = 'gym_data.db'

def init_db():
    """初始化数据库"""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS submissions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        phone TEXT NOT NULL,
        id_card TEXT,
        emergency_name TEXT NOT NULL,
        emergency_phone TEXT NOT NULL,
        signature TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    conn.commit()
    conn.close()

@app.route('/')
def index():
    """前端页面"""
    return send_from_directory('.', 'gym-form.html')

@app.route('/api/submit', methods=['POST'])
def submit():
    """提交数据"""
    data = request.json
    
    # 验证必填字段
    required = ['name', 'phone', 'emergencyName', 'emergencyPhone', 'signature']
    for field in required:
        if not data.get(field):
            return jsonify({'success': False, 'message': f'缺少字段：{field}'}), 400
    
    # 保存到数据库
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''INSERT INTO submissions 
        (name, phone, id_card, emergency_name, emergency_phone, signature)
        VALUES (?, ?, ?, ?, ?, ?)''',
        (data['name'], data['phone'], data.get('idCard', ''),
         data['emergencyName'], data['emergencyPhone'], data['signature']))
    conn.commit()
    conn.close()
    
    return jsonify({'success': True, 'message': '提交成功'})

@app.route('/api/admin/login', methods=['POST'])
def admin_login():
    """管理员登录"""
    data = request.json
    password = data.get('password', '')
    
    # 管理密码（请修改为您的密码）
    ADMIN_PASSWORD = 'geely2026'
    
    if password == ADMIN_PASSWORD:
        return jsonify({'success': True})
    else:
        return jsonify({'success': False, 'message': '密码错误'}), 401

@app.route('/api/admin/data')
def admin_data():
    """获取所有提交数据"""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('SELECT * FROM submissions ORDER BY created_at DESC')
    rows = c.fetchall()
    conn.close()
    
    records = []
    for row in rows:
        records.append({
            'id': row[0],
            'name': row[1],
            'phone': row[2],
            'idCard': row[3],
            'emergencyName': row[4],
            'emergencyPhone': row[5],
            'signature': row[6],
            'time': row[7]
        })
    
    return jsonify({'success': True, 'data': records})

@app.route('/api/admin/export')
def admin_export():
    """导出数据为CSV"""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('SELECT * FROM submissions ORDER BY created_at DESC')
    rows = c.fetchall()
    conn.close()
    
    # 创建CSV
    output = io.StringIO()
    output.write('\ufeff')  # UTF-8 BOM
    writer = csv.writer(output)
    writer.writerow(['姓名', '手机号', '身份证号', '紧急联系人姓名', '紧急联系人手机号', '提交时间'])
    
    for row in rows:
        writer.writerow([row[1], row[2], row[3], row[4], row[5], row[7]])
    
    # 返回CSV文件
    csv_data = output.getvalue()
    return send_file(
        io.BytesIO(csv_data.encode('utf-8')),
        mimetype='text/csv',
        as_attachment=True,
        download_name=f'健身房入会登记_{datetime.now().strftime("%Y%m%d")}.csv'
    )

@app.route('/api/admin/clear', methods=['POST'])
def admin_clear():
    """清空所有数据"""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('DELETE FROM submissions')
    conn.commit()
    conn.close()
    
    return jsonify({'success': True, 'message': '数据已清空'})

if __name__ == '__main__':
    init_db()
    print('服务器启动：http://localhost:5000')
    print('管理后台：http://localhost:5000/api/admin/data')
    app.run(host='0.0.0.0', port=5000, debug=False)
