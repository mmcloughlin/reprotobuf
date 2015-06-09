def is_array(descriptor):
    return (descriptor[0] == '[')

def detect_system_class(classname):
    # deal with system types
    # with optional_field_style=reftypes we would see other java.lang.*
    # classes, but we're not dealing with that right now
    if classname.startswith('java/lang/'):
        assert classname == 'java/lang/String'
        return 'string'
    return None

def extract_classname(descriptor):
    assert descriptor[0] == 'L'
    assert descriptor[-1] == ';'
    return descriptor[1:-1]

PRIMITIVE_DESCRIPTORS = {
    'Z':  'bool',
    'B':  'int32',
    'S':  'int32',
    'C':  'int32',
    'I':  'int32',
    'J':  'int64',
    'F':  'float',
    'D':  'double',
}

def to_protobuf_type(descriptor):
    protobuf_type = {}

    # deal with the bytes special case
    if descriptor == '[B':
        protobuf_type['type'] = 'bytes'
        return protobuf_type

    # deal with the array case
    if is_array(descriptor):
        protobuf_type['rule'] = 'repeated'
        descriptor = descriptor[1:]

    # deal with the bytes special case (again)
    # which is the *only* case when we should see multi-dim arrays
    if descriptor == '[B':
        protobuf_type['type'] = 'bytes'
        return protobuf_type
    assert not is_array(descriptor)

    # deal with object types
    if descriptor[0] == 'L':
        classname = extract_classname(descriptor)
        system_type = detect_system_class(classname)
        if system_type:
            protobuf_type['type'] = system_type
        else:
            protobuf_type['ref'] = classname
        return protobuf_type

    # otherwise we should be looking at a primitive type
    assert descriptor in PRIMITIVE_DESCRIPTORS
    protobuf_type['type'] = PRIMITIVE_DESCRIPTORS[descriptor]
    return protobuf_type
