# -*- coding: utf-8 -*-
from flask import Flask, render_template, request, jsonify, session, url_for, redirect
import sqlite3
from sqlite3 import Error
import os
import sys
#from main2 import led_states, toggle_led, cleanup, setup_gpio
from datetime import timedelta
import threading
#from TLChronosProMAIN_391 import clearLogsFromDB
#import psutil
import time
import socket



# setup_gpio()








app = Flask(__name__)
app.secret_key = "SEPLe"  ## set secret key for session

db_file = "sepleDB.db"

hostname = socket.gethostname()

def create_connection(db_file):
    conn = None
    try:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        db_path = os.path.join(base_dir, db_file)
        conn = sqlite3.connect(db_path)
        return conn
    except:
        return None

@app.after_request
def add_header(response):
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, post-check=0, pre-check=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response
    
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=59)


# def get_uptime():
#     return time.time() - psutil.boot_time()












@app.route('/home')
def home():
    if 'username' in session:
        db= create_connection('sepleDB.db')
        cursor = db.cursor()
        cursor.execute("SELECT username FROM users ")
        user_data = cursor.fetchone()
        cursor.close()
        db.close()
        
        db2 = create_connection('dexterpanel2.db')
        cursor2 = db2.cursor()
        cursor2.execute("SELECT * FROM systemLogs")
        logss_data = cursor2.fetchall()
        cursor2.close()
        db2.close()
        
        db3 = create_connection('modem_config.db')
        cursor3 = db3.cursor()
        cursor3.execute("SELECT * FROM modem_parameters")
        token_data= cursor3.fetchall()
        cursor3.close()
        db3.close()
        return render_template('landing.html',logg= logss_data, user= user_data, tokenData= token_data)
    return redirect(url_for('login'))
    









# @app.route('/stats')
# def stats():
#     data = {
#         'cpu': psutil.cpu_percent(interval=1),
#         'memory_used': psutil.virtual_memory().used / (1024 * 1024),  # in MB
#         'disk_used': psutil.disk_usage('/').used / (1024 * 1024 * 1024),  # in GB
#         'bytes_sent': psutil.net_io_counters().bytes_sent / (1024 * 1024),  # in MB
#         'bytes_recv': psutil.net_io_counters().bytes_recv / (1024 * 1024),  # in MB
#         'uptime': int(get_uptime()),  # in seconds
#         'cpu_temp':  psutil.sensors_temperatures()['cpu-thermal'][0].current, # in °C
#         'freq': psutil.cpu_freq(),
#         'network_interfaces': psutil.net_if_addrs()['eth0'][0]
#     }
#     return jsonify(data)











@app.route('/')
def index():
    return render_template('index.html')

@app.route('/delete')
def clear_logs():
    clearLogsFromDB()
    return redirect(url_for('logs'))














@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        db = create_connection(db_file)
        if db is None:
            return "Failed to connect to database"
        
        cursor = db.cursor()
        try:
            cursor.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password))
            user_data = cursor.fetchone()
            cursor.close()
            db.close()
            if user_data:
                session['username'] = username
                return redirect(url_for('home'))
            else:
                return render_template('index.html', alert_userpass=True) 
        except:
            return None

    return render_template('index.html')








@app.route('/resetpassword', methods=['GET', 'POST'])
def resetpassword():
    if request.method == 'POST': 
        username = request.form['username']
        password = request.form['password']
        npassword = request.form['newpassword']
        cpassword = request.form['cpassword']
        
        db = create_connection(db_file)
        if db is None:
            return "Failed to connect to database"
        
        cursor = db.cursor()
        try:
            cursor.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password))
            existing_user = cursor.fetchone()
            if existing_user:
                if npassword == cpassword:
                    cursor.execute("UPDATE users SET password=? WHERE username=?", (npassword, username))
                    db.commit()
                    cursor.close()
                    db.close()
                    return render_template('index.html', reset_password=True)
                else:
                    return render_template('reset.html', not_same=True)
            else:
                return render_template('reset.html', wrong_password=True)
        except Error as e:
            #print("Error executing SQL query:", e)
            return "Error executing SQL query"

    return render_template('reset.html')



def restart_server():
    """Restart the Flask application."""
    python = sys.executable
    os.execl(python, python, *sys.argv)
    
def session_clear():
    session.pop('username',None)
    


@app.route('/restart')    
def restart():
      # Restart the Flask application
    session_clear()  # Clear session data
     # Redirect to login page

    threading.Timer(10.0, lambda: restart_server()).start()  # Restart server in 10 second
    return render_template('index.html', restart=True)


@app.route('/terminate', methods=['POST', 'GET'])
def terminate():
    session_clear()
    threading.Timer(1.0, lambda: terminate_server()).start()
    return render_template('index.html', poweroff = True)
    
    



def terminate_server():
    """Terminate the Flask application."""
    os._exit(0)
    









@app.route('/device_config')
def device_config():
    if 'username' in session:
        username = session['username']
        db = create_connection(db_file)
        if db:
            try:
                cursor = db.cursor()
                cursor.execute("SELECT * FROM users WHERE username=?", (username,))
                user_data = cursor.fetchone()
                cursor.close()
                db.close()

                db3 = create_connection("dexterpanel2.db")
                cursor3 = db3.cursor()
                cursor3.execute("SELECT * FROM systemLogs ")
                logss_data = cursor3.fetchall()
                cursor3.close()
                db3.close()
                return render_template('device_config.html', logg = logss_data,user=user_data)
            except:
                return redirect(url_for('login'))
    return redirect(url_for('login'))






@app.route('/get_zone', methods=['GET','PUT'])
def get_zone():
    try:
        # First read from zone.txt to get hardware settings
        with open("zone.txt", "r") as file:
            lines = file.readlines()
            zones_data = []
            for i, line in enumerate(lines):
                if line.strip():  # Skip empty lines
                    activated, buzzer, device = map(int, line.strip().split())
                    # Convert numeric values to what frontend expects
                    device_name = None
                    if device == 1:
                        device_name = "BAS"
                    elif device == 2:
                        device_name = "FAS"
                    elif device == 3:
                        device_name = "Time Lock"
                    elif device == 4:
                        device_name = "BACS"
                    elif device == 5:
                        device_name = "CCTV"
                    elif device == 6:
                        device_name = "IAS"
                    
                    buzzer_status = "on" if buzzer == 1 else "off"
                    zones_data.append([i+1, activated, device_name, buzzer_status])
            
            return jsonify(zones_data)
    except:
        # If file read fails, try database
        db = create_connection(db_file)
        if db:
            cursor = db.cursor()
            cursor.execute("SELECT * FROM zone")
            zones_data = cursor.fetchall()
            cursor.close()
            db.close()
            return jsonify(zones_data)
        return jsonify([])


