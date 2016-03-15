'''
disasm.disassemble(path)
    Disassemble a python module from a *.pyc file. Returns a disasm.Module with
    the disassembly or raises a disasm.DisassemblerException if there was an
    error.

disasm.Module, disasm.CodeObject, disasm.Opcode
    Used to represent the disassembled module. Constant values are
    represented using native Python objects.

disasm.DisassemblerException
    Thrown by disasm.disassemble() when there was a problem with the
    disassembly. Apply str() to an exception to get a detailed description
    of the error.
'''

import unwind.op as op
import sys
import time
import struct

def disassemble(path):
    '''
    Disassemble a python module from file_object, an open file object
    containing a *.pyc file. Returns a disasm.Module with the disassembly
    or raises a disasm.DisassemblerException if there was an error.
    '''
    return _Disassembler().disassemble(open(path, 'rb'))

class DisassemblerException(Exception):
    '''
    Thrown by disasm.disassemble() when there was a problem with the
    disassembly. Apply str() to an exception to get a detailed description
    of the error.
    '''

class Opcode:
    '''
    Represents a disassembled opcode.

        self.offset = number of bytes from start of code object
        self.size = number of bytes used by this opcode
        self.opcode = string with opcode name
        self.argument = Python object with argument, will be None for
                        opcodes without arguments
    '''

    def __init__(self, offset, size, opcode, argument):
        self.offset = offset
        self.size = size
        self.opcode = opcode
        self.argument = argument

    def __repr__(self):
        return 'Opcode(offset = %s, size = %s, opcode = %s, argument = %s)' % (repr(self.offset), repr(self.size), repr(self.opcode), repr(self.argument))

class CodeObject:
    '''
    Represents a disassembled Python code object.

        self.co_argcount = number of arguments (not including * or ** args)
        self.co_kwonlyargcount = number of keyword arguments
        self.co_nlocals = number of local variables
        self.co_stacksize = virtual machine stack space required
        self.co_flags = bitmap: 1=optimized | 2=newlocals | 4=*arg | 8=**arg
        self.co_code = list of raw compiled bytecode
        self.co_consts = tuple of constants used in the bytecode
        self.co_names = tuple of names of local variables
        self.co_varnames = tuple of names of arguments and local variables
        self.co_freevars = tuple of names of variables used by parent scope
        self.co_cellvars = tuple of names of variables used by child scopes
        self.co_filename = file in which this code object was created
        self.co_name = name with which this code object was defined
        self.co_firstlineno = number of first line in Python source code
        self.co_lnotab = encoded mapping of line numbers to bytecode indices
        self.opcodes = list of disasm.Opcode instances
    '''

    def __init__(self, co_argcount=None, co_kwonlyargcount=None, co_nlocals=None, co_stacksize=None,
                 co_flags=None, co_code=None, co_consts=None, co_names=None, co_varnames=None,
                 co_freevars=None, co_cellvars=None, co_filename=None, co_name=None,
                 co_firstlineno=None, co_lnotab=None, opcodes=None):
        self.co_argcount = co_argcount
        self.co_kwonlyargcount = co_kwonlyargcount
        self.co_nlocals = co_nlocals
        self.co_stacksize = co_stacksize
        self.co_flags = co_flags
        self.co_code = co_code
        self.co_consts = co_consts
        self.co_names = co_names
        self.co_varnames = co_varnames
        self.co_freevars = co_freevars
        self.co_cellvars = co_cellvars
        self.co_filename = co_filename
        self.co_name = co_name
        self.co_firstlineno = co_firstlineno
        self.co_lnotab = co_lnotab
        self.opcodes = opcodes if opcodes else []

    def __repr__(self):
        global _indent
        result = 'CodeObject(\n'
        _indent += 1
        indent = _indent * _INDENT
        for f in ['co_argcount', 'co_kwonlyargcount', 'co_nlocals', 'co_stacksize',
                  'co_flags', 'co_filename', 'co_name', 'co_firstlineno']:
            result += indent + f + ' = %s,\n' % repr(getattr(self, f))
        _indent += 1
        result += indent + 'opcodes = [%s])' % ','.join('\n' + _indent * _INDENT + repr(o) for o in self.opcodes)
        _indent -= 2
        return result + ')'

