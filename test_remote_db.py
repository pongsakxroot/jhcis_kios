#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test Remote Database Connection
"""

import mysql.connector
import json

def test_remote_connection():
    """ทดสอบการเชื่อมต่อกับ remote database"""
    print("🔍 ทดสอบการเชื่อมต่อกับฐานข้อมูล Remote...")
    
    # โหลดการตั้งค่าจากไฟล์
    try:
        with open('db_config.json', 'r', encoding='utf-8') as f:
            config = json.load(f)
    except FileNotFoundError:
        print("❌ ไม่พบไฟล์ db_config.json")
        return False
    
    print(f"Host: {config['host']}")
    print(f"Port: {config['port']}")
    print(f"User: {config['user']}")
    print(f"Database: {config['database']}")
    print(f"Password: {'(มี)' if config['password'] else '(ไม่มี)'}")
    
    try:
        # ทดสอบการเชื่อมต่อ
        print("\n🔌 กำลังเชื่อมต่อ...")
        conn = mysql.connector.connect(**config)
        cursor = conn.cursor()
        
        print("✅ เชื่อมต่อสำเร็จ!")
        
        # ตรวจสอบ MySQL version
        cursor.execute("SELECT VERSION()")
        version = cursor.fetchone()
        print(f"📊 MySQL Version: {version[0]}")
        
        # ตรวจสอบตารางที่มีอยู่
        cursor.execute("SHOW TABLES")
        tables = cursor.fetchall()
        table_names = [table[0] for table in tables]
        print(f"📋 ตารางที่มี ({len(table_names)} ตาราง): {', '.join(table_names[:10])}{'...' if len(table_names) > 10 else ''}")
        
        # ตรวจสอบตารางสำคัญ
        important_tables = ['person', 'visit', 'chospital']
        for table in important_tables:
            if table in table_names:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                print(f"✅ ตาราง {table}: {count:,} รายการ")
            else:
                print(f"⚠️  ไม่พบตาราง {table}")
        
        # ตรวจสอบฟิลด์ในตาราง visit (สำหรับ NHSO)
        if 'visit' in table_names:
            cursor.execute("DESCRIBE visit")
            fields = cursor.fetchall()
            field_names = [field[0] for field in fields]
            
            nhso_fields = ['claimcode_nhso', 'correlationid_nhso', 'datetime_claim']
            print("\n🔍 ตรวจสอบฟิลด์ NHSO ในตาราง visit:")
            for field in nhso_fields:
                if field in field_names:
                    print(f"✅ พบฟิลด์ {field}")
                else:
                    print(f"⚠️  ไม่พบฟิลด์ {field}")
        
        # ทดสอบ query ข้อมูลตัวอย่าง
        if 'person' in table_names:
            cursor.execute("SELECT * FROM person LIMIT 1")
            sample_person = cursor.fetchone()
            if sample_person:
                print(f"\n📄 ตัวอย่างข้อมูล person: {sample_person}")
            else:
                print("\n⚠️  ไม่มีข้อมูลในตาราง person")
        
        cursor.close()
        conn.close()
        
        print("\n🎉 การทดสอบสำเร็จทั้งหมด!")
        return True
        
    except mysql.connector.Error as err:
        error_code = err.errno
        if error_code == 1045:
            print("❌ ข้อผิดพลาด: ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง")
        elif error_code == 2003:
            print(f"❌ ข้อผิดพลาด: ไม่สามารถเชื่อมต่อกับ {config['host']}:{config['port']}")
            print("💡 ตรวจสอบ:")
            print("   - IP Address และ Port ถูกต้องหรือไม่")
            print("   - Firewall อนุญาตการเชื่อมต่อหรือไม่")
            print("   - MySQL Server เปิดรับการเชื่อมต่อจากภายนอกหรือไม่")
        elif error_code == 1049:
            print(f"❌ ข้อผิดพลาด: ไม่พบฐานข้อมูล '{config['database']}'")
        else:
            print(f"❌ MySQL Error {error_code}: {err}")
        return False
        
    except Exception as e:
        print(f"❌ ข้อผิดพลาดอื่น: {e}")
        return False

def add_nhso_fields():
    """เพิ่มฟิลด์ NHSO ลงในตาราง visit (ถ้ายังไม่มี)"""
    print("\n🔧 ตรวจสอบและเพิ่มฟิลด์ NHSO...")
    
    try:
        with open('db_config.json', 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        conn = mysql.connector.connect(**config)
        cursor = conn.cursor()
        
        # ตรวจสอบฟิลด์ที่มีอยู่
        cursor.execute("DESCRIBE visit")
        fields = cursor.fetchall()
        field_names = [field[0] for field in fields]
        
        # ฟิลด์ที่ต้องเพิ่ม
        nhso_fields = {
            'claimcode_nhso': 'VARCHAR(50)',
            'correlationid_nhso': 'VARCHAR(100)',
            'datetime_claim': 'DATETIME'
        }
        
        for field_name, field_type in nhso_fields.items():
            if field_name not in field_names:
                print(f"➕ เพิ่มฟิลด์ {field_name}...")
                cursor.execute(f"ALTER TABLE visit ADD COLUMN {field_name} {field_type}")
                print(f"✅ เพิ่มฟิลด์ {field_name} สำเร็จ")
            else:
                print(f"✅ ฟิลด์ {field_name} มีอยู่แล้ว")
        
        conn.commit()
        cursor.close()
        conn.close()
        
        print("🎉 ปรับปรุงโครงสร้างตารางสำเร็จ!")
        return True
        
    except mysql.connector.Error as err:
        print(f"❌ ไม่สามารถปรับปรุงตารางได้: {err}")
        return False

def main():
    """ฟังก์ชันหลัก"""
    print("🌐 เครื่องมือทดสอบการเชื่อมต่อ Remote Database")
    print("=" * 50)
    
    if test_remote_connection():
        print("\n" + "=" * 50)
        choice = input("\nต้องการเพิ่มฟิลด์ NHSO ลงในตาราง visit หรือไม่? (y/n): ").lower()
        if choice == 'y':
            add_nhso_fields()
        
        print("\n🚀 ตอนนี้คุณสามารถรัน Flask app ได้แล้ว:")
        print("python3 app.py")
    else:
        print("\n❌ การเชื่อมต่อล้มเหลว")
        print("\n💡 แนะนำการแก้ไข:")
        print("1. ตรวจสอบ IP Address และ Port")
        print("2. ตรวจสอบ username/password")
        print("3. ตรวจสอบ Firewall")
        print("4. ตรวจสอบการตั้งค่า MySQL bind-address")

if __name__ == "__main__":
    main()