"""
한글 → PDF 변환 웹 서버
Flask 기반 REST API 서버
"""

import os
import uuid
import shutil
import zipfile
import threading
from datetime import datetime
from urllib.parse import unquote
from flask import Flask, request, jsonify, send_file, send_from_directory
from flask_cors import CORS
from werkzeug.utils import secure_filename

from converter import HwpToPdfConverter

# 앱 설정
app = Flask(__name__, static_folder='static')
CORS(app)

# 디렉토리 설정
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_DIR = os.path.join(BASE_DIR, 'uploads')
OUTPUT_DIR = os.path.join(BASE_DIR, 'outputs')

# 디렉토리 생성
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

# 허용 확장자
ALLOWED_EXTENSIONS = {'hwp', 'hwpx'}

# 변환 작업 상태 저장
conversion_tasks = {}


def allowed_file(filename):
    """허용된 파일 확장자인지 확인"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def generate_task_id():
    """고유 작업 ID 생성"""
    return str(uuid.uuid4())[:8]


def cleanup_old_files():
    """1시간 이상 된 파일 정리"""
    now = datetime.now().timestamp()
    for directory in [UPLOAD_DIR, OUTPUT_DIR]:
        for filename in os.listdir(directory):
            filepath = os.path.join(directory, filename)
            if os.path.isfile(filepath):
                file_age = now - os.path.getmtime(filepath)
                if file_age > 3600:  # 1시간
                    try:
                        os.remove(filepath)
                    except:
                        pass


@app.route('/')
def index():
    """메인 페이지"""
    return send_from_directory('static', 'index.html')


@app.route('/static/<path:filename>')
def serve_static(filename):
    """정적 파일 서빙"""
    return send_from_directory('static', filename)


@app.route('/api/convert', methods=['POST'])
def convert_files():
    """파일 변환 API"""
    if 'files' not in request.files:
        return jsonify({'error': '파일이 없습니다'}), 400
    
    files = request.files.getlist('files')
    if not files or all(f.filename == '' for f in files):
        return jsonify({'error': '선택된 파일이 없습니다'}), 400
    
    # 작업 ID 생성
    task_id = generate_task_id()
    task_upload_dir = os.path.join(UPLOAD_DIR, task_id)
    task_output_dir = os.path.join(OUTPUT_DIR, task_id)
    os.makedirs(task_upload_dir, exist_ok=True)
    os.makedirs(task_output_dir, exist_ok=True)
    
    # 작업 상태 초기화
    conversion_tasks[task_id] = {
        'status': 'processing',
        'total': 0,
        'completed': 0,
        'results': []
    }
    
    # 파일 저장 및 정보 수집
    file_infos = []
    for file in files:
        if file and file.filename and allowed_file(file.filename):
            # 원본 파일명 유지 (안전하게 처리)
            original_filename = file.filename
            # 파일명에서 안전하지 않은 문자만 제거
            safe_filename = secure_filename(original_filename)
            if not safe_filename:
                safe_filename = f"file_{uuid.uuid4()[:8]}.hwp"
            
            # 원본 파일명 보존 (확장자 제외한 이름)
            original_name_without_ext = os.path.splitext(original_filename)[0]
            
            filepath = os.path.join(task_upload_dir, safe_filename)
            file.save(filepath)
            
            file_infos.append({
                'path': filepath,
                'original_name': original_name_without_ext,
                'safe_filename': safe_filename
            })
    
    if not file_infos:
        return jsonify({'error': '유효한 HWP/HWPX 파일이 없습니다'}), 400
    
    conversion_tasks[task_id]['total'] = len(file_infos)
    
    # 백그라운드에서 변환 수행
    def convert_in_background():
        converter = HwpToPdfConverter()
        
        for info in file_infos:
            result = {
                'filename': info['original_name'],
                'success': False,
                'error': None,
                'pdf_filename': None
            }
            
            try:
                # PDF 파일명 생성 (원본 이름 유지)
                pdf_filename = info['original_name'] + '.pdf'
                pdf_path = os.path.join(task_output_dir, pdf_filename)
                
                # 변환 수행
                converter.convert(info['path'], pdf_path)
                
                result['success'] = True
                result['pdf_filename'] = pdf_filename
                
            except Exception as e:
                result['error'] = str(e)
            
            conversion_tasks[task_id]['results'].append(result)
            conversion_tasks[task_id]['completed'] += 1
        
        conversion_tasks[task_id]['status'] = 'completed'
        
        # 업로드 폴더 정리
        try:
            shutil.rmtree(task_upload_dir)
        except:
            pass
    
    # 스레드로 변환 실행
    thread = threading.Thread(target=convert_in_background)
    thread.start()
    
    return jsonify({
        'task_id': task_id,
        'message': '변환이 시작되었습니다',
        'total': len(file_infos)
    })


@app.route('/api/status/<task_id>', methods=['GET'])
def get_status(task_id):
    """변환 상태 확인 API"""
    if task_id not in conversion_tasks:
        return jsonify({'error': '작업을 찾을 수 없습니다'}), 404
    
    task = conversion_tasks[task_id]
    return jsonify({
        'status': task['status'],
        'total': task['total'],
        'completed': task['completed'],
        'results': task['results']
    })


@app.route('/api/download/<task_id>/<path:filename>', methods=['GET'])
def download_file(task_id, filename):
    """개별 PDF 다운로드"""
    # URL 디코딩 (한글 파일명 처리)
    decoded_filename = unquote(filename)
    
    task_output_dir = os.path.join(OUTPUT_DIR, task_id)
    filepath = os.path.join(task_output_dir, decoded_filename)
    
    if not os.path.exists(filepath):
        return jsonify({'error': '파일을 찾을 수 없습니다'}), 404
    
    return send_file(
        filepath,
        as_attachment=True,
        download_name=decoded_filename,
        mimetype='application/pdf'
    )


@app.route('/api/download-all/<task_id>', methods=['GET'])
def download_all(task_id):
    """모든 PDF를 ZIP으로 다운로드"""
    task_output_dir = os.path.join(OUTPUT_DIR, task_id)
    
    if not os.path.exists(task_output_dir):
        return jsonify({'error': '작업을 찾을 수 없습니다'}), 404
    
    # ZIP 파일 생성
    zip_filename = f'converted_{task_id}.zip'
    zip_path = os.path.join(OUTPUT_DIR, zip_filename)
    
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for filename in os.listdir(task_output_dir):
            if filename.endswith('.pdf'):
                filepath = os.path.join(task_output_dir, filename)
                zipf.write(filepath, filename)
    
    return send_file(
        zip_path,
        as_attachment=True,
        download_name=zip_filename,
        mimetype='application/zip'
    )


@app.route('/api/cleanup/<task_id>', methods=['DELETE'])
def cleanup_task(task_id):
    """작업 정리"""
    task_output_dir = os.path.join(OUTPUT_DIR, task_id)
    
    if os.path.exists(task_output_dir):
        try:
            shutil.rmtree(task_output_dir)
        except:
            pass
    
    if task_id in conversion_tasks:
        del conversion_tasks[task_id]
    
    return jsonify({'message': '정리 완료'})


if __name__ == '__main__':
    print("=" * 50)
    print("  한글 → PDF 변환 서버")
    print("  http://localhost:5000 에서 접속하세요")
    print("=" * 50)
    
    # 주기적으로 오래된 파일 정리
    cleanup_old_files()
    
    app.run(host='0.0.0.0', port=5000, debug=True, threaded=True)
