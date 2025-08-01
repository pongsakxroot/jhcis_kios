from flask import Flask, render_template, request, jsonify, redirect, url_for, session, make_response
import requests
import json
import mysql.connector
from datetime import datetime, timedelta
import re
import random
import base64
import hashlib
import os
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
import qrcode
from io import BytesIO

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'

# เพิ่ม context processor สำหรับ datetime
@app.context_processor
def utility_processor():
    def format_datetime(value, format='%d/%m/%Y'):
        if value is None:
            value = datetime.now()
        return value.strftime(format)
    
    def current_date():
        return datetime.now().strftime('%d/%m/%Y')
    
    def current_datetime():
        return datetime.now().strftime('%d/%m/%Y %H:%M:%S')
    
    return dict(
        format_datetime=format_datetime,
        current_date=current_date,
        current_datetime=current_datetime,
        now=datetime.now()
    )

# เก็บการตั้งค่าฐานข้อมูลในไฟล์
CONFIG_FILE = 'db_config.json'

def load_db_config():
    """โหลดการตั้งค่าฐานข้อมูลจากไฟล์"""
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            pass
    
    # ค่าเริ่มต้น
    default_config = {
        'host': 'localhost',
        'user': 'root',
        'password': '',
        'database': 'jhcis',
        'port': 3306
    }
    save_db_config(default_config)
    return default_config

def save_db_config(config):
    """บันทึกการตั้งค่าฐานข้อมูลลงไฟล์"""
    try:
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Error saving config: {e}")

# โหลดการตั้งค่าฐานข้อมูล
DB_CONFIG = load_db_config()

# เก็บข้อมูลชั่วคราวในหน่วยความจำแทน session
temp_data_store = {}

def get_db_connection():
    """สร้างการเชื่อมต่อฐานข้อมูล"""
    try:
        return mysql.connector.connect(**DB_CONFIG)
    except Exception as e:
        print(f"Database connection error: {e}")
        return None

def test_db_connection(config):
    """ทดสอบการเชื่อมต่อฐานข้อมูล"""
    try:
        conn = mysql.connector.connect(**config)
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        print(f"Database test error: {e}")
        return False

def read_smartcard():
    """อ่านข้อมูลจากบัตรประชาชนผ่าน API สปสช"""
    try:
        url = "http://127.0.0.1:8189/api/smartcard/read?readImageFlag=true"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            return response.json()
        return None
    except Exception as e:
        print(f"Error reading smartcard: {e}")
        return None

def parse_card_data(card_data):
    """แยกข้อมูลจากการ์ด - เก็บเฉพาะข้อมูลที่จำเป็น"""
    if not card_data:
        return None
    
    parsed_data = {
        'pid': card_data.get('pid', ''),
        'fname': card_data.get('fname', ''),
        'lname': card_data.get('lname', ''),
        'sex': card_data.get('sex', ''),
        'birthDate': card_data.get('birthDate', ''),
        'age': card_data.get('age', ''),
        'mainInscl': card_data.get('mainInscl', ''),
        'subInscl': card_data.get('subInscl', ''),
        'correlationId': card_data.get('correlationId', ''),
        'claimTypes': card_data.get('claimTypes', []),
        'hospMain': card_data.get('hospMain', {}),
        'mobile': ''
    }
    
    return parsed_data

def generate_session_id():
    """สร้าง session ID สำหรับเก็บข้อมูลชั่วคราว"""
    return hashlib.md5(f"{datetime.now()}{random.random()}".encode()).hexdigest()

def generate_random_phone():
    """สร้างเบอร์โทรศัพท์สุ่ม"""
    return f"0{random.randint(800000000, 999999999)}"

def get_person_data(pid):
    """ดึงข้อมูลบุคคลจากฐานข้อมูล"""
    try:
        conn = get_db_connection()
        if not conn:
            return None
            
        cursor = conn.cursor(dictionary=True)
        
        query = "SELECT * FROM person WHERE idcard = %s"
        cursor.execute(query, (pid,))
        result = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        return result
    except Exception as e:
        print(f"Error getting person data: {e}")
        return None

