from flask import Flask, request
from database_maneger import DatabaseMeneger
from json import dumps,loads
import os
from sys import argv
import threading
from queue import Queue

app = Flask(__name__)

pack_dir = 'C:/Users/yuval/projects/saiber_big_project/source/file_packages'
db_name = "C:\\Users\\yuval\\projects\\saiber_big_project\\source\\file_packages\\data_base.db"

ENCODER_INPUT=Queue()
MAX_SAVE_SIZE = 1000000
host_port = 4002

PERMITION_ERROR="you dont have permition"
PEER_EXISTENS_ERROR='the peer doesnt exist'

@app.route('/return_pack/<hash>', methods=["GET"])
def return_pack (hash):
    ip = request.args.get('ip')
    port = request.args.get('port')
    id = database.get_peer_id(ip, port)


    if id == None:
        return (PEER_EXISTENS_ERROR)
    pack_peer_id=database.foreign_pack_exist(hash)

    if not pack_peer_id:
        return ('I cant find the pack')

    if pack_peer_id !=id:
        return ('you dont have permittion')

    else:
        pack=open(pack_dir+'\\'+hash,'rb')
        text=pack.read()
        pack.close()
        return (text)



@app.route('/del_pack/<hash>', methods=["DELETE"])
def del_pack (hash):
    ip = request.args.get('ip')
    port = request.args.get('port')
    id = database.get_peer_id(ip, port)

    if id == None :
        return (PEER_EXISTENS_ERROR)


    exist = database.foreign_pack_exist(hash)

    if (id!= exist and exist):
        return (PERMITION_ERROR)
    if not id:
        return ("the pack doesnt exist")
    if not exist:
        return ('the pack doesnt exist')
    else:
        print("delete "+pack_dir+'\\'+hash)
        os.remove(pack_dir+'\\'+hash)
        database.del_foregn_packs(hash)
        return (f'deleted {hash}')

@app.route('/ask_per/<hash>', methods=["PUT"])
def ask_per(hash):
    '''ask permition to send file
    also check if there is space'''
    global MAX_SAVE_SIZE

    size = request.args.get('size')
    ip = request.args.get('ip')
    port = request.args.get('port')
    id = database.get_peer_id(ip, port)
    database.add_foregn_packs(id, hash, size)
    #print(ip,port,id,size)

    if id == None:
        return ('the peer doesnt exist')


    current_saves=database.total_save_files_size()
    #try:
    size=int(size)
    if size+current_saves < MAX_SAVE_SIZE:
        database.add_foregn_packs(id, hash, size)


    return str(size+current_saves < MAX_SAVE_SIZE)



@app.route('/put_pack/<hash>', methods=["PUT"])
def put_pack (hash):
    ip = request.args.get('ip')
    port = request.args.get('port')
    id = database.get_peer_id(ip, port)
    if id==None:
        return (PEER_EXISTENS_ERROR)

    have_permittion =database.foreign_pack_exist(hash)
    #print(hash,database.foreign_pack_exist(hash))
    exist=os.path.exists(os.path.join(pack_dir, hash))
    if (not have_permittion ):
        return (PERMITION_ERROR)
    if exist:
        return ('pack exist')
    else:

        with open(os.path.join(pack_dir, hash), "wb") as fp:

            fp.write(request.data)
        return ("writen secsesfully")



@app.route('/disconnect', methods=["DELETE"])
def disconect():
    '''delete all files and data related to this peer'''
    ip = request.args.get('ip')
    port = request.args.get('port')
    id = database.get_peer_id(ip, port)
    if id == None:
        return (PEER_EXISTENS_ERROR)
    else:
        packs_to_delete=database.del_peer(id)
        for pack in packs_to_delete:
            os.remove(pack+ '\\' + hash)
    return "disconected secsesfully"

@app.route('/self/del_file/<hash>', methods=["DELETE"])
def del_file(hash):
    '''del the file from db and return the list of packs to del'''

    pass

@app.route('/self/put_beckup/<path:filename>', methods=["PUT"])
def put_beckup(filename):
    '''create beckup'''
    ENCODER_INPUT.put(filename)
    return ("beckup "+filename)




class Server(threading.Thread):
    def __init__(self,pack_dir1, database1, MAX_SAVE_SIZE1, host_port1,encoder_input):
        global pack_dir
        global database
        global MAX_SAVE_SIZE
        global host_port
        global ENCODER_INPUT

        super(Server, self).__init__()

        pack_dir = pack_dir1
        MAX_SAVE_SIZE = MAX_SAVE_SIZE1
        host_port = host_port1
        database = database1
        ENCODER_INPUT=encoder_input

    def run(self):
        app.run(host='0.0.0.0', port=host_port)





#run(pack_dir,"C:\\Users\\yuval\\projects\\saiber_big_project\\source\\file_packages\\data_base.db",MAX_SAVE_SIZE,host_port)


if __name__=='__main__':
    try:
        (a, host_port, pack_dir, db_name) = argv  # I dont need the first arg
    except:
        pass

    database = DatabaseMeneger(db_name)
    app.run(host='0.0.0.0',port=host_port)




#cd C:\Users\yuval\projects\saiber_big_project\source
#server.py 4001 C:/Users/yuval/projects/saiber_big_project/source/file_packages C:\Users\yuval\projects\saiber_big_project\source\file_packages\data_base.db
