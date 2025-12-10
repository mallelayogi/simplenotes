from flask import Flask,request,redirect,render_template,url_for,flash,session,send_file
from flask_session import Session
from otp import genotp
import flask_excel as excel
import mimetypes
import re
from mails import mail_send
from etoken import endata,dcdata
import mysql.connector
from io import BytesIO
mydb = mysql.connector.connect(user='root',host='localhost',password='Yogi@251579',database='notesdb')
app = Flask(__name__)
app.config['SESSION_TYPE']='filesystem'
Session(app)
app.secret_key = 'flask@2025'
excel.init_excel(app)

@app.route('/')
def home():
    return render_template('welcome.html')

@app.route('/register',methods=['GET','POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username').strip()
        email = request.form.get('email').strip()
        password = request.form.get('password').strip()
        try:
            cursor = mydb.cursor(buffered=True)
            cursor.execute('select count(*) from user where usermail=%s',[email])
            email_count = cursor.fetchone()
            cursor.close()
        except Exception as e:
            print(e)
            flash('Could not connect to DB')
            return redirect(url_for('register'))
        else:
            if email_count:
                if email_count[0]==0:
                    gotp = genotp()
                    userdata = {'username':username, 'usermail':email, 'password':password, 'server_otp':gotp}
                    subject = f'OTP verification for login'
                    body = f'use the OTP {gotp} for login.'
                    mail_send(to=email,subject=subject,body=body)
                    flash('OTP is send to your Email')
                    return redirect(url_for('otpverify',server_data=endata(userdata)))
                elif email_count[0]==1:
                    flash('Email already existed please check')
                    return redirect(url_for('register'))
            else:
                flash('Email id not verified in DB')
    else:
        return render_template('register.html')


@app.route('/otpverify/<server_data>',methods=['GET','POST'])
def otpverify(server_data):
    if request.method == 'POST':
        user_otp = request.form['otp1']+request.form['otp2']+request.form['otp3']+request.form['otp4']+request.form['otp5']+request.form['otp6']
        
        try:
            deotp = dcdata(server_data) #userdata = {'username':username, 'usermail':email, 'password':password, 'server_otp':gotp}
        except Exception as e:
            print(e)
            flash('Could not verify OTP')
            return redirect(url_for('register'))
        else:
            if user_otp == deotp['server_otp']:
                try:
                    cursor =mydb.cursor(buffered=True)
                    cursor.execute('insert into user(username,usermail,password) values (%s,%s,%s)',[deotp['username'],deotp['usermail'],deotp['password']])
                    mydb.commit()
                    cursor.close()
                except Exception as e:
                    print(e)
                    flash('DataBase not Connected')
                    return redirect(url_for('otpverify',server_data=server_data))
                else:
                    flash('Details registerd successfully')
                    return redirect(url_for('login'))
            else:
                flask('OTP is Wrong please check')

    return render_template('otpverify.html')


@app.route('/login',methods=['GET','POST'])
def login():
    if request.method == 'POST':
        login_useremail = request.form.get('email').strip()
        login_password = request.form.get('password').strip()
        try:
            cursor = mydb.cursor(buffered=True)
            cursor.execute('select count(*) from user where usermail=%s',[login_useremail])
            email_count=cursor.fetchone()
        except Exception as e:
            print(e)
            flash('Could not connected to DB')
            return redirect(url_for('login'))
        else:
            if email_count[0] == 1:
                cursor.execute('select password from user where usermail=%s',[login_useremail])
                stored_password = cursor.fetchone()
                if stored_password:
                    if stored_password[0]==login_password:
                        session['user'] = login_useremail
                        return redirect(url_for('dashboard'))
                    else:
                        flash('Password Wrong')
                        return redirect(url_for('login'))
                else:
                    flash('Could not verify password')
                    return redirect(url_for('login'))
            elif email_count[0]==0:
                flash('Email not found please check')
                return redirect(url_for('login'))

    return render_template('login.html')


@app.route('/dashboard')
def dashboard():
    if session.get('user'):
        return render_template('dashboard.html')
    else:
        flash('please login')
        return redirect(url_for('login'))


@app.route('/addnotes',methods=['GET','POST'])
def addnotes():
    if session.get('user'):
        if request.method=='POST': 
            title = request.form.get('title').strip()
            description = request.form.get('description').strip()
            try:
                cursor = mydb.cursor(buffered=True)
                cursor.execute('select userid from user where usermail=%s',[session.get('user')])
                user_id = cursor.fetchone()
                if user_id:
                    cursor.execute('insert into notes(notes_title,notes_content,added_by) values(%s,%s,%s)', [title,description,user_id[0]])
                    mydb.commit()
                    cursor.close()
                else:
                    flash('Could not find user')
                    return redirect(url_for('addnotes'))
            except Exception as e:
                print(e)
                flash('Could not find DB')
                return redirect(url_for('addnotes'))
            else:
                flash('Notes added successfully')
        return render_template('addnotes.html')
    else:
        flash('Please login to Add Notes')
        return redirect(url_for('login'))

@app.route('/viewallnotes')
def viewallnotes():
    if session.get('user'):
        try:
            cursor = mydb.cursor(buffered=True)
            cursor.execute('select userid from user where usermail=%s',[session.get('user')])
            user_id = cursor.fetchone()
            if user_id:
                cursor.execute('select notesid,notes_title,created_at from notes where added_by=%s',[user_id[0]])
                allnotes_data = cursor.fetchall()
                cursor.close()
            else:
                flash('Could not get user data to fetch notes')
                return redirect(url_for('dashboard'))
        except Exception as e:
            print(e)
            flash('DB connection error')
            return redirect(url_for('dashboard'))
        else:
            return render_template('viewallnotes.html',allnotes_data=allnotes_data)

    else:
        flash('Please login')
        return redirect(url_for('login'))


@app.route('/viewnotes/<nid>')
def viewnotes(nid):
    if session.get('user'):
        try:
            cursor = mydb.cursor(buffered=True)
            cursor.execute('select userid from user where usermail=%s',[session.get('user')])
            user_id = cursor.fetchone()
            if user_id:
                cursor.execute('select * from notes where added_by=%s and notesid=%s',[user_id[0],nid])
                notes_data = cursor.fetchone()
                cursor.close()
            else:
                flash('Could not get user data to fetch notes')
                return redirect(url_for('dashboard'))
        except Exception as e:
            print(e)
            flash('DB connection error')
            return redirect(url_for('dashboard'))
        else:
            return render_template('viewnotes.html',notes_data=notes_data)

    else:
        flash('Please login')
        return redirect(url_for('login'))

@app.route('/deletenotes/<nid>')
def deletenotes(nid):
    if session.get('user'):
        try:
            cursor = mydb.cursor(buffered=True)
            cursor.execute('select userid from user where usermail=%s',[session.get('user')])
            user_id = cursor.fetchone()
            if user_id:
                cursor.execute('delete from notes where added_by=%s and notesid=%s',[user_id[0],nid])
                mydb.commit()
                cursor.close()
            else:
                flash('Could not get user data to fetch notes')
                return redirect(url_for('dashboard'))
        except Exception as e:
            print(e)
            flash('DB connection error')
            return redirect(url_for('dashboard'))
        else:
            flash('Notes deleted successfully')
            return redirect(url_for('viewallnotes'))
    else:
        flash('Please login')
        return redirect(url_for('login'))


@app.route('/updatenotes/<nid>')    
def updatenotes(nid):
    if session.get('user'):
        try:
            cursor=mydb.cursor(buffered=True)
            cursor.execute('select userid from user where usermail=%s',[session.get('user')])
            user_id=cursor.fetchone()
            if user_id:
                cursor.execute('select * from notes where added_by=%s and notesid=%s',[user_id[0],nid])
                notes_data=cursor.fetchone()
                cursor.close()
            else:
                flash('could not get the user data to found')
                return redirect(url_for('dashboard'))
        except Exception as e:
            print(e)
            flash('DB connection error')
            return redirect(url_for('viewallnotes'))
        else:
            if request.method=='POST':
                update_title = request.form.get('title').strip()
                update_desc = request.form.get('description').strip()
                try:
                    cursor=mydb.cursor(buffered=True)
                    cursor.execute('select userid from user where usermail=%s',[session.get('user')])
                    user_id=cursor.fetchone()
                    if user_id:
                        cursor.execute('update notes set notes_title=%s ,notes_content=%s where added_by=%s and notesid=%s',[update_title, update_desc, user_id[0], nid])
                        mydb.commit()
                        cursor.close()
                    else:
                        flash('could not get the user data to found')
                        return redirect(url_for('updatenotes',nid=nid))
                except Exception as e:
                    print(e)
                    flash('DB connection error')
                    return redirect(url_for('updatenotes',nid=nid))
                else:
                    flash('Notes Updated Successfully')
                    return (redirect('viewnotes',nid=nid))
 
            return render_template('updatenotes.html',notes_data=notes_data)
    else:
        flash('Please login')
        return redirect(url_for('login'))


@app.route('/getexceldata')
def getexceldata():
    if session.get('user'):
        try:
            cursor = mydb.cursor(buffered=True)
            cursor.execute('select userid from user where usermail=%s',[session.get('user')])
            user_id = cursor.fetchone()
            if user_id:
                cursor.execute('select notesid, notes_title, notes_content, created_at from notes where added_by=%s',[user_id[0]])
                allnotes_data = cursor.fetchall()
                cursor.close()
            else:
                flash('Could not get user data to fetch notes')
                return redirect(url_for('dashboard'))
        except Exception as e:
            print(e)
            flash('DB connection error')
            return redirect(url_for('dashboard'))
        else:
            if allnotes_data:
                array_data=[list(i) for i in allnotes_data]
                headings = ['Notes_id', 'Title', 'Content', 'Created_Time']
                array_data.insert(0,headings)
                return excel.make_response_from_array(array_data,'xlsx',filename='notesdata')
            else:
                flash('No notes found to get')
                return redirect(url_for('dashboard'))
    else:
        flash('Please login')
        return redirect(url_for('login'))

@app.route('/uploadfile',methods=['GET','POST'])
def uploadfile():
    if session.get('user'):
        if request.method=='POST':
            filedata = request.files.get('file')
            file_name = filedata.filename
            file_content = filedata.read()
            try:
                cursor = mydb.cursor(buffered=True)
                cursor.execute('select userid from user where usermail=%s',[session.get('user')])
                user_id = cursor.fetchone()
                if user_id:
                    cursor.execute('insert into filesdata(file_name,file_content,added_by) values(%s,%s,%s)',[file_name,file_content,user_id[0]])
                    mydb.commit()
                    cursor.close()
                else:
                    flash('Could not get user data to fetch files')
                    return redirect(url_for('dashboard'))
            except Exception as e:
                print(e)
                flash('DB connection error')
                return redirect(url_for('dashboard'))
            else:
                flash('File Uploaded Successfully..!')
                return redirect(url_for('uploadfile'))
        else:
            return render_template('uploadfile.html')
    else:
        flash('Please login to upload a file')
        return redirect(url_for('login'))


@app.route('/viewallfiles')
def viewallfiles():
    if session.get('user'):
        try:
            cursor = mydb.cursor(buffered=True)
            cursor.execute('select userid from user where usermail=%s',[session.get('user')])
            user_id = cursor.fetchone()
            if user_id:
                cursor.execute('select fileid,file_name,created_at from filesdata where added_by=%s',[user_id[0]])
                allfiles_data = cursor.fetchall()
                cursor.close()
            else:
                flash('Could not get user data to fetch files')
                return redirect(url_for('dashboard'))
        except Exception as e:
            print(e)
            flash('DB connection error')
            return redirect(url_for('dashboard'))
        else:
            return render_template('viewallfiles.html',files_data = allfiles_data)
    else:
        flash('Please login')
        return redirect(url_for('login'))


@app.route('/viewfile/<fileid>')
def viewfile(fileid):
    if session.get('user'):
        try:
            cursor = mydb.cursor(buffered=True)
            cursor.execute('select userid from user where usermail=%s',[session.get('user')])
            user_id = cursor.fetchone()
            if user_id:
                cursor.execute('select fileid,file_name,file_content from filesdata where added_by=%s and fileid=%s',[user_id[0],fileid])
                file_data = cursor.fetchone()
                cursor.close()
            else:
                flash('Could not get user data to fetch files')
                return redirect(url_for('dashboard'))
        except Exception as e:
            print(e)
            flash('DB connection error')
            return redirect(url_for('dashboard'))
        else:
            mime_type, encoding = mimetypes.guess_type(file_data[1])
            bytes_data = BytesIO(file_data[2])
            return send_file(bytes_data,mimetype=mime_type,as_attachment=False,download_name=file_data[1])
    else:
        flash('Please login')
        return redirect(url_for('login'))

@app.route('/downloadfile/<fid>')
def downloadfile(fid):
    if session.get('user'):
        try:
            cursor = mydb.cursor(buffered=True)
            cursor.execute('select userid from user where usermail=%s',[session.get('user')])
            user_id = cursor.fetchone()
            if user_id:
                cursor.execute('select fid,file_name,file_content from filesdata where added_by=%s and fid=%s',[user_id[0],fid])
                file_data = cursor.fetchone()
                cursor.close()
            else:
                flash('Could not get user data to fetch files')
                return redirect(url_for('dashboard'))
        except Exception as e:
            print(e)
            flash('DB connection error')
            return redirect(url_for('dashboard'))
        else:
            mime_type, encoding = mimetypes.guess_type(file_data[1])
            bytes_data = BytesIO(file_data[2])
            return send_file(bytes_data,mimetype=mime_type,as_attachment=True,download_name=file_data[1])
    else:
        flash('Please login')
        return redirect(url_for('login'))


@app.route('/search',methods=['POST'])
def search():
    if session.get('user'):
        search_data = request.form.get('q').strip()
        strg = ['A_Z0-9a-z']
        pattern = re.compile(f'^{strg}',re.IGNORECASE)
        if pattern.match(search_data):
            try:
                cursor = mydb.cursor(buffered=True)
                cursor.execute('select userid from user where usermail=%s',[session.get('user')])
                user_id = cursor.fetchone()
                if user_id:
                    cursor.execute('select notesid,notes_title,created_at from notes where added_by=%s and notes_title like %s',[user_id[0],search_data+'%'])
                    search_result = cursor.fetchall()
                    cursor.close()
                else:
                    flash('Could not get user data')
                    return redirect(url_for('dashboard'))
            except Exception as e:
                print(e)
                flash('DB connection error')
                return redirect(url_for('dashboard'))
            else:
                return render_template('viewallnotes.html',allnotes_data=search_result)
        else:
            flash('Search data is invalid')
            return redirect(url_for('dashboard'))
    else:
        flash('Please login')
        return redirect(url_for('login'))


@app.route('/logout')
def logout():
    if session.get('user'):
        session.pop('user')
        return redirect(url_for('login'))
    else:
        flash('Please login')
        return redirect(url_for('login'))

@app.route('/forgotpassword',methods=['GET','POST'])
def forgotpassword():
    if request.method=='POST':
        email=request.form.get('email').strip()
        try:
            cursor = mydb.cursor(buffered=True)
            cursor.execute('select count(*) from user where usermail=%s',[email])
            email_count=cursor.fetchone()
            cursor.close()
        except Exception as e:
            print(e)
            flash('Could not connected to DB')
            return redirect(url_for('login'))
        else:
            if email_count:
                if email_count[0] == 1:
                    subject = f' Password reset link for notes'
                    body = f'click on the given link to reset password {url_for('newpassword',data=endata(email),_external=True)} for login.'
                    mail_send(to=email,subject=subject,body=body)
                    flash('Reset link is send to your Email')
                    return redirect(url_for('forgotpassword'))
                elif email_count[0]==0:
                    flash('Email not found')
                    return redirect(url_for('register'))
            else:
                flash('Email id not verified in DB')
    return render_template('forgotpassword.html')

@app.route('/newpassword/<data>',methods=['GET','PUT'])
def newpassword(data):
    if request.method=='PUT':
        new_password = request.get_json('password')['password']
        try:
            ddata = dcdata(data)
        except Exception as e:
            print(e)
            flash('Could not verify email')
            return redirect(url_for('login'))
        else:
            try:
                cursor = mydb.cursor(buffered=True)
                cursor.execute('update user set password=%s where usermail=%s',[new_password,ddata])
                mydb.commit()
                cursor.close()
            except Exception as e:
                print(e)
                flash('DB not connected')
                return redirect(url_for('newpassword',data=data))
            else:
                flash('Password reset successfully')
                return 'ok'
    return render_template('newpassword.html',data=data)
                




if __name__ == '__main__':
    app.run(debug=True,use_reloader=True)