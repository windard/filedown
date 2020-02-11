# coding=utf-8

import sys
import time
import random
import requests
import threading
from multiprocessing.pool import ThreadPool
from tqdm import tqdm
import logging

try:
    from urlparse import urlparse
    import Queue
except ImportError:
    unicode = str
    import queue as Queue
    from urllib.parse import urlparse


session = requests.Session()
logger = logging.getLogger("downloader")


formatter = logging.Formatter('%(name)-12s %(asctime)s %(levelname)-8s '
                              '%(lineno)-4d %(message)s',
                              '%Y %b %d %a %H:%M:%S')
stream_handler = logging.StreamHandler(sys.stdout)
stream_handler.setFormatter(formatter)
logger.addHandler(stream_handler)
logger.setLevel(logging.DEBUG)


def worker(url, filename, start, end, queue, times=0):
    try:
        headers = {
            "Range": 'bytes={}-{}'.format(start, end)
        }
        resp = session.get(url, headers=headers)
        with open(filename, 'rb+') as f:
            f.seek(start)
            f.write(resp.content)
        queue.put(end - start)

    except Exception as e:
        if times >= 3:
            logger.error("worker error more than three times %r", e)
            return
        logger.error("worker error %r", e)
        time.sleep(random.random())
        worker(url, filename, start, end, queue, times + 1)


def update_progress(progress, queue):
    try:
        while 1:
            progress.update(queue.get())
    except Exception as e:
        logger.error("update progress error %r", e)


def download(url, chunk_size=1024 * 1024):
    if not isinstance(url, unicode):
        url = url.decode("utf-8")

    filename = urlparse(url).path.rsplit('/')[-1]
    queue = Queue.Queue()

    resp = session.head(url)
    content_length = int(resp.headers.get('Content-Length') or 0)
    if not content_length:
        return
    progress = tqdm(total=content_length, unit='B',
                    unit_scale=True, desc=filename)

    f = open(filename, 'wb')
    f.truncate(content_length)
    f.close()

    t = threading.Thread(target=update_progress, args=(progress, queue))
    t.setDaemon(True)
    t.start()

    pool = ThreadPool(40)

    for i in range(0, content_length, chunk_size):
        pool.apply_async(worker, (url, filename, i, i + chunk_size, queue))

    pool.close()
    pool.join()
    progress.close()


def main():
    if len(sys.argv) < 2 or sys.argv[1] in ['-h', '--help']:
        print("""Usage: only_download URL [thread_num]
    example: only_download https://baidu.com/index.html
        """)
        exit()
    if len(sys.argv) > 2:
        download(sys.argv[1], int(sys.argv[2]))
    download(sys.argv[1])


if __name__ == '__main__':
    main()
