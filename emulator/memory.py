import sys
from emulator.assembler import Assembler
from emulator.isr import load_isr


class Memory(object):

    def __init__(self, max_space, seg_size):
        self.max_space = max_space
        self.seg_size = seg_size
        self.space = [['0']] * self.max_space

    def is_null(self, loc):
        return self.space[loc] == ['0']

    def verify(self, loc):
        # Verify valid address
        if loc < 0 or loc > self.max_space:
            sys.exit(f"Memory Overflow when reading {loc}")

    def rb(self, loc):
        self.verify(loc)
        # print("Memory reading byte from", hex(loc))
        return self.space[loc]

    def wb(self, loc, content):
        # content is a list
        self.verify(loc)
        self.space[loc] = content
        
    def load(self, exe):
        # Loader
        self.refresh()
        print("loading assembly code to memory...")
        for seg, val in exe.space.items():
            adr = int(exe.seg_adr[seg], 16) * 16
            print(hex(adr))
            self.space[adr: adr + self.seg_size] = val
            print(self.space[adr:adr+100])
        # Load interrupt vector table and interrupt routines
        load_isr(self)
        print("successfully loaded!")
        print()

        
    def refresh(self):
        self.space = [['0']] * self.max_space


# class Cache_memory(Memory):
#     # Cache
#     def __init__(self, max_space):
#         super(Cache_memory, self).__init__(max_space, 0)

#     def is_null_space(self, loc):
#         return self.read_byte(loc) == [0]