def read_zone_file(file_path):
    try:
        with open(file_path, "r") as file:
            return [line.strip() for line in file.readlines()]
    except:
        return []

def log_file_change(file_type):
    try:
        db = create_connection("dexterpanel2.db")
        if db:
            cursor = db.cursor()
            timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
            message = "%s file updated" % file_type
            cursor.execute("INSERT INTO systemLogs (date, message) VALUES (?, ?)", 
                         (timestamp, message))
            db.commit()
            cursor.close()
            db.close()
    except:
        pass

@app.route('/update_zone', methods=['PUT'])
def update_zone():
    if request.method == 'PUT':
        data = request.json
        if not data:
            return redirect(url_for('device_config'))
        
        try:
            # Read existing lines from zone.txt
            lines = ["0 0 0" for _ in range(16)]  # Initialize with defaults
            try:
                with open("zone.txt", "r") as file:
                    file_lines = file.readlines()
                    for i, line in enumerate(file_lines):
                        if i < 16:  # Only process up to 16 lines
                            lines[i] = line.strip()
            except:
                pass

            # Update database and text file
            db = create_connection(db_file)
            if db:
                cursor = db.cursor()
                try:
                    for zone_data in data:    
                        zoneId = zone_data.get('zoneId')
                        if not zoneId or not isinstance(zoneId, int):
                            continue
                            
                        activated = zone_data.get('activated', 0)
                        selectedDevice = zone_data.get('selectedDevice', '')
                        buzzerStatus = zone_data.get('buzzerStatus', 'off')
                        
                        if 1 <= zoneId <= 16:  # Validate zone ID
                            # Update database
                            cursor.execute("SELECT * FROM zone WHERE zoneId=?", (zoneId,))
                            existing_zone = cursor.fetchone()
                            
                            if existing_zone:
                                cursor.execute("UPDATE zone SET activated=?, selectedDevice=?, buzzerStatus=? WHERE zoneId=?", 
                                            (activated, selectedDevice, buzzerStatus, zoneId))
                            else:
                                cursor.execute("INSERT INTO zone (zoneId, activated, selectedDevice, buzzerStatus) VALUES (?, ?, ?, ?)",
                                            (zoneId, activated, selectedDevice, buzzerStatus))

                            # Convert values for text file
                            device_num = 0
                            if selectedDevice == "BAS":
                                device_num = 1
                            elif selectedDevice == "FAS":
                                device_num = 2
                            elif selectedDevice == "Time Lock":
                                device_num = 3
                            elif selectedDevice == "BACS":
                                device_num = 4
                            elif selectedDevice == "CCTV":
                                device_num = 5
                            elif selectedDevice == "IAS":
                                device_num = 6

                            buzzer_num = 1 if buzzerStatus == "on" else 0
                            
                            # Update the corresponding line in the text file
                            lines[zoneId - 1] = "%d %d %d" % (activated, buzzer_num, device_num)

                    # Write all updates to zone.txt
                    with open("zone.txt", "w") as file:
                        file.write("\n".join(lines) + "\n")

                    # Log the change
                    log_file_change("Zone")

                    db.commit()
                    cursor.close()
                    db.close()
                    return jsonify({'Message': 'Done'})
                except:
                    if cursor:
                        cursor.close()
                    if db:
                        db.close()
                    return redirect(url_for('device_config'))
        except:
            return redirect(url_for('device_config'))
    return redirect(url_for('device_config'))


@app.route('/powerzone_config')
def powerzone_config():
    if 'username' in session:
        username = session['username']
        db = create_connection(db_file)
        if db:
            try:
                cursor = db.cursor()
                cursor.execute("SELECT * FROM users WHERE username=?", (username,))
                user_data = cursor.fetchone()
                cursor.close()
                db.close()
                db3 = create_connection("dexterpanel2.db")
                cursor3 = db3.cursor()
                cursor3.execute("SELECT * FROM systemLogs ")
                logss_data = cursor3.fetchall()
                cursor3.close()
                db3.close()
                return render_template('powerzone_config.html', logg = logss_data,user=user_data)
            except Error as e:
                #print(f"Database query error: {e}")
                return redirect(url_for('login'))
    return redirect(url_for('login'))







## Get power zone data route
@app.route('/get_powerzone', methods=['GET','PUT'])
def get_powerzone():
    if 'username' in session:
        try:
            # First read from powerzone.txt to get hardware settings
            with open("powerzone.txt", "r") as file:
                lines = file.readlines()
                zones_data = []
                for i, line in enumerate(lines):
                    if line.strip():  # Skip empty lines
                        activated, buzzer, device = map(int, line.strip().split())
                        # Convert numeric values to what frontend expects
                        device_name = None
                        if device == 1:
                            device_name = "BAS"
                        elif device == 2:
                            device_name = "FAS"
                        elif device == 3:
                            device_name = "Time Lock"
                        elif device == 4:
                            device_name = "BACS"
                        elif device == 5:
                            device_name = "NVR & DVR"
                        elif device == 6:
                            device_name = "IAS"
                        
                        buzzer_status = "on" if buzzer == 1 else "off"
                        zones_data.append([i+1, activated, device_name, buzzer_status])
                
                return jsonify(zones_data)
        except:
            # If file read fails, try database
            db = create_connection(db_file)
            if db:
                cursor = db.cursor()
                cursor.execute("SELECT * FROM powerzone")
                zones_data = cursor.fetchall()
                cursor.close()
                db.close()
                return jsonify(zones_data)
            return jsonify([])

