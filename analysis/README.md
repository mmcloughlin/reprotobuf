# Analysis

Message classes extend `MessageNano`. We can use androguard to find the
subclasses of `MessageNano`. Each of these classes has

* Fields
    - Fields of the class should be fields of the protobuf
    - Java [field descriptors](https://docs.oracle.com/javase/specs/jvms/se7/html/jvms-4.html) can be parsed into data types
    - Optional fields have corresponding `has<fieldname>` fields (although
      field names can start with `has`)
* `clear()` initializes the class
* `computeSerializedSize()` returns the size of the encoded form
    - contains calls to sizes of contained types
    - tags could be extracted from here
* `mergeFrom()`
    - loads fields
    - switch statement on the field tag
* `writeTo()`
    - writes fields
    - many calls to `write<type>(tag, ...)`
    - could potentially get the tags from here

We can also inspect the [code generator for these
classes](https://github.com/google/protobuf/tree/master/src/google/protobuf/compiler/javanano).

## Example Compilation

We can observe how the compiler works with a basic example that exercises many
of the features of protobuf. In this directory, `ExampleProtos.java` was
created from `example.proto` with

```
protoc --javanano_out . example.proto
```

The Google Play JavaNano classes appear to have been generated with an older
version of `protoc` than was used here. In particular they use the
`java_nano_generate_has` option which has since been deprecated.
