#!/usr/bin/python
#coding:utf-8
try:
    import simplejson as json
except:
    import json
import asyncio
import traceback
import requests,re,os
from urllib import parse
from bs4 import BeautifulSoup
requests.packages.urllib3.disable_warnings()
import sys


def logger_init(name=None):
    import logging
    logger_name = name
    logger = logging.getLogger(logger_name)
    logger.setLevel(logging.DEBUG)

    log_path = os.path.dirname(os.path.abspath(__file__))+ '/mappings.log'
    filehandler = logging.FileHandler(log_path)
    filehandler.setLevel(logging.INFO)

    console = logging.StreamHandler()
    console.setLevel(logging.DEBUG)

    fmt = "%(asctime)-15s %(levelname)s %(process)d %(message)s"
    datefmt = "%Y-%m-%d %A %H:%M:%S"
    formatter = logging.Formatter(fmt, datefmt)

    filehandler.setFormatter(formatter)
    console.setFormatter(formatter)

    logger.addHandler(filehandler)
    logger.addHandler(console)
    return logger

logger = logger_init('mapping')

headers = {
    "Connection": "close", 
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.138 Safari/537.36", 
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9", 
    "Accept-Language": "zh-CN,zh;q=0.9,es;q=0.8,fr;q=0.7,vi;q=0.6"
}
proxies = {"http": "","https": ""}
#proxies = {"http": "socks5://127.0.0.1:1086","https": "socks5://127.0.0.1:1086"}
#proxies = {"http": "http://127.0.0.1:8080","https": "http://127.0.0.1:8080"}
#proxies = {"http": "socks4://127.0.0.1:8080","https": "socks4://127.0.0.1:8080"}
def get_path(url):
    filename = os.path.basename(url)
    nurl =  url.replace(filename,'')
    return nurl,filename

def url_match(url1,url2):
    # 确保只有当前host的去检测
    schema1, netloc1, path1, _, _, _ = parse.urlparse(url1, 'http')
    schema2, netloc2, path2, _, _, _ = parse.urlparse(url2, 'http')
    if netloc1 == netloc2:
        return True
    return False

def check_url(url):
    urls = set()
    try:
        resp=requests.get(url,headers=headers, verify=False,timeout=60,proxies=proxies)
        bs=BeautifulSoup(resp.content,'html.parser')
        for link in bs.findAll("script"):
            if "src" in str(link) and "function" not in str(link):
                # 只要js文件
                if  link.get('src').endswith('.js'):
                    if "//" not in link.get('src'):
                        urls.add(url+link.get('src'))
                    else:
                        if "http" not in link.get('src'):
                            host = 'http:'+link.get('src')
                            if url_match(host,url):
                                urls.add(host)
                        else:
                            host = link.get('src')
                            if url_match(host,url):
                                urls.add(host)
        for link in bs.findAll("link"):
            if  link.get('href').endswith('.js'):
                urls.add(url+link.get('href'))

    except Exception as e:
        logger.error('[get script] {}'.format(traceback.format_exc()))
        pass
    return urls

@asyncio.coroutine
def check_map(url):
    try:
        resp=requests.get(url,headers=headers, verify=False,timeout=60, allow_redirects=False,proxies=proxies)
        if "sourceMappingURL" in str(resp.content):
            result = re.findall(r'\/\/# sourceMappingURL\=(.*?)\.map',str(resp.content))
            if len(result)>0:
                for mappingurl in result:
                    #print(len(mappingurl))
                    # 出现 多个sourceMappingURL，其中一个输出了源码，出现了超长字符bug
                    if len(mappingurl)<=30:
                        path_url,filename = get_path(url)
                        # chunk-vendor 开头的都是各种依赖
                        if  not filename.startswith("chunk-vendor"):
                            mapurl = path_url+mappingurl+'.map'
                            logger.info(url+"\tfound sourceMappingURL")
                            mappings = check_source(mapurl)
                            if not mappings:
                                if url == url+'.map':
                                    pass
                                else:
                                    logger.info("fuzz\t"+url+'.map')
                                    check_source(url+'.map')
            else:
                check_source(url+'.map')
        else:
            return False
    except Exception as e:
        logger.error('[get sourceMappingURL] {}'.format(traceback.format_exc()))
        return False

def check_source(url):
    urls = set()
    try:
        resp=requests.get(url,headers=headers, verify=False,timeout=600, allow_redirects=False,proxies=proxies)
        schema, netloc, path, _, _, _ = parse.urlparse(url, 'http')
        if resp.status_code == 200 and "mappings" in str(resp.content):
            #print re.findall(r'sourceMappingURL\=(.*?)\.map',resp.content)
            logger.info(url+'\tsuccess get mappings')
            result = json.loads(resp.content.decode('utf-8'))
            folder_name = netloc.replace(':', '_') + '/'.join(path.split('/')[:-1])
            if not os.path.exists(folder_name):
                os.makedirs(folder_name)
            #print netloc.replace(':', '_')+ '/'+result["file"]
            # 保留原始map，以免误报
            with open(netloc.replace(':', '_')+ '/'+result["file"]+'.map', 'wb') as outFile:
                outFile.write(resp.content)

            # try to run command
            # 'restore-source-tree --out-dir ' + folder_name+ '/out ' + netloc.replace(':', '_')+ '/'+result["file"]+'.map' 
            
            # netloc.replace(':', '_')+ '/out '

            # netloc.replace(':', '_')+ '/'+result["file"]+'.map' 

            # 单独拉取sourcesContent
            content = ''
            for name in result['sourcesContent']:
                content = content + name
            if len(content)>0:
                with open(netloc.replace(':', '_')+ '/'+result["file"], 'wb') as outFile:
                    outFile.write(content.encode())
            else:
                with open(netloc.replace(':', '_')+ '/'+result["file"], 'wb') as outFile:
                    outFile.write(str(result['sourcesContent']).encode())
            return True
        else:
            logger.info("存在sourceMappingURL\t%s，但是无法访问" % url)
            return False
    except Exception as e:
        logger.error('[mappings] {}'.format(traceback.format_exc()))
        pass
    return urls
'''
python2 
ChunkedEncodingError: ('Connection broken: IncompleteRead(5773 bytes read, 2323 more expected)', IncompleteRead(5773 bytes read, 2323 more expected))
该用py3
'''
def main(url):
    urls = check_url(url)
    if len(urls)>0:
        loop = asyncio.get_event_loop()
        tasks=[]
        for key in urls:
            logger.debug("check\t"+key)
            tasks.append(check_map(key))
        loop.run_until_complete(asyncio.wait(tasks))
        loop.close()

if __name__ == '__main__':
    if len(sys.argv) == 1:
        print
        print('    Usage: python3 '+ sys.argv[0] + ' http://www.example.com/')
        sys.exit(0)
    main(sys.argv[1])