def get_visit_data(visitno):
    """ดึงข้อมูล visit จากฐานข้อมูล"""
    try:
        conn = get_db_connection()
        if not conn:
            return None
            
        cursor = conn.cursor(dictionary=True)
        
        query = """
        SELECT v.*, p.fname, p.lname, p.idcard, p.mobile
        FROM visit v
        LEFT JOIN person p ON v.pid = p.pid
        WHERE v.visitno = %s
        """
        cursor.execute(query, (visitno,))
        result = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        return result
    except Exception as e:
        print(f"Error getting visit data: {e}")
        return None

def get_hospital_info():
    """ดึงข้อมูลโรงพยาบาล"""
    try:
        conn = get_db_connection()
        if not conn:
            return {"name": "โรงพยาบาลทดสอบ", "address": "ที่อยู่โรงพยาบาล"}
            
        cursor = conn.cursor(dictionary=True)
        
        # ปรับ query ตามโครงสร้างฐานข้อมูล JHCIS
        query = "SELECT * FROM chospital LIMIT 1"
        cursor.execute(query)
        result = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        if result:
            return {
                "name": result.get('hosname', 'โรงพยาบาลทดสอบ'),
                "address": result.get('address', 'ที่อยู่โรงพยาบาล'),
                "tel": result.get('tel', ''),
                "province": result.get('provname', '')
            }
        else:
            return {"name": "โรงพยาบาลทดสอบ", "address": "ที่อยู่โรงพยาบาล"}
            
    except Exception as e:
        print(f"Error getting hospital info: {e}")
        return {"name": "โรงพยาบาลทดสอบ", "address": "ที่อยู่โรงพยาบาล"}

def confirm_nhso_service(pid, claim_type, mobile, correlation_id, hn):
    """ขอ Authentication จาก NHSO API"""
    try:
        url = "http://127.0.0.1:8189/api/nhso-service/confirm-save"
        
        payload = {
            "pid": pid,
            "claimType": claim_type,
            "mobile": mobile,
            "correlationId": correlation_id,
            "hn": hn
        }
        
        headers = {
            'Content-Type': 'application/json',
            'Authorization': '1234567890'
        }
        
        print(f"Sending NHSO request: {payload}")  # Debug
        
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        
        print(f"NHSO response status: {response.status_code}")  # Debug
        print(f"NHSO response text: {response.text}")  # Debug
        
        if response.status_code == 200:
            return response.json()
        else:
            print(f"NHSO API error: {response.status_code} - {response.text}")
            return None
        
    except requests.exceptions.RequestException as e:
        print(f"NHSO API connection error: {e}")
        return None
    except Exception as e:
        print(f"Error confirming NHSO service: {e}")
        return None

def parse_nhso_date(nhso_date_str):
    """แปลงวันที่จาก NHSO response เป็น MySQL datetime format"""
    if not nhso_date_str:
        return datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    try:
        # NHSO อาจส่งมาในรูปแบบ ISO 8601
        if 'T' in nhso_date_str:
            # ตัดเอาเฉพาะส่วนวันที่และเวลา (ไม่รวม timezone)
            dt_str = nhso_date_str.split('T')[0] + ' ' + nhso_date_str.split('T')[1].split('.')[0]
            dt = datetime.strptime(dt_str, '%Y-%m-%d %H:%M:%S')
        else:
            # รูปแบบธรรมดา
            dt = datetime.strptime(nhso_date_str, '%Y-%m-%d %H:%M:%S')
        
        return dt.strftime('%Y-%m-%d %H:%M:%S')
    except Exception as e:
        print(f"Error parsing NHSO date {nhso_date_str}: {e}")
        return datetime.now().strftime('%Y-%m-%d %H:%M:%S')

def draw_centered_text(canvas_obj, x, y, text, font_name, font_size, page_width):
    """ฟังก์ชันสำหรับวาดข้อความตรงกลาง"""
    try:
        canvas_obj.setFont(font_name, font_size)
        text_width = canvas_obj.stringWidth(str(text), font_name, font_size)
        canvas_obj.drawString((page_width - text_width) / 2, y, str(text))
    except Exception as e:
        print(f"Error drawing centered text: {e}")
        canvas_obj.setFont("Helvetica", font_size)
        canvas_obj.drawString(10, y, str(text))

