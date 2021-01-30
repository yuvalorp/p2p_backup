import logging
import sqlite3 as lite
from os import path
from time import time
import sys
from threading import Lock
import threading
import queue

CREATE_FILE_TABLE_QUERY = '''CREATE TABLE IF NOT EXISTS file_table (
     path VARCHAR(512) PRIMARY KEY,
     last_update INTEGER,
     size INTEGER,
     proportion_original INTEGER,
     proportion_reed INTEGER, 
     file_date INTEGER  

     )'''

CREATE_PEER_TABLE_QUERY='''CREATE TABLE IF NOT EXISTS peer_table (
    _id INTEGER PRIMARY KEY,
    ip VARCHAR(30),
    port INTEGER

    )'''

CREATE_PACK_TABLE_QUERY='''CREATE TABLE IF NOT EXISTS packs_table (
    hash VARCHAR(260) PRIMARY KEY,
    file_path VARCHAR(512),
    peer_id INTEGER, 
    pack_number INTEGER,
    size INTEGER,
    FOREIGN KEY(file_path) REFERENCES file_table(file_path),
    FOREIGN KEY(peer_id) REFERENCES peer_table(_id))
    '''

CREATE_FOREIGN_PACK_TABLE_QUERY='''CREATE TABLE IF NOT EXISTS foregn_packs_table (
    hash VARCHAR(260) PRIMARY KEY,
    peer_id INTEGER,
    size INTEGER, 
    FOREIGN KEY(peer_id) REFERENCES peer_table(_id))'''


class Proxy(threading.Thread):
    def __init__(self,q,db_file):
        # create logger
        self.logger = logging.getLogger('data base proxy')
        self.logger.setLevel(logging.INFO)

        self.input_q = queue.Queue(maxsize=1)
        super(Proxy, self).__init__()
        # open database

        file_name = db_file
        # 'C:\\Users\\yuval\\projects\\drop_box\\clients_files.db'
        try:
            self.conn = lite.connect(file_name)
        except lite.Error:
            self.logger.critical("the database couldn't open ")
            sys.exit(1)
        finally:
            if self.conn:
                self.logger.info("the database opened successfully ")

                self.db_list_request([CREATE_FILE_TABLE_QUERY,
                                      CREATE_PEER_TABLE_QUERY,
                                      CREATE_PACK_TABLE_QUERY,
                                      CREATE_FOREIGN_PACK_TABLE_QUERY])
    def run(self):
        while True:
            self.input_q.get()



