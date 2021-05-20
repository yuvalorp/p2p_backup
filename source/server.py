from flask import Flask, request
import peer_client
import os
import threading
from queue import Queue
from json import dumps
from cryptography.hazmat.primitives import hashes
from random import shuffle,seed
from shutil import rmtree
import logging
app = Flask(__name__)

pack_dir = 'C:/Users/yuval/projects/saiber_big_project/source/file_packages'
db_name = "C:\\Users\\yuval\\projects\\saiber_big_project\\source\\file_packages\\data_base.db"
dir_to_write='C:\\Users\\yuval\\projects\\saiber_big_project\\source\\file_output'
ENCODER_INPUT=Queue()
MAX_SAVE_SIZE = 1000000
port = 4002
IP='127.0.0.1'

PERMITION_ERROR="you dont have permition"
PEER_EXISTENS_ERROR='the peer doesnt exist'

logger = logging.getLogger('peer_server')
logger.setLevel(logging.INFO)
#logger.info

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


@app.route('/self/del_file/<path>', methods=["DELETE"])
def del_file (path):

    pack_list=database.get_parts_of_file(path)

    for pack in pack_list:
        logger.info(peer_client.del_pack(pack['hash'],pack['ip'],pack['port'], IP, port))

    return ('deleted')

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
        return ("the peer doesnt exist")
    if not exist:
        return ('the pack doesnt exist')
    else:
        logger.info("delete "+pack_dir+'\\'+hash)
        os.remove(pack_dir+'\\'+hash)
        database.del_foregn_packs(hash)
        return ('deleted')

@app.route('/ask_per/<hash>', methods=["PUT"])
def ask_per(hash):
    '''ask permition to send file
    also check if there is space'''
    global MAX_SAVE_SIZE

    size = request.args.get('size')
    ip = request.args.get('ip')
    port = request.args.get('port')
    id = database.get_peer_id(ip, port)
    logger.info(str((ip, port, id)))
    database.add_foregn_packs(id, hash, size)

    if id == None:
        return ('the peer doesnt exist')


    current_saves=database.total_save_files_size()
    size=int(size)
    if size+current_saves < MAX_SAVE_SIZE:
        database.add_foregn_packs(id, hash, size)
    logger.info(str((size,current_saves,MAX_SAVE_SIZE,str(size+current_saves < MAX_SAVE_SIZE)) ) )
    return str(size+current_saves < MAX_SAVE_SIZE)


@app.route('/put_pack/<hash>', methods=["PUT"])
def put_pack (hash):
    ip = request.args.get('ip')
    port = request.args.get('port')
    id = database.get_peer_id(ip, port)

    if id==None:
        return (PEER_EXISTENS_ERROR)

    have_permittion =database.foreign_pack_exist(hash)
    exist=os.path.exists(os.path.join(pack_dir, hash))
    if (not have_permittion ):
        return (PERMITION_ERROR)
    if exist:
        return ('pack exist')
    else:

        with open(os.path.join(pack_dir, hash), "wb") as fp:

            fp.write(request.data)

        digest = hashes.Hash(hashes.SHA256())
        digest.update(request.data)
        q = digest.finalize()
        return ("writen secsesfully")