def create_queue_slip_80mm(visit_data, hospital_info):
    """สร้างใบนำทาง 80mm"""
    buffer = BytesIO()
    
    try:
        # ขนาดกระดาษ 80mm
        page_width = 80 * mm
        page_height = 150 * mm
        
        c = canvas.Canvas(buffer, pagesize=(page_width, page_height))
        
        y_position = page_height - 20
        
        # หัวข้อ
        hospital_name = str(hospital_info.get('name', 'Hospital'))
        draw_centered_text(c, 0, y_position, hospital_name, 
                          "Helvetica-Bold", 14, page_width)
        y_position -= 15
        
        hospital_address = str(hospital_info.get('address', 'Address'))
        draw_centered_text(c, 0, y_position, hospital_address, 
                          "Helvetica", 10, page_width)
        y_position -= 20
        
        # เส้นแบ่ง
        c.line(10, y_position, page_width-10, y_position)
        y_position -= 15
        
        draw_centered_text(c, 0, y_position, "Queue Slip", "Helvetica-Bold", 12, page_width)
        y_position -= 20
        
        # ข้อมูลผู้ป่วย
        c.setFont("Helvetica", 9)
        
        # Visit No
        visit_no = str(visit_data.get('visitno', ''))
        c.drawString(10, y_position, f"Visit: {visit_no}")
        y_position -= 12
        
        # ชื่อ-นามสกุล
        fname = str(visit_data.get('fname', ''))
        lname = str(visit_data.get('lname', ''))
        full_name = f"{fname} {lname}".strip()
        c.drawString(10, y_position, f"Name: {full_name}")
        y_position -= 12
        
        # เลขบัตรประชาชน
        idcard = str(visit_data.get('idcard', ''))
        c.drawString(10, y_position, f"ID: {idcard}")
        y_position -= 12
        
        # วันที่-เวลา
        visit_date = visit_data.get('visitdate', datetime.now().strftime('%Y-%m-%d'))
        visit_time = visit_data.get('timestart', datetime.now().strftime('%H:%M:%S'))
        c.drawString(10, y_position, f"Date: {visit_date}")
        y_position -= 12
        c.drawString(10, y_position, f"Time: {visit_time}")
        y_position -= 12
        
        # Queue Number
        queue_no = str(visit_data.get('qdiscloser', 'A001'))
        c.drawString(10, y_position, f"Queue: {queue_no}")
        y_position -= 12
        
        # NHSO Claim Code (ถ้ามี)
        claim_code = str(visit_data.get('claimcode_nhso', ''))
        if claim_code:
            c.drawString(10, y_position, f"Claim: {claim_code}")
            y_position -= 12
        
        y_position -= 8
        
        # QR Code สำหรับ Visit No
        try:
            qr = qrcode.QRCode(version=1, box_size=2, border=1)
            qr.add_data(f"VISIT:{visit_no}")
            qr.make(fit=True)
            
            qr_img = qr.make_image(fill_color="black", back_color="white")
            qr_buffer = BytesIO()
            qr_img.save(qr_buffer, format='PNG')
            qr_buffer.seek(0)
            
            # เพิ่ม QR Code ลงใน PDF
            c.drawInlineImage(qr_buffer, page_width/2 - 25, y_position - 50, 50, 50)
            y_position -= 60
        except Exception as e:
            print(f"QR Code error: {e}")
            y_position -= 20
        
        # ข้อความท้าย
        draw_centered_text(c, 0, y_position, "Please wait for your queue", 
                          "Helvetica", 8, page_width)
        y_position -= 10
        
        current_time = datetime.now().strftime('%d/%m/%Y %H:%M')
        draw_centered_text(c, 0, y_position, f"Printed: {current_time}", 
                          "Helvetica", 8, page_width)
        
        c.save()
        buffer.seek(0)
        return buffer
        
    except Exception as e:
        print(f"Error creating 80mm PDF: {e}")
        # สร้าง PDF เปล่าแทน
        buffer = BytesIO()
        c = canvas.Canvas(buffer, pagesize=(80 * mm, 150 * mm))
        c.setFont("Helvetica", 10)
        c.drawString(10, 100, "Error creating PDF")
        c.drawString(10, 80, f"Visit: {visit_data.get('visitno', '')}")
        c.save()
        buffer.seek(0)
        return buffer

