# ระบบลงทะเบียน OPD พร้อมการเชื่อมต่อ NHSO

ระบบลงทะเบียนผู้ป่วยนอกที่รองรับการอ่านบัตรประชาชนและการยืนยันสิทธิ์ผ่าน สปสช. (NHSO) พร้อมการพิมพ์ใบนำทางอัตโนมัติ

## ✨ คุณสมบัติหลัก

### 🔑 การจัดการ NHSO ที่ปรับปรุงแล้ว
- **ใช้ claimCode จาก NHSO**: บันทึกลงฟิลด์ `claimcode_nhso` ในตาราง visit
- **เก็บ correlationId**: บันทึกลงฟิลด์ `correlationid_nhso` 
- **ใช้วันที่จาก NHSO**: บันทึก `createdDate` จาก NHSO response
- **แสดงข้อมูล NHSO**: ในหน้า success แสดง claimCode และสถานะ
- **Fallback mechanism**: ถ้า NHSO ล้มเหลว จะใช้ claimType แทน claimCode

### 🏥 ระบบหลัก
- **อ่านบัตรประชาชน**: เชื่อมต่อกับเครื่องอ่านบัตรผ่าน API
- **ยืนยันสิทธิ์ NHSO**: ส่งข้อมูลไปยัง สปสช. เพื่อขอ Authentication
- **บันทึกข้อมูล JHCIS**: เพิ่มข้อมูล visit ลงฐานข้อมูลโรงพยาบาล
- **พิมพ์ใบนำทาง**: สร้าง PDF ขนาด 80mm และ 58mm พร้อม QR Code

### 🔧 การตั้งค่า
- **ตั้งค่าฐานข้อมูล**: กำหนดการเชื่อมต่อ MySQL/MariaDB
- **ทดสอบการเชื่อมต่อ**: ตรวจสอบการเชื่อมต่อฐานข้อมูลล่วงหน้า
- **โหมดทดสอบ**: ใช้ข้อมูลจำลองสำหรับการทดสอบระบบ

## 📊 ข้อมูล NHSO ที่บันทึก

### ตาราง visit (ฟิลด์ใหม่)
```sql
-- ฟิลด์สำหรับเก็บข้อมูล NHSO
claimcode_nhso VARCHAR(50)        -- รหัส Claim จาก NHSO
correlationid_nhso VARCHAR(100)   -- Correlation ID จากบัตรประชาชน
datetime_claim DATETIME           -- วันที่-เวลาจาก NHSO response
```

### ตัวอย่างข้อมูลที่บันทึก
```sql
INSERT INTO visit (
    -- ฟิลด์ปกติ
    visitno, pid, visitdate, timestart, qdiscloser,
    -- ฟิลด์ NHSO ใหม่
    claimcode_nhso, correlationid_nhso, datetime_claim
) VALUES (
    12345, 'P001', '2024-01-15', '08:30:00', 'A001',
    'PG0060001', '27d28b1f-58d2-4428-b255-71a51905f1f4', '2024-01-15 08:30:15'
);
```

## 🚀 การติดตั้ง

### 1. ติดตั้ง Dependencies
```bash
pip install -r requirements.txt
```

### 2. ตั้งค่าฐานข้อมูล
- เข้าไปที่ `/settings` เพื่อกำหนดการเชื่อมต่อฐานข้อมูล
- ทดสอบการเชื่อมต่อก่อนบันทึก

### 3. เริ่มใช้งาน
```bash
python app.py
```
เข้าใช้งานที่: `http://localhost:5000`

## 📋 การใช้งาน

### 1. อ่านบัตรประชาชน
- แตะบัตรประชาชนบนเครื่องอ่านบัตร
- ระบบจะอ่านข้อมูลและแสดงหน้าข้อมูลผู้ป่วย

### 2. เลือกบริการ
- เลือกประเภทบริการจากรายการ claimTypes
- ระบบจะส่งข้อมูลไป NHSO เพื่อขอ Authentication

### 3. ยืนยันและบันทึก
- ระบบบันทึกข้อมูลลง JHCIS พร้อมข้อมูล NHSO
- แสดงหน้าผลสำเร็จพร้อมสถานะ NHSO

