import sys

# read apk
#import androguard.core.bytecodes.apk as apk
#a = apk.APK(sys.argv[1])

import androguard.core.bytecodes.dvm as dvm
from androguard.core.analysis.analysis import *

import executor


# XXX must be library for this
def has_field_name(s):
    """
    fieldName -> hasFieldName
    """
    return 'has' + s[:1].upper() + s[1:]


class Reprotobuf(object):
    def __init__(self, classes_dex):
        self.dvm = dvm.DalvikVMFormat(classes_dex)
        self.vma = uVMAnalysis(self.dvm)

    @classmethod
    def from_classes_dex(cls, filename):
        with open(sys.argv[1], 'rb') as f:
            classes_dex = f.read()
        return cls(classes_dex)

    def get_proto_classes(self):
        def is_proto(cls):
            return ('MessageNano;' in cls.get_superclassname() and
                    'abstract' not in cls.get_access_flags_string())
        return filter(is_proto, self.dvm.get_classes())

    def get_fields_from_class(self, cls):
        """
        Deduce fields by inspecting the fields of the Java class.
        """
        # fetch all the fields
        fields = {}
        for field in cls.get_fields():
            name = field.get_name()
            fields[name] = {
                    'name': name,
                    'descriptor': field.get_descriptor(),
                    'required': True,
                    }
        # deduce optional ones from has* fields
        optional = []
        for name in fields:
            if has_field_name(name) in fields:
                optional.append(name)
        # mark the optional fields, and remove
        for name in optional:
            del fields[has_field_name(name)]
            fields[name]['required'] = False
        # remove _emptyArray if it exists
        fields.pop('_emptyArray', None)
        return fields

    def get_tags_from_class(self, cls):
        methods = [m for m in cls.get_methods() if m.get_name() == 'writeTo']
        if len(methods) == 0:
            return {}

        method = self.vma.get_method(methods[0])
        basic_blocks = method.basic_blocks.gets()

        e = executor.WriteToExecutor()

        for bb in basic_blocks:
            for inst in bb.get_instructions():
                e.run(inst)

        return e.get_tags()

# main ---------------------------------------------------------

rpb = Reprotobuf.from_classes_dex(sys.argv[1])
proto_classes = rpb.get_proto_classes()

for cls in proto_classes:
    print '>>>>>>>>', cls.get_name()
    # deduce fields
    fields = rpb.get_fields_from_class(cls)
    # deduce tags
    tag_map = rpb.get_tags_from_class(cls)
    for name, tag in tag_map.items():
        assert name in fields
        fields[name]['tag'] = tag
    # report
    tags = set()
    for name, properties in fields.items():
        for k, v in properties.items():
            print '%s=%s' % (k, v),
        if 'tag' in properties:
            tags.add(properties['tag'])
        else:
            print 'ERROR:TAG_MISSING',
        print

    if len(tags) < len(fields):
        print 'ERROR:TAGS_MISSING'
    if len(tags) == 0:
        print 'ERROR:ZERO_TAGS'
        continue
    if min(tags) != 1 or max(tags) != len(tags):
        print 'ERROR:TAGRANGE'
        upper = max(max(tags), len(tags))
        for t in range(1, upper+1):
            print '%2d' % (t),
        print
        for t in range(1, upper+1):
            print '..' if t in tags else 'xx',
        print
    print

