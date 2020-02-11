# -*- coding: utf-8 -*-
from __future__ import division

import sys
import time
import math
import click
import random
import requests
from urllib3 import Retry
from requests.adapters import HTTPAdapter

from gevent import monkey
monkey.patch_all()

import threading

from tqdm import tqdm

try:
    from urlparse import urlparse
    from Queue import Queue
except ImportError:
    from queue import Queue
    from urllib.parse import urlparse


s = requests.session()
retries = Retry(total=3, backoff_factor=0.1)
s.mount('http://', HTTPAdapter(max_retries=retries))
s.mount('https://', HTTPAdapter(max_retries=retries))


class FileDownException(Exception):
    pass


def ceil_div(a, b):
    return int(math.ceil(a / b))


class RequestHandler(object):

    def __init__(self, url=None, timeout=10, headers=None, cookies=None,
                 proxies=None):
        self.url = url
        self.timeout = timeout
        self.headers = headers or {}
        self.cookies = cookies or {}
        self.proxies = proxies or {}
        self.session = s

    def do_request(self, method, url=None, headers=None, cookies=None,
                   proxies=None, **kwargs):
        url = url or self.url
        if headers:
            self.headers.update(headers)
        if cookies:
            self.cookies.update(cookies)
        if proxies:
            self.proxies.update(proxies)
        resp = self.session.request(method=method,
                                    url=url,
                                    headers=self.headers,
                                    cookies=self.cookies,
                                    proxies=self.proxies,
                                    timeout=self.timeout,
                                    allow_redirects=False,
                                    **kwargs)
        return resp

    def get_content_length(self, url=None):
        resp = self.do_request('HEAD', url)
        if resp.status_code != 200:
            raise FileDownException("HEAD request not allow")
        return int(resp.headers['Content-Length'])

    def get_range_content(self, range_start, range_end, url=None):
        range_header = {'Range': 'bytes={}-{}'.format(range_start, range_end)}
        return self.do_request('GET', url, headers=range_header, stream=True)


class DownloadProcess(object):
    def __init__(self, url, thread_num, filename=None, headers=None,
                 cookies=None, proxies=None):
        self.url = url
        self.thread_num = thread_num
        self.filename = filename or self.parse_filename()
        self.queue = Queue(thread_num * 2)
        self.request_handler = RequestHandler(self.url, headers=headers,
                                              cookies=cookies, proxies=proxies)
        self.content_length = self.request_handler.get_content_length()
        self.interval = ceil_div(self.content_length, self.thread_num)
        self.progress = tqdm(total=self.content_length, unit='B',
                             unit_scale=True, desc=self.filename)

    def parse_filename(self):
        return urlparse(self.url).path.rsplit('/')[-1]

    def process(self):
        sys.stdout.write("\033[2K\033[E")
        sys.stdout.write('download process start. \n')
        sys.stdout.write(
            'length %d, filename %s \n' % (self.content_length, self.filename))

        f = open(self.filename, 'wb')
        f.truncate(self.content_length)
        f.close()

        t = threading.Thread(target=self.update_progress)
        t.setDaemon(True)
        t.start()

        download_handlers = []
        for i in range(self.thread_num):
            start = i * self.interval
            end = start + self.interval
            download_handlers.append(
                DownloadHandler(self.url, self.filename, self.queue, start,
                                end, str(i), self.request_handler))

        for d in download_handlers:
            d.start()
        for d in download_handlers:
            d.join()

        self.progress.close()
        sys.stdout.write('download process end. \n')

    def update_progress(self):
        while 1:
            self.progress.update(self.queue.get())


class DownloadHandler(threading.Thread):
    def __init__(self, url, filename, queue, start, end, name,
                 request_handler):
        super(DownloadHandler, self).__init__()
        self.url = url
        self.range_start = start
        self.range_end = end
        self.filename = filename
        self.queue = queue
        self.name = name
        self.request_handler = request_handler
        self.chunk_size = 1024 * 10
        self.downloaded = 0

    def process(self):
        try:
            resp = self.request_handler.get_range_content(
                range_start=self.range_start, range_end=self.range_end)
        except requests.ConnectionError as e:
            sys.stdout.write('Thread-%s %r\n' % (self.name, e))
            time.sleep(random.random())
            resp = self.request_handler.get_range_content(
                range_start=self.range_start, range_end=self.range_end)

        with open(self.filename, 'rb+') as f:
            f.seek(self.range_start)
            for data in resp.iter_content(chunk_size=self.chunk_size):
                f.write(data)
                self.queue.put(len(data))
                self.downloaded += len(data)

    def run(self):
        sys.stdout.write('Thread-%s start range %d-%d\n' % (
            self.name, self.range_start, self.range_end))

        try:
            self.process()
        except requests.ConnectionError as e:
            sys.stdout.write('Thread-%s %r\n' % (self.name, e))
            time.sleep(random.random())
            self.process()

        sys.stdout.write("Thread-%s end range %d-%d\n" % (
            self.name, self.range_start, self.range_end))


@click.command()
@click.option('-t', '--thread_num', default=8, help='Number of threads')
@click.option('-f', '--filename', help='Filename of download')
@click.option('-h', '--header', multiple=True, help='Headers to attach file')
@click.option('-c', '--cookie', multiple=True, help='Cookie to attach file')
@click.option('-p', '--proxy', multiple=True, help='Proxy to attach file')
@click.argument('url')
def main(url, thread_num, filename, cookie, header, proxy):
    """

    :param url:
    :param thread_num:
    :param filename:
    :param cookie:
    :param header:
    :param proxy: pip install "requests[socks]" first
    :return:
    """
    headers = dict([x.split('=') for x in header])
    cookies = dict([x.split('=') for x in cookie])
    proxies = dict([x.split('=') for x in proxy])
    DownloadProcess(url, thread_num, filename, headers=headers,
                    cookies=cookies, proxies=proxies).process()


if __name__ == '__main__':
    """
    两个问题
    1. 异常捕获和处理，ConnectionError
    2. 线程池用完后期下载速度乏力
    """
    main()
