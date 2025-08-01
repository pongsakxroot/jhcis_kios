#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MySQL Setup Script
ตั้งค่า MySQL และสร้างฐานข้อมูล jhcis
"""

import subprocess
import mysql.connector
import json
import sys
import time

def setup_mysql_auth():
    """ตั้งค่า authentication สำหรับ MySQL"""
    print("🔧 ตั้งค่า MySQL authentication...")
    
    # สร้างไฟล์ SQL สำหรับตั้งค่า
    sql_commands = """
-- อนุญาตการเชื่อมต่อแบบ native password
ALTER USER 'root'@'localhost' IDENTIFIED WITH mysql_native_password BY '';
FLUSH PRIVILEGES;

-- สร้างฐานข้อมูล jhcis
CREATE DATABASE IF NOT EXISTS jhcis CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- สร้างตารางพื้นฐาน
USE jhcis;

-- ตาราง person (ตัวอย่าง)
CREATE TABLE IF NOT EXISTS person (
    pid VARCHAR(20) PRIMARY KEY,
    hn VARCHAR(20),
    idcard VARCHAR(13),
    fname VARCHAR(100),
    lname VARCHAR(100),
    mobile VARCHAR(20),
    pcucodeperson VARCHAR(10),
    rightno VARCHAR(50)
);

-- ตาราง visit (ปรับปรุงให้รองรับ NHSO)
CREATE TABLE IF NOT EXISTS visit (
    visitno INT PRIMARY KEY AUTO_INCREMENT,
    pid VARCHAR(20),
    visitdate DATE,
    timestart TIME,
    timeend TIME,
    pcucode VARCHAR(10),
    pcucodeperson VARCHAR(10),
    rightcode VARCHAR(10),
    timeservice VARCHAR(10),
    flagservice VARCHAR(10),
    typein VARCHAR(10),
    servicetype VARCHAR(10),
    qdiscloser VARCHAR(10),
    rightno VARCHAR(50),
    hiciauthen_nhso VARCHAR(50),
    dateupdate DATETIME,
    claimcode_nhso VARCHAR(50),
    datetime_claim DATETIME,
    correlationid_nhso VARCHAR(100),
    FOREIGN KEY (pid) REFERENCES person(pid)
);

-- ตาราง chospital (ข้อมูลโรงพยาบาล)
CREATE TABLE IF NOT EXISTS chospital (
    hosname VARCHAR(200),
    address VARCHAR(200),
    tel VARCHAR(50),
    provname VARCHAR(100)
);

-- ใส่ข้อมูลตัวอย่าง
INSERT IGNORE INTO chospital (hosname, address, tel, provname) VALUES
('โรงพยาบาลทดสอบ', '123 ถนนทดสอบ อำเภอทดสอบ', '02-123-4567', 'กรุงเทพมหานคร');