## Update power zone data route
@app.route('/power_zone', methods=['PUT'])
def power_zone():
    if request.method == 'PUT':
        data = request.json
        if not data:
            return redirect(url_for('powerzone_config'))
        
        try:
            # Read existing lines from powerzone.txt
            lines = ["0 0 0" for _ in range(8)]  # Initialize with defaults
            try:
                with open("powerzone.txt", "r") as file:
                    file_lines = file.readlines()
                    for i, line in enumerate(file_lines):
                        if i < 8:  # Only process up to 8 lines
                            lines[i] = line.strip()
            except:
                pass

            # Update database and text file
            db = create_connection(db_file)
            if db:
                cursor = db.cursor()
                try:
                    for zone_data in data:
                        zoneId = zone_data.get('zoneId')
                        if not zoneId or not isinstance(zoneId, int):
                            continue
                            
                        activated = zone_data.get('activated', 0)
                        selectedDevice = zone_data.get('selectedDevice', '')
                        buzzerStatus = zone_data.get('buzzerStatus', 'off')
                        
                        if 1 <= zoneId <= 8:  # Validate zone ID
                            # Update database
                            cursor.execute("SELECT * FROM powerzone WHERE zoneId=?", (zoneId,))
                            existing_zone = cursor.fetchone()
                            if existing_zone:
                                cursor.execute("UPDATE powerzone SET activated=?, selectedDevice=?, buzzerStatus=? WHERE zoneId=?", 
                                            (activated, selectedDevice, buzzerStatus, zoneId))
                            else:
                                cursor.execute("INSERT INTO powerzone (zoneId, activated, selectedDevice, buzzerStatus) VALUES (?, ?, ?, ?)",
                                            (zoneId, activated, selectedDevice, buzzerStatus))

                            # Convert values for text file
                            device_num = 0
                            if selectedDevice == "BAS":
                                device_num = 1
                            elif selectedDevice == "FAS":
                                device_num = 2
                            elif selectedDevice == "Time Lock":
                                device_num = 3
                            elif selectedDevice == "BACS":
                                device_num = 4
                            elif selectedDevice == "NVR & DVR":
                                device_num = 5
                            elif selectedDevice == "IAS":
                                device_num = 6

                            buzzer_num = 1 if buzzerStatus == "on" else 0
                            
                            # Update the corresponding line in the text file
                            lines[zoneId - 1] = "%d %d %d" % (activated, buzzer_num, device_num)

                    # Write all updates to powerzone.txt
                    with open("powerzone.txt", "w") as file:
                        file.write("\n".join(lines) + "\n")

                    # Log the change
                    log_file_change("Power Zone")

                    db.commit()
                    cursor.close()
                    db.close()
                    return jsonify({'Message': 'Done'})
                except:
                    if cursor:
                        cursor.close()
                    if db:
                        db.close()
                    return redirect(url_for('powerzone_config'))
        except:
            return redirect(url_for('powerzone_config'))
    return redirect(url_for('powerzone_config'))





@app.route('/advanced')
def advanced():
    if 'username' in session:
        username = session['username']
        db = create_connection("sepleDB.db")
        cursor = db.cursor()
        cursor.execute("SELECT * FROM users WHERE username=?", (username,))
        user_data = cursor.fetchone()
        cursor.close()
        db.close()

        db3 = create_connection("dexterpanel2.db")
        cursor3 = db3.cursor()
        cursor3.execute("SELECT * FROM systemLogs ")
        logss_data = cursor3.fetchall()
        cursor3.close()
        db3.close()
        return render_template('advanced.html',logg = logss_data, user=user_data)
    return redirect(url_for('login'))






@app.route('/general')
def general():
    if 'username' in session:
        username = session['username']
        db = create_connection("sepleDB.db")
        cursor = db.cursor()
        cursor2 = db.cursor()
        cursor.execute("SELECT * FROM users WHERE username=?", (username,))
        cursor2.execute("SELECT * FROM general")
        user_data = cursor.fetchone()
        user_data2 = cursor2.fetchall()
        cursor.close()
        db.close()


        db3 = create_connection("dexterpanel2.db")
        cursor3 = db3.cursor()
        cursor3.execute("SELECT * FROM systemLogs ")
        logss_data = cursor3.fetchall()
        cursor3.close()
        db3.close()
        return render_template('general.html', user=user_data,logg = logss_data, user2 = user_data2)
    return redirect(url_for('login'))





@app.route('/general_data', methods=['GET', 'POST'])
def general_data():
    if request.method == 'POST':
        success_message = None
        error_message = None
        action = request.form.get('action')
        
        if action == 'change_password':
            current_password = request.form.get('currentPassword')
            new_password = request.form.get('newPassword')
            confirm_password = request.form.get('confirmPassword')
            
            if not all([current_password, new_password, confirm_password]):
                error_message = 'All password fields are required'
            elif new_password != confirm_password:
                error_message = 'New passwords do not match'
            else:
                db = create_connection(db_file)
                if db:
                    try:
                        cursor = db.cursor()
                        cursor.execute("SELECT * FROM users WHERE username=? AND password=?", 
                                     (session['username'], current_password))
                        if cursor.fetchone():
                            cursor.execute("UPDATE users SET password=? WHERE username=?", 
                                         (new_password, session['username']))
                            db.commit()
                            success_message = 'Password updated successfully'
                        else:
                            error_message = 'Current password is incorrect'
                    except Exception:
                        error_message = 'Error updating password'
                    finally:
                        cursor.close()
                        db.close()
                else:
                    error_message = 'Database connection failed'
        
        elif action == 'save_date':
            new_date = request.form.get('setDate')
            if not new_date:
                error_message = 'Please select a date'
            else:
                try:
                    success_message = 'Date updated successfully'
                except Exception:
                    error_message = 'Error updating date'
        
        else:
            brand_name = request.form.get('brandName')
            site_name = request.form.get('siteName')
            
            if not all([brand_name, site_name]):
                error_message = 'Both brand name and site name are required'
            else:
                db = create_connection(db_file)
                if db:
                    try:
                        cursor = db.cursor()
                        cursor.execute("SELECT * FROM general WHERE ID=1")
                        existing = cursor.fetchall()
                        if existing:
                            cursor.execute("UPDATE general SET brand_name=?, site_name=? WHERE ID=1", 
                                         (brand_name, site_name))
                        else:
                            cursor.execute("INSERT INTO general (brand_name, site_name) VALUES (?,?)", 
                                         (brand_name, site_name))
                        db.commit()
                        success_message = 'Brand and site information updated successfully'
                        
                        try:
                            db2 = create_connection("dexterpanel2.db")
                            if db2:
                                cursor2 = db2.cursor()
                                log_message = "General settings updated"
                                cursor2.execute("INSERT INTO systemLogs (date, message) VALUES (datetime('now', 'localtime'), ?)", 
                                              (log_message,))
                                db2.commit()
                                cursor2.close()
                                db2.close()
                        except:
                            pass
                            
                    except:
                        error_message = 'Error updating settings'
                    finally:
                        cursor.close()
                        db.close()
                else:
                    error_message = 'Database connection failed'
    
    return redirect(url_for('general', success_message=success_message, error_message=error_message))