@app.route('/self/disconect', methods=["DELETE"])
def send_disconnect():
    '''delete all files and data related to this peer'''
    logger.info("disconecting")
    list_of_packs=database.all_foregn_packs()

    for j in list_of_packs:

        pack_hash =j[0]
        pack_peer = database.get_ip_from_peer(j[1])
        pack_port = pack_peer['port']
        pack_ip = pack_peer['ip']
        pack_size=j[2]
        pack_peer=database.get_peer_id(pack_ip ,pack_port )
        list_of_peer=database.zero_save_peer()
        shuffle(list_of_peer)

        for peer_id in list_of_peer:
            if peer_id != pack_peer:

                peer = database.get_ip_from_peer(peer_id)
                host_port = peer['port']
                host = peer['ip']

                answer = peer_client.ask_per(pack_size, pack_hash, host, host_port, IP, pack_port)

                if answer == True:
                    pack = open(pack_dir + '\\' + pack_hash, 'rb')
                    text = pack.read()
                    pack.close()


                    answer = peer_client.put_pack(text, pack_hash, host, host_port,pack_ip, pack_port)

                    if answer == b"writen secsesfully" or answer == b"pack exist":
                        peer_client.moved_pack(pack_ip,pack_port, IP, port,pack_hash, host, host_port)#send that the pack moved to a new place


                        break
                    else:
                        logger.info(f"peer {peer} refused answer: {answer}")
                else:
                    logger.info(f"peer {peer} refused answer: {answer}")



    list_of_peer = database.get_all_peers()

    for peer in list_of_peer:
        host_port = peer[1]
        host = peer[0]

        logger.info(peer_client.send_disconnect(host, host_port, IP, port))

    logger.info("deleted_files")
    rmtree (pack_dir)
    logger.info('remove'+str(pack_dir))

    return 'goodbye'

@app.route('/exist', methods=["GET"])
def exist():
    '''delete all files and data related to this peer and find new place for them'''
    return 'true'

@app.route('/moved_pack', methods=["PUT"])
def moved_pack():
    '''delete all files and data related to this peer and find new place for them'''
    host = request.args.get('ip')
    host_port = request.args.get('port')

    pack_hash = request.args.get('hash')

    new_ip = request.args.get('new_ip')
    new_port = request.args.get('new_port')

    id = database.get_peer_id(host, host_port)
    if id == None:
        return (PEER_EXISTENS_ERROR)


    new_id = database.get_peer_id(new_ip,new_port)
    if new_id == None:
        if peer_client.exist(new_ip,new_port)=='true':
            database.add_peer(new_ip,new_port)
        else:
            return (PEER_EXISTENS_ERROR)
    database.update_pack_location(pack_hash,new_id)


    return ('ok')


@app.route('/disconect', methods=["DELETE"])
def disconnect():
    '''delete all files and data related to this peer and find new place for them'''
    host = request.args.get('ip')
    host_port = request.args.get('port')
    id = database.get_peer_id(host, host_port)
    if id == None:
        return (PEER_EXISTENS_ERROR)

    database.del_peer(id)
    return "disconected secsesfully"


@app.route('/self/put_beckup/<path:filename>', methods=["PUT"])
def put_beckup(filename):
    '''create beckup'''
    ENCODER_INPUT.put(filename)
    return ("beckup "+filename)

@app.route('/self/get_files_status/<path:dir_path>', methods=["GET"])
def get_files_status(dir_path):
    global dir_to_write
    '''return list of all the files in a dir and their status'''

    if not os.path.exists(dir_path):
        return ('{}')
    files={}
    beckuped=database.files_in_dir(dir_path)
    in_dir=os.listdir(dir_path)+os.listdir(dir_to_write)
    in_dir2=[os.path.join(dir_path,i) for i in in_dir]


    for f in in_dir2:
        if os.path.isdir(f):
            files[f]="directory"
        else:
            files[f]='doesnt_backuped'

    for f in beckuped:
        if f[0] in in_dir:
            files[f[0]]="bacuped"
        else:
            files[f[0]]="needs_reconstruction"

    ret=dumps(files)
    return(ret)

class Server(threading.Thread):
    def __init__(self,pack_dir1, database1,dir_to_write1, MAX_SAVE_SIZE1, host_port1,encoder_input,ip):
        global dir_to_write
        global pack_dir
        global database
        global MAX_SAVE_SIZE
        global port
        global ENCODER_INPUT
        global IP

        super(Server, self).__init__()

        pack_dir = pack_dir1
        dir_to_write=dir_to_write1
        MAX_SAVE_SIZE = MAX_SAVE_SIZE1
        port = host_port1
        IP=ip
        database = database1
        ENCODER_INPUT=encoder_input

    def run(self):
        app.run(host='0.0.0.0', port=port)



