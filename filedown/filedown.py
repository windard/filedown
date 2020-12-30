# -*- coding: utf-8 -*-

import os
import click
import logging
import requests
from tqdm import tqdm
from requests.adapters import HTTPAdapter
from multiprocessing import Queue
from multiprocessing import Manager
from multiprocessing import Pool as ProcessPool
from multiprocessing.pool import ThreadPool

from six.moves.urllib.parse import urlparse


request_session = requests.session()
request_session.mount('http://', HTTPAdapter(pool_maxsize=30))
request_session.mount('https://', HTTPAdapter(pool_maxsize=30))
logging.basicConfig(
    level=logging.INFO,
    format='%(name)-25s %(asctime)s %(levelname)-8s %(lineno)-4d %(message)s',
    datefmt='[%Y %b %d %a %H:%M:%S]',
)
logger = logging.getLogger(__name__)


class RequestHandler(object):
    def __init__(self, url=None, timeout=30, headers=None, cookies=None, proxies=None, session=None):
        self.url = url
        self.timeout = timeout
        self.headers = headers or {}
        self.cookies = cookies or {}
        self.proxies = proxies or {}
        self.session = session or request_session

    def do_request(self, method, url=None, headers=None, cookies=None, proxies=None, **kwargs):
        url = url or self.url
        if headers:
            self.headers.update(headers)
        if cookies:
            self.cookies.update(cookies)
        if proxies:
            self.proxies.update(proxies)
        resp = self.session.request(
            method=method,
            url=url,
            headers=self.headers,
            cookies=self.cookies,
            proxies=self.proxies,
            timeout=self.timeout,
            allow_redirects=False,
            **kwargs
        )
        return resp

    def handle(self, filename=None, task_queue=None, progress_queue=None, chunk_size=1024 * 1024):
        # type: (str, Queue, Queue, int) -> None
        while True:
            start = task_queue.get(timeout=2)

            try:
                range_header = {'Range': 'bytes={}-{}'.format(start, start + chunk_size)}
                resp = self.do_request('GET', headers=range_header)
                with open(filename, 'rb+') as f:
                    f.seek(start)
                    f.write(resp.content)
                content_length = int(resp.headers.get('Content-Length', 0))
            except requests.Timeout as e:
                logger.error("download timeout:%r", e)
                task_queue.put(start)
            except Exception as e:
                logger.error("download error:%r", e)
                task_queue.put(start)
            else:
                progress_queue.put(content_length)

    def get_content_length(self, url=None):
        resp = self.do_request('HEAD', url)
        return int(resp.headers.get('Content-Length', 0))


def worker(url, timeout, headers, cookies, proxies, filename, task_queue, progress_queue, chunk_size):
    handler = RequestHandler(url, timeout, headers, cookies, proxies)
    handler.handle(filename, task_queue, progress_queue, chunk_size)


class DownloadProcess(object):
    def __init__(
        self,
        url,
        thread=True,
        thread_num=30,
        chunk_size=1024 * 1024,
        timeout=30,
        filename=None,
        headers=None,
        cookies=None,
        proxies=None,
    ):
        self.url = url
        self.thread = thread
        self.thread_num = thread_num
        self.chunk_size = chunk_size
        self.timeout = timeout
        self.headers = headers
        self.cookies = cookies
        self.proxies = proxies
        self.filename = filename or self.parse_filename()
        self.request_handler = RequestHandler(self.url, headers=headers, cookies=cookies, proxies=proxies)
        self.content_length = self.request_handler.get_content_length()

    def parse_filename(self):
        return os.path.basename(urlparse(self.url).path)

    def process(self):
        if os.path.exists(self.filename) and os.path.getsize(self.filename) == self.content_length:
            print(u"【{}】: is exist".format(self.filename))
        else:
            f = open(self.filename, 'wb')
            f.truncate(self.content_length)
            f.close()

        if self.thread:
            worker_pool = ThreadPool(self.thread_num)
            task_queue = Queue()
            progress_queue = Queue()
        else:
            worker_pool = ProcessPool(self.thread_num)
            task_queue = Manager().Queue()
            progress_queue = Manager().Queue()

        progress = tqdm(total=self.content_length, unit='B', unit_scale=True, desc=u'【{}】'.format(self.filename))
        for start_index in range(0, self.content_length, self.chunk_size):
            task_queue.put(start_index)

        for thread in range(self.thread_num):
            worker_pool.apply_async(
                worker,
                (
                    self.url,
                    self.timeout,
                    self.headers,
                    self.cookies,
                    self.proxies,
                    self.filename,
                    task_queue,
                    progress_queue,
                    self.chunk_size,
                ),
            )

        while progress.total > progress.n:
            progress.update(progress_queue.get())

        worker_pool.close()
        progress.close()


@click.command()
@click.argument('url')
@click.option('--thread/--process', default=True, help='Use ThreadPool or ProcessPool')
@click.option('-w', '--worker_num', default=30, help='Number of workers')
@click.option('-s', '--chunk_size', default=1024 * 1024, help='Chunk size of each piece')
@click.option('-c', '--timeout', default=30, help='Timeout for chunk download')
@click.option('-f', '--filename', help='Filename of download')
@click.option('-h', '--headers', multiple=True, help='Headers to get file')
@click.option('-c', '--cookies', multiple=True, help='Cookie to get file')
@click.option('-p', '--proxies', multiple=True, help='Proxy to get file, pip install "requests[socks]"')
@click.help_option("-h", "--help")
def main(url, thread, worker_num, chunk_size, timeout, filename, headers, cookies, proxies):
    headers = dict([x.split('=') for x in headers])
    cookies = dict([x.split('=') for x in cookies])
    proxies = dict([x.split('=') for x in proxies])
    DownloadProcess(url, thread, worker_num, chunk_size, timeout, filename, headers, cookies, proxies).process()


if __name__ == '__main__':
    main()
