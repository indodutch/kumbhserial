# Kumbh Mela serial devices #

[![Build Status](https://travis-ci.org/indodutch/kumbhserial.svg?branch=master)](https://travis-ci.org/indodutch/kumbhserial)
[![Codacy Badge](https://api.codacy.com/project/badge/Grade/36476556fdc94aa1b4a15ea978924e93)](https://www.codacy.com/app/github_4/kumbhserial?utm_source=github.com&amp;utm_medium=referral&amp;utm_content=indodutch/kumbhserial&amp;utm_campaign=Badge_Grade)

Python 3 implementation for extracting data from devices in Kumbh Mela with a serial device driver.

## Installation ##

Use virtualenv or virtualenvwrapper to set up a suitable Python 3.4 or 3.5 environment.

Install the project with

```shell
pip install -r requirements.txt
```

## Usage ##

To read out the data from the download devices, run:

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

To read the Thinture GPS devices with `kumbhgps`. Again, see the options with `-h` flag.
