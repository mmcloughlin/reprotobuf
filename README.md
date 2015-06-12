# reprotobuf

Reverse engineer protobuf files from generated javanano code for android.

> This is development code which has only been tested against the Google Play
APK. As such it is still rough around the edges and may not work for other
cases.

## Installation

Either globally or inside a virtualenv:

```shell
pip install -r requirements.txt
```

## Usage

The main script works on the `classes.dex` file you'll find after you unzip
your APK. It writes to the directory `./output`, so please make sure that
exists.

```shell
python reprotobuf.py path/to/classes.dex
```

## Acknowledgments

Based on the [method for micro
protobuf](http://www.segmentationfault.fr/publications/reversing-google-play-and-micro-protobuf-applications/)
implemented in
[androproto.py](https://github.com/egirault/googleplay-api/blob/master/androguard/androproto.py),
and adapted for the nano case by
[androguard-protobuf-nano-extractor](https://github.com/bitpew/androguard-protobuf-nano-extractor).
