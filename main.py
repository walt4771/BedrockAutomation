import geoip2.database
from flask import Flask, session, send_file, request, abort, jsonify, render_template, redirect, url_for  # 서버 구현을 위한 Flask 객체 import
from waitress import serve

import zipfile
import os
from datetime import datetime
from time import sleep
import shutil
import subprocess

from mcstatus import BedrockServer

##
## Variables
## 
HOST = "HOST IP"
PATH_PROGRAM_ROOT = 'C:\\Users\\H3\\Documents'
PATH_BACKUPS      = PATH_PROGRAM_ROOT + '\\worldbackups'
PATH_WORLDS       = PATH_PROGRAM_ROOT + '\\bedrock-server\\worlds\\Bedrock level'
PATH_TEMP         = PATH_PROGRAM_ROOT + '\\worldbackups\\temp'
PATH_SERVER_ROOT  = PATH_PROGRAM_ROOT + '\\bedrock-server\\'

PASSWORD_ADMIN = 'ADMIN_KEY'
PASSWORD_USER  = 'USER_KEY'

app = Flask(__name__)  # Flask 객체 선언, 파라미터로 어플리케이션 패키지의 이름을 넣어줌.
app.secret_key = "ENCRYPTION_KEY"

##
## Functions
## 
def getZipList(dir: str):
    file_list = os.listdir(dir)
    return [file for file in reversed(sorted(file_list)) if file.endswith(".zip")]

def server_kill():
    os.system('taskkill /im bedrock_server.exe')

def server_start():
    subprocess.call('cmd /c start ' + PATH_SERVER_ROOT + 'bedrock_server.exe', shell=True)

##
## AUTH
## 
def authenticated(pw: str):
    if (pw == PASSWORD_USER) or (pw == PASSWORD_ADMIN):
        return True
    else:
        return False

@app.before_request
def limit_remote_addr():
    try:
        reader = geoip2.database.Reader('GeoLite2-Country.mmdb')
        country = reader.country(request.remote_addr).country.iso_code

        if country != 'KR':
            print(country)
            abort(403)

    except:
        abort(403)

    if 'pw' not in session:
        session['pw'] = None

@app.route('/logout')
def logout():
    session.pop('pw', None)
    return render_template('login.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        session['pw'] = request.form['pw']
        if authenticated(session['pw']):
            return redirect(url_for('getfilelist'))
        else:
            return render_template('login.html')
    else:
        return render_template('login.html')




##
## Services
## 
@app.route('/getfilelist')
def getfilelist():
    if not authenticated(session['pw']):
        return redirect(url_for('login'))

    # admin
    adminkey = False
    if session['pw'] == PASSWORD_ADMIN:
        adminkey = True

    post = list()

    for index, i in enumerate(getZipList(PATH_BACKUPS)):
        name = i.split("  ")
        a = {
                'index': str(index), 
                'memo': name[2], 
                'time': name[1].replace("-", ":"), 
                'date': name[0],
                'url': '/downloadfile?filenumber=' + str(index)
            }
        post.append(a)

    return render_template('filelist.html', posts=post, admin = adminkey)

@app.route('/downloadfile')
def downloadfile():
    if not authenticated(session['pw']):
        return redirect(url_for('login'))

    filenumber = int(request.args.get('filenumber'))

    return send_file(PATH_BACKUPS + "\\" + getZipList(PATH_BACKUPS)[filenumber], mimetype='application/zip', as_attachment=True)

@app.route('/backup')
def backup():
    if not authenticated(session['pw']):
        print(session['pw'])
        return redirect(url_for('login'))
        
    # isPlayerExists
    server = BedrockServer.lookup(HOST + ":19132")
    if server.status().players_online != 0:
        return "", 403

    current_time = datetime.now()
    current_time_str = current_time.strftime('%Y-%m-%d  %H-%M  ')

    try:
        # getArgs
        if request.args.get('memo'):
            memo = request.args.get('memo')
            print(memo)
            zip_file = zipfile.ZipFile(
                PATH_BACKUPS + "\\" + current_time_str + memo + "  " + ".zip", "w")
        else:
            zip_file = zipfile.ZipFile(
                PATH_BACKUPS + "\\" + current_time_str + "메모 없음  .zip", "w")

        for (path, dir, files) in os.walk(PATH_WORLDS):
            for file in files:
                zip_file.write(os.path.join(path, file), compress_type=zipfile.ZIP_DEFLATED)
        zip_file.close()
    except:
        return jsonify({"something": "went wrong"})

    return redirect(url_for('getfilelist'))

@app.route('/restore')
def restore():
    if not authenticated(session['pw']):
        print(session['pw'])
        return redirect(url_for('login'))

    if session['pw'] != PASSWORD_ADMIN:
        return redirect(url_for('login'))

    shutil.rmtree(PATH_TEMP + '\\Users', ignore_errors=True)
    latest_zip = zipfile.ZipFile(PATH_BACKUPS + "//" + getZipList(PATH_BACKUPS)[0])
    latest_zip.extractall(PATH_TEMP)

    server_kill()

    PATH_TEMP_EXTRACTED = PATH_TEMP + '\\Users\\H3\\Documents\\bedrock-server\\worlds\\Bedrock level'
    shutil.rmtree(PATH_WORLDS, ignore_errors=True)

    shutil.move(PATH_TEMP_EXTRACTED, PATH_WORLDS)
    sleep(3)

    server_start()
    
    return redirect(url_for('getfilelist'))

@app.route('/reset')
def reset():
    if not authenticated(session['pw']):
        print(session['pw'])
        return redirect(url_for('login'))

    if session['pw'] != PASSWORD_ADMIN:
        return redirect(url_for('login'))

    server_kill()
    sleep(2)
    server_start()

    return redirect(url_for('getfilelist'))

if __name__ == "__main__":
    serve(app, host=HOST, port=8000)
    # app.run(debug=False, host=HOST, port=8000)
