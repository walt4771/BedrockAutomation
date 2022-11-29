import geoip2.database
from flask import Flask, send_file, request, abort, jsonify, render_template, redirect, url_for  # 서버 구현을 위한 Flask 객체 import
import zipfile
import os
from datetime import datetime
from mcstatus import BedrockServer

HOST = "192.168.0.12"

app = Flask(__name__)  # Flask 객체 선언, 파라미터로 어플리케이션 패키지의 이름을 넣어줌.

@app.before_request
def limit_remote_addr():

    try:
        reader = geoip2.database.Reader('mmdb file')
        country = reader.country(request.remote_addr).country.iso_code

        print(country)
        if country != 'KR':
            abort(403)
    except:
        abort(403)


@app.route('/getfilelist')  
def getfilelist(): 
    path_dir = 'C:\\Users\\Intel\\Documents\\worldbackups'
    file_list = os.listdir(path_dir)
    file_list_zip = [file for file in reversed(sorted(file_list)) if file.endswith(".zip")]

    post = list()

    for index, i in enumerate(file_list_zip):
        name = i.split("  ")
        a = {'index': str(index), 'memo': name[2], 'time': name[1].replace("-", ":"), 'date': name[0],
             'url': '/downloadfile?filenumber=' + str(index)}
        post.append(a)

    return render_template('filelist.html', posts=post)


@app.route('/downloadfile')
def downloadfile():
    # filename = "Bedrock level 2022-07-12 10-51-45.zip"
    filenumber = int(request.args.get('filenumber'))

    # filelist = getfilelist.get(self)

    path_dir = 'C:\\Users\\Intel\\Documents\\worldbackups\\'
    file_list = os.listdir(path_dir)
    file_list_zip = [file for file in reversed(sorted(file_list)) if file.endswith(".zip")]

    return send_file(path_dir + file_list_zip[filenumber], mimetype='application/zip', as_attachment=True)


@app.route('/backup')
def backup():
    # isPlayerExists
    server = BedrockServer.lookup(HOST + ":19132")
    if server.status().players_online != 0:
        return "", 403

    file_path = 'C:\\Users\\Intel\\Documents\\bedrock-server\\worlds\\Bedrock level'

    current_time = datetime.now()
    current_time_str = current_time.strftime('%Y-%m-%d  %H-%M  ')

    try:
        # getArgs
        if request.args.get('memo'):
            memo = request.args.get('memo')
            print(memo)
            zip_file = zipfile.ZipFile(
                "C:\\Users\\Intel\\Documents\\worldbackups" + "\\" + current_time_str + memo + "  " + ".zip", "w")
        else:
            zip_file = zipfile.ZipFile(
                "C:\\Users\\Intel\\Documents\\worldbackups" + "\\" + current_time_str + "메모 없음  .zip", "w")

        for (path, dir, files) in os.walk(file_path):
            for file in files:
                zip_file.write(os.path.join(path, file), compress_type=zipfile.ZIP_DEFLATED)
        zip_file.close()
    except:
        return jsonify({"something": "went wrong"})

    return redirect(url_for('getfilelist'))


if __name__ == "__main__":
    app.run(debug=False, host='192.168.0.12', port=8000)
