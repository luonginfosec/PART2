import time
import re
from pprint import pprint
from emulator.assembler import Assembler, to_decimal

class CPU(object):
    
    def __init__(self, BIU, EU, gui_mode):
        self.cycle_count = 0
        self.BIU = BIU
        self.EU = EU
        self.gui_mode = gui_mode

    def iterate(self, debug=False):
        self.cycle_count += 1
        if debug:
            self.EU.print(f"clock cycle {self.cycle_count}: fetching...\n")

        self.fetch_cycle()

        self.cycle_count += 1
        if debug:
            print(f"clock cycle {self.cycle_count}: executing...\n")

        self.execute_cycle()

        if (debug or self.EU.interrupt):
            self.print_state()
            if not self.gui_mode :
                self.debug()
                self.EU.interrupt = False

    def debug(self):
        while True:
            cmd = input("Press Enter to continue...\n> ").strip()
            if not cmd:
                return
            cmd = cmd.upper().split()
            if cmd[0] == 'A': # input and run the code (simple code)
                asm_code = input("Run code > ")
                ins = [s for s in re.split(" |,", asm_code.strip().upper()) if s]
                self.EU.print(ins)
                self.EU.opcode = ins[0]
                if len(ins) > 1:
                    self.EU.opd = ins[1:]
                self.EU.get_opbyte()
                self.EU.control_circuit()
                return

            if cmd[0] == 'D': # show memory:  d 0x20000
                if len(cmd) == 2:
                    adr1 = self.EU.get_int(cmd[1])
                    self.show_memory(adr1, adr1 + 50)
                elif len(cmd) == 3:
                    adr1 = to_decimal(cmd[1])
                    adr2 = to_decimal(cmd[2])
                    self.show_memory(adr1, adr2)

            elif cmd[0] == 'R': # show registers
                self.show_regs()

    def fetch_cycle(self):
        # Instruction fetch cycle
        self.BIU.run()
        pass

    def execute_cycle(self):
        # Instruction execution cycle
        self.EU.run()
        pass
    
    def check_done(self):
        # Check if there are no instructions, end CPU operation
        if self.EU.interrupt or self.EU.shutdown:
            return True
        return  self.BIU.instruction_queue.empty() and \
                not self.BIU.remain_instruction()

    def show_regs(self):
        for key, val in list(self.EU.reg.items())[:4]:
            print(key, '0x{:0>4x}'.format(val), end='   ')
        print()
        for key, val in list(self.EU.reg.items())[4:]:
            print(key, '0x{:0>4x}'.format(val), end='   ')
        print()
        for key, val in self.BIU.reg.items():
            print(key, '0x{:0>4x}'.format(val), end='   ')
        print()
        print('S ', self.EU.FR.sign, end='  ')
        print('Z', self.EU.FR.zero, end='   ')
        print('AC', self.EU.FR.auxiliary, end='  ')
        print('P', self.EU.FR.parity, end='   ')
        print('CY', self.EU.FR.carry, end='  ')
        print('O', self.EU.FR.overflow, end='   ')
        print('D ', self.EU.FR.direction, end='  ')
        print('I', self.EU.FR.interrupt, end='   ')
        print('T ', self.EU.FR.trap, end='  ')
        print()

    def show_memory(self, begin, end):
        pprint(self.BIU.memory.space[begin: end], compact=True)

    def print_state(self):
        # Print runtime state
        print("\nPipeline:")
        pprint(list(self.BIU.instruction_queue.queue))
        print("\nMemory of CS:IP:")
        self.show_memory(self.BIU.cs_ip, self.BIU.cs_ip + 10)
        print("\nMemory of DS:")
        self.show_memory(self.BIU.reg['DS']*16, self.BIU.reg['DS']*16 + 40)
        print("\nRegisters:")
        self.show_regs()
        print("\nIR:  ", self.EU.IR)
        print("Next:", self.BIU.next_ins)
        print('-' * 80)
    
    def print_end_state(self):
        # Print end state
        self.EU.print("Clock ended\n")
        self.EU.print(f"CPU ran a total of {self.cycle_count} clock cycles\n")