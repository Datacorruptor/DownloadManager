import os
import winsound

import requests
import concurrent.futures
import random
import threading
import time
from pynput import keyboard
from pynput.keyboard import Key


listening = False

def on_press(key):
    global listening
    try:
        if ord(key.char) != 12:
            if key.char == 'a' and listening:
                AddNew()
            elif key.char == 'z'and listening:
                exit(0)
            else:
                print('alphanumeric key {0} {1} pressed'.format(key.char,ord(key.char)))

    except AttributeError:
        if key != Key.ctrl_l:
            if key == Key.ctrl_r:
                listening = not listening
                print('listening is now' ,listening)
            else:
                print('special key {0} pressed'.format(key))


listener = keyboard.Listener(on_press=on_press)
listener.start()


info = {}


executor = concurrent.futures.ThreadPoolExecutor(4)


def startDownloadBatch(urls=None):
    if urls is None:
        urls = [defaulturl]*10
    print(urls)
    x = threading.Thread(target=downloadBatch,args=(urls,))
    x.start()

def downloadBatch(urls=None):
    print(urls)
    if urls is None:
        urls = [defaulturl]*10
    executor.map(downloadFile, urls)


def downloadFile(url,dir = "downloads",filename = None):
    if not os.path.exists(dir):
        os.mkdir(dir)
    if filename is None:
        rnd = str(random.randint(1000000, 9999999))
        filename=rnd+'_'+url.split("/")[-1]

    r = requests.head(url)
    print(r.headers)
    total_length = int(r.headers.get('content-length'))
    chunk_size = 1024 * 1024 * 1
    es = total_length // chunk_size + 1
    info[filename] = 0
    info[filename+'.size'] = es
    try:
        print(r.headers['Accept-Ranges'])

        c = 0
        bytesstrings = []

        print(total_length)
        print(chunk_size)
        for i in range(0,total_length,chunk_size):
            bytesstrings.append('bytes='+str(i)+'-'+str(min(i+chunk_size-1,total_length-1)))
            c+=1

        print(c)
        inner_executor = concurrent.futures.ThreadPoolExecutor(8)
        inner_executor.map(downloadFileChunk,[url]*c,bytesstrings,range(c),[filename]*c)

        inner_executor.shutdown()

        with open(os.path.join(dir, filename), "wb") as file:
            for i in range(0,c):
                chunk = open(filename+".part"+str(i), 'rb').read()
                file.write(chunk)
                print("Joining " + str(i))
                os.remove(filename+".part"+str(i))




    except Exception:

        r = requests.get(url, stream=True)
        info[filename] = 0
        info[filename + '.size'] = es
        print('started ' + filename)
        with open(os.path.join(dir, filename), "wb") as file:
            for chunk in r.iter_content(chunk_size=chunk_size):
                if chunk:
                    print('chunking')
                    file.write(chunk)
                    info[filename] = info[filename]+1
                    file.flush()


    print('DONE ' + filename)
    duration = 1000  # milliseconds
    freq = 440  # Hz
    winsound.Beep(freq, duration)
    info.pop(filename)
    info.pop(filename + '.size')

def downloadFileChunk(url,bytes,index,name):
    with open(os.path.join(name+".part"+str(index)), "wb") as file:
        headers = {'Range': bytes}
        r = requests.get(url,headers=headers)
        chunk = r.content
        file.write(chunk)
        file.flush()
        info[name]+=1


def Info():
    global update
    info_copy = info.copy()
    updatestring = ""
    updatestring += 'currently working on ' + str(len(info_copy)//2) + ' downloads\n'
    for k in info_copy:
        if not k.endswith('.size'):
            updatestring += str(k)+" "+str(info_copy[k])+"/"+str(info_copy[k+'.size'])+'\n'

    os.system('cls' if os.name == 'nt' else 'clear')

    print(updatestring)

    if len(info_copy)==0:
        update = False

def AddNew():
    global update
    update = False
    x = input('new link:')
    links = x.split()
    startDownloadBatch(links)
    update = True


update = True

defaulturl = 'http://speedtest.ftp.otenet.gr/files/test1Gb.db'
#defaulturl = 'http://speedtest.ftp.otenet.gr/files/test100Mb.db'

# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    startDownloadBatch([defaulturl]*1)
    print('hey')
    while True:
        time.sleep(1)
        if update:
            Info()


