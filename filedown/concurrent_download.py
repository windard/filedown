# -*- coding: utf-8 -*-

import os
import six
import click
import logging
import requests
from tqdm import tqdm
from requests import adapters
from concurrent.futures import ThreadPoolExecutor

from six.moves.urllib.parse import urlparse
from six.moves.queue import Queue

logging.basicConfig(
    level=logging.INFO,
    format='%(name)-25s %(asctime)s %(levelname)-8s %(lineno)-4d %(message)s',
    datefmt='[%Y %b %d %a %H:%M:%S]',
)
logger = logging.getLogger(__name__)
session = requests.Session()
session.mount('http://', adapters.HTTPAdapter(pool_maxsize=30))
session.mount('https://', adapters.HTTPAdapter(pool_maxsize=30))


def worker(url, filename, start, end, queue, timeout, pool):
    try:
        headers = {"Range": 'bytes={}-{}'.format(start, end)}
        resp = session.get(url, headers=headers, timeout=timeout)
        with open(filename, 'rb+') as f:
            f.seek(start)
            f.write(resp.content)

    except Exception as e:
        logger.error("download error:%r" % e)
        pool.submit(worker, url, filename, start, end, queue, timeout, pool)
    else:
        queue.put(end - start)


def download(url, thread_num=30, chunk_size=1024 * 1024, timeout=30):
    if not isinstance(url, six.text_type):
        url = url.decode("utf-8")

    filename = os.path.basename(urlparse(url).path)
    progress_queue = Queue()

    resp = session.head(url)
    content_length = int(resp.headers.get('Content-Length') or 0)
    if not content_length:
        return

    if os.path.exists(filename) and os.path.getsize(filename) == content_length:
        print(u"【{}】: already exist, which will be overwritten.".format(filename))
    else:
        f = open(filename, 'wb')
        f.truncate(content_length)
        f.close()

    progress = tqdm(total=content_length, unit='B', unit_scale=True, desc=u"【{}】".format(filename))

    pool = ThreadPoolExecutor(thread_num)

    for i in range(0, content_length, chunk_size):
        pool.submit(worker, url, filename, i, i + chunk_size, progress_queue, timeout, pool)

    while progress.total > progress.n:
        progress.update(progress_queue.get())

    progress.close()


@click.command()
@click.help_option("-h", "--help")
@click.argument('url')
@click.option("-n", "--num", help="thread number", default=30)
@click.option("-c", "--chunk", help="chunk download size", default=1024 * 1024)
@click.option("-t", "--timeout", help="chunk download timeout", default=30)
def main(url, num, chunk, timeout):
    download(url, num, chunk, timeout)


if __name__ == '__main__':
    main()
