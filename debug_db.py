#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Database Connection Debug Script
ใช้สำหรับตรวจสอบปัญหาการเชื่อมต่อฐานข้อมูล
"""

import mysql.connector
import json
import os
import sys

def test_basic_connection():
    """ทดสอบการเชื่อมต่อฐานข้อมูลแบบพื้นฐาน"""
    print("=== ทดสอบการเชื่อมต่อฐานข้อมูล ===")
    
    # ตัวอย่างการตั้งค่าที่พบบ่อย
    test_configs = [
        {
            'name': 'XAMPP Default',
            'host': 'localhost',
            'user': 'root',
            'password': '',
            'database': 'jhcis',
            'port': 3306
        },
        {
            'name': 'AppServ Default',
            'host': 'localhost',
            'user': 'root',
            'password': 'root',
            'database': 'jhcis',
            'port': 3306
        },
        {
            'name': 'WAMP Default',
            'host': 'localhost',
            'user': 'root',
            'password': '',
            'database': 'jhcis',
            'port': 3306
        },
        {
            'name': 'Local MySQL',
            'host': '127.0.0.1',
            'user': 'root',
            'password': '',
            'database': 'jhcis',
            'port': 3306
        }
    ]
    
    for config in test_configs:
        print(f"\n--- ทดสอบ {config['name']} ---")
        try:
            print(f"Host: {config['host']}")
            print(f"Port: {config['port']}")
            print(f"User: {config['user']}")
            print(f"Password: {'(มี)' if config['password'] else '(ไม่มี)'}")
            print(f"Database: {config['database']}")
            
            # ทดสอบการเชื่อมต่อ
            conn = mysql.connector.connect(**config)
            cursor = conn.cursor()
            cursor.execute("SELECT VERSION()")
            version = cursor.fetchone()
            print(f"✅ เชื่อมต่อสำเร็จ! MySQL Version: {version[0]}")
            
            # ตรวจสอบฐานข้อมูล jhcis
            cursor.execute("SHOW DATABASES LIKE 'jhcis'")
            db_exists = cursor.fetchone()
            if db_exists:
                print("✅ พบฐานข้อมูล jhcis")
                
                # ตรวจสอบตารางสำคัญ
                cursor.execute("USE jhcis")
                cursor.execute("SHOW TABLES LIKE 'person'")
                person_table = cursor.fetchone()
                if person_table:
                    print("✅ พบตาราง person")
                else:
                    print("⚠️  ไม่พบตาราง person")
                
                cursor.execute("SHOW TABLES LIKE 'visit'")
                visit_table = cursor.fetchone()
                if visit_table:
                    print("✅ พบตาราง visit")
                else:
                    print("⚠️  ไม่พบตาราง visit")
                    
            else:
                print("⚠️  ไม่พบฐานข้อมูล jhcis")
            
            cursor.close()
            conn.close()
            
            # บันทึกการตั้งค่าที่ใช้ได้
            save_working_config(config)
            return True
            
        except mysql.connector.Error as err:
            print(f"❌ ข้อผิดพลาด MySQL: {err}")
        except Exception as e:
            print(f"❌ ข้อผิดพลาดอื่น: {e}")
    
    return False

def save_working_config(config):
    """บันทึกการตั้งค่าที่ใช้ได้"""
    try:
        with open('db_config.json', 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
        print(f"💾 บันทึกการตั้งค่าลงไฟล์ db_config.json แล้ว")
    except Exception as e:
        print(f"❌ ไม่สามารถบันทึกการตั้งค่าได้: {e}")

def check_mysql_service():
    """ตรวจสอบสถานะบริการ MySQL"""
    print("\n=== ตรวจสอบบริการ MySQL ===")
    
    import subprocess
    import platform
    
    system = platform.system().lower()
    
    try:
        if system == 'windows':
            # ตรวจสอบบน Windows
            result = subprocess.run(['sc', 'query', 'mysql'], 
                                  capture_output=True, text=True)
            if 'RUNNING' in result.stdout:
                print("✅ บริการ MySQL กำลังทำงาน")
            else:
                print("❌ บริการ MySQL ไม่ทำงาน")
                print("💡 ลองเริ่มบริการ MySQL ใน Services หรือ XAMPP Control Panel")
        else:
            # ตรวจสอบบน Linux/Mac
            result = subprocess.run(['pgrep', 'mysql'], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                print("✅ บริการ MySQL กำลังทำงาน")
            else:
                print("❌ บริการ MySQL ไม่ทำงาน")
                print("💡 ลองรัน: sudo systemctl start mysql")
                
    except Exception as e:
        print(f"❌ ไม่สามารถตรวจสอบบริการได้: {e}")

def check_port():
    """ตรวจสอบพอร์ต 3306"""
    print("\n=== ตรวจสอบพอร์ต 3306 ===")
    
    import socket
    
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        result = sock.connect_ex(('localhost', 3306))
        sock.close()
        
        if result == 0:
            print("✅ พอร์ต 3306 เปิดอยู่")
        else:
            print("❌ พอร์ต 3306 ปิดอยู่")
            print("💡 ตรวจสอบว่า MySQL Server ทำงานอยู่หรือไม่")
            
    except Exception as e:
        print(f"❌ ไม่สามารถตรวจสอบพอร์ตได้: {e}")

def manual_config():
    """ให้ผู้ใช้ใส่การตั้งค่าเอง"""
    print("\n=== การตั้งค่าด้วยตนเอง ===")
    
    config = {}
    config['host'] = input("Host (localhost): ") or 'localhost'
    config['port'] = int(input("Port (3306): ") or 3306)
    config['user'] = input("Username (root): ") or 'root'
    config['password'] = input("Password (Enter สำหรับไม่มีรหัส): ")
    config['database'] = input("Database (jhcis): ") or 'jhcis'
    
    print(f"\n--- ทดสอบการตั้งค่าของคุณ ---")
    try:
        conn = mysql.connector.connect(**config)
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        cursor.close()
        conn.close()
        
        print("✅ เชื่อมต่อสำเร็จ!")
        save_working_config(config)
        return True
        
    except Exception as e:
        print(f"❌ ไม่สามารถเชื่อมต่อได้: {e}")
        return False

def main():
    """ฟังก์ชันหลัก"""
    print("🔍 เครื่องมือตรวจสอบการเชื่อมต่อฐานข้อมูล JHCIS")
    print("=" * 50)
    
    # ตรวจสอบการติดตั้ง mysql-connector-python
    try:
        import mysql.connector
        print("✅ mysql-connector-python ติดตั้งแล้ว")
    except ImportError:
        print("❌ ยังไม่ได้ติดตั้ง mysql-connector-python")
        print("💡 รัน: pip install mysql-connector-python")
        return
    
    # ตรวจสอบบริการ MySQL
    check_mysql_service()
    
    # ตรวจสอบพอร์ต
    check_port()
    
    # ทดสอบการเชื่อมต่อ
    if test_basic_connection():
        print("\n🎉 พบการตั้งค่าที่ใช้ได้แล้ว!")
    else:
        print("\n❌ ไม่พบการตั้งค่าที่ใช้ได้")
        
        while True:
            choice = input("\nต้องการใส่การตั้งค่าเอง? (y/n): ").lower()
            if choice == 'y':
                if manual_config():
                    print("\n🎉 การตั้งค่าสำเร็จ!")
                    break
                else:
                    continue
            elif choice == 'n':
                break
            else:
                print("กรุณาใส่ y หรือ n")
    
    print("\n📝 คำแนะนำเพิ่มเติม:")
    print("1. ตรวจสอบว่า MySQL/MariaDB ทำงานอยู่")
    print("2. ตรวจสอบ username/password ให้ถูกต้อง")
    print("3. ตรวจสอบว่าฐานข้อมูล jhcis มีอยู่จริง")
    print("4. ตรวจสอบ Firewall ที่อาจบล็อกพอร์ต 3306")
    print("5. หากใช้ XAMPP/WAMP ตรวจสอบว่าเปิด Apache และ MySQL แล้ว")

if __name__ == "__main__":
    main()