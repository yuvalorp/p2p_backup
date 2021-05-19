import httplib2
from socket import timeout as socket_timeout
def return_pack(file_hash,host,host_port,ip,port):
    h = httplib2.Http(timeout=1)

    try:
        (response, content)=h.request(f"http://{host}:{host_port}/return_pack/{file_hash}?ip={ip}&port={port}","GET")


    except (ConnectionRefusedError, socket_timeout,httplib2.ServerNotFoundError) as e:
        return (type(False,e))

    if content == b'I cant find the pack' or content == 'you dont have permittion':
        return (False,content)
    else:
        return (True,content)

def delete_pack(file_hash,host,host_port,ip,port):
    h = httplib2.Http(timeout=1)

    try:
        (response, content)=h.request(f"http://{host}:{host_port}/del_pack/{file_hash}?ip={ip}&port={port}","DELETE")
        return content

    except (ConnectionRefusedError, socket_timeout,httplib2.ServerNotFoundError) as e:
        return (e)



def ask_per(file_size,file_hash,host,host_port,ip,port):
    #ask permittion to save a pack

    h = httplib2.Http(timeout=1)

    try:
        (response, content)=h.request(f"http://{host}:{host_port}/ask_per/{file_hash}?size={file_size}&ip={ip}&port={port}","PUT")

    except (ConnectionRefusedError,socket_timeout,httplib2.ServerNotFoundError) as e:
        return (type(e))
    else:
        if content != b"True":
            return (content)
        else:
            return (True)


def put_pack(text,file_hash,host,host_port,ip,port):

    h = httplib2.Http(timeout=1)

    try:
        (response, content) = h.request(f"http://{host}:{host_port}/put_pack/{file_hash}?ip={ip}&port={port}",
                                        "PUT", body=text,
                                        headers={'content-length': str(len(text))})


    except (ConnectionRefusedError, socket_timeout, httplib2.ServerNotFoundError) as e:
        return (type(e))
    else:
        if content != "writen secsesfully":
            return (content)
        else:
            return ("writen secsesfully")


def del_peer(host_port,ip,port):
    '''say to the server about disconection'''
    h = httplib2.Http(timeout=1)
    try:
        (response, content) = h.request(f"http://{host}:{host_port}/del_peer?ip={ip}&port={port}","PUT")
        return content

    except (ConnectionRefusedError, socket_timeout, httplib2.ServerNotFoundError) as e:
        return (type(e))


def del_pack(pack_hash,host,host_port,ip,port):

    h = httplib2.Http(timeout=1)


    try:
        (response, content)=h.request(f"http://{host}:{host_port}/del_pack/{pack_hash}?ip={ip}&port={port}","DELETE")
        return content

    except (ConnectionRefusedError, socket_timeout, httplib2.ServerNotFoundError) as e:
        return (type(e))

def send_disconnect(host,host_port,ip,port):

    h = httplib2.Http(timeout=1)

    try:
        (response, content)=h.request(f"http://{host}:{host_port}/disconect?ip={ip}&port={port}","DELETE")
        return content

    except (ConnectionRefusedError, socket_timeout, httplib2.ServerNotFoundError) as e:
        return (type(e))


def moved_pack(host,host_port,ip,port,pack_hash,new_ip,new_port):
    '''send that the pack with the hash "pack_hash" moved to new_ip,new_port'''

    h = httplib2.Http(timeout=1)
    try:
        (response, content)=h.request(f"http://{host}:{host_port}/moved_pack?ip={ip}&port={port}&hash={pack_hash}&new_ip={new_ip}&new_port={new_port}","PUT")
        return content

    except (ConnectionRefusedError, socket_timeout, httplib2.ServerNotFoundError) as e:
        return (type(e))


def exist(host,host_port):
    try:
        h = httplib2.Http(timeout=1)
        (response, content)=h.request(f"http://{host}:{host_port}/exist","GET")
        return (content)
    except:
        return(False)


if __name__ =='__main__':
    # the resever
    host = 'localhost'
    host_port = 5000
    # the sender
    ip = "123.243.345.456"
    port = 5001