class Module:
    '''
    Represents a disassembled Python module.

        self.magic = 32-bit magic number from marshal format
        self.timestamp = unix timestamp when the file was compiled
        self.python_version = interpreter version as a string
        self.body = disassembled code in a disasm.CodeObject
    '''

    def __init__(self, magic, timestamp, python_version, body):
        self.magic = magic
        self.timestamp = timestamp
        self.python_version = python_version
        self.body = body

    def __repr__(self):
        global _indent
        result = 'Module(\n'
        _indent += 1
        indent = _indent * _INDENT
        result += indent + 'magic = %s,\n' % repr(self.magic)
        result += indent + 'timestamp = %s,\n' % repr(self.timestamp)
        result += indent + 'python_version = %s,\n' % repr(self.python_version)
        result += indent + 'body = %s' % repr(self.body)
        _indent -= 1
        return result + ')'

# Used by __repr__() for disassembled objects
_indent = 0
_INDENT = '    '

# Indicates the type of object to unmarshal
_TYPE_NULL = ord('0')
_TYPE_NONE = ord('N')
_TYPE_FALSE = ord('F')
_TYPE_TRUE = ord('T')
_TYPE_STOP_ITER = ord('S')
_TYPE_ELLIPSIS = ord('.')
_TYPE_INT = ord('i')
_TYPE_INT64 = ord('I')
_TYPE_FLOAT = ord('f')
_TYPE_BINARY_FLOAT = ord('g')
_TYPE_COMPLEX = ord('x')
_TYPE_BINARY_COMPLEX = ord('y')
_TYPE_LONG = ord('l')
_TYPE_STRING = ord('s')
_TYPE_INTERNED = ord('t')
_TYPE_STRING_REF = ord('R')
_TYPE_TUPLE = ord('(')
_TYPE_LIST = ord('[')
_TYPE_DICT = ord('{')
_TYPE_CODE = ord('c')
_TYPE_UNICODE = ord('u')
_TYPE_SET = ord('<')
_TYPE_FROZEN_SET = ord('>')

INDENT = "    "

class _PyObject():


    def __init__(self, val=0, print_raw=0, skip_it=0):
        self.val = val
        self.print_raw = print_raw
        self.skip_it = skip_it

    def __repr__(self):
        if self.print_raw:
            return "{}".format(self.val)
        return self.val.__repr__()

class _FuncCall():
    

    def __init__(self, func_name, pargs, kargs, pargs_ext=None, kargs_ext=None):
        self.func_name = func_name
        self.pargs = pargs
        self.kargs = kargs
        all_args = [_.__repr__() for _ in self.pargs]
        if pargs_ext:
            all_args.append("*{}".format(pargs_ext.__repr__()))
        all_args.extend([k.val + "=" + str(v) for k,v in self.kargs.iteritems()])
        if kargs_ext:
            all_args.append("**{}".format(kargs_ext.__repr__()))
        self.args_repr = ", ".join(all_args)
        self.val =  ''.join([self.func_name, "(", self.args_repr, ")"])

    def __repr__(self):
        return self.val

class _MathOperation(): 


    def __init__(self, val1, val2, operation):
        self.val1 = val1
        self.val2 = val2
        self.operation = operation

    def __repr__(self):
        return "({} {} {})".format(self.val1, self.operation, self.val2)

class _Assigment():


    def __init__(self, name, val, indent=0):
        self.name = name
        self.val = val
        self.indent = indent

    def __repr__(self):
        return self.indent *_INDENT + "{} = {}".format(self.name, self.val)