def create_queue_slip_58mm(visit_data, hospital_info):
    """สร้างใบนำทาง 58mm"""
    buffer = BytesIO()
    
    try:
        # ขนาดกระดาษ 58mm
        page_width = 58 * mm
        page_height = 120 * mm
        
        c = canvas.Canvas(buffer, pagesize=(page_width, page_height))
        
        y_position = page_height - 15
        
        # หัวข้อ
        hospital_name = str(hospital_info.get('name', 'Hospital'))
        draw_centered_text(c, 0, y_position, hospital_name, 
                          "Helvetica-Bold", 10, page_width)
        y_position -= 12
        
        hospital_address = str(hospital_info.get('address', 'Address'))
        draw_centered_text(c, 0, y_position, hospital_address, 
                          "Helvetica", 8, page_width)
        y_position -= 15
        
        # เส้นแบ่ง
        c.line(5, y_position, page_width-5, y_position)
        y_position -= 12
        
        draw_centered_text(c, 0, y_position, "Queue Slip", "Helvetica-Bold", 10, page_width)
        y_position -= 15
        
        # ข้อมูลผู้ป่วย
        c.setFont("Helvetica", 7)
        
        # Visit No
        visit_no = str(visit_data.get('visitno', ''))
        c.drawString(5, y_position, f"Visit: {visit_no}")
        y_position -= 10
        
        # ชื่อ-นามสกุล
        fname = str(visit_data.get('fname', ''))
        lname = str(visit_data.get('lname', ''))
        full_name = f"{fname} {lname}".strip()
        if len(full_name) > 25:
            full_name = full_name[:22] + "..."
        c.drawString(5, y_position, f"Name: {full_name}")
        y_position -= 10
        
        # เลขบัตรประชาชน
        idcard = str(visit_data.get('idcard', ''))
        c.drawString(5, y_position, f"ID: {idcard}")
        y_position -= 10
        
        # วันที่-เวลา
        visit_date = visit_data.get('visitdate', datetime.now().strftime('%Y-%m-%d'))
        visit_time = visit_data.get('timestart', datetime.now().strftime('%H:%M:%S'))
        c.drawString(5, y_position, f"Date: {visit_date}")
        y_position -= 10
        c.drawString(5, y_position, f"Time: {visit_time}")
        y_position -= 10
        
        # Queue Number - ขนาดใหญ่
        queue_no = str(visit_data.get('qdiscloser', 'A001'))
        draw_centered_text(c, 0, y_position, f"Queue: {queue_no}", 
                          "Helvetica-Bold", 12, page_width)
        y_position -= 25
        
        # QR Code ขนาดเล็ก
        try:
            qr = qrcode.QRCode(version=1, box_size=1, border=1)
            qr.add_data(f"VISIT:{visit_no}")
            qr.make(fit=True)
            
            qr_img = qr.make_image(fill_color="black", back_color="white")
            qr_buffer = BytesIO()
            qr_img.save(qr_buffer, format='PNG')
            qr_buffer.seek(0)
            
            # เพิ่ม QR Code ลงใน PDF
            c.drawInlineImage(qr_buffer, page_width/2 - 15, y_position - 30, 30, 30)
            y_position -= 35
        except Exception as e:
            print(f"QR Code error: {e}")
            y_position -= 20
        
        # ข้อความท้าย
        draw_centered_text(c, 0, y_position, "Please wait", "Helvetica", 6, page_width)
        y_position -= 8
        
        current_time = datetime.now().strftime('%d/%m/%Y %H:%M')
        draw_centered_text(c, 0, y_position, f"Print: {current_time}", "Helvetica", 6, page_width)
        
        c.save()
        buffer.seek(0)
        return buffer
        
    except Exception as e:
        print(f"Error creating 58mm PDF: {e}")
        # สร้าง PDF เปล่าแทน
        buffer = BytesIO()
        c = canvas.Canvas(buffer, pagesize=(58 * mm, 120 * mm))
        c.setFont("Helvetica", 8)
        c.drawString(5, 80, "Error creating PDF")
        c.drawString(5, 60, f"Visit: {visit_data.get('visitno', '')}")
        c.save()
        buffer.seek(0)
        return buffer

