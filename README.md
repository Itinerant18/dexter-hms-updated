# 🚀 **Dexter Web Application (Version 2.0.2 - README**

---

## 🌟 1. Introduction & Purpose

Welcome to **Dexter Web Application** – a powerful, user-friendly control panel designed for **device management, system monitoring, and network control**. This **Flask-based web application** provides a seamless and intuitive experience, enabling users to configure and monitor their devices effortlessly.

### 🔥 **Key Benefits**
✅ **Modern Web Interface** – Sleek, responsive, and mobile-friendly UI.  
✅ **Full System Control** – Manage device settings, network configurations, and power zones.  
✅ **Secure Authentication** – User login with session handling.  
✅ **Data Persistence** – Stores settings in SQLite databases & config files.  
✅ **Easy File Uploads** – Upload and manage files directly through the web interface.  

---

## 🎯 2. Features & Functionality

### 🎨 **User Interface (UI)**
✨ **Fully Responsive:** Works across desktops, tablets, and mobile devices.  
✨ **Interactive Elements:** Dropdowns, toggles, and buttons for seamless control.  
✨ **Dark & Light Theme Ready:** (Future-proof for UI enhancements).  

### ⚡ **System Management**
✔ **Advanced Settings:** Modify system parameters via an intuitive UI.  
✔ **Sleep Mode & Reset:** Put the system in sleep mode or restore default settings.  
✔ **Zone Management:** Configure zones using `zone.txt` and `powerZoneSettings.txt`.  
✔ **Network Configuration:** Manage network settings via `modem_config.db`.  
✔ **Authentication:** Secure login system for admin users.  

### 🔄 **Data Storage & Persistence**
🗂 **SQLite Databases:**  
   - `sepleDB.db` → Core system data.  
   - `dexterpanel2.db` → Control panel settings.  
   - `modem_config.db` → Network configurations.  
📁 **Config Files:** Stores user settings (`zone.txt`, `powerZoneSettings.txt`).  
📤 **Uploads Folder:** Secure file upload system.  

---

## 🏗 3. Architecture & Workflow

**📌 Architecture Overview:**
1️⃣ **Client (Browser)** → Loads UI & interacts with the server.  
2️⃣ **Flask Web Server** → Handles requests, processes system actions.  
3️⃣ **Database & Config Files** → Stores and retrieves system settings.  
4️⃣ **Managed Devices** → Interfaces with connected hardware.  

🔄 **Typical User Flow:**
1️⃣ **Login** 🔑 → 2️⃣ **Navigate Settings** ⚙ → 3️⃣ **Modify & Save** ✅ → 4️⃣ **System Updates** 🔄

---

## 🛠 4. Technology Stack

📌 **Backend:** Python 3.x (Flask)  
📌 **Frontend:** HTML5, CSS3, JavaScript  
📌 **Templating Engine:** Jinja2  
📌 **Database:** SQLite  
📌 **Python Libraries:** Flask, Flask-SQLAlchemy, Flask-Login, Requests, Pyserial  

---

## 📂 5. Project Structure

```
📦 Dexter Web App
├── 📜 seple.py           # Main Flask app
├── 📜 requirements.txt   # Dependencies
├── 📂 templates/         # UI Templates (HTML)
│   ├── layout.html       # Base template
│   ├── advanced.html     # Advanced settings page
|   |
.   .
.   .
├── 📂 static/            # Frontend assets
│   ├── css/             # Stylesheets
│   ├── js/              # JavaScript files
├── 📂 uploads/           # File uploads
├── 📂 databases/         # Data storage
│   ├── sepleDB.db        # Core system database
│   ├── dexterpanel2.db   # Panel settings
│   ├── modem_config.db   # Network configurations
├── 📂 config/            # Configuration files
│   ├── zone.txt
│   ├── powerZoneSettings.txt
│   ├── powerzone.txt
```

---

## 🚀 6. Installation & Running

### 🛑 **Prerequisites**
🔹 Python 3.x  
🔹 pip  
🔹 Git (for cloning repository)  

### 📌 **Setup Instructions**