@app.route('/maintenance')
def maintenance():
    if 'username' in session:
        username = session['username']
        db = create_connection("sepleDB.db")
        cursor = db.cursor()
        cursor.execute("SELECT * FROM users WHERE username=?", (username,))
        user_data = cursor.fetchone()
        cursor.close()
        db.close()

        db3 = create_connection("dexterpanel2.db")
        cursor3 = db3.cursor()
        cursor3.execute("SELECT * FROM systemLogs ")
        logss_data = cursor3.fetchall()
        cursor3.close()
        db3.close()
        return render_template('maintenance.html',logg = logss_data, user=user_data)
    return redirect(url_for('login'))


@app.route('/system_test')
def system_test():
    if 'username' in session:
        username = session['username']
        db = create_connection("sepleDB.db")
        cursor = db.cursor()
        cursor.execute("SELECT * FROM users WHERE username=?", (username,))
        user_data = cursor.fetchone()
        cursor.close()
        db.close()

        db3 = create_connection("dexterpanel2.db")
        cursor3 = db3.cursor()
        cursor3.execute("SELECT * FROM systemLogs ")
        logss_data = cursor3.fetchall()
        cursor3.close()
        db3.close()

        # Initialize LED states if not exists
        led_states = {
            1: False,  # Lamp Test
            2: False,  # Relay Test
            3: False   # Buzzer Test
        }
        
        return render_template('systemTest.html', logg=logss_data, user=user_data, led_states=led_states)
    return redirect(url_for('login'))





@app.route('/control', methods=['POST'])
def control():
    if request.method == 'POST':
        try:
            led_id = int(request.form['led'])
            return redirect(url_for('system_test'))
        except:
            return redirect(url_for('system_test'))
    





@app.route('/logs')
def logs():
    if 'username' in session:
        username = session['username']
        
        # Connect to the first database (sepleDB.db)
        db1 = create_connection("sepleDB.db")
        cursor1 = db1.cursor()
        cursor1.execute("SELECT * FROM users WHERE username=?", (username,))
        user_data = cursor1.fetchone()
        cursor1.close()
        db1.close()
        
        # Connect to the second database (dexterpanel2.db)
        db2 = create_connection("dexterpanel2.db")
        cursor2 = db2.cursor()
        cursor2.execute("SELECT * FROM systemLogs")
        logs_data = cursor2.fetchall()
        cursor2.close()
        db2.close()
        
        # Return the logs data in reverse order (newest first)
        logs_data = list(reversed(logs_data))
        
        # Get additional data
        db3 = create_connection("dexterpanel2.db")
        cursor3 = db3.cursor()
        cursor3.execute("SELECT * FROM systemLogs")
        logss_data = cursor3.fetchall()
        cursor3.close()
        db3.close()
        
        return render_template('logs.html', user=user_data, logs=logs_data, logg=logss_data)
    
    # Handle unauthenticated requests
    return redirect(url_for('login'))





@app.route('/reports')
def reports():
    if 'username' in session:
        username = session['username']
        db = create_connection("sepleDB.db")
        cursor = db.cursor()
        cursor.execute("SELECT * FROM users WHERE username=?",(username,))
        user_data = cursor.fetchone()
        cursor.close()
        db.cursor()

        db3 = create_connection("dexterpanel2.db")
        cursor3 = db3.cursor()
        cursor3.execute("SELECT * FROM systemLogs ")
        logss_data = cursor3.fetchall()
        cursor3.close()
        db3.close()
        return render_template('reports.html', user=user_data, logg = logss_data)
    return redirect(url_for('login'))




@app.route('/connectivity_settings')
def connectivity_settings():
    if 'username' in session:
        username = session['username']
        db = create_connection("sepleDB.db")
        cursor = db.cursor()
        cursor.execute("SELECT * FROM users WHERE username=?", (username,))
        user_data = cursor.fetchone()
        cursor.close()
        db.cursor()

        db3 = create_connection("dexterpanel2.db")
        cursor3 = db3.cursor()
        cursor3.execute("SELECT * FROM systemLogs ")
        logss_data = cursor3.fetchall()
        cursor3.close()
        db3.close()
        return render_template('connectivity_sett.html',logg = logss_data, user = user_data)
    return redirect(url_for('login')) 





@app.route('/get_eSim')
def get_eSim():
    if 'username' in session:
        db = create_connection(db_file)
        if db:
            cursor = db.cursor()
            cursor.execute("SELECT * FROM eSim")
            net_data = cursor.fetchall()
            cursor.close()
            db.close()
            return jsonify(net_data)
        else:
            return jsonify([])





@app.route('/neteSim_data', methods=['PUT'])
def neteSim_data():
    if request.method == 'PUT':
        data = request.json 
        eSim_activated = data.get('eSim_activated')
        select_network = data.get('select_network')
        id = 1
        db = create_connection(db_file)
        if db:
            cursor = db.cursor()
            cursor.execute("SELECT * from eSim WHERE ID=1")
            existing = cursor.fetchone()
            if existing:
                cursor.execute("UPDATE eSim SET eSim_activated=?, select_network=? WHERE ID=1",(eSim_activated, select_network))
            else:
                cursor.execute("INSERT INTO eSim (eSim_activated, select_network, ID) VALUES (?, ?, ?)",(eSim_activated, select_network, id))
        db.commit()
        cursor.close()
        db.close()
        return ({"done":"data"})
   
    



    
@app.route('/gnss')
def gnss():
    if 'username' in session:
        username = session['username']
        db = create_connection("sepleDB.db")
        cursor = db.cursor()
        cursor.execute("SELECT * FROM users WHERE username=?", (username,))
        user_data = cursor.fetchone()
        cursor.close()
        db.cursor()


        db3 = create_connection("dexterpanel2.db")
        cursor3 = db3.cursor()
        cursor3.execute("SELECT * FROM systemLogs ")
        logss_data = cursor3.fetchall()
        cursor3.close()
        db3.close()
        return render_template('net_Gnss.html',logg=logss_data, user = user_data)
    return redirect(url_for('login'))





@app.route('/get_gnss')
def get_gnss():
    if 'username' in session:
        db = create_connection(db_file)
        if db:
            cursor = db.cursor()
            cursor.execute("SELECT * FROM gnss")
            gnss_data = cursor.fetchall()
            cursor.close()
            db.close()
            return jsonify(gnss_data)
        else:
            return jsonify([])





