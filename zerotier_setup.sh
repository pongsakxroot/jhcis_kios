#!/bin/bash

echo "🌐 ZeroTier Setup Script"
echo "========================"

# ตรวจสอบว่า ZeroTier ติดตั้งแล้วหรือยัง
if command -v zerotier-cli &> /dev/null; then
    echo "✅ ZeroTier ติดตั้งแล้ว"
else
    echo "📦 กำลังติดตั้ง ZeroTier..."
    
    # วิธี 1: ใช้ official installer
    echo "🔄 ลองใช้ official installer..."
    curl -s https://install.zerotier.com | sudo bash
    
    # ถ้าไม่ได้ ลองใช้ apt
    if ! command -v zerotier-cli &> /dev/null; then
        echo "🔄 ลองใช้ apt package manager..."
        sudo apt update
        sudo apt install -y zerotier-one
    fi
fi

# ตรวจสอบการติดตั้ง
if command -v zerotier-cli &> /dev/null; then
    echo "✅ ZeroTier ติดตั้งสำเร็จ"
    
    # เริ่ม service
    echo "🚀 เริ่ม ZeroTier service..."
    sudo systemctl enable zerotier-one
    sudo systemctl start zerotier-one
    
    # รอสักครู่
    echo "⏳ รอ ZeroTier เริ่มทำงาน..."
    sleep 3
    
    # แสดงสถานะ
    echo "📊 สถานะ ZeroTier:"
    sudo zerotier-cli info
    
    # Join network
    echo "🔗 Join ZeroTier network 60ee7c034ac1fafa..."
    sudo zerotier-cli join 60ee7c034ac1fafa
    
    echo "⏳ รอการเชื่อมต่อ..."
    sleep 5
    
    # แสดงสถานะ network
    echo "📋 สถานะ network:"
    sudo zerotier-cli listnetworks
    
    # ทดสอบ ping
    echo "🏓 ทดสอบ ping ไป 192.168.9.101..."
    if ping -c 3 -W 5 192.168.9.101; then
        echo "✅ เชื่อมต่อกับ 192.168.9.101 สำเร็จ"
        
        # ทดสอบ MySQL port
        echo "🔌 ทดสอบ MySQL port 3306..."
        if nc -z -w5 192.168.9.101 3306; then
            echo "✅ MySQL port 3306 เปิดอยู่"
        else
            echo "❌ MySQL port 3306 ไม่สามารถเข้าถึงได้"
        fi
    else
        echo "❌ ไม่สามารถเชื่อมต่อกับ 192.168.9.101 ได้"
        echo "💡 กรุณาตรวจสอบ:"
        echo "   - Network admin ได้ approve การเชื่อมต่อแล้วหรือไม่"
        echo "   - ZeroTier network ตั้งค่าถูกต้องหรือไม่"
    fi
    
else
    echo "❌ ไม่สามารถติดตั้ง ZeroTier ได้"
    echo "💡 ลองติดตั้งด้วยตนเอง:"
    echo "   curl -s https://install.zerotier.com | sudo bash"
fi

echo "🏁 เสร็จสิ้น"