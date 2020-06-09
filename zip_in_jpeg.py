from bottle import *
import os
import sys
import struct
import zipfile
import datetime
import math
import shutil

def logging(request):
    logfile = '/lib/share/python/work/access_log'
    log = (datetime.datetime.utcnow() + datetime.timedelta(hours=9)).strftime('%Y-%m-%d %H:%M:%S') + ', '
    log += 'access from : ' + request.remote_addr + ', '
    log += 'method : ' + request.method + ', '
    log += 'path : ' + request.urlparts.path + '\n'
    with open(logfile, mode='a') as f:
        f.write(log)

@get('/upload')
def upload():
    logging(request)
    
    #def
    d_title = {
        'en':'Zip in Jpeg Service.',
        'ja':'Zip in Jpeg サービス'
    }
    d_note = {
        'en':'Note',
        'ja':'注意事項'
    }
    d_note1 = {
        'en':'Image to be shown by clicking Create button includes zipped embed data.',
        'ja':'作成ボタンを押すことによって表示される画像には、Zip化データが埋め込まれています。'
    }
    d_note2 = {
        'en':'After downloading image, You can easily find data by modifying extension from jpg to zip.',
        'ja':'拡張子をjpgからzipへ変更することでダウンロードした画像から埋め込みデータを取り出せます。'
    }
    d_note3 = {
        'en':'When the upload file size is large, it is embeded as divided zip.',
        'ja':'アップロードファイルのサイズが大きい場合、データは分割zipとして埋め込まれます。'
    }
    d_note4 = {
        'en':'Upload size must be less than 10MB.',
        'ja':'アップロードサイズは10MB以下までです。'
    }
    d_btn = {
        'en':'Create',
        'ja':'作成'
    }
    d_jpegfile = {
        'en':'Jpeg File',
        'ja':'Jpegファイル'
    }
    d_datafile = {
        'en':'File to Embed into Image',
        'ja':'画像に埋め込むファイル'
    }

    d_lang = {
        'en':'en',
        'ja':'ja'
    }
    lang = d_lang.get(request.query.get('lang'), 'en')
    html = '''
    <!DOCTYPE html>
    <html>
    <head>
    <title>Zip in Jpeg Service</title>
    </head>
    <body>
        <form action="/upload" method="post" enctype="multipart/form-data">
            <h2>
                {title}
            </h2>
            <div style="margin-bottom:10px">
                <a style="margin:5px" href="http://sistemainformatico.tk:8080/upload?lang=en">ENGLISH</a>
                <a style="margin:5px" href="http://sistemainformatico.tk:8080/upload?lang=ja">JAPANESE</a>
            </div>
            <fieldset>
                <legend>{jpegfile}</legend>
                <input type="file" name="jpeg">
            </fieldset>
            <fieldset>
                <legend>{datafile}</legend>
                <input type="file" name="data">
            </fieldset>
            <div style="margin:20px">
                <input type="hidden" name="lang" value="{language}">
                <input type="submit" value="{btn}">
            </div>
            <lu>
                {note}
                <li>{note1}</li>
                <li>{note2}</li>
                <li>{note3}</li>
                <li>{note4}</li>
            </lu>
            <div style="margin-top:10px">
                <a href="https://sistemainformatico.tk">Developer's site</a>
            </div>
        </form>
    </body>
    </html>
    '''.format(language=lang,
        title=d_title.get(lang),
        note=d_note.get(lang),
        note1=d_note1.get(lang),
        note2=d_note2.get(lang),
        note3=d_note3.get(lang),
        note4=d_note4.get(lang),
        btn=d_btn.get(lang),
        jpegfile=d_jpegfile.get(lang),
        datafile=d_datafile.get(lang)
    )
    return html

