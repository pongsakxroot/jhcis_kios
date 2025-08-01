#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Simple Database Test
"""

print("🔍 ทดสอบการเชื่อมต่อฐานข้อมูล...")

try:
    import mysql.connector
    print("✅ mysql.connector โหลดได้")
except ImportError as e:
    print(f"❌ ไม่สามารถโหลด mysql.connector: {e}")
    exit(1)

# ทดสอบการเชื่อมต่อพื้นฐาน
configs = [
    {
        'host': 'localhost',
        'user': 'root',
        'password': '',
        'port': 3306
    },
    {
        'host': '127.0.0.1',
        'user': 'root',
        'password': '',
        'port': 3306
    },
    {
        'host': 'localhost',
        'user': 'root',
        'password': 'root',
        'port': 3306
    }
]

for i, config in enumerate(configs):
    print(f"\n--- ทดสอบการตั้งค่า {i+1} ---")
    print(f"Host: {config['host']}")
    print(f"User: {config['user']}")
    print(f"Password: {'(ไม่มี)' if not config['password'] else '(มี)'}")
    
    try:
        conn = mysql.connector.connect(**config)
        print("✅ เชื่อมต่อสำเร็จ!")
        
        cursor = conn.cursor()
        cursor.execute("SHOW DATABASES")
        databases = cursor.fetchall()
        print(f"📋 ฐานข้อมูลที่มี: {len(databases)} รายการ")
        
        # ตรวจสอบว่ามี jhcis หรือไม่
        db_names = [db[0] for db in databases]
        if 'jhcis' in db_names:
            print("✅ พบฐานข้อมูล jhcis")
        else:
            print("⚠️ ไม่พบฐานข้อมูล jhcis")
            print(f"💡 ฐานข้อมูลที่มี: {', '.join(db_names[:5])}...")
        
        cursor.close()
        conn.close()
        
        # บันทึกการตั้งค่าที่ใช้ได้
        import json
        config['database'] = 'jhcis'
        with open('db_config.json', 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
        print("💾 บันทึกการตั้งค่าแล้ว")
        
        break
        
    except mysql.connector.Error as err:
        print(f"❌ MySQL Error: {err}")
    except Exception as e:
        print(f"❌ Error: {e}")

print("\n🏁 เสร็จสิ้น")