@app.route('/net_gnss', methods=['PUT'])
def net_gnss():
    if request.method == 'PUT':
        data = request.json
        gnss_activated = data.get('gnss_activated')
        db = create_connection(db_file)
        if db:
            cursor = db.cursor()
            cursor.execute("SELECT * FROM gnss WHERE ID=1")
            existing = cursor.fetchone()
            if existing:
                cursor.execute("UPDATE gnss SET gnss_activated=? WHERE ID=1", (gnss_activated,))
            else:
                cursor.execute("INSERT INTO gnss (gnss_activated) VALUES (?)", (gnss_activated,))
        db.commit()
        cursor.close()
        db.close()
        return ({"data": "done"})










@app.route('/lan')
def lan():
    if 'username' in session:
        username = session['username']
        db = create_connection("sepleDB.db")
        cursor = db.cursor()
        cursor2 = db.cursor()
        cursor.execute("SELECT * FROM users WHERE username=?", (username,))
        cursor2.execute("SELECT * FROM lan")
        user2_data= cursor2.fetchall()
        user_data = cursor.fetchone()
        cursor.close()
        db.cursor()

        db3 = create_connection("dexterpanel2.db")
        cursor3 = db3.cursor()
        cursor3.execute("SELECT * FROM systemLogs ")
        logss_data = cursor3.fetchall()
        cursor3.close()
        db3.close()
        return render_template('Lan.html', user = user_data,logg = logss_data, user2 = user2_data)
    return redirect(url_for('login'))




@app.route('/data2_lan', methods=['PUT'])
def data2_lan():
    if request.method == 'PUT':
        data = request.json
        network_led_sts = data.get('network_led_sts')
        wireless_lan = data.get('wireless_lan')
        ip_module = data.get('ip_module')
        static_or_dynamic = data.get('static_or_dynamic')
        db = create_connection(db_file)
        if db:
            cursor = db.cursor()
            cursor.execute("SELECT * FROM lan WHERE ID=1")
            
            existing = cursor.fetchone()
            if existing:
                cursor.execute("UPDATE lan SET network_led_sts=?, wireless_lan=?,ip_module=?, static_or_dynamic=? WHERE ID=1", (network_led_sts,wireless_lan,ip_module, static_or_dynamic))
            else:
                cursor.execute("INSERT INTO lan (network_led_sts,wireless_lan,ip_module,static_or_dynamic) VALUES (?,?,?,?)", (network_led_sts ,wireless_lan,ip_module,static_or_dynamic))
        db.commit()
        cursor.close()
        db.close()
        return jsonify([])
    



@app.route('/get_data2lan')
def get_data2lan():
    if 'username' in session:
        db = create_connection(db_file)
        if db:
            cursor = db.cursor()
            cursor.execute("SELECT network_led_sts,wireless_lan,ip_module,static_or_dynamic  FROM lan")
            get_data = cursor.fetchall()
            cursor.close()
            db.close()
            return jsonify(get_data)






@app.route('/data_lan', methods =['POST'])
def data_lan():
    if request.method == 'POST':
        set_ip_address = request.form['set_ip_address']
        set_port_no = request.form['set_port_no']
        subnet_mask = request.form['subnet_mask']
        gate_way = request.form['gate_way']
        preferred_dns = request.form['preferred_dns']
        alternate_dns = request.form['alternate_dns']
        apn_settings = request.form['apn_settings']
        
        db = create_connection(db_file)
        if db:
            cursor = db.cursor()
            cursor.execute("SELECT * FROM lan WHERE ID=1")
            existing = cursor.fetchall()
            if existing:
                cursor.execute("UPDATE lan SET set_ip_address=?, set_port_no=?, subnet_mask=?, gate_way=?, preferred_dns=?, alternate_dns=?, apn_settings=? WHERE ID=1",
                             (set_ip_address, set_port_no, subnet_mask, gate_way, preferred_dns, alternate_dns, apn_settings))
            else:
                cursor.execute("INSERT INTO lan (set_ip_address, set_port_no, subnet_mask, gate_way, preferred_dns, alternate_dns, apn_settings) VALUES(?,?,?,?,?,?,?)",
                             (set_ip_address, set_port_no, subnet_mask, gate_way, preferred_dns, alternate_dns, apn_settings))
    db.commit()
    cursor.close()
    db.close()
    return redirect(url_for('lan'))
    # return ({"data":"send"})





@app.route('/net_gsm')
def net_gsm():
    if 'username' in session:
        username = session['username']
        db = create_connection("sepleDB.db")
        cursor = db.cursor()
        cursor.execute("SELECT * FROM users WHERE username=?", (username,))
        user_data = cursor.fetchone()
        cursor.close()
        db.cursor()

        db3 = create_connection("dexterpanel2.db")
        cursor3 = db3.cursor()
        cursor3.execute("SELECT * FROM systemLogs ")
        logss_data = cursor3.fetchall()
        cursor3.close()
        db3.close()
        return render_template('net_Gsm.html',logg = logss_data, user = user_data)
    return redirect(url_for('login'))





@app.route('/get_gsm')
def get_gsm():
    if 'username' in session:
        db = create_connection(db_file)
        if db:
            cursor = db.cursor()
            cursor.execute("SELECT * FROM gsm")
            gsm_data = cursor.fetchall()
            cursor.close()
            db.close()
            return jsonify(gsm_data)
        else:
            return jsonify({"data": "error"})
            





@app.route('/netdata_gsm', methods=['PUT'])
def netdata_gsm():
    if request.method == 'PUT':
        data = request.json
        gsm_activated = data.get('gsm_activated')
        db = create_connection(db_file)
        if db:
            cursor = db.cursor()
            cursor.execute("SELECT * FROM gsm WHERE ID=1")
            existing = cursor.fetchall()
            if existing:
                cursor.execute("UPDATE gsm SET gsm_activated=? WHERE ID=1", (gsm_activated,))
            else:
                cursor.execute("INSERT INTO gsm (gsm_activated) VALUES (?)", (gsm_activated,))
        db.commit()
        cursor.close()
        db.close()
        return ({"data":"send"})
    