@route('/upload', method='POST')
def do_upload():
    logging(request)

    root = '/lib/share/python/work'
    div = '/'
    dir = (root + datetime.datetime.now().strftime('%Y%m%d%H%M%S'))
    
    #get image and data
    jpeg = request.files.get('jpeg')
    data = request.files.get('data')
    #check request params
    if (jpeg is None) or (data is None):
        return "No file selected!"
    #check extension
    if not jpeg.filename.lower().endswith(('.jpg', '.jpeg')):
        return 'File extension not allowed!'
    #check request size (must be less than 10M)
    req_size = request.content_length 
    if req_size > (10 * 1024 * 1024):
        return "File size exceeded its limit(10M)!"
    #filename
    jpgfile = dir + div + "original.jpg"
    datafile = dir + div + data.filename
    #save
    os.makedirs(dir, exist_ok=False)
    jpeg.save(jpgfile)
    data.save(datafile)

    tmpfile = dir + div + 'tmp.zip'
    zfile = dir + div + 'zfile.zip'
    outfile = dir + div + 'out.jpg'

    #compress
    if not jpeg.filename.lower().endswith(('.zip')):
        compFile = zipfile.ZipFile(tmpfile, 'w', zipfile.ZIP_DEFLATED)
        compFile.write(datafile, os.path.split(datafile)[1])
        compFile.close()
    else:
        tmpfile = datafile

    #divide
    zip = bin_div(tmpfile)

    #compress divided files
    if len(zip) > 1:
        compFile = zipfile.ZipFile(zfile, 'w', zipfile.ZIP_STORED)
        for i in range(len(zip)):
            compFile.write(zip[i], os.path.split(zip[i])[1])
        compFile.close()
    else:
        zfile = tmpfile

    genzip(jpgfile, zfile, outfile)

    response.content_type = 'image/jpeg'
    with open(outfile, 'rb') as fh:
        content = fh.read()
    response.set_header('Content-Length', str(len(content)))

    print('delete work dir : ' + dir)
    shutil.rmtree(dir)
    return content

def bin_div(file, size=60*1024):
    length = os.path.getsize(file)
    div_num = math.ceil((length + size - 1) / size)
    last = (size * div_num) - length
    outfiles = []
    bin = open(file, 'rb')
    for i in range(div_num):
        read_size = last if i == div_num-1 else size
        data = bin.read(read_size)
        if len(data) > 0:
            out = open(file  + '.' + format(i+1,'03d'), 'wb')
            outfiles.append(file + '.' + format(i+1,'03d'))
            out.write(data)
            out.close()
    bin.close()
    return outfiles

#Class which creates binary file byte by byte
class BinWriter:
    fout = None
    pos = 0
    def __init__(self, path):
        self.fout = open(path,'wb')
    def write(self, data):
        self.fout.write(data.to_bytes(1,byteorder='little'))
        self.pos += 1
    def close(self):
        if self.fout is not None:
            self.fout.close()
    def getCurrentPos(self):
        return self.pos

