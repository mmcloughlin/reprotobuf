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
        return filter(lambda c: "MessageNano;" in c.get_superclassname(),
                self.dvm.get_classes())

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
        print '>>OPTIONAL', optional
        for name in optional:
            del fields[has_field_name(name)]
            fields[name]['required'] = False
        return fields

    def get_tags_from_class(self, cls):
        methods = [m for m in cls.get_methods() if m.get_name() == 'writeTo']
        assert len(methods) == 1

        method = self.vma.get_method(methods[0])
        basic_blocks = method.basic_blocks.gets()

        e = executor.WriteToExecutor()

        for bb in basic_blocks:
            for inst in bb.get_instructions():
                e.run(inst)

# main ---------------------------------------------------------

rpb = Reprotobuf.from_classes_dex(sys.argv[1])
proto_classes = rpb.get_proto_classes()

for cls in proto_classes:
    print '>>>>>>>>', cls.get_name()
    # deduce fields
    fields = rpb.get_fields_from_class(cls)
    for name, properties in fields.items():
        print '  ', name, properties['required'], properties['descriptor']
    # deduce tags
    rpb.get_tags_from_class(cls)

