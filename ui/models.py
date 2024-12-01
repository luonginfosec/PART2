from PyQt5.QtCore import Qt
from PyQt5.QtGui import QBrush, QColor
from ui.datamodel import DataItem, DataModel

class RegistersModel(DataModel):
    def __init__(self, registers, items, parent=None):
        super(RegistersModel, self).__init__(("Name", "Data"), parent)

        self.registers = registers  # This class, or it can be a variable, is used to find values in createItem
        for item in items:
            self._rootItem.appendChild(self.createItem(item))

    def createItem(self, name):
        item = (name, self.registers.reg[name])  # self.registers.get_reg(name) is used to find the address of the corresponding register by name
        return DataItem(item)

class FlagModel(DataModel):
    def __init__(self, registers, items, parent=None):
        super(FlagModel, self).__init__(("Name", "Data"), parent)

        self.registers = registers  # This class, or it can be a variable, is used to find values in createItem
        for item in items:
            self._rootItem.appendChild(self.createItem(item))

    def format(self, data, bits):
        # Not debugged
        if isinstance(data, int):
            return str.format("0x{0:0%dx}" % 1, data)
        else:
            return data

    def createItem(self, name):
        item = (name, self.registers.FR.get_FR_reg(name))  # self.registers.get_reg(name) is used to find the address of the corresponding register by name
        return DataItem(item)

class CodeSegModel(DataModel):
    def __init__(self, BIU, ip, parent=None):
        super(CodeSegModel, self).__init__(("Addr.", "Data"), parent)
        self.ip = ip
        # Memory range not fully displayed code
        for addr in range(int('30000', 16), int('300ff', 16)):
            info = BIU.read_byte(addr)
            item = (hex(addr), ' '.join(info))
            self._rootItem.appendChild(DataItem(item))

    def data(self, index, role):
        if role == Qt.BackgroundRole and self.ip >= 0 and index.row() == self.ip:
            return QBrush(QColor("#6a4791"))

        return super(CodeSegModel, self).data(index, role)

class StackSegModel(DataModel):
    def __init__(self, BIU, sp, parent=None):
        super(StackSegModel, self).__init__(("Addr.", "Data"), parent)
        self.sp = sp
        # Memory range not fully displayed stack
        for addr in range(int('60000', 16), int('5ff00', 16), -1):
            info = BIU.read_byte(addr)
            item = (hex(addr), ' '.join(info))
            self._rootItem.appendChild(DataItem(item))

    def data(self, index, role):
        if role == Qt.BackgroundRole and self.sp >= 0 \
            and index.row() == (0x10000 - self.sp) % 0x10000:
            return QBrush(QColor("#53917f"))

        return super(StackSegModel, self).data(index, role)

class DataSegModel(DataModel):
    def __init__(self, BIU, parent=None):
        super(DataSegModel, self).__init__(("Addr.", "Data"), parent)

        # Memory range not fully displayed data
        for addr in range(int('20000', 16), int('200ff', 16)):
            info = BIU.read_byte(addr)
            if isinstance(info, int):
                item = (hex(addr), hex(info))
            else:
                item = (hex(addr), info[0])
            self._rootItem.appendChild(DataItem(item))