def get_latest_qdiscloser():
    """ดึงหมายเลข qdiscloser ล่าสุด"""
    try:
        conn = get_db_connection()
        if not conn:
            return "A001"
            
        cursor = conn.cursor(dictionary=True)
        
        query = """
        SELECT qdiscloser FROM visit 
        WHERE visitdate = CURDATE() 
        AND qdiscloser IS NOT NULL
        ORDER BY qdiscloser DESC LIMIT 1
        """
        
        cursor.execute(query)
        result = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        if result and result['qdiscloser']:
            # สร้างหมายเลขคิวใหม่
            last_queue = result['qdiscloser']
            if last_queue.startswith('A'):
                try:
                    num = int(last_queue[1:]) + 1
                    return f"A{num:03d}"
                except:
                    return "A001"
            else:
                return "A001"
        else:
            return "A001"
            
    except Exception as e:
        print(f"Error getting qdiscloser: {e}")
        return "A001"

def create_visit(person_data, card_data, claim_type, nhso_response=None):
    """สร้าง visit ใหม่ในฐานข้อมูล พร้อมข้อมูล NHSO"""
    try:
        conn = get_db_connection()
        if not conn:
            return None
            
        cursor = conn.cursor()
        
        # ดึงหมายเลข visitno ล่าสุด
        cursor.execute("SELECT visitno FROM visit ORDER BY visitno DESC LIMIT 1")
        last_visit = cursor.fetchone()
        visitno = (last_visit[0] + 1) if last_visit else 1
        
        # ดึง qdiscloser ล่าสุด
        qdiscloser = get_latest_qdiscloser()
        
        # วันที่และเวลาปัจจุบัน
        current_date = datetime.now().strftime('%Y-%m-%d')
        current_time = datetime.now().strftime('%H:%M:%S')
        current_datetime = f"{current_date} {current_time}"
        
        # เตรียมข้อมูล NHSO
        claim_code_nhso = None
        correlation_id_nhso = card_data.get('correlationId', '')
        nhso_created_date = None
        
        if nhso_response and nhso_response.get('status') == 'success':
            # ใช้ claimCode จาก NHSO response
            claim_code_nhso = nhso_response.get('claimCode', '')
            
            # ใช้วันที่จาก NHSO response
            if nhso_response.get('createdDate'):
                nhso_created_date = parse_nhso_date(nhso_response.get('createdDate'))
            else:
                nhso_created_date = current_datetime
        else:
            # Fallback: ใช้ claimType แทน claimCode ถ้า NHSO ล้มเหลว
            claim_code_nhso = claim_type
            nhso_created_date = current_datetime
        
        # เพิ่ม visit ใหม่
        insert_query = """
        INSERT INTO visit (
            pcucode, visitno, pid, visitdate, pcucodeperson, rightcode,
            timeservice, flagservice, typein, timestart, servicetype,
            qdiscloser, timeend, rightno, hiciauthen_nhso, dateupdate,
            claimcode_nhso, datetime_claim, correlationid_nhso
        ) VALUES (
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
        )
        """
        
        values = (
            person_data.get('pcucodeperson', ''), visitno, person_data.get('pid', ''),
            current_date, person_data.get('pcucodeperson', ''), '00',
            '2', '00', '1', current_time, '1',
            qdiscloser, current_time, person_data.get('rightno', ''),
            'PG0060001', current_datetime,
            claim_code_nhso, nhso_created_date, correlation_id_nhso
        )
        
        cursor.execute(insert_query, values)
        conn.commit()
        
        print(f"Created visit {visitno} with NHSO data:")
        print(f"  - claimcode_nhso: {claim_code_nhso}")
        print(f"  - correlationid_nhso: {correlation_id_nhso}")
        print(f"  - datetime_claim: {nhso_created_date}")
        
        cursor.close()
        conn.close()
        
        return visitno
        
    except Exception as e:
        print(f"Error creating visit: {e}")
        return None

# Routes
@app.route('/')
def index():
    """หน้าแรก - อ่านบัตรประชาชน"""
    return render_template('index.html')

@app.route('/settings')
def settings():
    """หน้าตั้งค่า"""
    return render_template('settings.html', config=DB_CONFIG)

