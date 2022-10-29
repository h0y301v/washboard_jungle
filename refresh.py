from pymongo import MongoClient

client = MongoClient('mongodb://test:test@localhost', 27017)
db = client.dbwash


def refresh_nextday():
    for i in range(0,48):
        db.cards.delete_one({"cards_num":str(i)}) 
    for i in range(240,288):
        db.cards.update_one({"cards_num":str(i)}, {"$set":{"id":"none", "room":"","hash":"FFFFFF","fontcolor":"black"}}) 
    for i in range(48,480):
        db.cards.update_one({"cards_num":str(i)}, {"$set":{"cards_num":str(i-48)}}) 
    for i in range(432,480):
        db.cards.insert_one({"cards_num":str(i) ,"id":"none", "room":"","hash":"FFFFFF","fontcolor":"black"})


refresh_nextday()