1️⃣ **Clone the Repository**  
```bash
$ git clone <your-repository-url>
$ cd Dexterweb2.0.2
```

2️⃣ **Create & Activate Virtual Environment**  
```bash
$ python -m venv .venv
$ source .venv/bin/activate   # macOS/Linux
$ .\.venv\Scripts\activate   # Windows
```

3️⃣ **Install Dependencies**  
```bash
$ pip install -r requirements.txt
```

4️⃣ **Run the Application**  
```bash
$ python seple.py
```

5️⃣ **Access Dexter in Browser**  
🔗 Open: `http://127.0.0.1:5000/`

---

## 🔒 7. Security Considerations

🚧 **Input Validation:** Prevent XSS & SQL Injection.  
🔐 **Authentication:** Secure user login & session handling.  
🛑 **Disable Debug Mode:** Avoid `debug=True` in production.  
📁 **File Upload Security:** Restrict file types & sizes.  

---

## 🔧 8. Troubleshooting

❌ **ModuleNotFoundError:** Activate the virtual environment before running.  
❌ **Database Errors:** Ensure `.db` files exist with correct permissions.  
❌ **Static Files Not Loading:** Verify correct paths (`url_for('static', filename='...')`).  

---

## 🤝 9. Contributing

💡 Found an issue? Open a **GitHub Issue**!  
📌 Want to contribute? Submit a **Pull Request** with a detailed description!  

---

![Screenshot (59)](https://github.com/user-attachments/assets/3a461fb5-7aeb-4eb8-b3ad-37db242d6f34)
![Screenshot (58)](https://github.com/user-attachments/assets/77aad114-880d-4acc-91b7-e6621152b0f3)
![Screenshot (57)](https://github.com/user-attachments/assets/ceb34bf1-2a69-4049-800d-a752ce6af77a)
![Screenshot (56)](https://github.com/user-attachments/assets/dfd3139f-4b26-4a75-9c43-e41465a445f1)
![Screenshot (73)](https://github.com/user-attachments/assets/ef7da226-9c30-47bb-adc4-a558fdc97db3)
![Screenshot (72)](https://github.com/user-attachments/assets/ba764d8d-5aa0-4f6b-b1b8-c142b56b101b)
![Screenshot (71)](https://github.com/user-attachments/assets/a6c0458a-aac2-4e4f-9090-62a661692346)
![Screenshot (70)](https://github.com/user-attachments/assets/42bb0a93-cfec-400b-9ad4-b586eebb2e47)
![Screenshot (69)](https://github.com/user-attachments/assets/a9a585e6-5de6-4d8b-aa57-6c2903725550)
![Screenshot (68)](https://github.com/user-attachments/assets/1d92fb50-8f94-4d69-a1d0-c5239fbf085e)
![Screenshot (67)](https://github.com/user-attachments/assets/b76d205c-2b8f-4dfe-b2cb-45c9fef96a2f)
![Screenshot (66)](https://github.com/user-attachments/assets/4eee0b52-8e5b-4630-908d-7af9d77a9bea)
![Screenshot (65)](https://github.com/user-attachments/assets/e06b7f77-8aed-498e-9f04-24cc51569b1e)
![Screenshot (64)](https://github.com/user-attachments/assets/1513cecc-b8ed-4467-9a2a-9ad2d143b15a)
![Screenshot (63)](https://github.com/user-attachments/assets/dc27851e-7861-40bb-ad61-394d39fd6b1c)
![Screenshot (62)](https://github.com/user-attachments/assets/8bf6af4d-beac-490e-965f-1ad836cd6a60)
![Screenshot (61)](https://github.com/user-attachments/assets/8c7f053d-200b-4baf-baa2-639ced90aa74)
![Screenshot (60)](https://github.com/user-attachments/assets/8bb1dce7-88fa-46fe-87b7-0a85e81744a4)

## 📜 10. License

📖 This project is licensed under the **MIT License**. See the `LICENSE` file for details.

---

## 📧 11. Contact / Support

📩 For questions or support, contact: **[itinerant018@gmail.com]**  

---

🎉 **Thank you for using Dexter Web Application!** 🚀