@app.route('/come_soon')
def come_soon():
    if 'username' in session:
        username = session['username']
        db = create_connection('sepleDB.db')
        cursor = db.cursor()
        cursor.execute("SELECT * FROM users WHERE username=?", (username,))
        user = cursor.fetchone()
        cursor.close()
        db.close()

        db3 = create_connection("dexterpanel2.db")
        cursor3 = db3.cursor()
        cursor3.execute("SELECT * FROM systemLogs ")
        logss_data = cursor3.fetchall()
        cursor3.close()
        db3.close()
        
        return render_template('coming_soon.html',logg = logss_data, user = user)
    return redirect(url_for('login'))






@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))




@app.route('/connection')
def connection():
    if 'username' in session:

        username = session['username']
        db = create_connection("sepleDB.db")
        db2 = create_connection("/home/pi/Test3/modem_config.db")
        cursor = db2.cursor()
        cursor.execute("SELECT * FROM modem_parameters")
        data = cursor.fetchall()
        cursor2 = db.cursor()
        cursor2.execute("SELECT * FROM users WHERE username=?",(username,))
        user_data = cursor2.fetchone()
        cursor.close()
        db.close()

        db3 = create_connection("dexterpanel2.db")
        cursor3 = db3.cursor()
        cursor3.execute("SELECT * FROM systemLogs ")
        logss_data = cursor3.fetchall()
        cursor3.close()
        db3.close()
        return render_template('Connection.html', data=data,logg= logss_data, user= user_data)
    return redirect(url_for('login'))




@app.route('/acces_token', methods=['POST'])
def acces_token():
    if request.method == 'POST':
        access_token = request.form['access_token']
        db = create_connection("/home/pi/Test3/modem_config.db")
        if db:
            cursor = db.cursor()
            cursor.execute("SELECT * FROM modem_parameters WHERE id=1")
            existing = cursor.fetchall()
            if existing:
                cursor.execute("UPDATE modem_parameters SET access_token=? WHERE id=1", (access_token,))
            else:

                cursor.execute("INSERT INTO modem_parameters (access_token) VALUES (?)", (access_token,))
    db.commit()
    cursor.close()
    db.close()
    return redirect(url_for('connection'))




@app.route('/x509', methods=['POST'])
def x509():
    if request.method == 'POST':
        x509 = request.form.get('x509')
        db = create_connection('/home/pi/Test3/modem_config.db')
        if db:
            cursor = db.cursor()
            cursor.execute("SELECT * FROM modem_parameters WHERE id=1")
            existing = cursor.fetchall()
            if existing:
                cursor.execute("UPDATE modem_parameters SET x509=? WHERE id=1", (x509,))
            else:

                cursor.execute("INSERT INTO modem_parameters (x509) VALUES (?)", (x509,))
    db.commit()
    cursor.close()
    db.close()
    return redirect(url_for('connection'))




@app.route('/mqtt_basic', methods=['POST'])
def mqtt_basic():

    if request.method == 'POST':

        clintId = request.form.get('client_id')
        username = request.form.get('user_name')
        password= request.form.get('password')
    
        db = create_connection('/home/pi/Test3/modem_config.db')
        if db:
            cursor = db.cursor()
            cursor.execute("SELECT * FROM modem_parameters WHERE id=1")
            existing = cursor.fetchall()
            if existing:
                cursor.execute("UPDATE modem_parameters SET client_id=?,user_name=?,password=?  WHERE id=1", (clintId, username, password))
            else:
                cursor.execute("INSERT INTO modem_parameters (client_id, user_name, password) VALUES (?,?,?)", (clintId, username, password))  
    db.commit()
    cursor.close()
    db.close()
    return redirect(url_for('connection'))  
    




@app.route("/SOL")
def SOL():
    if 'username' in session:
        username = session['username']
        db = create_connection("sepleDB.db")
        cursor = db.cursor()
        cursor.execute("SELECT * FROM users WHERE username=?", (username,))
        user_data = cursor.fetchone()
        cursor.close()
        db.cursor()
        
        db2 = create_connection("dexterpanel2.db")
        cursor2 = db2.cursor()
        cursor2.execute("SELECT * FROM systemLogs ")
        logss_data = cursor2.fetchall()
        cursor2.close()
        db2.close()
        

        db3 = create_connection("sepleDB.db")
        cursor3 = db3.cursor()
        cursor3.execute("SELECT * FROM provision ")
        data = cursor3.fetchall()
        cursor3.close()
        db3.close()
        
        
        return render_template('sol_id.html', user = user_data,data = data, logg = logss_data)
    return redirect(url_for('login'))
    


@app.route('/provision', methods=['GET', 'POST'])
def provision():
    if 'username' not in session:
        return redirect(url_for('login'))
        
    try:
        # Here we need to add the logic to provision the device
        db3 = create_connection("dexterpanel2.db")
        if db3:
            cursor3 = db3.cursor()
            log_message = "Device provisioning initiated"
            cursor3.execute("INSERT INTO systemLogs (date, message) VALUES (datetime('now', 'localtime'), ?)", 
                          (log_message,))
            db3.commit()
            cursor3.close()
            db3.close()
    except:
        pass
        
    # Get user data
    db = create_connection('sepleDB.db')
    cursor = db.cursor()
    cursor.execute("SELECT * FROM users WHERE username=?", (session['username'],))
    user = cursor.fetchone()
    cursor.close()
    db.close()

    # Get system logs
    db3 = create_connection("dexterpanel2.db")
    cursor3 = db3.cursor()
    cursor3.execute("SELECT * FROM systemLogs ")
    logss_data = cursor3.fetchall()
    cursor3.close()
    db3.close()
    
    return render_template('provisioning.html', 
                         logg=logss_data, 
                         user=user)







@app.route("/send_data", methods=['GET','POST'])
def sendData():
    if request.method == 'POST':
        deviceName = request.form['deviceName']
        id = request.form['id']
        userName = request.form['userName']
        password = request.form['password']
        
        
        db = create_connection(db_file)
        if db:
            cursor = db.cursor()
            cursor.execute("SELECT * FROM provision")
            existing = cursor.fetchall()
            if existing:
                cursor.execute("UPDATE provision SET E_deviceName=?, E_id=?,E_userName=?,E_passWord=?",(deviceName,id,userName,password))
            else:
                cursor.execute("INSERT INTO provision (E_deviceName, E_id,E_userName,E_passWord) VALUES(?,?,?,?)",(deviceName,id,userName,password))
    db.commit()
    cursor.close()
    db.close()
    return redirect(url_for('provision'))
    # return ({"data":"send"}) 
    


