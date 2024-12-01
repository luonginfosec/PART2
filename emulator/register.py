import sys

# class General_register(object):
#     # General-purpose register
#     def __init__(self, list):
#         self.list = list
#         self.reg_count = len(list)
#         self.space = {}
#         for reg_name in list:
#             self.space[reg_name] = 0
#         print("initialize register done:")
#         print(self.space)
#         print()
    
#     def read(self, reg_name):
#         if reg_name not in self.list:
#             sys.exit("register name error")
#         return self.space[reg_name]
    
#     def read_int(self, reg_name):
#         if reg_name not in self.list:
#             sys.exit("register name error")
#         return int(self.space[reg_name])
    
#     def write(self, reg_name, content):
#         # content is a list
#         if reg_name not in self.list:
#             sys.exit("register name error")
#         self.space[reg_name] = content

# class Register(int):

#     def __new__(cls, value=0, *args, **kwargs):
#         return  super(cls, cls).__new__(cls, value)

#     def __str__(self):
#         return "%d" % int(self)

#     def __repr__(self):
#         return "%d" % int(self)

#     def __len__(self):
#         return self.bit_length()
    
#     def __add__(self, other):
#         res = super(Register, self).__add__(other)
#         return self.__class__(res)

#     def __sub__(self, other):
#         res = super(Register, self).__sub__(other)
#         return self.__class__(res)

#     def __mul__(self, other):
#         res = super(Register, self).__mul__(other)
#         return self.__class__(res)

#     def __div__(self, other):
#         res = super(Register, self).__div__(other)
#         return self.__class__(res)
    
#     def __truediv__(self, other):
#         res = super(Register, self).__truediv__(other)
#         return self.__class__(res)
    
#     def __floordiv__(self, other):
#         res = super(Register, self).__floordiv__(other)
#         return self.__class__(res)
    
#     def __rshift__(self, other):
#         res = super(Register, self).__rshift__(other)
#         return self.__class__(res)

#     def __lshift__(self, other):
#         res = super(Register, self).__lshift__(other)
#         return self.__class__(res)
    
#     def __and__(self, other):
#         res = super(Register, self).__and__(other)
#         return self.__class__(res)

#     def __or__(self, other):
#         res = super(Register, self).__or__(other)
#         return self.__class__(res)

#     def __neg__(self):
#         res = super(Register, self).__neg__()
#         return self.__class__(res)

#     def __pos__(self):
#         res = super(Register, self).__pos__()
#         return self.__class__(res)

#     def __invert__(self):
#         res = super(Register, self).__invert__()
#         return self.__class__(res)

#     @property
#     def hex(self):
#         return hex(self)

#     @property
#     def bin(self):
#         return bin(self)

#     @property
#     def high(self):
#         return self >> 8 & 0xff

#     @property
#     def low(self):
#         return self & 0xff

#     def write_high(self, num):
#         # Operand check should be here
#         return (self & 0xff) + (num << 8)

#     def write_low(self, num):
#         # Operand check should be here
#         return (self & 0xff00) + num

class Flag_register(object):
    # Flag register
    # 16-bit flag register, where 9 bits are used, and the other 7 bits are reserved
    def __init__(self):
        # status flags
        self.sign = 0       # S
        self.zero = 0       # Z
        self.auxiliary = 0  # AC unused
        self.parity = 0     # P
        self.carry = 0      # CY
        self.overflow = 0   # O
        # control flags
        self.direction = 0  # D
        self.interrupt = 0  # I
        self.trap = 0       # T
    
    def get_int(self):
        return (self.overflow << 11) + (self.direction << 10) + (self.interrupt << 9) + \
            (self.trap << 8) + (self.sign << 7) + (self.zero << 6) + (self.auxiliary << 4) + \
                (self.parity << 2) + (self.carry)

    def get_low(self):
        return self.get_int() & 0xff

    def set_low(self, num):
        self.sign = num >> 7 & 1
        self.zero = num >> 6 & 1
        self.auxiliary = num >> 4 & 1
        self.parity = num >> 2 & 1
        self.carry = num & 1

    def set_int(self, num):
        self.set_low(num & 0xff)
        self.overflow = num >> 11 & 1
        self.direction = num >> 10 & 1
        self.interrupt = num >> 9 & 1
        self.trap = num >> 8 & 1

    def get_FR_reg(self,name):
        self.reg = {
            'CF': self.carry,
            'PF': self.parity,
            'AF': self.auxiliary,
            'Z': self.zero,
            'S': self.sign,
            'O': self.overflow,
            'TF': self.trap,
            'IF': self.interrupt,
            'DF': self.direction
        }
        return self.reg[name]
        
# class Register_file(object):
#     # Register file
#     def __init__(self, DS_START, CS_START, SS_START, ES_START):
#         # General Purpose Registers
#         self.GR = General_register(["AX","BX","CX","DX"])
#         # Segment Registers
#         self.DS = Register(DS_START)
#         self.CS = Register(CS_START)
#         self.SS = Register(SS_START)
#         self.ES = Register(ES_START)
#         # Pointers and Index Registers
#         self.SP = Register()
#         self.BP = Register()
#         self.SI = Register()
#         self.DI = Register()
#         # Control register
#         self.IP = Register()
#         self.FR = Flag_register()