-- ใส่ข้อมูลผู้ป่วยตัวอย่าง
INSERT IGNORE INTO person (pid, hn, idcard, fname, lname, mobile, pcucodeperson, rightno) VALUES
('P001', 'HN001', '1111111111119', 'ทดสอบ', 'ระบบ', '0812345678', 'PCU001', 'RIGHT001');
"""
    
    try:
        # เขียนไฟล์ SQL
        with open('/tmp/setup.sql', 'w', encoding='utf-8') as f:
            f.write(sql_commands)
        
        # รัน MySQL script
        result = subprocess.run([
            'sudo', 'mysql', '-u', 'root', '<', '/tmp/setup.sql'
        ], shell=True, capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ ตั้งค่า MySQL สำเร็จ")
            return True
        else:
            print(f"❌ ข้อผิดพลาดในการตั้งค่า: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ ข้อผิดพลาด: {e}")
        return False

def test_connection():
    """ทดสอบการเชื่อมต่อหลังตั้งค่า"""
    print("\n🧪 ทดสอบการเชื่อมต่อ...")
    
    configs = [
        {
            'host': 'localhost',
            'user': 'root',
            'password': '',
            'database': 'jhcis',
            'port': 3306
        },
        {
            'host': '127.0.0.1',
            'user': 'root',
            'password': '',
            'database': 'jhcis',
            'port': 3306
        }
    ]
    
    for i, config in enumerate(configs):
        try:
            print(f"\n--- ทดสอบการตั้งค่า {i+1} ---")
            print(f"Host: {config['host']}")
            print(f"Database: {config['database']}")
            
            conn = mysql.connector.connect(**config)
            cursor = conn.cursor()
            
            # ทดสอบ query
            cursor.execute("SELECT COUNT(*) FROM person")
            person_count = cursor.fetchone()[0]
            print(f"✅ เชื่อมต่อสำเร็จ! จำนวนข้อมูลใน person: {person_count}")
            
            cursor.execute("SELECT COUNT(*) FROM visit")
            visit_count = cursor.fetchone()[0]
            print(f"✅ จำนวนข้อมูลใน visit: {visit_count}")
            
            cursor.close()
            conn.close()
            
            # บันทึกการตั้งค่าที่ใช้ได้
            with open('db_config.json', 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
            print("💾 บันทึกการตั้งค่าลงไฟล์ db_config.json แล้ว")
            
            return True
            
        except mysql.connector.Error as err:
            print(f"❌ MySQL Error: {err}")
        except Exception as e:
            print(f"❌ Error: {e}")
    
    return False

def setup_mysql_alternative():
    """วิธีการตั้งค่าทางเลือก"""
    print("\n🔄 ลองวิธีการตั้งค่าทางเลือก...")
    
    try:
        # ใช้ mysql_secure_installation แบบไม่ interactive
        commands = [
            "sudo mysql -e \"ALTER USER 'root'@'localhost' IDENTIFIED WITH mysql_native_password BY '';\"",
            "sudo mysql -e \"FLUSH PRIVILEGES;\"",
            "sudo mysql -e \"CREATE DATABASE IF NOT EXISTS jhcis CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;\"",
            "sudo mysql jhcis -e \"CREATE TABLE IF NOT EXISTS person (pid VARCHAR(20) PRIMARY KEY, hn VARCHAR(20), idcard VARCHAR(13), fname VARCHAR(100), lname VARCHAR(100), mobile VARCHAR(20), pcucodeperson VARCHAR(10), rightno VARCHAR(50));\"",
            "sudo mysql jhcis -e \"CREATE TABLE IF NOT EXISTS visit (visitno INT PRIMARY KEY AUTO_INCREMENT, pid VARCHAR(20), visitdate DATE, timestart TIME, timeend TIME, pcucode VARCHAR(10), pcucodeperson VARCHAR(10), rightcode VARCHAR(10), timeservice VARCHAR(10), flagservice VARCHAR(10), typein VARCHAR(10), servicetype VARCHAR(10), qdiscloser VARCHAR(10), rightno VARCHAR(50), hiciauthen_nhso VARCHAR(50), dateupdate DATETIME, claimcode_nhso VARCHAR(50), datetime_claim DATETIME, correlationid_nhso VARCHAR(100));\"",
            "sudo mysql jhcis -e \"CREATE TABLE IF NOT EXISTS chospital (hosname VARCHAR(200), address VARCHAR(200), tel VARCHAR(50), provname VARCHAR(100));\"",
            "sudo mysql jhcis -e \"INSERT IGNORE INTO chospital (hosname, address, tel, provname) VALUES ('โรงพยาบาลทดสอบ', '123 ถนนทดสอบ อำเภอทดสอบ', '02-123-4567', 'กรุงเทพมหานคร');\"",
            "sudo mysql jhcis -e \"INSERT IGNORE INTO person (pid, hn, idcard, fname, lname, mobile, pcucodeperson, rightno) VALUES ('P001', 'HN001', '1111111111119', 'ทดสอบ', 'ระบบ', '0812345678', 'PCU001', 'RIGHT001');\""
        ]
        
        for cmd in commands:
            print(f"รัน: {cmd}")
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            if result.returncode != 0:
                print(f"❌ Error: {result.stderr}")
                return False
            else:
                print("✅ สำเร็จ")
        
        return True
        
    except Exception as e:
        print(f"❌ ข้อผิดพลาด: {e}")
        return False

def main():
    """ฟังก์ชันหลัก"""
    print("🔧 เครื่องมือตั้งค่า MySQL สำหรับ JHCIS")
    print("=" * 50)
    
    # รอให้ MySQL เริ่มทำงานเสร็จ
    print("⏳ รอ MySQL เริ่มทำงาน...")
    time.sleep(5)
    
    # ทดสอบว่า MySQL ทำงานอยู่หรือไม่
    try:
        result = subprocess.run(['pgrep', 'mysql'], capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ MySQL กำลังทำงาน")
        else:
            print("❌ MySQL ไม่ทำงาน กรุณาเริ่ม MySQL ก่อน")
            return
    except:
        print("⚠️ ไม่สามารถตรวจสอบสถานะ MySQL ได้")
    
    # ลองตั้งค่าด้วยวิธีทางเลือก
    if setup_mysql_alternative():
        print("\n✅ ตั้งค่า MySQL สำเร็จ!")
        
        # ทดสอบการเชื่อมต่อ
        if test_connection():
            print("\n🎉 ระบบพร้อมใช้งาน!")
            print("\nตอนนี้คุณสามารถรัน Flask app ได้แล้ว:")
            print("python3 app.py")
        else:
            print("\n❌ การทดสอบการเชื่อมต่อล้มเหลว")
    else:
        print("\n❌ ไม่สามารถตั้งค่า MySQL ได้")
    
    print("\n📝 หมายเหตุ:")
    print("- หากยังมีปัญหา ลองรัน: sudo mysql_secure_installation")
    print("- ตรวจสอบ log ได้ที่: /var/log/mysql/error.log")

if __name__ == "__main__":
    main()