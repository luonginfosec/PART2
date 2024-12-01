import re
import os
import sys
import ast
from pprint import pprint
from emulator.instructions import all_ins, transfer_control_ins

data_def_ins = ['DB', 'DW', 'DD', 'DQ', 'DT', 'DUP']

def to_int_str(matched):
    string = matched.group()
    idx = re.search(r'[,\s\]]', string).span()[0]
    suffix = string[idx:]
    string = string[:idx]
    int_str = str(to_decimal(string))
    # print("int_st:", int_str)
    return int_str + suffix

def to_decimal(num):
    # Convert all kinds of string representations of numbers to decimal
    # print(f"converting {num} to decimal")
    if isinstance(num, int):
        return int(num)
    if num.startswith('0x'):
        return int(num, 16)
    if num.startswith('0X'):
        return int(num[2:], 16)
    num = num.upper()
    if num[-1] == 'B':
        res = int(num.rstrip('B'), 2)
    elif num[-1] == 'O':
        res = int(num.rstrip('O'), 8)
    elif num[-1] == 'D':
        res = int(num.rstrip('D'), 10)
    elif num[-1] == 'H':
        res = int(num.rstrip('H'), 16)
    else:
        res = int(num)
    return res

class Assembler(object):
    # Assembler - Actually It's an Interpreter :)
    def __init__(self, seg):
        self.name = ''
        self.title = ''
        self.space = {} # Segment space
        self.seg_adr = {'DS': hex(seg['DS']), 'CS': hex(seg['CS']), 'SS': hex(seg['SS']), 'ES': hex(seg['ES'])}
        self.seg_id = {} # Segment names
        self.seg_len = {} # Actual segment lengths
        self.tags = {} # Labels
        self.vars = {} # Variables
        self.ip = '0'    # Program entry offset
        self.ins_origin = [] # Original instructions before conversion and splitting

    def compile(self, code):
        instructions = self.__preprocessing(code)
        for ip in range(len(instructions)):
            ins = instructions[ip]
            if ins[0] == 'NAME': # Module name
                self.name = ins[1] 
            elif ins[0] == 'TITLE': # File name
                self.title = ins[1]
            elif ins[0] == 'ASSUME': # ASSUME must be before segments
                self.__assume(ins[1:])
            elif len(ins) > 1 and ins[1] == 'SEGMENT':
                ip = self.__segment(instructions, ip)
            elif ins[0] == 'END':
                self.ip = self.tags[ins[1]]['offset']

        self.__eval_id()

        # print()
        # for key, val in self.space.items():
        #     print(key,':')
        #     pprint(val[:100], compact=True)
        #     print()
        # print("seg_id:",self.seg_id)
        # print("\ntags:")
        # pprint(self.tags)
        # print("\nvars:")
        # pprint(self.vars)
        # print("\ninitital ip:", self.ip)
        return self

    def __eval_id(self):  #TODO(Zubin) make it simple
        # Provide labels (for jmp loop) and variables
        var_dict = {}
        for key, val in self.seg_id.items():
            var_dict[key] = str(self.seg_adr[val]) # Interpret segment name as segment address
        for key, val in self.vars.items():
            # var_dict[key] = hex(int(val['seg'], 16) * 16 + int(val['offset'], 16)) # Interpret variable as real address
            for k, v in self.seg_adr.items():
                if v == val['seg']:
                    seg_name = k
            var_dict[key] = seg_name + ':[' + str(hex(int(val['offset'], 16))) + ']' # Interpret variable as "segment address: offset address"
        # print("var_dict:", var_dict)
        for key, val in self.space.items(): # Traverse each segment
            for i in range(len(self.space[key])): # Traverse each line of code
                ins = self.space[key][i]
                if ins:
                    if ins[0] in transfer_control_ins and ins[-1] in self.tags.keys():
                        # jmp/call empty/short tag -> jmp/call tag.offset
                        # loop/jcxz tag -> loop/jcxz tag.offset
                        # jmp/call near ptr tag -> jmp/call tag.offset
                        # jmp/call far ptr tag -> jmp/call tag.seg:tag.offset
                        for s in ['SHORT', 'NEAR', 'PTR']:
                            if s in ins:
                                self.space[key][i].remove(s)
                        if ins[1] == 'FAR':
                            self.space[key][i].remove('FAR')
                            dst = self.tags[ins[1]]['seg'] + ':' + self.tags[ins[1]]['offset']
                            self.space[key][i][1] = dst
                        else:
                            self.space[key][i][1] = self.tags[ins[1]]['offset']
                    j = 0
                    while j < len(ins):
                        for s in ['SEG', 'OFFSET', 'TYPE']:
                            if ins[j] == s:
                                self.space[key][i].remove(s)
                                if ins[j] in self.vars.keys():
                                    self.space[key][i][j] = self.vars[ins[j]][s.lower()] 
                                else:
                                    self.space[key][i][j] = self.tags[ins[j]][s.lower()] 
                        # Replace variables and labels
                        for k, v in var_dict.items():
                            if ins[j] == k:
                                self.space[key][i][j] = v
                            elif ins[j][:len(k)] == k and ins[j][len(k)] == '[':
                                self.space[key][i][j] = v + ins[j][len(k):]
                        j += 1
                        # Variable: MOV BX,A[SI]  A = a.seg*16 + a.offset
                        # Variable: add ax, Item  Item = [a.seg*16 + a.offset]
                        # Segment name: MOV AX,DRG    ORG = org.seg

    def __segment(self, instructions, ip):
        seg_ip = 0  # Current segment offset, i.e., '$' 
        seg_ins = instructions[ip]
        seg_tmp = seg_ins[0]
        seg_name = self.seg_id[seg_tmp] # CS DS SS ES
        self.space[seg_name] = [['0']] * int('10000', 16)
        for i in range(ip+1, len(instructions)):
            ins = instructions[i]
            for j in range(len(ins)):
                if ins[j] == '$':
                    ins[j] == str(hex(seg_ip))
            ins_ori = self.ins_origin[i]
            if ins[0] == 'ORG':
                seg_ip = to_decimal(ins[1])
            elif ins[0] == 'EVEN': # The following memory variable starts from the next even address unit
                seg_ip += seg_ip % 2
            elif ins[0] == 'ALIGN':
                num = to_decimal(ins[1])
                assert num & (num-1) == 0, "Num should be power of 2"  # num should be a power of 2
                seg_ip += (-seg_ip) % num 
            elif ins[0] == seg_tmp:
                assert ins[1] == 'ENDS', "Compile Error: segment ends fault"
                self.seg_len[seg_name] = seg_ip
                return i + 1

            elif ':' in ins[0]: # Data label
                tag_list = ins[0].split(':')
                tag = tag_list[0]
                self.tags[tag] = {'seg': self.seg_adr[seg_name],
                                  'offset': hex(seg_ip),
                                  'type': 0} # TODO(Zubin) set type
                if len(ins) == 1:                   # case1: start:\n mov ...
                    pass
                else:
                    if tag_list[1]:                 # case2: start:mov ...
                        ins[0] = tag_list[1] # Remove label
                    else:                           # case3: start: mov ... 
                        ins = ins[1:] # Remove label
                    self.space[seg_name][seg_ip] = ins
                    seg_ip += 1
            
            elif ins[0] in data_def_ins: # Data definition pseudo-instructions
                byte_list = self.__data_define(ins, ins_ori)
                self.space[seg_name][seg_ip:seg_ip+len(byte_list)] = byte_list
                seg_ip += len(byte_list)
            elif len(ins) > 2 and ins[1] in data_def_ins:
                var = ins[0]
                self.vars[var] = {'seg': self.seg_adr[seg_name],
                                  'offset': hex(seg_ip),
                                  'type': 0}      # TODO(Zubin) set type
                var_ori = ins_ori.split()[0] # Actual variable name (not converted to uppercase)
                byte_list = self.__data_define(ins[1:], ins_ori.replace(var_ori, '', 1).strip())
                self.space[seg_name][seg_ip:seg_ip+len(byte_list)] = byte_list
                seg_ip += len(byte_list)
            else: # Assembly instructions without data labels are directly sent to segment space
                self.space[seg_name][seg_ip] = ins
                seg_ip += 1

    def __data_define(self, ins, ins_ori):
        var = ins[0]
        var_ori = ins_ori.split()[0]
        byte_list = []

        if len(ins) > 2 and ins[2][:3] == 'DUP': # db Imm dup ()
            times = to_decimal(ins[1])
            idx = ins_ori.find('(')
            dup_str = var + ' ' + ins_ori[idx + 1:-1]
            dup_list = [s for s in re.split(" |,", dup_str.strip().upper()) if s]
            byte_list = self.__data_define(dup_list, dup_str) * times

        elif var == 'DB': # DB 'A', 'D', 0Dh, '$'   DB 1, 3, 5, 7, 9, 11
            db_str = ins_ori.replace(var_ori, '', 1).strip()
            byte_list = self.__str_to_bytes(db_str)

        elif var == 'DW':
            dw_str = ins_ori.replace(var_ori, '', 1).strip()
            byte_list = self.__str_to_words(dw_str)

        elif var == 'DD':
            dd_str = ins_ori.replace(var_ori, '', 1).strip()
            byte_list = self.__str_to_dwords(dd_str)
            
        else:
            sys.exit("Compile Error")
        
        # print("bytes_list: ", byte_list)
        return byte_list

    @classmethod
    def __str_to_bytes(cls, string):
        string = re.sub(r"[0-9A-Fa-f]+[HhBbOo]{1}[,\s\]]+", to_int_str, '[' + string + ']')
        str_list =  ast.literal_eval(string)
        byte_list = []
        for item in str_list:
            if isinstance(item, int):
                byte_list.append([hex(item)])
            elif isinstance(item, str):
                for s in item:
                    byte_list.append([hex(ord(s))])
            else:
                sys.exit("Compile Error: str to hex")
        return byte_list

    @classmethod
    def __str_to_words(cls, string):
        string = re.sub(r"[0-9A-Fa-f]+[HhBbOo]{1}[,\s\]]+", to_int_str, '[' + string + ']')
        str_list =  ast.literal_eval(string)
        byte_list = []
        for item in str_list:
            assert isinstance(item, int), "Compile Error: str to hex"
            high, low = item >> 8, item & 0x0ff
            byte_list.append([hex(low)])  # little endian
            byte_list.append([hex(high)]) 
        return byte_list

    @classmethod
    def __str_to_dwords(cls, string):
        string = re.sub(r"[0-9A-F]+[HhBbOo]{1}[,\s\]]+", to_int_str, '[' + string + ']')
        str_list =  ast.literal_eval(string)
        byte_list = []
        for item in str_list:
            assert isinstance(item, int), "Compile Error: str to hex"
            byte_list.append([hex(item & 0x0ff)]) # little endian
            byte_list.append([hex(item >> 8 & 0x0ff)])
            byte_list.append([hex(item >> 16 & 0x0ff)])
            byte_list.append([hex(item >> 24)])
        return byte_list

    def __assume(self, ins):
        for i in ins:
            i = i.split(':')
            self.seg_id[i[1]] = i[0]

    def __strip_comments(self, text):
        return re.sub(r'(?m) *;.*n?', '', str(text))

    def __remove_empty_line(self, text):
        return os.linesep.join([s.strip() for s in text.splitlines() if s.strip()])

    def __preprocessing(self, code):
        code = self.__strip_comments(code)
        code = self.__remove_empty_line(code)
        code = code.replace('?', '0')
        instructions = []
        for line in code.split(os.linesep):
            instructions.append([s for s in re.split(" |,", line.strip().upper()) if s])
            self.ins_origin.append(line.strip())
        # for i in range(len(instructions)):
        #     print(instructions[i])
        # print()
        return instructions