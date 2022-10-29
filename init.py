import requests
from pymongo import MongoClient

client = MongoClient('mongodb://test:test@localhost', 27017)
db = client.dbwash

def insert_all():
#    db.cards.drop()
    for i in range(48*10):
        db.cards.insert_one({"cards_num":str(i) ,"id":"none", "room":"","hash":"FFFFFF","fontcolor":"black"})
   

insert_all()

#파일 입출력으로 today랑 파일내용 다르면 -> 1분마다 체크해서 -> db 18칸 앞으로 밀고, 18칸 빈칸 만들어주기
