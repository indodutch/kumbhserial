# README #

Python 3 implementation of the data logging example code.

### Setup ###

Install requirements first

```shell
pip install -r requirements.txt
pip install -e .
```

### Run ###

To use read out the raw data from the download devices, run:

```shell
kumbhdownload
```
Use `kumbhdownload -h` to see usage information.
Unless otherwise specified, the binary data ends up in the `./data/raw` directory.

To use read out the time from the sniffer, run:

```shell
kumbhsniffer
```
Unless otherwise specified, sniffer JSON data ends up in the `./data/sniffer` directory.

### License ###
Copyright 2016 Zoltan Beck, Netherlands eScience Center

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

[http://www.apache.org/licenses/LICENSE-2.0](http://www.apache.org/licenses/LICENSE-2.0)

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