@app.route('/save-settings', methods=['POST'])
def save_settings():
    """บันทึกการตั้งค่าฐานข้อมูล"""
    try:
        new_config = {
            'host': request.form.get('host', 'localhost'),
            'user': request.form.get('user', 'root'),
            'password': request.form.get('password', ''),
            'database': request.form.get('database', 'jhcis'),
            'port': int(request.form.get('port', 3306))
        }
        
        # ทดสอบการเชื่อมต่อ
        if test_db_connection(new_config):
            global DB_CONFIG
            DB_CONFIG = new_config
            save_db_config(new_config)
            return jsonify({'success': True, 'message': 'บันทึกการตั้งค่าสำเร็จ'})
        else:
            return jsonify({'success': False, 'message': 'ไม่สามารถเชื่อมต่อฐานข้อมูลได้'}), 400
            
    except Exception as e:
        return jsonify({'success': False, 'message': f'เกิดข้อผิดพลาด: {str(e)}'}), 400

@app.route('/test-connection', methods=['POST'])
def test_connection():
    """ทดสอบการเชื่อมต่อฐานข้อมูล"""
    try:
        config = {
            'host': request.form.get('host', 'localhost'),
            'user': request.form.get('user', 'root'),
            'password': request.form.get('password', ''),
            'database': request.form.get('database', 'jhcis'),
            'port': int(request.form.get('port', 3306))
        }
        
        if test_db_connection(config):
            return jsonify({'success': True, 'message': 'เชื่อมต่อฐานข้อมูลสำเร็จ'})
        else:
            return jsonify({'success': False, 'message': 'ไม่สามารถเชื่อมต่อฐานข้อมูลได้'}), 400
            
    except Exception as e:
        return jsonify({'success': False, 'message': f'เกิดข้อผิดพลาด: {str(e)}'}), 400

@app.route('/read-card', methods=['POST'])
def read_card():
    """อ่านข้อมูลจากบัตรประชาชน"""
    card_data = read_smartcard()
    
    if not card_data:
        return jsonify({'error': 'ไม่สามารถอ่านบัตรได้ กรุณาตรวจสอบการเชื่อมต่อ'}), 400
    
    parsed_data = parse_card_data(card_data)
    if not parsed_data:
        return jsonify({'error': 'ไม่สามารถอ่านข้อมูลจากบัตรได้'}), 400
    
    # สร้าง session ID และเก็บข้อมูลในหน่วยความจำ
    session_id = generate_session_id()
    temp_data_store[session_id] = parsed_data
    
    # เก็บเฉพาะ session_id ใน session
    session['data_id'] = session_id
    session['pid'] = parsed_data['pid']
    
    return jsonify({'success': True, 'redirect': '/patient-info'})

@app.route('/patient-info')
def patient_info():
    """หน้าแสดงข้อมูลผู้ป่วย"""
    data_id = session.get('data_id')
    if not data_id or data_id not in temp_data_store:
        return redirect(url_for('index'))
    
    card_data = temp_data_store[data_id]
    
    # ดึงข้อมูลเพิ่มเติมจากฐานข้อมูล
    person_data = get_person_data(card_data['pid'])
    if person_data:
        card_data['mobile'] = person_data.get('mobile', '')
        card_data['hn'] = person_data.get('hn', '')
    
    return render_template('patient_info.html', data=card_data)

@app.route('/select-service')
def select_service():
    """หน้าเลือกบริการ"""
    data_id = session.get('data_id')
    if not data_id or data_id not in temp_data_store:
        return redirect(url_for('index'))
    
    card_data = temp_data_store[data_id]
    claim_types = card_data.get('claimTypes', [])
    
    return render_template('service_selection.html', 
                         data=card_data, 
                         claim_types=claim_types)