@app.route("/send_data2", methods=['GET','POST'])
def sendData2():
    if request.method == 'POST':
        ethernetDeviceName = request.form['ethernetDeviceName']
        
        
        db = create_connection(db_file)
        if db:
            cursor = db.cursor()
            cursor.execute("SELECT * FROM provision")
            existing = cursor.fetchall()
            if existing:
                cursor.execute("UPDATE provision SET etn_deviceName=?",(ethernetDeviceName,))
            else:
                cursor.execute("INSERT INTO provision (etn_deviceName) VALUES(?)",(ethernetDeviceName,))
    db.commit()
    cursor.close()
    db.close()
    return redirect(url_for('provision'))
    # return ({"data":"send"}) 
    





@app.route('/output_controls')
def output_controls():
    if 'username' in session:
        username = session['username']
        db = create_connection('sepleDB.db')
        cursor = db.cursor()
        cursor.execute("SELECT * FROM users WHERE username=?", (username,))
        user = cursor.fetchone()
        cursor.close()
        db.close()

        db3 = create_connection("dexterpanel2.db")
        cursor3 = db3.cursor()
        cursor3.execute("SELECT * FROM systemLogs ")
        logss_data = cursor3.fetchall()
        cursor3.close()
        db3.close()
        
        return render_template('output_controls.html',logg = logss_data, user = user)
    return redirect(url_for('login'))










@app.route('/device_management')
def device_management():
    if 'username' in session:
        username = session['username']
        db = create_connection('sepleDB.db')
        cursor = db.cursor()
        cursor.execute("SELECT * FROM users WHERE username=?", (username,))
        user = cursor.fetchone()
        cursor.close()
        db.close()

        db3 = create_connection("dexterpanel2.db")
        cursor3 = db3.cursor()
        cursor3.execute("SELECT * FROM systemLogs ")
        logss_data = cursor3.fetchall()
        cursor3.close()
        db3.close()
        
        return render_template('deviceManagement.html',logg = logss_data, user = user)
    return redirect(url_for('login'))






@app.route('/protocol_config')
def protocol_config():
    if 'username' in session:
        username = session['username']
        db = create_connection('sepleDB.db')
        cursor = db.cursor()
        cursor.execute("SELECT * FROM users WHERE username=?", (username,))
        user = cursor.fetchone()
        cursor.close()
        db.close()

        db3 = create_connection("dexterpanel2.db")
        cursor3 = db3.cursor()
        cursor3.execute("SELECT * FROM systemLogs ")
        logss_data = cursor3.fetchall()
        cursor3.close()
        db3.close()
        
        return render_template('protocol_config.html',logg = logss_data, user = user)
    return redirect(url_for('login'))





@app.route('/OTA')
def OTA():
    if 'username' in session:
        username = session['username']
        db = create_connection('sepleDB.db')
        cursor = db.cursor()
        cursor.execute("SELECT * FROM users WHERE username=?", (username,))
        user = cursor.fetchone()
        cursor.close()
        db.close()

        db3 = create_connection("dexterpanel2.db")
        cursor3 = db3.cursor()
        cursor3.execute("SELECT * FROM systemLogs ")
        logss_data = cursor3.fetchall()
        cursor3.close()
        db3.close()
        
        return render_template('OTA.html',logg = logss_data, user = user)
    return redirect(url_for('login'))


@app.route('/device_credential')
def device_credential():
    if 'username' in session:
        username = session['username']
        db = create_connection('sepleDB.db')
        cursor = db.cursor()
        cursor.execute("SELECT * FROM users WHERE username=?", (username,))
        user = cursor.fetchone()
        
        # Get e-SIM credentials
        esim_credentials = None
        try:
            cursor.execute("SELECT * FROM device_credentials WHERE type='esim' AND id=1")
            result = cursor.fetchone()
            if result:
                # Convert tuple to dictionary
                esim_credentials = {
                    'id': result[0],
                    'type': result[1],
                    'device_key': result[2],
                    'device_secret': result[3],
                    'sol_id': result[4],
                    'client_id': result[5],
                    'username': result[6],
                    'password': result[7],
                    'access_token': result[8],
                    'device_name': result[9]
                }
        except:
            # Table might not exist yet
            pass
            
        # Get Ethernet credentials
        ethernet_credentials = None
        try:
            cursor.execute("SELECT * FROM device_credentials WHERE type='ethernet' AND id=1")
            result = cursor.fetchone()
            if result:
                # Convert tuple to dictionary
                ethernet_credentials = {
                    'id': result[0],
                    'type': result[1],
                    'device_key': result[2],
                    'device_secret': result[3],
                    'sol_id': result[4],
                    'client_id': result[5],
                    'username': result[6],
                    'password': result[7],
                    'access_token': result[8],
                    'device_name': result[9]
                }
        except:
            # Table might not exist yet
            pass
            
        cursor.close()
        db.close()

        # Get system logs
        db3 = create_connection("dexterpanel2.db")
        cursor3 = db3.cursor()
        cursor3.execute("SELECT * FROM systemLogs ")
        logss_data = cursor3.fetchall()
        cursor3.close()
        db3.close()
        
        # Get success/error messages from query parameters if they exist
        success_message = request.args.get('success_message')
        error_message = request.args.get('error_message')
        
        return render_template('deviceCredential.html',
                              logg=logss_data, 
                              user=user, 
                              esim_credentials=esim_credentials,
                              ethernet_credentials=ethernet_credentials,
                              success_message=success_message,
                              error_message=error_message)
    return redirect(url_for('login'))


