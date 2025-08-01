#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Quick Test Script for ZeroTier and Database
"""

import subprocess
import socket
import json
import sys

def check_zerotier():
    """ตรวจสอบสถานะ ZeroTier"""
    print("🔍 ตรวจสอบ ZeroTier...")
    
    try:
        # ตรวจสอบว่า zerotier-cli มีอยู่หรือไม่
        result = subprocess.run(['which', 'zerotier-cli'], 
                               capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ ZeroTier ติดตั้งแล้ว")
            
            # ตรวจสอบสถานะ
            try:
                result = subprocess.run(['sudo', 'zerotier-cli', 'info'], 
                                      capture_output=True, text=True, timeout=10)
                if result.returncode == 0:
                    print(f"📊 ZeroTier Info: {result.stdout.strip()}")
                    
                    # ตรวจสอบ networks
                    result = subprocess.run(['sudo', 'zerotier-cli', 'listnetworks'], 
                                          capture_output=True, text=True, timeout=10)
                    if result.returncode == 0:
                        print(f"📋 Networks: {result.stdout.strip()}")
                        
                        # ตรวจสอบว่า join network แล้วหรือยัง
                        if '60ee7c034ac1fafa' in result.stdout:
                            print("✅ อยู่ใน network 60ee7c034ac1fafa แล้ว")
                            return True
                        else:
                            print("⚠️  ยังไม่ได้ join network 60ee7c034ac1fafa")
                            return False
                else:
                    print("❌ ZeroTier service ไม่ทำงาน")
                    return False
            except subprocess.TimeoutExpired:
                print("⏰ ZeroTier command timeout")
                return False
                
        else:
            print("❌ ZeroTier ยังไม่ได้ติดตั้ง")
            return False
            
    except Exception as e:
        print(f"❌ Error checking ZeroTier: {e}")
        return False

def check_network_connectivity():
    """ตรวจสอบการเชื่อมต่อ network"""
    print("\n🌐 ตรวจสอบการเชื่อมต่อ network...")
    
    host = "192.168.9.101"
    port = 3306
    
    # ทดสอบ ping
    try:
        result = subprocess.run(['ping', '-c', '3', '-W', '5', host], 
                               capture_output=True, text=True, timeout=20)
        if result.returncode == 0:
            print(f"✅ Ping {host} สำเร็จ")
            ping_success = True
        else:
            print(f"❌ Ping {host} ล้มเหลว")
            ping_success = False
    except subprocess.TimeoutExpired:
        print(f"⏰ Ping {host} timeout")
        ping_success = False
    except Exception as e:
        print(f"❌ Ping error: {e}")
        ping_success = False
    
    # ทดสอบ port
    print(f"🔌 ทดสอบ port {port}...")
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        result = sock.connect_ex((host, port))
        sock.close()
        
        if result == 0:
            print(f"✅ Port {port} เปิดอยู่")
            port_success = True
        else:
            print(f"❌ Port {port} ปิดอยู่หรือไม่สามารถเข้าถึงได้")
            port_success = False
    except Exception as e:
        print(f"❌ Port test error: {e}")
        port_success = False
    
    return ping_success and port_success

def check_database_connection():
    """ทดสอบการเชื่อมต่อฐานข้อมูล"""
    print("\n🗄️  ทดสอบการเชื่อมต่อฐานข้อมูล...")
    
    try:
        import mysql.connector
        
        # โหลดการตั้งค่า
        try:
            with open('db_config.json', 'r', encoding='utf-8') as f:
                config = json.load(f)
        except FileNotFoundError:
            print("❌ ไม่พบไฟล์ db_config.json")
            return False
        
        print(f"📡 เชื่อมต่อไปยัง {config['host']}:{config['port']}")
        print(f"👤 User: {config['user']}")
        print(f"🗄️  Database: {config['database']}")
        
        # ทดสอบการเชื่อมต่อ
        conn = mysql.connector.connect(**config)
        cursor = conn.cursor()
        
        cursor.execute("SELECT VERSION()")
        version = cursor.fetchone()
        print(f"✅ เชื่อมต่อสำเร็จ! MySQL Version: {version[0]}")
        
        # ตรวจสอบตาราง
        cursor.execute("SHOW TABLES")
        tables = cursor.fetchall()
        table_count = len(tables)
        print(f"📋 พบ {table_count} ตาราง")
        
        cursor.close()
        conn.close()
        
        return True
        
    except ImportError:
        print("❌ ไม่พบ mysql.connector กรุณาติดตั้ง: pip install mysql-connector-python")
        return False
    except Exception as e:
        print(f"❌ Database connection error: {e}")
        return False

def main():
    """ฟังก์ชันหลัก"""
    print("🚀 Quick Test - ZeroTier & Database Connectivity")
    print("=" * 50)
    
    # ตรวจสอบ ZeroTier
    zerotier_ok = check_zerotier()
    
    # ตรวจสอบ network
    network_ok = check_network_connectivity()
    
    # ตรวจสอบฐานข้อมูล
    database_ok = check_database_connection()
    
    # สรุปผล
    print("\n" + "=" * 50)
    print("📊 สรุปผลการทดสอบ:")
    print(f"ZeroTier: {'✅' if zerotier_ok else '❌'}")
    print(f"Network: {'✅' if network_ok else '❌'}")
    print(f"Database: {'✅' if database_ok else '❌'}")
    
    if zerotier_ok and network_ok and database_ok:
        print("\n🎉 ระบบพร้อมใช้งาน!")
        print("🚀 รัน Flask app: python3 app.py")
    else:
        print("\n❌ ยังมีปัญหา กรุณาแก้ไขตามคำแนะนำ:")
        
        if not zerotier_ok:
            print("1. ติดตั้ง ZeroTier: curl -s https://install.zerotier.com | sudo bash")
            print("2. Join network: sudo zerotier-cli join 60ee7c034ac1fafa")
        
        if not network_ok:
            print("3. รอ admin อนุมัติการเชื่อมต่อใน ZeroTier Central")
            print("4. ตรวจสอบ firewall และ network settings")
        
        if not database_ok:
            print("5. ตรวจสอบ username/password ฐานข้อมูล")
            print("6. ตรวจสอบ MySQL server settings")

if __name__ == "__main__":
    main()