@app.route('/confirm-service', methods=['POST'])
def confirm_service():
    """ยืนยันการใช้บริการ พร้อมจัดการข้อมูล NHSO"""
    data_id = session.get('data_id')
    if not data_id or data_id not in temp_data_store:
        return jsonify({'error': 'ไม่พบข้อมูล กรุณาอ่านบัตรใหม่'}), 400
    
    card_data = temp_data_store[data_id]
    selected_claim_type = request.form.get('claim_type')
    
    if not selected_claim_type:
        return jsonify({'error': 'กรุณาเลือกบริการ'}), 400
    
    # ตรวจสอบข้อมูลผู้ป่วยในฐานข้อมูล
    person_data = get_person_data(card_data['pid'])
    
    if not person_data:
        return jsonify({'error': 'ไม่พบข้อมูลผู้ป่วยในระบบ JHCIS'}), 400
    
    # สร้างเบอร์โทรศัพท์หากไม่มี
    mobile = person_data.get('mobile') or generate_random_phone()
    
    # ขอ Authentication จาก NHSO
    nhso_response = None
    nhso_status = 'failed'
    
    try:
        nhso_result = confirm_nhso_service(
            card_data['pid'],
            selected_claim_type,
            mobile,
            card_data['correlationId'],
            person_data.get('hn', '')
        )
        
        if nhso_result:
            nhso_response = nhso_result
            nhso_status = 'success'
            print("NHSO Authentication successful")
            print(f"NHSO Response: {nhso_result}")
        else:
            print("NHSO Authentication failed, continuing without it")
            
    except Exception as e:
        print(f"NHSO Authentication error: {e}, continuing without it")
    
    # สร้าง visit ใหม่ พร้อมข้อมูล NHSO
    visitno = create_visit(person_data, card_data, selected_claim_type, nhso_response)
    
    if not visitno:
        return jsonify({'error': 'ไม่สามารถสร้าง visit ได้'}), 400
    
    # เก็บข้อมูลสำหรับหน้า success
    session['last_visitno'] = visitno
    session['nhso_status'] = nhso_status
    session['claim_code'] = nhso_response.get('claimCode', selected_claim_type) if nhso_response else selected_claim_type
    session['correlation_id'] = card_data.get('correlationId', '')
    
    # ลบข้อมูลชั่วคราวหลังใช้งานเสร็จ
    if data_id in temp_data_store:
        del temp_data_store[data_id]
    
    return jsonify({
        'success': True,
        'visitno': visitno,
        'message': 'ลงทะเบียนสำเร็จ',
        'nhso_status': nhso_status,
        'claim_code': nhso_response.get('claimCode', selected_claim_type) if nhso_response else selected_claim_type,
        'correlation_id': card_data.get('correlationId', '')
    })

@app.route('/success')
def success():
    """หน้าแสดงผลสำเร็จ พร้อมข้อมูล NHSO"""
    visitno = session.get('last_visitno')
    nhso_status = session.get('nhso_status', 'unknown')
    claim_code = session.get('claim_code', '')
    correlation_id = session.get('correlation_id', '')
    
    # ดึงข้อมูล visit เพื่อแสดงข้อมูลที่สมบูรณ์
    visit_data = None
    if visitno:
        visit_data = get_visit_data(visitno)
    
    return render_template('success.html', 
                         visitno=visitno,
                         nhso_status=nhso_status,
                         claim_code=claim_code,
                         correlation_id=correlation_id,
                         visit_data=visit_data)

@app.route('/test-print')
def test_print():
    """ทดสอบการพิมพ์"""
    # สร้างข้อมูลจำลอง
    test_visit_data = {
        'visitno': '12345',
        'fname': 'ทดสอบ',
        'lname': 'ระบบ',
        'idcard': '1234567890123',
        'visitdate': datetime.now().strftime('%Y-%m-%d'),
        'timestart': datetime.now().strftime('%H:%M:%S'),
        'qdiscloser': 'A001',
        'claimcode_nhso': 'PG0060001',
        'correlationid_nhso': 'test-correlation-id'
    }
    
    # เก็บข้อมูลทดสอบใน session
    session['last_visitno'] = '12345'
    session['nhso_status'] = 'success'
    session['claim_code'] = 'PG0060001'
    session['correlation_id'] = 'test-correlation-id'
    
    return render_template('success.html', 
                         visitno='12345',
                         nhso_status='success',
                         claim_code='PG0060001',
                         correlation_id='test-correlation-id')

