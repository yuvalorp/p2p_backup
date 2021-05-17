from reedsolo import RSCodec
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import hashes
import threading
import queue
from os import path,urandom
import logging

from time import time
import  database_maneger
import peer_client
from random import shuffle
PACKAGE_SIZE = 1024  # size of every package to send

class Splitter(threading.Thread):
    # split the file to small packages

    def __init__(self, package_size, size_files_input=100, size_results=20, packeg_n=16):
        """
        create logger
        """
        self.logger = logging.getLogger('splitter')
        self.logger.setLevel(logging.INFO)

        if size_results < packeg_n:
            self.logger.critical("size_results<packeg_n -> the next levels will be anable to run")
            raise RuntimeError()

        self.package_size = package_size
        self.files_input = queue.Queue(maxsize=size_files_input)
        self.packeg_n = packeg_n
        self.packeg_q = queue.Queue(maxsize=size_results)

        self.running = False

        super(Splitter, self).__init__()

    def stop(self):
        self.running = False

    def run(self):
        self.logger.info("runing")

        self.running = True
        while self.running:
            # self.results.append(n)
            file_path = self.files_input.get()

            file = open(file_path, 'rb')
            s = None
            s1 = ""
            p_counter = 0
            packege_list = []

            while s != b"":
                s = file.read(self.package_size)


                s1 = s + b"\x00" * (self.package_size - len(s))
                packege_list.append(s1)

                # self.packeg_q.put({"packege":s,"path":file_path})
                p_counter += 1


                if p_counter == self.packeg_n:
                    #self.logger.info(f'create {len(packege_list)} packs')
                    self.packeg_q.put({"packages": packege_list, "path": file_path})
                    packege_list = []
                    p_counter = 0


            file.close()

            while p_counter != (self.packeg_n):

                p_counter += 1
                packege_list.append(b"\x00" * self.package_size)
            #self.logger.info(f'create {len(packege_list)} packs')


            self.packeg_q.put({"packages": packege_list, "path": file_path})
            self.packeg_q.put("file end")

            self.logger.info("end file: " + file_path)


class AddReed5(threading.Thread):
    """
    add reed5 to the packages
    packeg_n-> number of packages to add to them reed5 at once
    packeg_q->Queue evrey node is Dictionary that have
    {"packages":list of the text of the packages,"path":the path of the file}
    or "file end"
    """

    def __init__(self, PACKEGE_SIZE, NUMBER_OF_ERRORS, packeg_q, size_results=10, packeg_n=16):
        # create logger
        self.logger = logging.getLogger('add_reed')
        self.logger.setLevel(logging.INFO)

        self.PACKEGE_SIZE = PACKEGE_SIZE
        self.NUMBER_OF_ERRORS = NUMBER_OF_ERRORS
        self.rsc = RSCodec(NUMBER_OF_ERRORS)

        #give information about how much the reed will be able to fix
        #maxerrors, maxerasures = self.rsc.maxerrata(verbose=True)
        #self.logger.info("This codec can correct up to"+maxerrors+" errors and"+ maxerasures+" erasures independently")

        self.packeg_q = packeg_q


        self.packeg_proportion = {"normal": packeg_n, "reed5": self.check_len_reed(NUMBER_OF_ERRORS, packeg_n)}

        self.reed5_q = queue.Queue(maxsize=size_results)
        super(AddReed5, self).__init__()

    def run(self):
        self.logger.info("runing")
        file_path = ""

        while True:

            p = self.packeg_q.get()

            if p == "file end":
                self.reed5_q.put("file end")
                self.logger.info("end file: " + file_path)
            else:

                file_path = p['path']

                packege_list = p["packages"]

                key=p['key']


                packege_output = [b""] * self.packeg_proportion["reed5"]

                for symbol_index in range(self.PACKEGE_SIZE):
                    string_to_do_reed = b""
                    for packege_index in range(self.packeg_proportion["normal"]):


                        string_to_do_reed += (packege_list[packege_index][symbol_index]).to_bytes(1, byteorder='big')

                    reed = self.add_reed5(self.NUMBER_OF_ERRORS, string_to_do_reed)

                    for packege_index in range(self.packeg_proportion["reed5"]):
                        packege_output[packege_index] +=(reed[packege_index]).to_bytes(1, byteorder='big')



                self.reed5_q.put({"packages": packege_list + packege_output, "path": file_path,"key":key})

    def add_reed5(self, NUMBER_OF_ERORERS, s1):
        '''

        :param NUMBER_OF_ERORERS: number of errors that the reed5 will be able to fix
        :param s1: the string to add reed to it
        :return: the reed5 without the original string
        '''


        s2 = self.rsc.encode(s1)

        return (s2[len(s1):])

    def check_len_reed(self, NUMBER_OF_ERORERS, PACKEGE_SIZE):
        """
        returns the size to add
        """
        return (len(self.add_reed5(NUMBER_OF_ERORERS, PACKEGE_SIZE * b"0")))


