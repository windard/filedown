## filedown

多线程下载器

### Install

```
pip install filedown
```

或者

```
python setup.py install
```

### Usage

安装之后有两个下载命令，差异不大，择优使用。

1. filedown

```
$ filedown -h
Usage: filedown [OPTIONS] URL

Options:
  --thread / --process      Use ThreadPool or ProcessPool
  -w, --worker_num INTEGER  Number of workers
  -s, --chunk_size INTEGER  Chunk size of each piece
  -c, --timeout INTEGER     Timeout for chunk download
  -f, --filename TEXT       Filename of download
  -h, --headers TEXT        Headers to get file
  -c, --cookies TEXT        Cookie to get file
  -p, --proxies TEXT        Proxy to get file, pip install "requests[socks]"
  -h, --help                Show this message and exit.
```

2. concurrent_download

```
$ concurrent_download -h
Usage: concurrent_download [OPTIONS] URL

Options:
  -h, --help             Show this message and exit.
  -n, --num INTEGER      thread number
  -c, --chunk INTEGER    chunk download size
  -t, --timeout INTEGER  chunk download timeout

```

