import sys
import queue
import time
import pprint

class bus_interface_unit(object):

    def __init__(self, instruction_queue_size, exe, memory):
        # Prefetch instruction queue
        self.instruction_queue = queue.Queue(instruction_queue_size) # Prefetch input queue
        
        self.reg = {
            'DS': int(exe.seg_adr['DS'], 16),
            'CS': int(exe.seg_adr['CS'], 16),
            'SS': int(exe.seg_adr['SS'], 16),
            'ES': int(exe.seg_adr['ES'], 16),
            'IP': int(exe.ip, 16)
        }
        self.pre_fetch_ip = self.reg['IP']

        # print("Initial DS:", hex(self.reg['DS']))
        # print("Initial CS:", hex(self.reg['CS']))
        # print("Initial SS:", hex(self.reg['SS']))
        # print("Initial ES:", hex(self.reg['ES']))
        # print("Initial IP:", hex(self.reg['IP']))
        
        self.memory = memory # External bus to memory

    @property
    def cs_ip(self):
        return self.reg['CS'] * 16 + self.reg['IP']

    @property
    def cs_pre_ip(self):
        return self.reg['CS'] * 16 + self.pre_fetch_ip

    def read_byte(self, loc):
        return self.memory.rb(loc)

    def read_word(self, loc):
        return self.read_byte(loc + 1) + self.read_byte(loc)

    def read_dword(self, loc):
        # return list
        return self.read_byte(loc + 3) + self.read_byte(loc + 2) + \
               self.read_byte(loc + 1) + self.read_byte(loc)

    def write_byte(self, loc, content):
        # content can be：int、list
        if isinstance(content, int):
            content = [hex(content)]
        elif isinstance(content, list):
            pass
        else:
            sys.exit("Error write_byte")
        self.memory.wb(loc, content)

    def write_word(self, loc, content): # little endian
        if isinstance(content, int):
            self.write_byte(loc, content & 0x0ff)
            self.write_byte(loc + 1, (content >> 8) & 0x0ff)
        elif isinstance(content, list):
            for res in content:
                self.write_byte(loc, [res])
                loc += 1
        else:
            sys.exit("Error write_word")

    def write_dword(self, loc, content): # little endian
        if isinstance(content, int):
            self.write_byte(loc, content & 0x0ff)
            self.write_byte(loc + 1, (content >> 8) & 0x0ff)
            self.write_byte(loc + 2, (content >> 16) & 0x0ff)
            self.write_byte(loc + 3, content >> 24)
        else:
            sys.exit("Error write_byte")

    def run(self):
        # Imitate the 8086 instruction fetch mechanism, and fetch instructions when there are 2 or more instructions missing in the queue.
        if self.instruction_queue.qsize() <= self.instruction_queue.maxsize - 2:
            self.fill_instruction_queue()
    @property
    def next_ins(self):
        # Pipeline next instruction
        ins_list = list(self.instruction_queue.queue)
        if ins_list:
            return ins_list[0]
        else:
            return "Pipline is emtpy."

    def flush_pipeline(self):
        # Refresh when there is a branch pipeline
        # print("Flushing pipeline...")
        self.instruction_queue.queue.clear()
        self.pre_fetch_ip = self.reg['IP']

    def remain_instruction(self):
        # Determine whether there are instructions in the cache that need to be executed
        return not self.memory.is_null(self.cs_pre_ip)

    def fetch_one_instruction(self):
        # Get a single instruction
        instruction = self.memory.rb(self.cs_pre_ip)
        self.instruction_queue.put(instruction)
        self.pre_fetch_ip += 1
        # print("Fetching one ins to pipeline:")
        # pprint.pprint(list(self.instruction_queue.queue))
        # print()

    def fill_instruction_queue(self):
        # print("filling pipeline...")
        while not self.instruction_queue.full():
            # time.sleep(0.2)
            if not self.memory.is_null(self.cs_pre_ip):
                self.fetch_one_instruction()
            else:
                break
