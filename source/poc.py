from reedsolo import RSCodec
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import hashes
import threading
import queue
from os import path,urandom
import logging

from json import loads,dumps


NUMBER_OF_ERRORS = 9  # number of errors that the reed5 will be able to fix
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

        super(Splitter, self).__init__()

    def run(self):
        self.logger.info("runing")

        while True:
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
                    self.packeg_q.put({"packages": packege_list, "path": file_path})
                    packege_list = []
                    p_counter = 0


            file.close()

            while p_counter != (self.packeg_n):

                p_counter += 1
                packege_list.append(b"\x00" * self.package_size)




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
            packege = []

            i = 0
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

                # put all the packages in the queue

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
        return (len(self.add_reed5(NUMBER_OF_ERRORS, PACKEGE_SIZE * b"0")))


class Crypto(threading.Thread):
    # encrypt the packets

    def __init__(self, file_input, size_results=10):
        # create logger
        self.logger = logging.getLogger('writer')
        self.logger.setLevel(logging.INFO)

        self.packet_input = file_input
        self.key = urandom(32)


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

                self.packet_output.put(pack_list)

    def encrypt(self,s,key):
        return (s)

        chiper = Cipher(algorithms.AES(key), modes.ECB())
        encryptor = chiper.encryptor()
        q=encryptor.update(s) + encryptor.finalize()

        return (q)






class Writer(threading.Thread):
    # write the packages in the right place from the Add_reed5

    def __init__(self, q_input, dir_to_write,packeg_proportion):
        # create logger
        self.logger = logging.getLogger('writer')
        self.logger.setLevel(logging.INFO)

        self.q_input = q_input
        self.dir_to_write = dir_to_write
        #self.package_n = packeg_proportion["normal"] + packeg_proportion["reed5"]
        self.packeg_proportion=packeg_proportion

        super(Writer, self).__init__()

    def run(self):
        self.logger.info("runing")
        directory = ""
        while True:

            pack = self.q_input.get()




            if pack == "file end":
                self.logger.info("end file: " + directory)
            else:

                directory = pack["path"]

                file_name = path.basename(directory)
                list_of_hash = []

                for i in range(self.packeg_proportion["normal"] + self.packeg_proportion["reed5"]):
                    file_hash=self.find_hash(pack["packages"][i])

                    file_path = self.dir_to_write + "\\" +file_hash

                    file = open(file_path, 'wb')



                    file.write(pack["packages"][i])


                    list_of_hash.append(file_hash)

                    file.close()


                self.add_to_meta(file_name, list_of_hash,(pack['key']).hex())

    def find_hash(self, s):
        digest = hashes.Hash(hashes.SHA256())
        digest.update(s)
        q = digest.finalize()

        return (q.hex())

    def add_to_meta(self, file_name, list_of_hash,key):
        """
        add list of hash of packages to the list in the meta data file of this file
        meta data =>{"name":"name of the file","packages":[[24242,24324,23463],[24242,24324,23463]]<=list of list of hash,
        packeg_proportion:{"normal":16,'reed5':9}<=how mach packs we have per number of original packs}

        :param list_of_hash: list of hash to had to the meta
        :return: nothing
        """

        meta_data_file_path = self.dir_to_write + "\\" + "meta_"+ file_name.split('.')[0]+'.json'
        if path.exists(meta_data_file_path):
            meta_data_file = open(meta_data_file_path, "r")
            meta_data = meta_data_file.read()
            meta_data_file.close()



            meta_data = loads(meta_data)
            #print(list_of_hash)

            meta_data["packages"] += [list_of_hash]
            meta_data['key']=key

            meta_data = dumps(meta_data)

            meta_data_file = open(meta_data_file_path, "w")
            meta_data_file.write(meta_data)
            meta_data_file.close()
        else:
            meta_data = {"name": file_name, "packages": [list_of_hash],'packeg_proportion':self.packeg_proportion,'key':key}

            meta_data = dumps(meta_data)

            meta_data_file = open(meta_data_file_path, "w")
            meta_data_file.write(meta_data)
            meta_data_file.close()


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    split = Splitter(PACKAGE_SIZE )
    split.files_input.put("C:\\Users\\yuval\\projects\\saiber_big_project\\poc\\test2.jpg")
    #split.files_input.put("C:\\Users\\yuval\\projects\\saiber_big_project\\poc\\test.txt")

    cryp = Crypto(split.packeg_q)

    reed = AddReed5(PACKAGE_SIZE, NUMBER_OF_ERRORS,cryp.packet_output)

    writer = Writer(reed.reed5_q, "C:\\Users\\yuval\\projects\\saiber_big_project\\poc\\file_packages"
                    ,reed.packeg_proportion)


    split.start()
    cryp.start()

    reed.start()


    writer.start()
