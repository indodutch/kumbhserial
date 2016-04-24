# README #

Python 3 implementation of the data logging example code.

### Setup ###

Install requirements first

```shell
pip install -r requirements.txt
pip install .
```

### Run ###

To use read out the data from the download devices, run:

```shell
kumbhdownload
```
Use `kumbhdownload -h` to see usage information. In particular, use the `-J` option to disable the parser and only write raw text.
Unless otherwise specified, the binary data ends up in the `./data/raw/processed` and the JSON data ends up in the `./data/detections` and `./data/system` directories.

To use read out the time from the sniffer, run:

```shell
kumbhsniffer
```
Unless otherwise specified, sniffer JSON data ends up in the `./data/sniffer` directory.

To process any unprocessed files, run `kumbhprocessor`.
