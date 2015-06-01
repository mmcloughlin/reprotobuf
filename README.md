# reprotobuf
Reverse engineer protobuf nano

## Acknowledgments

Based on the [method for micro
protobuf](http://www.segmentationfault.fr/publications/reversing-google-play-and-micro-protobuf-applications/)
implemented in
[androproto.py](https://github.com/egirault/googleplay-api/blob/master/androguard/androproto.py),
and adapted for the nano case by
[androguard-protobuf-nano-extractor](https://github.com/bitpew/androguard-protobuf-nano-extractor).

## Ideas

* Use androguard to find the subclasses of `MessageNano`
* Fields of the class should be fields of the protobuf
* Java [field descriptors](https://docs.oracle.com/javase/specs/jvms/se7/html/jvms-4.html) can be parsed into data types
* Optional fields have corresponding `has<fieldname>` fields
* Getting the protobuf number for each field is harder
