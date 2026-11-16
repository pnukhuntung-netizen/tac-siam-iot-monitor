# TAC SIAM CORP LTD. — Industrial IoT Monitor (V50.2)

Streamlit Dashboard สำหรับติดตามสถานะเครื่องจักร ยอดการผลิต (Count A) ประสิทธิภาพ OEE และพลังงานไฟฟ้าของ **บริษัท แทค สยาม คอร์ป จำกัด (TAC SIAM CORP LTD.)** โดยดึงข้อมูลจาก Google Sheets (`Sheet1`) แบบ Real-time โดยไม่แก้ไขโค้ด ESP32 V50.2

## โครงสร้างไฟล์ในโปรเจกต์
- `app.py` : ไฟล์หลักของหน้า Dashboard (ดึงข้อมูลจาก `Sheet1` โดยยึด Row 3 เป็นหัวตาราง และ Row 4 เป็นข้อมูลล่าสุดเสมอ)
- `requirements.txt` : รายการไลบรารี Python (`streamlit`, `pandas`, `plotly`)
- `README.md` : คู่มือการติดตั้งและ Deploy ขึ้น Streamlit Community Cloud

## วิธีนำขึ้นใช้งานบน Streamlit Cloud (ด้วยบัญชี pnukhuntung@gmail.com)
1. ล็อกอินเข้า [GitHub](https://github.com) ด้วยอีเมล `pnukhuntung@gmail.com`
2. สร้าง Repository ใหม่ (ตั้งค่าเป็น **Public**) เช่น `tac-siam-iot-monitor`
3. อัปโหลดไฟล์ `app.py`, `requirements.txt` และ `README.md` เข้าไปใน Repository
4. เข้าเว็บไซต์ [share.streamlit.io](https://share.streamlit.io) กด **Continue with GitHub**
5. กด **Create app** -> เลือก Repository `tac-siam-iot-monitor` -> เลือก Main file path เป็น `app.py` -> กด **Deploy**
6. เปิดลิงก์เว็บแอปบนมือถือ แล้วกด **เพิ่มลงในหน้าจอหลัก (Add to Home Screen)** เพื่อใช้งานเต็มจอเหมือนแอปพลิเคชัน
