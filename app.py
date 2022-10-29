from flask_jwt_extended import *
from datetime import datetime
from datetime import time
from datetime import timedelta
import time
import requests
from functools import wraps
from flask import Flask, render_template, jsonify, request, redirect, url_for, make_response, Response, current_app
from pymongo import MongoClient
import random
import hashlib
import jwt
import locale

locale.setlocale(locale.LC_ALL,'')

app = Flask(__name__)
client = MongoClient('mongodb://test:test@localhost', 27017)
db = client.dbwash
SECRET_KEY = 'clean'




@app.route('/')
def home():
    if request.cookies.get('mytoken'): # 토큰이 있는 경우
        return redirect(url_for('washboard'))

    return render_template('login.html')

@app.route('/signup')
def signup():
    if request.cookies.get('mytoken'): # 토큰이 있는 경우
        return redirect(url_for('washboard'))
    return render_template('signup.html')


# decorator 함수
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwagrs):
        access_token = get_access_token() # 요청의 토큰 정보를 받아옴
        if access_token is not None: # 토큰이 있는 경우
            print("토큰이 있는 경우")
            payload = check_access_token(access_token) # 토큰 유효성 확인
            if payload is None: # 토큰 decode 실패 시 401 반환
                return render_template('login.html')
        else: # 토큰이 없는 경우 401 반환
            print("토큰이 없는 경우")
            return render_template('login.html')

        return f(*args, **kwagrs)

    return decorated_function



@app.route('/washboard')
@login_required
def washboard():
    cards = db.cards
    user = db.users
    data = list(cards.find())
    now = [[(datetime.today()+timedelta(days=i)).strftime('%m-%d'), (datetime.today()+timedelta(days=i)).strftime("%a")] for i in range(4)]
    

    token_receive = request.cookies.get('mytoken')
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
        user_info = db.cards.find_one({"id": payload['id']})
        user_color = [db.users.find_one({"id": payload['id']})['hash'], db.users.find_one({"id": payload['id']})['fontcolor']]
        return render_template('washboard.html', title="세탁예약",id=user_info, data=data, current_time = now, user_data=user_color)
    except jwt.ExpiredSignatureError:
        return render_template('login.html')
    except jwt.exceptions.DecodeError:
        return render_template('login.html')

# token을 decode하여 반환함, decode에 실패하는 경우 payload = None으로 반환
def check_access_token(access_token):
    try:
        payload = jwt.decode(access_token, SECRET_KEY, "HS256")
        now = datetime.now() 
        if payload['exp'] < datetime.timestamp(now):  # 토큰이 만료된 경우
            payload = None
    except jwt.InvalidTokenError:
        payload = None
    
    return payload

@app.route('/api/login', methods=['POST'])
def sign_in():
    # 로그인
    username_receive = request.form['username_give']
    password_receive = request.form['password_give']  # 유저가 아이디 pw 입력
    pw_hash = hashlib.sha256(password_receive.encode('utf-8')).hexdigest()  # 유저가 입력한 pw를 해쉬화
    result = db.users.find_one({'id': username_receive, 'pw': pw_hash}) 
    # 아이디와 유저가 입력한 해쉬화된 pw가 DB에 저장되어 있는 해쉬화된 pw와 일치하는지 확인 
    if result:  # 일치한다면
        payload = {
            'id': username_receive,
            'exp': datetime.utcnow() + timedelta(seconds=60 * 60 * 24)  # 로그인 24시간 유지
        } 
        # 유저 아이디와 유효기간을 담고 있는 payload 생성
        
        token = jwt.encode(payload, SECRET_KEY, algorithm='HS256').decode('utf-8')
        resp = make_response(render_template("login.html"))
        resp.set_cookie('mytoken',token) 
        # jwt기반 토큰 생성
        return resp
        # 찾지 못하면
    else:
        return jsonify({'result': 'fail', 'msg': '아이디/비밀번호가 일치하지 않습니다.'})

@app.route('/showday', methods=['GET'])
def read_memos():
    result = list(db.cards.find({}, {'_id': 0}))
    return jsonify({'result': 'success', 'cards': result})

def get_access_token():
    return request.cookies.get('mytoken')


@app.route('/api/name', methods=['POST'])
def check():
    name_receive = request.form['name_give']
    user = list(db.users.find({'id':name_receive}))
    if user:
        return "1"
    else:
        return "0"
        