class _CommandHandler():


    def __init__(self):
        self.stack = list()
        self.result = list()

        self.indent_count = 0
        self.INDENT_SIZE = "    "

        self.slice_expression = [op.SLICE_0, op.SLICE_1, op.SLICE_2, op.SLICE_3]
        self.slice_statemant = [op.STORE_SLICE_0, op.STORE_SLICE_1, op.STORE_SLICE_2,
                                op.STORE_SLICE_3, op.DELETE_SLICE_0, op.DELETE_SLICE_1,
                                op.DELETE_SLICE_2, op.DELETE_SLICE_3, op.STORE_SUBSCR,
                                op.DELETE_SUBSCR]
        self.math_operations = [op.BINARY_POWER, op.BINARY_MULTIPLY, op.BINARY_FLOOR_DIVIDE,
                                op.BINARY_TRUE_DIVIDE, op.BINARY_MODULO, op.BINARY_ADD,
                                op.BINARY_SUBTRACT, op.BINARY_LSHIFT, op.BINARY_RSHIFT,
                                op.BINARY_AND, op.BINARY_XOR, op.BINARY_OR,

                                op.INPLACE_POWER, op.INPLACE_MULTIPLY, op.INPLACE_FLOOR_DIVIDE,
                                op.INPLACE_TRUE_DIVIDE, op.INPLACE_MODULO, op.INPLACE_ADD,
                                op.INPLACE_SUBTRACT, op.INPLACE_LSHIFT, op.INPLACE_RSHIFT,
                                op.INPLACE_AND, op.INPLACE_XOR, op.INPLACE_OR
                                ]

        self.function_call = [op.CALL_FUNCTION, op.CALL_FUNCTION_VAR,
                                op.CALL_FUNCTION_KW, op.CALL_FUNCTION_VAR_KW]

        self.pwr_operations = [op.BINARY_POWER, op.INPLACE_POWER]
        self.mul_operations = [op.BINARY_MULTIPLY, op.INPLACE_MULTIPLY]
        self.floor_div_operations = [op.BINARY_FLOOR_DIVIDE, op.INPLACE_FLOOR_DIVIDE]
        self.true_div_operations = [op.BINARY_TRUE_DIVIDE, op.INPLACE_TRUE_DIVIDE]
        self.mod_operations = [op.BINARY_MODULO, op.INPLACE_MODULO]
        self.add_operations = [op.BINARY_ADD, op.INPLACE_ADD]
        self.sub_operations = [op.BINARY_SUBTRACT, op.INPLACE_SUBTRACT]
        self.shl_operations = [op.BINARY_LSHIFT, op.INPLACE_LSHIFT]
        self.shr_operations = [op.BINARY_RSHIFT, op.INPLACE_RSHIFT]
        self.and_operations = [op.BINARY_AND, op.INPLACE_AND]
        self.xor_operations = [op.BINARY_XOR, op.INPLACE_XOR]
        self.or_operations = [op.BINARY_OR, op.INPLACE_OR]

    def indent(self):
        return self.indent_count * self.INDENT_SIZE

    def inc_indent(self):
        self.indent_count += 1

    def dec_indent(self):
        self.indent_count -= 1

    def pop(self):
        return self.stack.pop()

    def pop_n(self, n):
        return [self.pop() for _ in range(n)]

    def pop_n_rev(self, n):
        temp = self.pop_n(n)
        temp.reverse()
        return temp

    def push(self, val):
        self.stack.append(val)

    def top(self):
        return self.stack[-1]

    def rotate(self, n, l):
        return l[n:] + l[:n]

    def pop_n_rev_rot(self, shiftn, popn):
        return self.rotate(shiftn, self.pop_n_rev(popn))


    def read_kargs(self, num):
        kargs = dict()
        for _ in range(num):
            val = self.pop()
            key = self.pop()
            kargs[key] = val
        return kargs

    def read_pargs(self, num):
        pargs = list()
        for _ in range(num):
            pargs.insert(0, self.pop())
        return pargs

    #TODO add loops, if, function declaration, class, declaration
    def handle(self, opcode, arg):
        print(opcode, arg, self.stack)
        if opcode == op.NOP: pass
        elif opcode == op.POP_TOP: self.pop()
        elif opcode == op.ROT_TWO: self.stack[-2:] = self.rotate(2, self.stack[-2:])
        elif opcode == op.ROT_THREE: self.stack[-3:] = self.rotate(3, self.stack[-3:])
        elif opcode == op.ROT_FOUR: self.stack[-4:] = self.rotate(4, self.stack[-4:])

        elif opcode == op.UNARY_POSITIVE: pass
        elif opcode == op.UNARY_NEGATIVE: self.top().val = "-" + self.top().val
        elif opcode == op.UNARY_NOT: self.top().val = "not " + self.top().val
        elif opcode == op.UNARY_INVERT: self.top().val = "~" + self.top().val

        elif opcode == op.LOAD_CONST: self.push(_PyObject(arg))
        elif opcode == op.LOAD_NAME: self.push(_PyObject(arg, print_raw=1))

        elif opcode == op.BUILD_LIST: self.push(self._make_list(arg))
        elif opcode == op.BUILD_SET: self.push(set(self._make_list(arg)))
        elif opcode == op.BUILD_TUPLE: self.push(tuple(self._make_list(arg)))

        elif opcode == op.BUILD_MAP: self.push(dict())
        elif opcode == op.STORE_MAP:
            key = self.pop()
            value = self.pop()
            self.stack[-1][key] = value

        elif opcode in self.math_operations:
            val2 = self.pop()
            val1 = self.pop()
            
            if opcode in self.pwr_operations: cmd = "**"
            elif opcode in self.mul_operations: cmd = "*"
            elif opcode in self.floor_div_operations: cmd = "//"
            elif opcode in self.true_div_operations: cmd = "/"
            elif opcode in self.mod_operations: cmd = "%"
            elif opcode in self.add_operations: cmd = "+"
            elif opcode in self.sub_operations: cmd = "-"
            elif opcode in self.shl_operations: cmd = "<<"
            elif opcode in self.shr_operations: cmd = ">>"
            elif opcode in self.and_operations: cmd = "&"
            elif opcode in self.xor_operations: cmd = "^"
            elif opcode in self.or_operations: cmd = "|"

            self.push(_MathOperation(val1, val2, cmd))


        elif opcode in self.slice_expression:
            if opcode == op.SLICE_0: val = "{}[:]".format(*self.pop_n_rev(1))
            elif opcode == op.SLICE_1: val = "{}[{}:]".format(*self.pop_n_rev(2))
            elif opcode == op.SLICE_2: val = "{}[:{}]".format(*self.pop_n_rev(2))
            elif opcode == op.SLICE_3: val = "{}[{}:{}]".format(*self.pop_n_rev(3))

            self.push(_PyObject(val, print_raw=1))

        elif opcode in self.slice_statemant:
            if opcode == op.STORE_SLICE_0: var = "{}[:] = {}".format(*self.pop_n(2))
            elif opcode == op.STORE_SLICE_1: var = "{}[{}:] = {}".format(*self.pop_n_rev_rot(1, 3))
            elif opcode == op.STORE_SLICE_2: var = "{}[:{}] = {}".format(*self.pop_n_rev_rot(1, 3))
            elif opcode == op.STORE_SLICE_3: var = "{}[{}:{}] = {}".format(*self.pop_n_rev_rot(1,4))

            elif opcode == op.DELETE_SLICE_0: var = "del {}[:]".format(self.pop())
            elif opcode == op.DELETE_SLICE_1: var = "del {}[{}:]".format(*self.pop_n_rev(2))
            elif opcode == op.DELETE_SLICE_2: var = "del {}[{}:]".format(*self.pop_n_rev(2))
            elif opcode == op.DELETE_SLICE_3: var = "del {}[{}:{}]".format(*self.pop_n_rev(3))

            elif opcode == op.DELETE_SUBSCR: var = "del {}[{}]".format(*pop_n_rev(2))
            elif opcode == op.STORE_SUBSCR: var = "{}[{}] = {}".format(*self.pop_n_rev_rot(1, 3))
            self.result.append(self.indent() + var)
        elif opcode == op.BINARY_SUBSCR:
            tos = self.pop()
            tos1 = self.pop()
            self.push("{}[{}]".format(tos1, tos))


        # TODO fix module import 
        elif opcode == op.IMPORT_NAME:
            _ = self.pop()
            self.push(arg)

        elif opcode == op.IMPORT_STAR:
            self.result.append(self.indent() + "from {} import *".format(self.pop()))
        elif opcode == op.IMPORT_FROM:
            self.push("{}.{}".format(self.top(), arg))


        elif opcode == op.PRINT_ITEM_TO: self.result.append(self.indent() + "print >> {}, {}".format(self.top(), self.pop()))
        elif opcode == op.PRINT_NEWLINE_TO: self.result.append(self.indent() + "print >> {}".format(self.pop()))
        elif opcode == op.PRINT_ITEM: self.result.append(self.indent() + "print({}, end='')".format(self.pop()))
        elif opcode == op.PRINT_NEWLINE: self.result.append(self.indent() + "print()")

        elif opcode in self.function_call:
            pargc = arg & 0xff
            kargc = (arg >> 8) & 0xff

            ext_list = ext_dict = None
            if opcode == op.CALL_FUNCTION: pass
            elif opcode == op.CALL_FUNCTION_VAR: ext_list = self.pop()
            elif opcode == op.CALL_FUNCTION_KW: ext_dict = self.pop()
            elif opcode == op.CALL_FUNCTION_VAR_KW: ext_dict = self.pop(); ext_list = self.pop()

            kargs = self.read_kargs(kargc)
            pargs = self.read_pargs(pargc)
            func_name = self.pop().__repr__()

            self.push(_FuncCall(func_name, pargs, kargs, ext_list, ext_dict))

        elif opcode == op.MAKE_FUNCTION:
            code_obj = self.pop().val

            func_name = code_obj.co_name
            argc = code_obj.co_argcount
            kwargc = arg
            local_vars = code_obj.co_varnames

            all_args = list() 
            all_args.extend(local_vars[:argc-kwargc])
            all_args.extend(["{}={}".format(key, val) for key,val in zip(local_vars[argc-kwargc:argc], self.pop_n_rev(2))])

            self.result.append(self.indent() + "def {}({}):".format(func_name, ", ".join(all_args)))
            #self.inc_indent()

            #no need to STORE_NAME the function declaration
            self.push(_PyObject(skip_it=1))

        elif opcode == op.RETURN_VALUE:
            if arg:
                self.result.append(self.indent() + "return {}".format(arg))
            self.dec_indent()
        elif opcode == op.DELETE_NAME: self.result.append(self.indent() + "del {}".format(arg))
        elif opcode == op.STORE_NAME:
            tos = self.pop()
            if hasattr(tos, "skip_it") and not tos.skip_it:
                self.result.append(self.indent() + _Assigment(arg, tos).__repr__())

    def _make_list(self, argc):
        temp = temp = [self.stack.pop() for _ in range(argc)]
        temp.reverse()
        return temp

    def print_result(self):
        for command in self.result:
            print(command)




