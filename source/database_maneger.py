import logging
import sqlite3 as lite
from time import time
import sys
from json import loads
import threading
import queue


CREATE_FILE_TABLE_QUERY = '''CREATE TABLE IF NOT EXISTS file_table (
     path VARCHAR(512) PRIMARY KEY,
     last_update INTEGER,
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
    def __init__(self,db_file):
        # create logger
        self.logger = logging.getLogger('data base proxy')
        self.logger.setLevel(logging.INFO)

        self.input_q = queue.Queue(maxsize=1)
        self.output_q = queue.Queue(maxsize=1)
        super(Proxy, self).__init__()
        # open database

        self.db_name = db_file
        # 'C:\\Users\\yuval\\projects\\drop_box\\clients_files.db'

    def run(self):
        try:
            self.conn = lite.connect(self.db_name)
        except lite.Error:
            self.logger.critical("the database couldn't open ")
            sys.exit(1)

        self.logger.info("the database opened successfully ")
        self.conn.execute(CREATE_FILE_TABLE_QUERY)
        self.conn.execute(CREATE_PEER_TABLE_QUERY)
        self.conn.execute(CREATE_PACK_TABLE_QUERY)
        self.conn.execute(CREATE_FOREIGN_PACK_TABLE_QUERY)

        self.conn.commit()


        while True:
            (request, parameters)=self.input_q.get()
            #print(request,'  ', parameters)

            answer = self.conn.execute(request, parameters)
            self.conn.commit()
            self.output_q.put(answer.fetchall())



class DatabaseMeneger:
    def __init__(self,db_file,peers_list_file,my_peer):
        """
        meneger the sql database
        """
        #create logger
        self.logger = logging.getLogger('data base')
        self.logger.setLevel(logging.INFO)

        self.proxy = Proxy(db_file)
        self.proxy.start()
        self.input_q = self.proxy.input_q
        self.output_q=self.proxy.output_q

        self.load_peers(peers_list_file,my_peer)

    def db_request(self,request,parameters=tuple()):
        self.input_q.put([request,parameters])
        return(self.output_q.get())

    def db_list_request(self, request_list):
        '''
        get list of request
        '''

        for request in request_list:
            if type(request) == str:
                self.input_q.put([request, tuple()])
                answer = self.output_q.get()

            elif len(request) == 2:

                self.input_q.put([request[0], request[1]])
                answer = self.output_q.get()

        return answer

    def load_peers(self,peers_file_path,my_peer):
        peers_file=open(peers_file_path)
        peer_list=loads(peers_file.read())
        for peer in peer_list:
            if peer[0]!=my_peer[0] or peer[1]!=int(my_peer[1]):

                self.add_peer(peer[0],peer[1])

    def get_parts_of_file(self,file_path):

        arr=self.db_request('''SELECT hash,file_path,size, pack_number,peer_table._id , ip, port
        FROM (SELECT * FROM packs_table WHERE file_path=(?)) INNER JOIN peer_table
        WHERE peer_id = peer_table._id ORDER BY pack_number''',(file_path,))

        arr2=[]
        for a in arr:
            arr2.append({'hash':a[0],'file_path':a[1],'size':a[2],'pack_number':a[3] , 'ip':a[5], 'port':a[6]})

        return (arr2)

    def get_peer_id(self,ip,port):
        exist_in_database = self.db_request('''SELECT _id FROM peer_table WHERE ip=? AND port=? LIMIT 1''',(ip,port))
        a=exist_in_database

        if a!=[]:

            return (a[0][0])

    def file_beckup_exist(self,path):
        '''
        if exist return last update else return False
        '''
        exist_in_database = self.db_request('''SELECT path,last_update FROM file_table WHERE path=? LIMIT 1''', (path,))
        if (exist_in_database == []):
            return (None)
        else:
            return (exist_in_database[0][1])

    def pack_exist(self,hash):
        exist_in_database = self.db_request('''SELECT hash FROM packs_table WHERE hash=? LIMIT 1''',
                                            (hash,))
        return(exist_in_database != None)

    def add_file(self,file_path,proportion,file_date):
        '''
        add file to database
        the hash list also include the peer ip
        last_update- last time updated the beckup
        '''
        if self.file_beckup_exist(file_path) ==None:

            self.db_request('''INSERT INTO file_table (path,last_update, proportion_original,proportion_reed,file_date)
                            VALUES (?,?,?,?,?)''',
                                (file_path,time(),proportion["normal"],proportion["reed5"],file_date))

    def add_pack(self,file_path,hash,peer_id,pack_number,pack_size):
        if self.db_request('''SELECT hash FROM packs_table WHERE hash=? LIMIT 1''', (hash,))==[]:
            self.db_request(
                '''INSERT INTO packs_table (hash,file_path, peer_id,pack_number,size) VALUES (?,?,?,?,?)''',
                (hash, file_path, peer_id, pack_number, pack_size))
        else: return('pack exist in database')

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


    def update_pack_location(self,pack_hash,new_place):
        self.db_request(
            '''UPDATE packs_table SET peer_id=(?) WHERE hash=(?)''',
            (new_place, pack_hash))

    def update_dir_time(self,dir_path):
        self.db_request(
            '''UPDATE packs_table SET last_update=(?) WHERE path=(?)''',
            (time(), dir_path))

    def del_dir(self,dir_path):
        a = self.db_request(
            "SELECT * from file_table WHERE path LIKE (?)", (dir_path + '[/\]%'))

    def del_peer(self,peer_id):
        pass

        packs_to_delete=self.db_request('''SELECT hash FROM foregn_packs_table WHERE peer_id=?''', (peer_id,))

        #deleting
        self.db_list_request([('''DELETE FROM packs_table WHERE peer_id=?''', (peer_id,)),
                              ('''DELETE FROM foregn_packs_table WHERE peer_id=?''', (peer_id,)),
                              ('''DELETE FROM peer_table WHERE _id=?''', (peer_id,))])
        return(packs_to_delete)

    def get_ip_from_peer(self,peer_id):
        #print(peer_id)
        a=self.db_request('''SELECT ip,port FROM peer_table WHERE _id=? LIMIT 1''', (peer_id,))
        dic={}
        dic["ip"]=a[0][0]
        dic["port"]=a[0][1]

        return(dic)

    def del_file(self,file_path):
        hash_list=self.get_parts_of_file(file_path)

        for pack in hash_list:
            self.db_request('''DELETE FROM packs_table WHERE hash=?''',(pack['hash'],))

        self.db_request('''DELETE FROM file_table WHERE path=?''', (file_path,))

    def del_foregn_packs(self,hash):
        self.db_request('''DELETE FROM foregn_packs_table WHERE hash=?''', (hash,))

    def add_foregn_packs(self,peer_id,pack_hash,size):
        ex=self.foreign_pack_exist(pack_hash)
        if not ex:
            self.db_request(
                '''INSERT INTO foregn_packs_table (hash,peer_id,size) VALUES (?,?,?)''',
                (pack_hash, peer_id,size))

    def total_save_for_peer(self):
        '''return the total save file in every peer'''
        a=self.db_request(
            '''SELECT peer_id,sum(size) FROM packs_table GROUP BY peer_id ORDER BY sum(size)''')
        return (a)

    def zero_save_peer(self):
        '''return the peers that dosent save your data'''
        a=self.db_request(
            ''' SELECT _id as peer_id FROM peer_table EXCEPT SELECT peer_id FROM packs_table''')
        return ([i[0] for i in a])

    def all_foregn_packs(self):
        a=self.db_request(
            ''' SELECT * FROM foregn_packs_table''')
        return (a)

    def saves_in_peer(self,peer_id):
        '''return all packs that saved in peer'''
        a = self.db_request('''SELECT hash FROM packs_table WHERE peer_id=(?) ''',(peer_id,))
        return(a)

    def total_save_files_size(self):
        '''return the total save file for all peers'''
        a = self.db_request(
            '''SELECT sum(size) FROM packs_table ''')
        ans=a[0][0]
        if ans==None:
            ans=0
        return (ans)

    def files_in_dir(self,dir_path):
        a=self.db_request(
            "SELECT * from file_table WHERE path LIKE (?)",(dir_path+'[/\]%',))
        return (a)

    def foreign_pack_exist(self,hash):
        '''if exist return the peer id'''

        exist_in_database = self.db_request('''SELECT hash,peer_id FROM foregn_packs_table WHERE hash=? LIMIT 1''',
                                            (str(hash),))

        if (exist_in_database !=[] and exist_in_database !=None):
            #if exist_in_database[0][1]:self.logger.error('peer_id=None')

            return exist_in_database[0][1]
        else:

            return False

    def get_all_files(self):
        return self.db_request('''SELECT path,last_update FROM file_table''')

    def get_all_peers(self):
        return self.db_request('''SELECT ip,port FROM peer_table''')