#Class which analyse pk header of zip archive 
class ZipAnalyser:
    zfin = None
    zipSize = 0
    pk34entrys = []
    pk34entrys_new = []
    pk34sizes = []
    pk12entry = 0
    pk12entry_new = 0
    pk12num = 0
    pk12size = 0
    pk56entry = 0
    MAX_SEGMENTSIZE = 0xFFEF
    PK34HEADERSIZE = 30
    PK12HEADERSIZE = 46
    PK56HEADERSIZE = 22
    def __init__(self, zipPath):
        #calc zip size
        self.zipSize = os.path.getsize(zipPath)
        #open zip file
        self.zfin = open(zipPath,'rb')
    def __get_pk56entry(self):
        #find pk56header from tail
        for i in range(self.zipSize):
            pos = self.zipSize - i - self.PK56HEADERSIZE
            if(pos < 0):
                return -1
            self.zfin.seek(pos)
            #retreave 4 bytes
            header = self.zfin.read(4)
            #is pk56 header?
            if(header[0] == 0x50 and header[1] == 0x4b and header[2] == 0x05 and header[3] == 0x06):
                return pos
        return -1
    def close(self):
        if self.zfin is not None:
            self.zfin.close()
    def load(self):
        self.pk56entry = self.__get_pk56entry()
        if(self.pk56entry < 0):
            return -1
        #move to PK56 header 
        self.zfin.seek(self.pk56entry)
        pk56header = self.zfin.read(self.PK56HEADERSIZE) 
        self.pk12num = byte2int(0,0,pk56header[9], pk56header[8])
        self.pk12size =  byte2int(pk56header[15], pk56header[14], pk56header[13], pk56header[12])
        self.pk12entry = byte2int(pk56header[19], pk56header[18], pk56header[17], pk56header[16])
        self.pk12entry_new = byte2int(pk56header[19], pk56header[18], pk56header[17], pk56header[16])
        #move to PK12 header
        nameoffset = 0
        filenamesize = 0
        for i in range(self.pk12num):
            self.zfin.seek(self.pk12entry + i * self.PK12HEADERSIZE + nameoffset)
            pk12header = self.zfin.read(self.PK12HEADERSIZE)
            filenamesize = byte2int(0, 0, pk12header[29], pk12header[28])
            nameoffset += filenamesize
            pk34entry = byte2int(pk12header[45], pk12header[44], pk12header[43], pk12header[42])
            pk34size = self.PK34HEADERSIZE + filenamesize + byte2int(pk12header[23],pk12header[22],pk12header[21],pk12header[20])
            if(pk34size > self.MAX_SEGMENTSIZE):
                return -1
            self.pk34entrys.append(pk34entry)
            self.pk34entrys_new.append(pk34entry)
            self.pk34sizes.append(pk34size)
        return 0
    def getFileNum(self):
        return self.pk12num
    def getPk34Data(self, i):
        self.zfin.seek(self.pk34entrys[i])
        return self.zfin.read(self.pk34sizes[i])
    def setPK34EntryPoint(self, i, newentrypoint):
        self.pk34entrys_new[i] = newentrypoint
    def getPK12Data(self):
        self.zfin.seek(self.pk12entry)
        pk12data = bytearray(self.zfin.read(self.pk12size))
        offset = 0
        for i in range(self.pk12num):
            filenamesize = byte2int(0, 0, pk12data[offset+29], pk12data[offset+28])
            newentrypoint = self.pk34entrys_new[i]
            nep4 = int(newentrypoint / (256 * 256 * 256))
            nep3 = int(newentrypoint / (256 * 256 ) % (256))
            nep2 = int(newentrypoint / (256) % (256))
            nep1 = int(newentrypoint % 256)
            pk12data[offset+42] = nep1 
            pk12data[offset+43] = nep2 
            pk12data[offset+44] = nep3 
            pk12data[offset+45] = nep4 
            offset += self.PK12HEADERSIZE + filenamesize
        return pk12data
    def setPK12EntryPoint(self, newentrypoint):
        self.pk12entry_new = newentrypoint
    def getPK56Data(self):
        self.zfin.seek(self.pk56entry)
        pk56data = bytearray(self.zfin.read(self.PK56HEADERSIZE))
        newentrypoint = self.pk12entry_new
        nep4 = int(newentrypoint / (256 * 256 * 256))
        nep3 = int(newentrypoint / (256 * 256 ) % (256))
        nep2 = int(newentrypoint / (256) % (256))
        nep1 = int(newentrypoint % 256)
        pk56data[16] = nep1 
        pk56data[17] = nep2 
        pk56data[18] = nep3 
        pk56data[19] = nep4 
        return pk56data

#useful functions
def getHex(value):
    hexcode = hex(value)
    if(len(hexcode) == 4):
        return hexcode[-2:]
    if(len(hexcode) == 3):
        return ('0' + hexcode[-1:])
    return ''
