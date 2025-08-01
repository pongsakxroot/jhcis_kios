# คำแนะนำการตั้งค่า ZeroTier และเชื่อมต่อฐานข้อมูล

## 1. ติดตั้ง ZeroTier One

### วิธีที่ 1: ใช้ Official Installer
```bash
curl -s https://install.zerotier.com | sudo bash
```

### วิธีที่ 2: ใช้ APT Package Manager  
```bash
sudo apt update
sudo apt install -y zerotier-one
```

## 2. เริ่ม ZeroTier Service

```bash
sudo systemctl enable zerotier-one
sudo systemctl start zerotier-one
```

## 3. Join ZeroTier Network

```bash
sudo zerotier-cli join 60ee7c034ac1fafa
```

## 4. ตรวจสอบสถานะ

```bash
# แสดงข้อมูล ZeroTier
sudo zerotier-cli info

# แสดงรายการ network ที่ join
sudo zerotier-cli listnetworks
```

## 5. รออนุมัติการเชื่อมต่อ

⚠️ **สำคัญ**: Network administrator ต้องอนุมัติการเชื่อมต่อของคุณใน ZeroTier Central Console

## 6. ทดสอบการเชื่อมต่อ

```bash
# ทดสอบ ping
ping -c 3 192.168.9.101

# ทดสอบ MySQL port
nc -z -w5 192.168.9.101 3306
```

## 7. ทดสอบฐานข้อมูล

หลังจาก ZeroTier เชื่อมต่อสำเร็จแล้ว:

```bash
python3 test_remote_db.py
```

## 8. รัน Flask Application

หากทุกอย่างเรียบร้อย:

```bash
python3 app.py
```

## การแก้ปัญหา

### ถ้า ping ไม่ผ่าน:
- ตรวจสอบว่า admin อนุมัติการเชื่อมต่อแล้ว
- รอสักครู่ (อาจใช้เวลา 1-2 นาที)
- ลอง restart ZeroTier: `sudo systemctl restart zerotier-one`

### ถ้า MySQL port ไม่เปิด:
- ตรวจสอบ firewall ฝั่ง server
- ตรวจสอบการตั้งค่า MySQL bind-address

### ถ้าเชื่อมต่อฐานข้อมูลไม่ได้:
- ตรวจสอบ username/password
- ตรวจสอบชื่อฐานข้อมูล
- ตรวจสอบ user privileges

## การตั้งค่าฐานข้อมูลปัจจุบัน

```json
{
  "host": "192.168.9.101",
  "user": "admin", 
  "password": "suntisuk",
  "database": "jhcisdb",
  "port": 3306
}
```

## หมายเหตุ

- IP 192.168.9.101 อยู่ใน ZeroTier network
- ต้อง join network 60ee7c034ac1fafa ก่อน
- ต้องได้รับการอนุมัติจาก network admin
- ระบบจะทำงานได้เมื่อเชื่อมต่อ ZeroTier สำเร็จ