@app.route('/api/register', methods=['POST'])
def sign_up():
    username_receive = request.form['username_give']
    password_receive = request.form['password_give']
    room_receive = request.form['room_give']
    password_hash = hashlib.sha256(password_receive.encode('utf-8')).hexdigest() # password 해쉬화 함수
    color_hash = hashlib.sha256((username_receive+password_receive).encode('utf-8')).hexdigest()
    
    r = int(color_hash[0:2],16)
    g = int(color_hash[2:4],16)
    b = int(color_hash[4:6],16)
    yiq = ((r * 299) + (g * 587) + (b * 114)) / 1000
    fontcolor='000000' if (yiq >= 120) else 'FFFFFF'

    doc = {
        "id": username_receive,  # 아이디
        "pw": password_hash,  # 비밀번호
        "room":room_receive,
        "hash":color_hash[0:6],
        "fontcolor":fontcolor
    }
    db.users.insert_one(doc) # 유저가 입력한 아이디 pw 닉네임을 DB에 저장

    return render_template('login.html')


@app.route('/api/book', methods=['POST'])
def book():
    card_id = request.form['card_id']
    card_num = request.form['card_num']
     
    if get_access_token(): # 토큰이 있는 경우
        payload = check_access_token(get_access_token()) # 토큰 유효성 확인
        if payload is None: 
            return render_template('login.html')
    else: # 토큰이 없는 경우 401 반환
        return render_template('login.html')

    usercard_all= db.cards.find({"id": payload['id']})
    usercard_all = list(usercard_all)
    if db.cards.find_one({'cards_num':card_num})['id'] == 'none' :
        if len(usercard_all) >= 1 and (int(usercard_all[0]['cards_num'])-(int(card_num))>1 or int(usercard_all[-1]['cards_num'])-(int(card_num))<-1 ) :
            return jsonify({'result': 'fail', 'msg': '연속된 시간으로 예약해주세요'})
        # if usercard_all
        elif len(usercard_all) >=4 and (card_id != payload['id']):
            return jsonify({'result': 'fail', 'msg': '본인의 예약시간이 꽉 찼습니다.'})

        card_hash= db.users.find_one({"id": payload['id']})['hash']
        card_fontcolor= db.users.find_one({"id": payload['id']})['fontcolor']
        card_room = db.users.find_one({"id": payload['id']})['room']
        db.cards.update_one({'cards_num': card_num}, {'$set': {'id': payload['id'] ,'room':card_room,'hash':card_hash, 'fontcolor':card_fontcolor}})
        return jsonify({'result': 'success', 'msg': '예약'})

    elif card_id == payload['id']:
        indexfront = int(card_num) - int(usercard_all[0]['cards_num'])
        indexback = int(usercard_all[-1]['cards_num']) - int(card_num)
        if indexfront>=indexback:
            i = indexfront
            j = len(usercard_all)
        else:
            i = 0
            j = len(usercard_all) - indexback
        for k in range(i,j):
            newCardNum = usercard_all[k]['cards_num']
            db.cards.update_one({'cards_num': newCardNum}, {'$set': {'id': "none",'room':"", 'hash':"FFFFFF", 'fontcolor':"black"}})
        return jsonify({'result': 'success', 'msg': '취소'})
    else:
        return jsonify({'result': 'fail', 'msg': '이미 예약된 시간입니다.', 'refresh': 1})

        

#예약 현황 정보 쿼리
@app.route('/booked', methods=['POST'])
def booked():
    user_id = request.form['user_id']
    usercard_all= db.cards.find({"id": user_id})
    usercard_all = list(usercard_all)
    a=[]
    now = []
    for uc in usercard_all:
        a.append(uc['cards_num'])
    
    if a:
        # now = [월일,시작시간,끝나는시간,요일]
        now = [(datetime.fromtimestamp(int(time.time())-int(time.time())%86400-32400)+timedelta(days=(int(min(a)))%240/48)).strftime('%H:%M'),(datetime.fromtimestamp(int(time.time())-int(time.time())%86400-32400)+timedelta(days=(int(max(a)))%240/48 )+timedelta(minutes=30)).strftime('%H:%M'), (datetime.fromtimestamp(int(time.time())-int(time.time())%86400-32400)+timedelta(days=(int(min(a)))%240/48 )).strftime("%m/%d"), (datetime.fromtimestamp(int(time.time())-int(time.time())%86400-32400)+timedelta(days=(int(min(a)))%240/48 )).strftime("%a")] 
        return jsonify({'min': min(a),'now':now})
    else:
        return jsonify({'result':'none'})

#없는 경로 접속시 리디렉션
@app.errorhandler(404)
def page_not_found(error):
    if get_access_token():
        return redirect(url_for('washboard'))
    else:
        return render_template('login.html')


if __name__ == '__main__':
	app.run('0.0.0.0', port=80, debug=True)
