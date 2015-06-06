import re

class SmaliExecutor(object):
    def __init__(self):
        inst_sep = ['-', '/']
        inst_split_pattern = '|'.join(map(re.escape, inst_sep))
        self.inst_split_re = re.compile(inst_split_pattern)

    def run(self, inst):
        name = inst.get_name()
        inst_parts = self.inst_split_re.split(name)
        for i in range(len(inst_parts)):
            method_name = '_'.join(inst_parts[:i+1])
            try:
                method = getattr(self, method_name)
                return method(inst)
            except:
                continue
        return None


class WriteToExecutor(SmaliExecutor):
    def __init__(self):
        super(WriteToExecutor, self).__init__()
        self.reset_state()

    def reset_state(self):
        self.last_const = None
        self.last_field_name = None

    def const(self, inst):
        #print '>>', inst.get_name()
        literals = inst.get_literals()
        assert len(literals) == 1
        self.last_const = literals[0]

    def iget(self, inst):
        #print '>>', inst.get_name()
        #print '>>>', inst.get_operands()
        class_name, field_type, field_name = inst.cm.get_field(inst.CCCC)
        self.last_field_name = field_name

    def invoke_virtual(self, inst):
        #print '>>', inst.get_name()
        #print '>>>', inst.get_operands()
        method = inst.cm.get_method_ref(inst.BBBB)
        method_name = method.get_name()
        if not method_name.startswith('write'):
            return
        print '>>>', self.last_const, self.last_field_name
        assert self.last_const
        assert self.last_field_name
        self.reset_state()



# if (this.backgroundAction != null) {
#     codedOutputByteBufferNano.writeMessage(4, this.backgroundAction);
# }


#    const/4 v0, 0x4
#
#    iget-object v1, p0, Lcom/google/android/finsky/analytics/PlayStore$PlayStoreLogEvent;->backgroundAction:Lcom/google/android/finsky/analytics/PlayStore$PlayStoreBackgroundActionEvent;
#
#    invoke-virtual {p1, v0, v1}, Lcom/google/protobuf/nano/CodedOutputByteBufferNano;->writeMessage(ILcom/google/protobuf/nano/MessageNano;)V
