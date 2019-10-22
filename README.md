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

1. filedown

```
$ filedown --help
Usage: filedown [OPTIONS] URL

  :param url: :param thread_num: :param filename: :param cookie: :param
  header: :param proxy: pip install "requests[socks]" first :return:

Options:
  -t, --thread_num INTEGER  Number of threads
  -f, --filename TEXT       Filename of download
  -h, --header TEXT         Headers to attach file
  -c, --cookie TEXT         Cookie to attach file
  -p, --proxy TEXT          Proxy to attach file
  --help                    Show this message and exit.
```

2. only_download

```
$ only_download --help
Usage: only_download URL [thread_num]
    example: only_download https://baidu.com/index.html

```

