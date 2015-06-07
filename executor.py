import re

import androguard.core.bytecodes.dvm as dvm

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
        self.tags = {}
        self.registers = {}
        self.last_field_name = None

    def const(self, inst):
        print inst.get_name(), 'OPERANDS:', inst.get_operands()
        operands = inst.get_operands()
        assert len(operands) == 2
        assert operands[0][0] == dvm.OPERAND_REGISTER
        reg = operands[0][1]
        assert operands[1][0] == dvm.OPERAND_LITERAL
        val = operands[1][1]
        self.registers[reg] = val

    def iget(self, inst):
        print inst.get_name(), 'OPERANDS:', inst.get_operands()
        class_name, field_type, field_name = inst.cm.get_field(inst.CCCC)
        self.last_field_name = field_name

    def invoke_virtual(self, inst):
        print inst.get_name(), 'OPERANDS:', inst.get_operands()
        method = inst.cm.get_method_ref(inst.BBBB)
        method_name = method.get_name()
        if not method_name.startswith('write'):
            return

        operands = inst.get_operands()
        assert operands[1][0] == dvm.OPERAND_REGISTER
        reg = operands[1][1]

        assert reg in self.registers
        assert self.last_field_name
        self.tags[self.last_field_name] = self.registers[reg]

    def get_tags(self):
        return self.tags


# if (this.backgroundAction != null) {
#     codedOutputByteBufferNano.writeMessage(4, this.backgroundAction);
# }


#    const/4 v0, 0x4
#
#    iget-object v1, p0, Lcom/google/android/finsky/analytics/PlayStore$PlayStoreLogEvent;->backgroundAction:Lcom/google/android/finsky/analytics/PlayStore$PlayStoreBackgroundActionEvent;
#
#    invoke-virtual {p1, v0, v1}, Lcom/google/protobuf/nano/CodedOutputByteBufferNano;->writeMessage(ILcom/google/protobuf/nano/MessageNano;)V
