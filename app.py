from flask import (Flask, request, render_template, flash, 
                   redirect, url_for, send_from_directory)
import os
from flask_sqlalchemy import SQLAlchemy
from flask_login import (UserMixin, LoginManager, 
                         login_user, login_required, logout_user)                         
from datetime import datetime
from flask_admin import Admin 
from flask_admin.contrib.sqla import ModelView
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from pdf_edit import pdf_edit


# Flaskのインスタンス作成
app = Flask(__name__)
key = os.urandom(13)
app.secret_key = key


# データベースの用意
URI = 'sqlite:///sample.db'
app.config['SQLALCHEMY_DATABASE_URI'] = URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


# DBの初期化コマンド
@app.cli.command('initdb')
def initialize_DB():
    db.create_all()
    
    
# ユーザー管理のモデル
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), nullable=False, unique=True)
    pw = db.Column(db.String(15))


# データ管理のモデル
class Data(db.Model):
    data_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(30), unique=False)
    title = db.Column(db.String(30), unique=False)
    file_path = db.Column(db.String(64), index=True, unique=False)
    date = db.Column(db.DateTime, nullable=False, default=datetime.now())


# ログイン機能の有効化
login_manager = LoginManager()
login_manager.init_app(app)

login_manager.login_view = 'login'
login_manager.login_message = False


# 管理画面の有効化
admin = Admin(app)
admin.add_view(ModelView(User, db.session))


# ユーザーオブジェクトの取得
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)


# サインアップ
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    header = '<Flask>PDF編集アプリケーション'
    if request.method == 'POST':
        username = request.form['username']
        pw = request.form['password']
        register_user = User(
            username=username,
            pw=generate_password_hash(pw, method='sha256')
            )
        db.session.add(register_user)
        db.session.commit()
        flash('サインアップを完了しました')
        return redirect('/login')
    else:
        return render_template('signup.html', header=header)


# ログイン
@app.route('/login', methods=['GET', 'POST'])
def login():
    header = '<Flask>PDF編集アプリケーション'
    if request.method == "POST":
        username = request.form['username']
        pw = request.form['password']
        auth_user = User.query.filter_by(username=username).first()
        if not auth_user:
            flash(
                'ユーザー情報がありません。サインアップしてから利用してください'
                )
            return redirect('/login')
        elif check_password_hash(auth_user.pw, pw):
            login_user(auth_user)
            flash('ログインに成功しました')
            return redirect('/')
        else:
            flash('ログインに失敗しました')
            return redirect('/login')
    else:
        return render_template('login.html', header=header)


# ログアウト
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect('/login')


# 一覧画面
@app.route('/')
@login_required # 順序に注意
def index():
    header = '<Flask>PDF編集アプリケーション'
    all_data = Data.query.all()
    return render_template('index.html', 
                           header=header,
                           all_data=all_data)


# アップロード画面
@app.route('/upload', methods=['GET', 'POST'])
@login_required
def upload():
    if request.method == 'POST':
        name = request.form['name']
        title = request.form['title']
        file = request.files['file']
        file_path = 'static/' + secure_filename(file.filename)
        file.save(file_path)
        register_data = Data(name=name,
                             title=title,
                             file_path=file_path)
        db.session.add(register_data)
        db.session.commit()
        flash('アップロードに成功しました')
        return redirect('/')
    else:
        header = '<Flask>PDF編集アプリケーション'
        return render_template('upload.html', header=header)


# アップロードデータの削除
@app.route('/delete/<int:data_id>')
@login_required
def delete(data_id):
    delete_data = Data.query.get(data_id)
    delete_file = delete_data.file_path
    db.session.delete(delete_data)
    db.session.commit()
    os.remove(delete_file)
    flash('データを削除しました')
    return redirect(url_for('index'))


# PDFの編集
@app.route('/graph/<int:data_id>')   
@login_required
def FileEdit(data_id):
    data = Data.query.get(data_id)
    file_path = data.file_path
    pdf_edit(file_path)
    flash('処理が完了しました')
    return redirect('/') 


# ダウンロード・削除画面
@app.route('/dd')
@login_required
def dd():
    files = os.listdir('download')
    header = '<Flask>PDF編集アプリケーション'
    return render_template('dd.html', header=header, files=files)


# ファイルのダウンロード
@app.route('/download/<string:file>')
@login_required
def download(file):
    return send_from_directory('download', file, as_attachment=True)


# ファイルの削除
@app.route('/output_delete/<string:file>')
@login_required
def output_delete(file):
    delete_file_path = 'download/' + file
    os.remove(delete_file_path)
    return redirect('/')


# サーバーの起動
if __name__ == '__main__':
    app.run(debug=True)