class Crypto(threading.Thread):
    # encrypt the packets

    def __init__(self, file_input,key, size_results=20):
        # create logger
        self.logger = logging.getLogger('Crypto')
        self.logger.setLevel(logging.INFO)
        self.packet_input = file_input
        self.key=key

        self.packet_output = queue.Queue(maxsize=size_results)
        super(Crypto, self).__init__()

    def run(self):
        self.logger.info("runing")
        while True:
            pack_list = self.packet_input.get()

            if pack_list=="file end":
                self.packet_output.put("file end")
                self.logger.info("end file" )
                self.key = urandom(32)
            else:
                packets = pack_list['packages']
                new_packets=[""]*len(packets)

                for i in range(len(packets)):
                    new_packets[i]=self.encrypt(packets[i],self.key)
                pack_list['packages']=new_packets
                pack_list['key']=self.key
                #self.logger.info(f"encrypt {len(pack_list['packages'])} packs")

                self.packet_output.put(pack_list)

    def encrypt(self,s,key):

        chiper = Cipher(algorithms.AES(key), modes.ECB())
        encryptor = chiper.encryptor()
        q=encryptor.update(s) + encryptor.finalize()

        return (q)


class Sender(threading.Thread):
    # write the packages in the right place from the Add_reed5

    def __init__(self, q_input, dir_to_write, packeg_proportion, database,ip,port):
        # create logger
        self.logger = logging.getLogger('sender')
        self.logger.setLevel(logging.INFO)

        self.q_input = q_input
        self.dir_to_write = dir_to_write
        # self.package_n = packeg_proportion["normal"] + packeg_proportion["reed5"]
        self.packeg_proportion = packeg_proportion


        self.database = database
        self.ip=ip
        self.port=port

        super(Sender, self).__init__()

    def run(self):
        pack_num=0
        self.logger.info("runing")
        file_path= ""
        while True:
            pack = self.q_input.get()
            if pack == "file end":
                self.database.add_file(file_path, self.packeg_proportion, time())
                self.logger.info("end file: " + file_path)
                pack_num=0
            else:
                file_path = pack["path"]
                '''for i in pack["packages"]:
                    print( self.find_hash(i))'''


                for i in range(self.packeg_proportion["normal"] + self.packeg_proportion["reed5"]):

                    file_hash = self.find_hash(pack["packages"][i])+bytes(str(pack_num), 'utf-8').hex()

                    zero_list=self.database.zero_save_peer()
                    shuffle(zero_list)
                    list_of_peer = zero_list+["log"]+[i[0] for i in self.database.total_save_for_peer()]


                    while len(list_of_peer)!=0:

                        peer_id=list_of_peer[0]
                        list_of_peer.remove(peer_id)
                        if peer_id=='log':pass
                        else:


                            peer=self.database.get_ip_from_peer(peer_id)
                            host_port=peer['port']
                            host = peer['ip']

                            answer = peer_client.ask_per(PACKAGE_SIZE, file_hash, host, host_port, self.ip, self.port)

                            if answer == True:



                                answer = peer_client.put_pack(pack["packages"][i], file_hash, host, host_port, self.ip, self.port)


                                if answer == b"writen secsesfully":
                                    #print(file_path, file_hash, peer_id, pack_num, PACKAGE_SIZE)

                                    self.database.add_pack(file_path, file_hash, peer_id, pack_num, PACKAGE_SIZE)

                                    self.logger.info(f"beckuped pack {file_hash} in peer {peer} ")

                                    pack_num += 1
                                    break
                                else:
                                    self.logger.info(f"peer {peer} refused answer: {answer} ")
                            else:
                                self.logger.info(f"peer {peer} refused answer: {answer} ")

    def find_hash(self, s):
        digest = hashes.Hash(hashes.SHA256())
        digest.update(s)
        q = digest.finalize()

        return (q.hex())

if __name__ == '__main__':
    database_path="C:\\Users\\yuval\\projects\\saiber_big_project\\source\\file_packages\\data_base.db"
    key_file_path = r'C:\Users\yuval\projects\saiber_big_project\source\passward.txt'
    database = database_maneger.DatabaseMeneger(database_path,'C:\\Users\\yuval\\projects\\saiber_big_project\\source\\peers.json',['127.0.0.1','5002'])
    logging.basicConfig(level=logging.INFO)
    split = Splitter(PACKAGE_SIZE )
    split.files_input.put("C:\\Users\\yuval\\projects\\saiber_big_project\\source\\files_for_tests\\test2.jpg")
    #split.files_input.put("C:\\Users\\yuval\\projects\\saiber_big_project\\source\\test.txt")

    cryp = Crypto(split.packeg_q,key_file_path)

    reed = AddReed5(PACKAGE_SIZE, NUMBER_OF_ERRORS,cryp.packet_output)




    split.start()
    cryp.start()

    reed.start()