class DatabaseMeneger:
    def __init__(self, db_file):
        """
        meneger the sql database
        """
        #create logger
        self.logger = logging.getLogger('data base')
        self.logger.setLevel(logging.INFO)

        self.db_lock = Lock()

        #open database


        file_name = db_file
        # 'C:\\Users\\yuval\\projects\\drop_box\\clients_files.db'
        try:
            self.conn = lite.connect(file_name)
        except lite.Error:
            self.logger.critical("the database couldn't open ")
            sys.exit(1)
        finally:
            if self.conn:
                self.logger.info("the database opened successfully ")

                self.db_list_request([CREATE_FILE_TABLE_QUERY,
                                      CREATE_PEER_TABLE_QUERY,
                                      CREATE_PACK_TABLE_QUERY,
                                      CREATE_FOREIGN_PACK_TABLE_QUERY])

    def db_request(self,request,parameters=tuple()):
        self.db_lock.acquire()
        answer=self.conn.execute(request, parameters)
        self.conn.commit()
        self.db_lock.release()
        return answer

    def db_list_request(self,request_list):
        '''
        get list of request
        '''
        self.db_lock.acquire()
        for request in request_list:
            if type(request) == str:


                answer=self.conn.execute(request)
            elif len(request) == 2:
                answer=self.conn.execute(request[0],request[1])
            self.conn.commit()
        self.db_lock.release()
        return answer

    def get_parts_of_file(self,file_path):

        #arr=self.conn.execute('''SELECT * FROM packs_table WHERE file_path=? ORDER BY pack_number''', (file_path,)).fetchall()
        arr=self.db_request('''SELECT hash,size, pack_number,peer_table._id , ip, port
        FROM (SELECT * FROM packs_table WHERE file_path=(?)) INNER JOIN peer_table
        WHERE peer_id = peer_table._id ''',(file_path,)).fetchall()

        arr2=[]
        hash_list=[]
        for a in arr:
            arr2.append({'hash':a[0],'file_path':a[1],'size':a[2],'pack_number':a[3] ,'pack_id':a[4] , 'ip':a[5], 'port':a[6]})
            hash_list.append(a[0])

        return (arr2)

    def get_peer_id(self,ip,port):
        exist_in_database = self.db_request('''SELECT _id FROM peer_table WHERE ip=? AND port=? LIMIT 1''',(ip,port))
        a=exist_in_database.fetchone()
        if a!=None:
            return (a[0])

    def file_beckup_exist(self,path):
        '''
        if exist return last update else return False
        '''
        exist_in_database = self.db_request('''SELECT path,last_update FROM file_table WHERE path=? LIMIT 1''', (path,)).fetchone()
        if (exist_in_database == None):
            return (None)
        else:
            return (exist_in_database[1])

    def pack_exist(self,hash):
        exist_in_database = self.db_request('''SELECT hash FROM packs_table WHERE hash=? LIMIT 1''',
                                            (hash,)).fetchone()
        return(exist_in_database != None)

    def add_file(self,hash_list,file_path,size,proportion,file_date,pack_size):
        '''
        add file to database
        the hash list also include the peer ip, port
        last_update- last time updated the beckup
        '''
        self.db_request('''INSERT INTO file_table (path,last_update,size, proportion_original,proportion_reed,file_date)
                            VALUES (?,?,?,?,?,?)''',
                            (file_path,time(),size,proportion["original"],proportion["reed"],file_date))

        i=0

        for pack in hash_list:

            self.db_request(
                '''INSERT INTO packs_table (hash,file_path,peer_id, pack_number,size) VALUES (?,?,?,?,?)''',
                (pack['hash'],file_path,pack['peer_id'],i,pack_size))

            i+=1

    def add_peer(self,ip,port):
        '''
        return the new peer_id
        '''
        id=self.get_peer_id(ip,port)
        if id==None:

            self.db_request('''INSERT INTO peer_table (ip,port)
                                        VALUES (?,?)''',(ip,port))

            return(self.db_request('''SELECT last_insert_rowid()'''))
        else:
            return(id)

    def del_peer(self,peer_id):
        packs_to_delete=self.db_request('''SELECT hash FROM foregn_packs_table hash WHERE peer_id=?''', (peer_id))
        #deleting
        self.db_list_request([('''DELETE FROM peer_table WHERE _id=?''', (peer_id)),
                              ('''DELETE FROM packs_table WHERE peer_id=?''', (peer_id)),
                              ('''DELETE FROM foregn_packs_table WHERE peer_id=?''', (peer_id))])
        return(packs_to_delete)

    def get_ip_from_peer(self,peer_id):
        print(peer_id)

        a=self.db_request('''SELECT ip,port FROM peer_table WHERE _id=? LIMIT 1''', (peer_id,)).fetchone()
        dic={}
        dic["ip"]=a[0]
        dic["port"]=a[1]

        return(dic)

    def del_file(self,file_path):
        hash_list=self.get_parts_of_file(file_path)

        for pack in hash_list:
            self.db_request('''DELETE FROM pack_table WHERE hash=?''',(pack['hash'],))

        self.db_request('''DELETE FROM file_table WHERE path=?''', (file_path,))

    def del_foregn_packs(self,hash):
        self.db_request('''DELETE FROM foregn_packs_table WHERE hash=?''', (hash,))

    def add_foregn_packs(self,peer_id,pack_hash,size):
        if not self.foreign_pack_exist(pack_hash):
            self.db_request(
                '''INSERT INTO foregn_packs_table (hash,peer_id,size) VALUES (?,?,?)''',
                (pack_hash, peer_id,size))

    def total_save_for_peer(self):
        '''return the total save file in every peer'''
        a=self.db_request(
            '''SELECT peer_id,sum(size) FROM packs_table GROUP BY peer_id ORDER BY sum(size)''')
        return (a.fetchall())

    def total_save_files_size(self):
        '''return the total save file for all peers'''
        a = self.db_request(
            '''SELECT sum(size) FROM packs_table ''')
        return (a.fetchone()[0])

    def files_in_dir(self,dir_path):
        a=self.db_request(
            "SELECT * from file_table WHERE path LIKE (?)",(dir_path+'[/\]%'))
        return (a.fetchall())
    def foreign_pack_exist(self,hash):
        '''if exist return the peer id'''

        exist_in_database = self.db_request('''SELECT hash,peer_id FROM foregn_packs_table WHERE hash=? LIMIT 1''',
                                            (str(hash),)).fetchone()
        if (exist_in_database != None):
            return exist_in_database[1]
        else:
            return False

if __name__=='__main__':
    data_base=DatabaseMeneger("C:\\Users\\yuval\\projects\\saiber_big_project\\source\\file_packages\\data_base.db")

    for i in range(10):
        data_base.add_peer('123.243.345.456',5000+i)

    data_base.add_file([{'hash':'23324','peer_id':900},{'hash':'7324','peer_id':2},{'hash':'983433424','peer_id':4},{'hash':'3124','peer_id':5}],
                       'c/f',2000000,{"original":16,"reed":9},time(),1024)

    print(data_base.get_parts_of_file('c/d'))
    print(data_base.get_peer_id('123.243.345.456',5555))
    print(data_base.file_beckup_exist('c/d'))
    print(data_base.get_ip_from_peer(3))
    data_base.add_foregn_packs(3,'gd23rwdew',1024)
    #print(data_base.total_save_files_size())
    print(data_base.foreign_pack_exist('test_pac'))