@app.route('/device_credentials', methods=['POST'])
def save_device_credentials():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    try:
        if 'deviceKey' in request.form:
            device_type = 'esim'
            device_key = request.form.get('deviceKey')
            if not device_key:
                return redirect(url_for('device_credential'))
                
            db = create_connection(db_file)
            if not db:
                return redirect(url_for('device_credential'))
                
            cursor = db.cursor()
            try:
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS device_credentials (
                        id INTEGER,
                        type TEXT,
                        device_key TEXT,
                        device_secret TEXT,
                        sol_id TEXT,
                        client_id TEXT,
                        username TEXT,
                        password TEXT,
                        access_token TEXT,
                        device_name TEXT,
                        PRIMARY KEY (id, type)
                    )
                ''')
                
                cursor.execute("SELECT * FROM device_credentials WHERE type=? AND id=1", (device_type,))
                existing = cursor.fetchone()
                
                if existing:
                    cursor.execute('''
                        UPDATE device_credentials 
                        SET device_key=?, device_secret=?, sol_id=?, client_id=?, username=?, password=? 
                        WHERE type=? AND id=1
                    ''', (device_key, device_secret, sol_id, client_id, username, password, device_type))
                else:
                    cursor.execute('''
                        INSERT INTO device_credentials 
                        (id, type, device_key, device_secret, sol_id, client_id, username, password) 
                        VALUES (1, ?, ?, ?, ?, ?, ?, ?)
                    ''', (device_type, device_key, device_secret, sol_id, client_id, username, password))
                
                db.commit()
                
                db2 = create_connection("dexterpanel2.db")
                if db2:
                    cursor2 = db2.cursor()
                    log_message = "e-SIM device credentials updated"
                    cursor2.execute("INSERT INTO systemLogs (date, message) VALUES (datetime('now', 'localtime'), ?)", (log_message,))
                    db2.commit()
                    cursor2.close()
                    db2.close()
                
                return redirect(url_for('device_credential'))
            except:
                return redirect(url_for('device_credential'))
            finally:
                cursor.close()
                db.close()
                
        elif 'ethernetDeviceKey' in request.form:
            # Similar changes for ethernet credentials...
            pass
        else:
            return redirect(url_for('device_credential'))
            
    except:
        return redirect(url_for('device_credential'))


@app.route('/integration_settings')
def integration_settings():
    if 'username' in session:
        username = session['username']
        db = create_connection('sepleDB.db')
        cursor = db.cursor()
        cursor.execute("SELECT * FROM users WHERE username=?", (username,))
        user = cursor.fetchone()
        
        # Get integration data
        hikvision_nvr_data = None
        hikvision_bacs_data = None
        dahua_nvr_data = None
        
        try:
            # HIKVISION NVR data
            try:
                cursor.execute("SELECT ip_address, device_name, device_password, port_number, is_active FROM hikvision_nvr_integration WHERE id=1")
                result = cursor.fetchone()
                if result:
                    hikvision_nvr_data = {
                        'ip_address': result[0],
                        'device_name': result[1],
                        'device_password': result[2],
                        'port_number': result[3],
                        'is_active': result[4]
                    }
            except:
                pass
            
            # HIKVISION BACS data
            try:
                cursor.execute("SELECT ip_address, device_name, device_password, port_number, is_active FROM hikvision_bacs_integration WHERE id=1")
                result = cursor.fetchone()
                if result:
                    hikvision_bacs_data = {
                        'ip_address': result[0],
                        'device_name': result[1],
                        'device_password': result[2],
                        'port_number': result[3],
                        'is_active': result[4]
                    }
            except:
                pass
            
            # DAHUA NVR data
            try:
                cursor.execute("SELECT ip_address, device_name, device_password, port_number, is_active FROM dahua_nvr_integration WHERE id=1")
                result = cursor.fetchone()
                if result:
                    dahua_nvr_data = {
                        'ip_address': result[0],
                        'device_name': result[1],
                        'device_password': result[2],
                        'port_number': result[3],
                        'is_active': result[4]
                    }
            except:
                pass
        except:
            pass
            
        cursor.close()
        db.close()

        db3 = create_connection("dexterpanel2.db")
        cursor3 = db3.cursor()
        cursor3.execute("SELECT * FROM systemLogs ")
        logss_data = cursor3.fetchall()
        cursor3.close()
        db3.close()
        
        return render_template('integrationSettings.html', 
                            logg=logss_data, 
                            user=user, 
                            hikvision_nvr_data=hikvision_nvr_data,
                            hikvision_bacs_data=hikvision_bacs_data,
                            dahua_nvr_data=dahua_nvr_data)
    return redirect(url_for('login'))


@app.route('/save_integration', methods=['POST'])
def save_integration():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    try:
        device_type = request.form.get('device_type')
        ip_address = request.form.get('ip_address')
        device_name = request.form.get('device_name')
        port_number = request.form.get('port_number')
        
        if not all([device_type, ip_address, device_name, port_number]):
            return redirect(url_for('integration_settings'))
            
        db = create_connection(db_file)
        if not db:
            return redirect(url_for('integration_settings'))
            
        cursor = db.cursor()
        
        table_name = ''
        if device_type == 'hikvision-nvr':
            table_name = 'hikvision_nvr_integration'
        elif device_type == 'hikvision-bacs':
            table_name = 'hikvision_bacs_integration'
        elif device_type == 'dahua-nvr':
            table_name = 'dahua_nvr_integration'
        else:
            return redirect(url_for('integration_settings'))
        
        try:
            # Create table
            create_table_sql = '''
                CREATE TABLE IF NOT EXISTS %s (
                    id INTEGER PRIMARY KEY,
                    ip_address TEXT NOT NULL,
                    device_name TEXT NOT NULL,
                    device_password TEXT,
                    port_number INTEGER NOT NULL,
                    is_active INTEGER DEFAULT 1
                )
            ''' % table_name
            cursor.execute(create_table_sql)
            
            # Check if record exists
            cursor.execute("SELECT * FROM %s WHERE id=1" % table_name)
            existing = cursor.fetchone()
            
            try:
                port_number = int(port_number)
            except ValueError:
                port_number = 8000
            
            device_password = request.form.get('device_password')
            
            if existing:
                update_sql = "UPDATE %s SET ip_address=?, device_name=?, device_password=?, port_number=?, is_active=1 WHERE id=1" % table_name
                cursor.execute(update_sql, (ip_address, device_name, device_password, port_number))
            else:
                insert_sql = "INSERT INTO %s (ip_address, device_name, device_password, port_number, is_active) VALUES (?,?,?,?,1)" % table_name
                cursor.execute(insert_sql, (ip_address, device_name, device_password, port_number))
            
            db.commit()
            
            # Log the integration configuration
            db2 = create_connection("dexterpanel2.db")
            if db2:
                cursor2 = db2.cursor()
                log_message = "Integration configuration updated for %s" % device_type
                cursor2.execute("INSERT INTO systemLogs (date, message) VALUES (datetime('now', 'localtime'), ?)", (log_message,))
                db2.commit()
                cursor2.close()
                db2.close()
                
        except:
            return redirect(url_for('integration_settings'))
        finally:
            cursor.close()
            db.close()
            
    except:
        return redirect(url_for('integration_settings'))
    
    return redirect(url_for('integration_settings'))




if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", threaded= True)
