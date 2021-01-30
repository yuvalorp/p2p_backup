from json import  loads,dumps
import httplib2

host='localhost'
host_port=5000
ip="123.243.345.456"
port=5001

def return_pack(file_hash,host,host_port):
    global ip
    global port
    h = httplib2.Http()

    (response, content)=h.request(f"http://{host}:{host_port}/return_pack/{file_hash}?ip={ip}&port={port}","GET")

    return (response['status'], content)

def ask_per(file_size,file_hash,host,host_port):
    #ask permittion to save a pack
    global ip
    global port
    h = httplib2.Http()
    print("reqwest: "+f"http://{host}:{host_port}/ask_per/{file_hash}?size={file_size}&ip={ip}&port={port}")
    print()

    (response, content)=h.request(f"http://{host}:{host_port}/ask_per/{file_hash}?size={file_size}&ip={ip}&port={port}","PUT")

    return (response['status'], content)

def put_pack(text,file_hash,host,host_port):
    global ip
    global port
    h = httplib2.Http()

    (response, content)=h.request(f"http://{host}:{host_port}/put_pack/{file_hash}?ip={ip}&port={port}",
               "PUT", body=text,
               headers={ 'content-length': str(len(text))})

    return (response['status'], content)

def del_pack(file_hash,host,host_port):
    global ip
    global port
    h = httplib2.Http()

    (response, content)=h.request(f"http://{host}:{host_port}/del_pack/{file_hash}?ip={ip}&port={port}","DELETE")

    return (response['status'], content)

def disconect(host,host_port):
    global ip
    global port
    h = httplib2.Http()
    (response, content)=h.request(f"http://{host}:{host_port}/disconect?ip={ip}&port={port}","DELETE")
    return (response['status'], content)


#print(ask_per(1024,'test_pack',host,host_port))
#print(put_pack('sfsfds','test_pack',host,host_port))
#print(return_pack('test_pack',host,host_port))
#print(del_pack('test_pack',host,host_port))
if __name__ =='__main__':
    print(ask_per(1024,'test_pack',host,4002))