### 4. พิมพ์ใบนำทาง
- เลือกขนาดกระดาษ 80mm หรือ 58mm
- ใบนำทางจะแสดง claimCode และข้อมูล NHSO

## 🔄 Flow การทำงาน NHSO

### สำเร็จ (NHSO Authentication Success)
```
1. อ่านบัตร → 2. เลือกบริการ → 3. ส่งข้อมูลไป NHSO
4. ได้ claimCode จาก NHSO → 5. บันทึก claimCode ลงฐานข้อมูล
6. แสดงสถานะ "สำเร็จ" พร้อม claimCode
```

### ล้มเหลว (NHSO Authentication Failed)
```
1. อ่านบัตร → 2. เลือกบริการ → 3. ส่งข้อมูลไป NHSO
4. NHSO ล้มเหลว → 5. ใช้ claimType แทน claimCode
6. แสดงสถานะ "ล้มเหลว" แต่ระบบดำเนินการต่อไป
```

## 🔧 API Endpoints

### การอ่านบัตร
- `POST /read-card` - อ่านข้อมูลจากบัตรประชาชน
- `GET /api/test-smartcard` - API ทดสอบข้อมูลบัตร

### การยืนยันสิทธิ์
- `POST /confirm-service` - ยืนยันการใช้บริการพร้อมส่งข้อมูลไป NHSO

### การพิมพ์
- `GET /print-slip/<paper_size>` - พิมพ์ใบนำทาง (80mm/58mm)

### การตั้งค่า
- `GET /settings` - หน้าตั้งค่าฐานข้อมูล
- `POST /save-settings` - บันทึกการตั้งค่า
- `POST /test-connection` - ทดสอบการเชื่อมต่อฐานข้อมูล

## 🧪 การทดสอบ

### ทดสอบโดยไม่ใช้บัตรจริง
เข้าไปที่ `/test-card` เพื่อใช้ข้อมูลจำลอง

### ทดสอบการพิมพ์
เข้าไปที่ `/test-print` เพื่อทดสอบการพิมพ์ใบนำทาง

## ⚙️ การกำหนดค่า

### ไฟล์ Config
- `db_config.json` - เก็บการตั้งค่าฐานข้อมูล

### ตัวแปรสำคัญ
```python
# URL สำหรับเครื่องอ่านบัตร
SMARTCARD_API = "http://127.0.0.1:8189/api/smartcard/read"

# URL สำหรับ NHSO API
NHSO_API = "http://127.0.0.1:8189/api/nhso-service/confirm-save"
```

## 📝 หมายเหตุ

### ข้อมูล NHSO ที่สำคัญ
- **claimCode**: รหัสที่ได้จาก NHSO (ถ้าสำเร็จ) หรือ claimType (ถ้าล้มเหลว)
- **correlationId**: ID จากบัตรประชาชนสำหรับเชื่อมโยงข้อมูล
- **createdDate**: วันที่-เวลาจาก NHSO response

### Fallback Mechanism
ถ้า NHSO API ล้มเหลว ระบบจะ:
1. ใช้ claimType แทน claimCode
2. ใช้เวลาปัจจุบันแทน createdDate จาก NHSO
3. แสดงสถานะ "ล้มเหลว" แต่ยังคงดำเนินการต่อไป

## 🔍 การแก้ไขปัญหา

### ปัญหาการเชื่อมต่อ NHSO
- ตรวจสอบ URL และ Authorization header
- ดูข้อมูล Debug ใน Console

### ปัญหาฐานข้อมูล
- ตรวจสอบการตั้งค่าใน `/settings`
- ดูข้อมูล Error ใน Console

### ปัญหาการพิมพ์
- ตรวจสอบ reportlab และ qrcode dependencies
- ดูข้อมูล Error ใน PDF generation

## 📞 การสนับสนุน
พร้อมเพย์  087-7875854

หากพบปัญหาหรือต้องการความช่วยเหลือ กรุณาตรวจสอบ:
1. Log ใน Console
2. การตั้งค่าฐานข้อมูล
3. การเชื่อมต่อ NHSO API
