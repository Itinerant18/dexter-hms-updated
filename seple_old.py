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
    except Error as e:
        ##print("Error connecting to database:", e)
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
        except Error as e:
            #print("Error executing SQL query:", e)
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
    """Device Config route."""
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
            except Error as e:
                #print(f"Database query error: {e}")
                return redirect(url_for('login'))
    return redirect(url_for('login'))



@app.route('/update_zone', methods=['PUT'])
def update_zone():
    if request.method == 'PUT':
        data = request.json  # Assuming JSON data is sent from the client-side
        if not data:
            return jsonify({'error': 'No JSON data received'}), 400
        
        db = create_connection(db_file)
        if db:
            cursor = db.cursor()
            try:
                for zone_data in data:    
                    zoneId = zone_data.get('zoneId')
                    activated = zone_data.get('activated')
                    selectedDevice = zone_data.get('selectedDevice')
                    buzzerStatus = zone_data.get('buzzerStatus')
                    
                    if zoneId:
                        cursor.execute("SELECT * FROM zone WHERE zoneId=?", (zoneId,))
                        existing_zone = cursor.fetchone()
                        
                        if existing_zone:
                            cursor.execute("UPDATE zone SET activated=?, selectedDevice=?, buzzerStatus=? WHERE zoneId=?", (activated, selectedDevice, buzzerStatus, zoneId))
                        else:
                            cursor.execute("INSERT INTO zone (zoneId, activated, selectedDevice, buzzerStatus) VALUES (?, ?, ?, ?)", (zoneId, activated, selectedDevice, buzzerStatus))
                            # print(selectedDevice)
                        selectedDevice_txt=0
                        if selectedDevice == "Burglar Alarm":
                            selectedDevice_txt = 1
                        elif selectedDevice=='Fire Alarm':
                            selectedDevice_txt = 2
                        elif selectedDevice == 'Time Lock':
                            selectedDevice_txt=3
                        elif selectedDevice =='ACCESS CONTROL':
                            selectedDevice_txt=4
                        elif selectedDevice =='CCTV':
                            selectedDevice_txt=5
                        elif selectedDevice=='I.A.S':
                            selectedDevice_txt=6
                        else:
                            selectedDevice_txt=0


                        buzzerStatus_txt=0
                        if buzzerStatus=='on':
                            buzzerStatus_txt=1
                        elif buzzerStatus =='off':
                            buzzerStatus_txt=0
                        else:
                            buzzerStatus_txt=0

                        file_path = "zone.txt"

                        # Read existing lines or handle missing file
                        try:
                            with open(file_path, "r") as file:
                                lines = file.readlines()
                        except FileNotFoundError:
                            lines = []

                        # Define new data to add
                        new_data = "{} {} {}\n".format(activated, buzzerStatus_txt, selectedDevice_txt)


                        # If file is empty or has more than 16 lines, replace everything with new data
                        if not lines or len(lines) >= 16:
                            lines = lines[1:]  # Replace with a single new line
                        lines.append(new_data)  

                        # Write back to file
                        with open(file_path, "w") as file:
                            # file.write("\n")
                            file.writelines(lines)
                            # file.write("\n")


                        # print(activated, p_buzzerStatus_txt, p_selectedDevice_txt)
                
                
                db.commit()
                cursor.close()
                db.close()
                return jsonify({'Message': 'Done'})
            except Error as e:
                #print(f"Error executing SQL query: {e}")
                return jsonify({'error': str(e)}), 500
        else:
            return "Failed to connect to database"

    return jsonify({'error': 'Invalid request method'}), 405


@app.route('/get_zone', methods=['GET','PUT'])
def get_zone():
    db = create_connection(db_file)
    if db:
        cursor = db.cursor()
        cursor.execute("SELECT * FROM zone")
        zones_data = cursor.fetchall()
        cursor.close()
        db.close()
        return jsonify(zones_data)
    else:
        return jsonify([])
    

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
        db = create_connection(db_file)
        if db:
            cursor = db.cursor()
            cursor.execute("SELECT * FROM powerzone")
            zones_data = cursor.fetchall()
            cursor.close()
            db.close()
            return jsonify(zones_data)
        else:
            return jsonify([])