# Holds intermediate state useful during disassembly. Only the disassemble()
# method is meant to be called directly.
class _Disassembler:
    def __init__(self):
        self.magic = None
        self.string_table = None
        self.file = None

    def disassemble(self, file):
        self.magic, timestamp = struct.unpack('=II', file.read(8))
        self.string_table = []
        self.file = file

        version = op.python_version_from_magic(self.magic)
        if not version:
            raise DisassemblerException('Unknown magic header number %d' % self.magic)

        return Module(self.magic, timestamp, 'Python ' + version, self.unmarshal_node())

    def unmarshal_collection(self, type):
        count = self.read_int32()
        nodes = [self.unmarshal_node() for i in range(count)]
        return type(nodes)

    def read_byte_array(self):
        count = self.read_int32()
        return list(struct.unpack('=' + 'B' * count, self.file.read(count)))

    def read_string_ascii(self):
        return ''.join(chr(c) for c in self.read_byte_array())

    def read_string_utf8(self):
        count = self.read_int32()
        return self.file.read(count).decode('utf8')

    def read_int8(self):
        return struct.unpack('=b', self.file.read(1))[0]

    def read_int16(self):
        return struct.unpack('=h', self.file.read(2))[0]

    def read_int32(self):
        return struct.unpack('=i', self.file.read(4))[0]

    def unmarshal_node(self):
        type = self.read_int8()

        # Global singletons
        if type == _TYPE_NONE: return None
        elif type == _TYPE_TRUE: return True
        elif type == _TYPE_FALSE: return False

        # Collections
        elif type == _TYPE_TUPLE: return self.unmarshal_collection(tuple)
        elif type == _TYPE_LIST: return self.unmarshal_collection(list)
        elif type == _TYPE_SET: return self.unmarshal_collection(set)
        elif type == _TYPE_FROZEN_SET: return self.unmarshal_collection(frozenset)

        # Numbers
        elif type == _TYPE_INT: return self.read_int32()
        elif type == _TYPE_INT64: return struct.unpack('=q', self.file.read(8))[0]
        elif type == _TYPE_BINARY_FLOAT: return struct.unpack('=d', self.file.read(8))[0]
        elif type == _TYPE_BINARY_COMPLEX: return complex(*struct.unpack('=dd', self.file.read(16)))
        elif type == _TYPE_LONG:
            nbits = self.read_int32()
            if not nbits:
                return 0
            n = 0
            for i in range(abs(nbits)):
                digit = self.read_int16()
                n |= digit << (i * 15)
            return n if nbits > 0 else -n

        # Strings
        elif type == _TYPE_STRING: return self.read_string_ascii()
        elif type == _TYPE_UNICODE: return self.read_string_utf8()
        elif type == _TYPE_INTERNED:
            data = self.read_string_ascii()
            self.string_table.append(data)
            return data
        elif type == _TYPE_STRING_REF:
            index = self.read_int32()
            if index < 0 or index >= len(self.string_table):
                raise DisassemblerException('String index %d is outside string table' % index)
            return self.string_table[index]

        # Code objects
        elif type == _TYPE_CODE:
            co = CodeObject()
            co.co_argcount = self.read_int32()
            co.co_kwonlyargcount = self.read_int32() if op.has_kwonlyargcount(self.magic) else 0
            co.co_nlocals = self.read_int32()
            co.co_stacksize = self.read_int32()
            co.co_flags = self.read_int32()
            type = self.read_int8()
            if type != _TYPE_STRING:
                raise DisassemblerException('Bytecode was not marshalled as a string (type was 0x%02X instead of 0x%02X)' % (type, _TYPE_STRING))
            co.co_code = self.read_byte_array()
            co.co_consts = self.unmarshal_node()
            co.co_names = self.unmarshal_node()
            co.co_varnames = self.unmarshal_node()
            co.co_freevars = self.unmarshal_node()
            co.co_cellvars = self.unmarshal_node()
            co.co_filename = self.unmarshal_node()
            co.co_name = self.unmarshal_node()
            co.co_firstlineno = self.read_int32()
            co.co_lnotab = self.unmarshal_node()

            # Start disassembly
            argument = 0
            i = 0
            handler = _CommandHandler()
            while i < len(co.co_code):
                offset = i
                opcode = op.from_bytecode(co.co_code[i], self.magic)
                if opcode is None:
                    raise DisassemblerException('Unknown bytecode 0x%02X' % co.co_code[i])
                i += 1

                if op.has_argument(opcode):
                    lo, hi = co.co_code[i:i + 2]
                    argument |= (lo | (hi << 8))
                    i += 2

                # The upper 16 bits of 32-bit arguments are stored in a fake
                # EXTENDED_ARG opcode that precedes the actual opcode
                if opcode == op.EXTENDED_ARG:
                    argument <<= 16
                    continue

                # Decode the opcode argument if present
                arg = None
                if op.has_argument(opcode):
                    if opcode == op.LOAD_CONST:
                        if argument >= len(co.co_consts):
                            raise DisassemblerException('Invalid argument %d for opcode %s' % (argument, opcode))
                        arg = co.co_consts[argument]
                    elif opcode in [op.LOAD_NAME, op.STORE_NAME, op.DELETE_NAME,
                                op.LOAD_ATTR, op.STORE_ATTR, op.DELETE_ATTR,
                                op.LOAD_GLOBAL, op.STORE_GLOBAL, op.DELETE_GLOBAL,
                                op.IMPORT_NAME, op.IMPORT_FROM]:
                        if argument >= len(co.co_names):
                            raise DisassemblerException('Invalid argument %d for opcode %s' % (argument, opcode))
                        arg = co.co_names[argument]
                    elif opcode in [op.LOAD_FAST, op.STORE_FAST, op.DELETE_FAST]:
                        if argument >= len(co.co_varnames):
                            raise DisassemblerException('Invalid argument %d for opcode %s' % (argument, opcode))
                        arg = co.co_varnames[argument]
                    else:
                        arg = argument

                # Record disassembled opcode
                co.opcodes.append(Opcode(offset, i - offset, opcode, arg))
                handler.handle(opcode, arg)
                argument = 0

            handler.print_result()
            return co

        else:
            raise DisassemblerException('Cannot unmarshal unknown type 0x%02X' % type)
