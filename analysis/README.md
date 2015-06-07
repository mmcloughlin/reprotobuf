# Analysis

Message classes extend `MessageNano`. We can use androguard to find the
subclasses of `MessageNano`. Each of these classes has

* Fields
    - Fields of the class should be fields of the protobuf
    - Java [field descriptors](https://docs.oracle.com/javase/specs/jvms/se7/html/jvms-4.html) can be parsed into data types
    - Optional fields have corresponding `has<fieldname>` fields (although
      field names can start with `has`)
    - `_emptyArray` is a special field added by the code generator
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

Note that empty messages are valid, and the generated code will not have a
`writeTo()` method.

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


## Deducing Field Tags from Dalvik

The `writeTo()` method looks something like the following

```java
@Override
public void writeTo(CodedOutputByteBufferNano codedOutputByteBufferNano) throws IOException {
    if (this.hasDownloadSize || this.downloadSize != 0) {
        codedOutputByteBufferNano.writeInt64(1, this.downloadSize);
    }
    if (this.hasSignature || !this.signature.equals("")) {
        codedOutputByteBufferNano.writeString(2, this.signature);
    }
    if (this.hasDownloadUrl || !this.downloadUrl.equals("")) {
        codedOutputByteBufferNano.writeString(3, this.downloadUrl);
    }
    if (this.additionalFile != null && this.additionalFile.length > 0) {
        for (int i = 0; i < this.additionalFile.length; ++i) {
            AppFileMetadata appFileMetadata = this.additionalFile[i];
            if (appFileMetadata == null) continue;
            codedOutputByteBufferNano.writeMessage(4, appFileMetadata);
        }
    }
    if (this.downloadAuthCookie != null && this.downloadAuthCookie.length > 0) {
        for (int i = 0; i < this.downloadAuthCookie.length; ++i) {
            HttpCookie httpCookie = this.downloadAuthCookie[i];
            if (httpCookie == null) continue;
            codedOutputByteBufferNano.writeMessage(5, httpCookie);
        }
    }
    if (this.hasForwardLocked || this.forwardLocked) {
        codedOutputByteBufferNano.writeBool(6, this.forwardLocked);
    }

    ...
}
```

We will attempt to deduce the field tags from the calls to
`CodedOutputByteBufferNano.write<type>(<tag>, )` methods. We can use
androguard to process the smali code. The block for `downloadUrl` above looks
like

```smali
.line 924
:cond_3
iget-boolean v2, p0, Lcom/google/android/finsky/protos/AndroidAppDelivery$AndroidAppDeliveryData;->hasDownloadUrl:Z

if-nez v2, :cond_4

iget-object v2, p0, Lcom/google/android/finsky/protos/AndroidAppDelivery$AndroidAppDeliveryData;->downloadUrl:Ljava/lang/String;

const-string v3, ""

invoke-virtual {v2, v3}, Ljava/lang/String;->equals(Ljava/lang/Object;)Z

move-result v2

if-nez v2, :cond_5

.line 925
:cond_4
const/4 v2, 0x3

iget-object v3, p0, Lcom/google/android/finsky/protos/AndroidAppDelivery$AndroidAppDeliveryData;->downloadUrl:Ljava/lang/String;

invoke-virtual {p1, v2, v3}, Lcom/google/protobuf/nano/CodedOutputByteBufferNano;->writeString(ILjava/lang/String;)V
```

The `const/4` instruction tells us the tag, and the protobuf field name can be
extracted from the `iget` command. We can iterate through the instructions in
the `writeTo()` method, and record the results when we encounter
`invoke-virtual` instructions. This seems to be robust to `repeated` fields
too. There are some awkward cases, like the `downloadSize` field below where
we have to disambiguate two `const` commands. To properly handle cases like
this, we decide to track which register the constant is written into, and
reference the value in the subsequent `invoke-virtual`.

```smali
.prologue
const/4 v8, 0x1

const-wide/16 v6, 0x0

.line 918
iget-boolean v2, p0, Lcom/google/android/finsky/protos/AndroidAppDelivery$AndroidAppDeliveryData;->hasDownloadSize:Z

if-nez v2, :cond_0

iget-wide v2, p0, Lcom/google/android/finsky/protos/AndroidAppDelivery$AndroidAppDeliveryData;->downloadSize:J

cmp-long v2, v2, v6

if-eqz v2, :cond_1

.line 919
:cond_0
iget-wide v2, p0, Lcom/google/android/finsky/protos/AndroidAppDelivery$AndroidAppDeliveryData;->downloadSize:J

invoke-virtual {p1, v8, v2, v3}, Lcom/google/protobuf/nano/CodedOutputByteBufferNano;->writeInt64(IJ)V
```