## Update power zone data route
@app.route('/power_zone', methods=['PUT'])
def power_zone():
    if request.method == 'PUT':
        data = request.json
        if not data:
            return jsonify({'error': 'No JSON data received'}), 400
        db = create_connection(db_file)
        if db:
            cursor = db.cursor()
            try:    
                for zone_data in data:
                    zoneId = zone_data['zoneId']
                    activated = zone_data['activated']
                    selectedDevice = zone_data['selectedDevice']
                    buzzerStatus = zone_data['buzzerStatus']
                    if zoneId:
                        cursor.execute("SELECT * FROM powerzone WHERE zoneId=?", (zoneId,))
                        existing_zone = cursor.fetchone()
                        if existing_zone:
            
                            cursor.execute("UPDATE powerzone SET activated=?, selectedDevice=?, buzzerStatus=? WHERE zoneId=?", (activated, selectedDevice, buzzerStatus, zoneId))
                        else:
                            cursor.execute("INSERT INTO powerzone (zoneId, activated, selectedDevice, buzzerStatus) VALUES (?, ?, ?, ?)", (zoneId, activated, selectedDevice, buzzerStatus))

                        # print(selectedDevice)
                        p_selectedDevice_txt = 0
                        if selectedDevice == "Burglar Alarm":
                            p_selectedDevice_txt = 1
                        elif selectedDevice=='Fire Alarm':
                            p_selectedDevice_txt = 2
                        elif selectedDevice == 'Time Lock':
                            p_selectedDevice_txt=3
                        elif selectedDevice =='Access Control':
                            p_selectedDevice_txt=4
                        elif selectedDevice=='NVR/DVR':
                            p_selectedDevice_txt=5
                        else:
                            p_selectedDevice_txt=0


                        p_buzzerStatus_txt =0
                        if buzzerStatus=='on':
                            p_buzzerStatus_txt=1
                        elif buzzerStatus =='off':
                            p_buzzerStatus_txt=0
                        else:
                            p_buzzerStatus_txt=0

                        
                        file_path = "/home/pi/TLChronosPro/powerZoneSettings.txt"

                        # Read existing lines or handle missing file
                        try:
                            with open(file_path, "r") as file:
                                lines = file.readlines()
                        except FileNotFoundError:
                            lines = []

                        # Define new data to add
                        new_data = "{} {} {}\n".format(activated, p_buzzerStatus_txt, p_selectedDevice_txt)


                        # If file is empty or has more than 16 lines, replace everything with new data
                        if not lines or len(lines) >= 16:
                            lines = lines[1:]  # Replace with a single new line
                        lines.append(new_data)  

                        # Write back to file
                        with open(file_path, "w") as file:
                            # file.write("\n")
                            file.writelines(lines)
                            # file.write("\n")


                        # print(activated, p_buzzerStatus_txt, p_selectedDevice_txt)
                
                db.commit()
                cursor.close()
                db.close()
                return jsonify({'msg': 'done'})
            except Error as e:
                #print(f"Error executing SQL query: {e}")
                return jsonify({'error': str(e)}), 500
            
        else:
            return "Failed to connect database"
    return jsonify({'error': 'Invalid request method'})


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


@app.route('/general_data', methods=['GET','POST'])
def general_data():
    if request.method == 'POST':
        brand_name =request.form['brandName']
        site_name = request.form['siteName']
        
        db = create_connection(db_file)
        if db:
            cursor = db.cursor()
            cursor.execute("SELECT * FROM general WHERE ID=1")
            existing = cursor.fetchall()
            if existing:
                cursor.execute("UPDATE general SET brand_name=?, site_name=? WHERE ID=1", (brand_name, site_name))
            else:
                cursor.execute("INSERT INTO general (brand_name, site_name) VALUES (?,?)", (brand_name, site_name))
    db.commit()
    cursor.close()
    db.close()
    return redirect(url_for('general'))
            

#@app.route('/system_test', methods=['GET'])
#def system_test():
    #if 'username' in session:
        #username = session['username']
        #db = create_connection("sepleDB.db")
        #cursor = db.cursor()
        #cursor.execute("SELECT * FROM users WHERE username=?", (username,))
        #user_data = cursor.fetchone()
        #cursor.close()
        #db.close()
                
        #led_id = int(request.form['led'])
        #current_state = led_states[led_id]
        #new_state = not current_state
        #led_states[led_id] = new_state
        #GPIO.output(led_pins[led_id], GPIO.HIGH if new_state else GPIO.LOW)
        #print ("changed")
        #return render_template('system_test.html', user=user_data)
    #return redirect(url_for('login'))



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
        
        db2 = create_connection("dexterpanel2.db")
        cursor2 = db2.cursor()
        cursor2.execute("SELECT * FROM systemLogs")
        logss_data = cursor2.fetchall()
        cursor2.close()
        db2.close()
        return render_template('system_test.html',logg = logss_data,user = user_data)
    return redirect(url_for('login'))

@app.route('/control', methods=['POST'])
def control():
    if request.method == 'POST':
        led_id = int(request.form['led'])
        toggle_led(led_id)
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
        
        # Connect to the second database (anotherDB.db)
        db2 = create_connection("dexterpanel2.db")
        cursor2 = db2.cursor()
        cursor2.execute("SELECT * FROM systemLogs")
        logs_data = cursor2.fetchall()
        cursor2.close()
        db2.close()
        logs_data = reversed(logs_data)


        

        db3 = create_connection("dexterpanel2.db")
        cursor3 = db3.cursor()
        cursor3.execute("SELECT * FROM systemLogs ")
        logss_data = cursor3.fetchall()
        cursor3.close()
        db3.close()
        #logg = reversed(logss_data)
        
        
        
        return render_template('logs.html', user=user_data, logs=logs_data, logg = logss_data)
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

@app.route('/net_eSim')
def net_eSim():
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
        return render_template('net_eSim.html',logg = logss_data, user = user_data)
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
        dns_setups = request.form['dns_setups']
        apn_settings = request.form['apn_settings']
        
        
        db = create_connection(db_file)
        if db:
            cursor = db.cursor()
            cursor.execute("SELECT * FROM lan WHERE ID=1")
            existing = cursor.fetchall()
            if existing:
                cursor.execute("UPDATE lan SET set_ip_address=?,set_port_no=?,subnet_mask=?,gate_way=?, dns_setups=?, apn_settings =? WHERE ID=1",(set_ip_address,set_port_no,subnet_mask,gate_way,dns_setups,apn_settings))
            else:
                cursor.execute("INSERT INTO lan (set_ip_address, set_port_no, subnet_mask, gate_way, dns_setups, apn_settings) VALUES(?,?,?,?,?,?)",(set_ip_address,set_port_no,subnet_mask,gate_way,dns_setups,apn_settings))
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
    


@app.route("/provision")
def provision():
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
        
        
        return render_template('provision.html', user = user_data,data = data, logg = logss_data)
    return redirect(url_for('login'))
    
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
    



if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", threaded= True)
