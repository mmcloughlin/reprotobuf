# Analysis

Message classes extend `MessageNano`. We can use androguard to find the
subclasses of `MessageNano`. We also need to exclude a few `abstract`
subclasses like `ParcelableMessageNano`, which do not correspond to protobuf
message types. Each of the actual message classes has

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

The class `com.google.android.finsky.protos.DocumentV2$WideCardContainer` also
presents another edge case, where the `const` commands actually appear
out-of-order. This is another case where we need to track which register the
constants live in.

```smali
.method public writeTo(Lcom/google/protobuf/nano/CodedOutputByteBufferNano;)V
    .locals 3
    .parameter "output"
    .annotation system Ldalvik/annotation/Throws;
        value = {
            Ljava/io/IOException;
        }
    .end annotation

    .prologue
    const/4 v2, 0x2

    .line 6760
    iget-boolean v0, p0, Lcom/google/android/finsky/protos/DocumentV2$WideCardContainer;->hasRowCount:Z

    if-nez v0, :cond_0

    iget v0, p0, Lcom/google/android/finsky/protos/DocumentV2$WideCardContainer;->rowCount:I

    if-eq v0, v2, :cond_1

    .line 6761
    :cond_0
    const/4 v0, 0x1

    iget v1, p0, Lcom/google/android/finsky/protos/DocumentV2$WideCardContainer;->rowCount:I

    invoke-virtual {p1, v0, v1}, Lcom/google/protobuf/nano/CodedOutputByteBufferNano;->writeInt32(II)V

    .line 6763
    :cond_1
    iget-boolean v0, p0, Lcom/google/android/finsky/protos/DocumentV2$WideCardContainer;->hasShowOrdinals:Z

    if-nez v0, :cond_2

    iget-boolean v0, p0, Lcom/google/android/finsky/protos/DocumentV2$WideCardContainer;->showOrdinals:Z

    if-eqz v0, :cond_3

    .line 6764
    :cond_2
    iget-boolean v0, p0, Lcom/google/android/finsky/protos/DocumentV2$WideCardContainer;->showOrdinals:Z

    invoke-virtual {p1, v2, v0}, Lcom/google/protobuf/nano/CodedOutputByteBufferNano;->writeBool(IZ)V

    .line 6766
    :cond_3
    invoke-super {p0, p1}, Lcom/google/protobuf/nano/MessageNano;->writeTo(Lcom/google/protobuf/nano/CodedOutputByteBufferNano;)V

    .line 6767
    return-void
.end method
```

## Java Type Descriptors

We need to map from the [field descriptor
syntax](https://docs.oracle.com/javase/specs/jvms/se7/html/jvms-4.html#jvms-4.3.2)
to protobuf types. For the primitive types, we will need to determine a
mapping to [protobuf scalar
types](https://developers.google.com/protocol-buffers/docs/proto#scalar).

The mapping is specified in the [javanano
code](https://github.com/google/protobuf/blob/ed3c8a11f98995c6bf210566ea10659cb3f3abff/src/google/protobuf/compiler/java/java_helpers.cc#L263-L307)
as follows

```cpp
JavaType GetJavaType(const FieldDescriptor* field) {
  switch (GetType(field)) {
    case FieldDescriptor::TYPE_INT32:
    case FieldDescriptor::TYPE_UINT32:
    case FieldDescriptor::TYPE_SINT32:
    case FieldDescriptor::TYPE_FIXED32:
    case FieldDescriptor::TYPE_SFIXED32:
      return JAVATYPE_INT;

    case FieldDescriptor::TYPE_INT64:
    case FieldDescriptor::TYPE_UINT64:
    case FieldDescriptor::TYPE_SINT64:
    case FieldDescriptor::TYPE_FIXED64:
    case FieldDescriptor::TYPE_SFIXED64:
      return JAVATYPE_LONG;

    case FieldDescriptor::TYPE_FLOAT:
      return JAVATYPE_FLOAT;

    case FieldDescriptor::TYPE_DOUBLE:
      return JAVATYPE_DOUBLE;

    case FieldDescriptor::TYPE_BOOL:
      return JAVATYPE_BOOLEAN;

    case FieldDescriptor::TYPE_STRING:
      return JAVATYPE_STRING;

    case FieldDescriptor::TYPE_BYTES:
      return JAVATYPE_BYTES;

    case FieldDescriptor::TYPE_ENUM:
      return JAVATYPE_ENUM;

    case FieldDescriptor::TYPE_GROUP:
    case FieldDescriptor::TYPE_MESSAGE:
      return JAVATYPE_MESSAGE;

    // No default because we want the compiler to complain if any new
    // types are added.
  }

  GOOGLE_LOG(FATAL) << "Can't get here.";
  return JAVATYPE_INT;
}
```

So for primitive types we have

| Descriptor | Java | Protobuf |
| Z | boolean | bool   |
| B | byte    | int32  |
| S | short   | int32  |
| C | char    | int32  |
| I | int     | int32  |
| J | long    | int64  |
| F | float   | float  |
| D | double  | double |

Then we have to deal with complex types: object and array types.

Array types are indicated by an initial `[`, followed by the descriptor of the
type contained in the array (which can be another array). In the case of
protobuf fields, we should generally only see up to one `[` character at the
start, indicating this is a `repeated` field. However there is one exception
because of the `bytes` protobuf type. The java descriptor for `bytes` is `[B`,
and `repeated bytes` is therefore `[[B`.