@app.route('/print-slip/<paper_size>')
def print_slip(paper_size):
    """พิมพ์ใบนำทาง"""
    visitno = session.get('last_visitno')
    if not visitno:
        return "ไม่พบข้อมูล Visit", 404
    
    # ดึงข้อมูล visit
    visit_data = get_visit_data(visitno)
    if not visit_data:
        # สร้างข้อมูลจำลองถ้าไม่พบในฐานข้อมูล
        visit_data = {
            'visitno': visitno,
            'fname': 'ทดสอบ',
            'lname': 'ระบบ',
            'idcard': '1234567890123',
            'visitdate': datetime.now().strftime('%Y-%m-%d'),
            'timestart': datetime.now().strftime('%H:%M:%S'),
            'qdiscloser': 'A001',
            'claimcode_nhso': session.get('claim_code', ''),
            'correlationid_nhso': session.get('correlation_id', '')
        }
    
    # ดึงข้อมูลโรงพยาบาล
    hospital_info = get_hospital_info()
    
    # สร้างใบนำทางตามขนาดกระดาษ
    try:
        if paper_size == '80mm':
            pdf_buffer = create_queue_slip_80mm(visit_data, hospital_info)
            filename = f"queue_slip_80mm_{visitno}.pdf"
        elif paper_size == '58mm':
            pdf_buffer = create_queue_slip_58mm(visit_data, hospital_info)
            filename = f"queue_slip_58mm_{visitno}.pdf"
        else:
            return "ขนาดกระดาษไม่ถูกต้อง", 400
        
        # ส่งไฟล์ PDF
        response = make_response(pdf_buffer.getvalue())
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = f'inline; filename={filename}'
        
        return response
        
    except Exception as e:
        print(f"Error creating PDF: {e}")
        return f"เกิดข้อผิดพลาดในการสร้าง PDF: {str(e)}", 500

@app.route('/api/test-smartcard')
def test_smartcard():
    """API สำหรับทดสอบการอ่านบัตร"""
    # ส่งข้อมูลจำลองสำหรับทดสอบ
    test_data = {
        "pid": "1111111111119",
        "titleName": "001",
        "fname": "ทดสอบ",
        "lname": "ระบบ",
        "nation": "099",
        "birthDate": "25240624",
        "sex": "ชาย",
        "transDate": "2018-02-01T17:30:04",
        "mainInscl": "(SSS) สิทธิประกันสังคม",
        "subInscl": "(S1) สิทธิเบิกกองทุนประกันสังคม (ผู้ประกันตน)",
        "age": "44 ปี 1 เดือน 8 วัน",
        "checkDate": "2025-08-01T14:34:28",
        "claimTypes": [
            {
                "claimType": "PG0060001",
                "claimTypeName": "เข้ารับบริการรักษาทั่วไป (OPD/ IPD/ PP)"
            },
            {
                "claimType": "PG0110001",
                "claimTypeName": "Self Isolation"
            },
            {
                "claimType": "PG0120001",
                "claimTypeName": "UCEP PLUS (ผู้ป่วยกลุ่มอาการสีเหลืองและสีแดง)"
            }
        ],
        "correlationId": "27d28b1f-58d2-4428-b255-71a51905f1f4",
        "hospMain": {
            "hcode": "10716",
            "hname": "รพ.น่าน"
        },
        "startDateTime": "2017-01-01T00:00:00"
    }
    return jsonify(test_data)

@app.route('/test-card')
def test_card():
    """หน้าทดสอบระบบโดยไม่ต้องใช้บัตรจริง"""
    # สร้างข้อมูลจำลอง
    test_data = {
        'pid': '1111111111119',
        'fname': 'ทดสอบ',
        'lname': 'ระบบ',
        'sex': 'ชาย',
        'birthDate': '25240624',
        'age': '44 ปี 1 เดือน 8 วัน',
        'mainInscl': '(SSS) สิทธิประกันสังคม',
        'subInscl': '(S1) สิทธิเบิกกองทุนประกันสังคม (ผู้ประกันตน)',
        'correlationId': '27d28b1f-58d2-4428-b255-71a51905f1f4',
        'claimTypes': [
            {
                'claimType': 'PG0060001',
                'claimTypeName': 'เข้ารับบริการรักษาทั่วไป (OPD/ IPD/ PP)'
            },
            {
                'claimType': 'PG0110001',
                'claimTypeName': 'Self Isolation'
            }
        ],
        'hospMain': {
            'hcode': '10716',
            'hname': 'รพ.น่าน'
        },
        'mobile': '0812345678'
    }
    
    # สร้าง session ID และเก็บข้อมูลทดสอบ
    session_id = generate_session_id()
    temp_data_store[session_id] = test_data
    
    # เก็บ session_id
    session['data_id'] = session_id
    session['pid'] = test_data['pid']
    
    return redirect(url_for('patient_info'))

@app.errorhandler(404)
def not_found(error):
    """จัดการ 404 Error"""
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    """จัดการ 500 Error"""
    return render_template('500.html'), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)