def byte2int(b1,b2,b3,b4):
    return (256 * 256 * 256 * b1 + 256 * 256 * b2 + 256 * b3 + b4)

#main function
def genzip(jpgfile, zipfile, outfile):
    #original jpeg file to import zip file
    #original file must be in accordance with jpeg format 
    with open(jpgfile, 'rb') as fh:
        bin_data = fh.read()
    #bin_data = open(jpgfile, 'rb').read()

    #output jpeg file writing class
    binWriter = BinWriter(outfile)

    #load zip 
    #each archived data in zip must be less than 0xFFEF bytes 
    zipAnalyser = ZipAnalyser(zipfile)
    if(zipAnalyser.load() != 0):
        print('zip load error!')
        zipAnalyser.close()
        binWriter.close()
        sys.exit()

    #process start
    binary_size = len(bin_data)
    idx = 0

    #SOI
    tag1 = getHex(bin_data[idx])
    binWriter.write(bin_data[idx])
    idx = idx + 1
    tag2 = getHex(bin_data[idx])
    binWriter.write(bin_data[idx])
    idx = idx + 1
    print(tag1 + tag2)

    picadd = 0
    while idx < binary_size:
        #get jpeg segment TAG
        tag1 = getHex(bin_data[idx])
        binWriter.write(bin_data[idx])
        idx = idx + 1
        tag2 = getHex(bin_data[idx])
        binWriter.write(bin_data[idx])
        idx = idx + 1

        # is EOI?
        if((tag1 + tag2) == 'ffd9'):
            print(tag1 + tag2)
            #PK56 headers
            pk56data = zipAnalyser.getPK56Data()
            pk56size = len(pk56data)
            binWriter.write(int(255))
            binWriter.write(int(226))
            binWriter.write(int((pk56size + 2)/256))
            binWriter.write(int((pk56size + 2)%256))
            for i in range(pk56size):
                binWriter.write(pk56data[i])
            break

        if(tag1 != 'ff'):
            #Image area
            for i in range(idx, binary_size - 2):
                binWriter.write(bin_data[idx])
                idx = idx + 1
            print('Image : ...')
            continue

        #calc segment length and output segment data as it is
        ulen = bin_data[idx]
        binWriter.write(bin_data[idx])
        idx = idx + 1
        llen = bin_data[idx]
        binWriter.write(bin_data[idx])
        idx = idx + 1
        segment_size = ulen * 256 + llen
        record = ""
        print(tag1 + tag2 + ' : Len=' + str(segment_size))
        for i in range(idx, idx + segment_size - 2):
            binWriter.write(bin_data[idx])
            idx = idx + 1
    
        if(picadd == 0):
            #embed zip archive in FFE2 segment
            #PK34 heraders and archived data
            filenum = zipAnalyser.getFileNum()
            for i in range (filenum):
                pk34data = zipAnalyser.getPk34Data(i)
                pk34size = len(pk34data)
                binWriter.write(int(255))
                binWriter.write(int(226))
                binWriter.write(int((pk34size + 2)/256))
                binWriter.write(int((pk34size + 2)%256))
                zipAnalyser.setPK34EntryPoint(i, binWriter.getCurrentPos())
                for j in range(pk34size):
                    binWriter.write(pk34data[j])
            #PK12 headers
            pk12data = zipAnalyser.getPK12Data()
            pk12size = len(pk12data)
            binWriter.write(int(255))
            binWriter.write(int(226))
            binWriter.write(int((pk12size + 2)/256))
            binWriter.write(int((pk12size + 2)%256))
            zipAnalyser.setPK12EntryPoint(binWriter.getCurrentPos())
            for i in range(pk12size):
                binWriter.write(pk12data[i])            
            picadd = 1

    zipAnalyser.close()
    binWriter.close()

if __name__ == '__main__':
    run(host="0.0.0.0",port=8080,debug=True)    
