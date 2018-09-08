import sys
if sys.version_info[0] < 3:
    from codecs import open

from codecs import BOM_UTF16_LE, BOM_UTF16_BE, BOM_UTF8

__doc__ = """This script helps to handle configuration files (*.ini)

cfg = Config(file_path[, comment_char, escape_char])

value = cfg[<section>][<key>]

value = cfg[<section>, <key>]

cfg[<section>][<key>] = value

cfg.save()"""

__version__ = 1.9

# encodings for files
encodings = ["ascii", "utf-8", "utf-16", None]

import traceback

def open_file(path, mode="r"):
    for encoding in encodings:
        try:
            f = open(path, mode)
            if "r" in mode:
                f.read()
                f.seek(0)
            return f
        except: traceback.print_exc()
    raise IOError("'{}' couldn't be read".format(path))

def to_bytes(content):
    enc = 0
    if content.startswith(BOM_UTF8):
        enc = 8
        content = content[2:]
        

    if content.startswith(BOM_UTF16_LE):
        enc = 16
        content = content[2:]

    if content.startswith(BOM_UTF16_BE):
        enc = 16.2
        content = content[2:]

    out = b""

    if enc == 16:
        out = content.decode("utf-16-le").encode("utf-8")
    elif enc == 16.2:
        out = content.decode("utf-16-be").encode("utf-8")
    else:
        out = content

    return out.splitlines(True)


class _Pointer:
    def __init__(self, line, from_, text, config):
        self.line = line
        self.from_ = from_
        self.to = from_ + len(text)
        self.config = config

    def set(self, value):
        text = (value)
        self.config.content[self.line] = self.config.content[self.line][:self.from_] + text + self.config.content[self.line][self.to:]
        self.to = self.from_ + len(text)

    def __call__(self):
        return self.config.content[self.line][self.from_:self.to]

class _SecIter:
    def __init__(self, iterable):
        self.iterable = iterable

    def __next__(self):
        return next(self.iterable).decode()

class _Section:
    def __init__(self, dict_, no_decode = False):
        self.dict = dict_
        self.nd = no_decode

    def __getitem__(self, key):
        key_type = type(key)
        if key_type == str:
            key = key.encode()
        if not self.nd:return eval(self.dict[key]())
        else: return self.dict[key]().decode()

    def __setitem__(self, key, value):
        if type(value) == str:
            value = value.encode()
        if type(key) == str:
            key = key.encode()
##        if not key in self.dict: # new
##            self.key =
        self.dict[key].set(value)
        
    __contains__ = lambda self, key: self.dict.__contains__(key.encode() if type(key) == str else key)

    __iter__ = lambda self: _SecIter(iter(self.dict))

class _CfgIter:
    def __init__(self, iterable):
        self.iterable = iterable

    def __next__(self):
        return next(self.iterable).decode()

class _UnencodedDictIter:
    def __init__(self, iterator):
        self.iterator = iterator

    def __next__(self):
        return next(self.iterator).decode()

class _UnencodedDict:
    def __init__(self, dict_=None):
        if dict_ == None:
            dict_ = {}
        self.dict = dict_

    def __getitem__(self, key):
        if type(key) == str:
            key = key.encode()

        return self.dict[key]

    def __setitem__(self, key, value):
        if type(key) == str:
            key = key.encode()

        self.dict[key] = value

    __contains__ = lambda self, key: self.dict.__contains__(key.encode() if type(key) == str else key)

    __iter__ = lambda self: _UnencodedDictIter(iter(self.dict))

    __repr__ = lambda self: self.dict.__repr__()
    __str__ = lambda self: self.dict.__str__()

    pop = lambda self, *args: self.dict.pop(*args)

    clear = lambda self, *args: self.dict.clear(*args)

class Config:
    def __init__(self, path, comment_char=";", escape_char="\\", section_only=False, no_decode=False):
        file = open_file(path, "rb")
        self.content = to_bytes(file.read())
        file.close()

        self.path = path

        self.comment_char = comment_char
        self.escape_char = escape_char

        self.config_dict = {}

        self.section_only = section_only

        self.no_decode = no_decode

        if not section_only: self._interpret()
        else: self._interpret_section_only()

    def _remove_comments(self, text, return_escape_char = True):
        ignore = False
        out = b""
        for char in text:
            char = bytes((char,))
            if ignore:
                out += char
                ignore = False
                continue
            
            if char == self.escape_char:
                if return_escape_char:
                    out += char
                ignore = True
                continue
            
            if char == self.comment_char:
                return out

            out += char
        return out

    def _interpret_section_only(self):
        section = None
        for line in self.content:
            line_strip = self._remove_comments(line).strip()
            if len(line_strip) >= 2 and line_strip[0] == b"["[0] and line_strip[-1] == b"]"[0]: # new section
                section = line_strip[1:-1]
                
                if section in self.config_dict:
                    raise SyntaxError("section {} redefinition.".format(section))
                self.config_dict[section] = []
                continue

            self.config_dict[section].append(line_strip)

    def _interpret(self):
        section = None
        line_index = -1
        for line in self.content:
            line_index += 1
            line_strip = self._remove_comments(line).strip()
            if len(line_strip) >= 2 and line_strip[0] == b"["[0] and line_strip[-1] == b"]"[0]: # new section
                section = line_strip[1:-1]
                
                if section in self.config_dict:
                    raise SyntaxError("section {} redefinition.".format(section))
                self.config_dict[section] = {}
                continue

            eq_index = line_strip.find(b"=")

            if eq_index != -1: # probably a definition
                left_strip = line_strip[:eq_index].strip()
                
                left = left_strip

                right_strip = line_strip[eq_index+1:].strip()
                right_index = line.index(right_strip)
                
                right = _Pointer(line_index, right_index, right_strip, self)


                self.config_dict[section][left] = right

    def __getitem__(self, key):
        if type(key) in (slice, tuple):
            if len(key) == 2:
                return _Section(self.config_dict[(key[0]).encode() if type(key[0]) == str else key[0]], no_decode=self.no_decode)[key[1]]
            raise IndexError(key)
        
        if self.section_only:
            if type(key) == str:
                key = key.encode()
            return self.config_dict[key]
        return _Section(self.config_dict[(key).encode() if type(key) == str else key], no_decode=self.no_decode)

    def __setitem__(self, key, value):
        if type(key) in (slice, tuple):
            if len(key) == 2:
                _Section(self.config_dict[(key[0]).encode() if type(key[0]) == str else key[0]], no_decode=self.no_decode)[key[1]] = value
                return
        raise IndexError(key)
        
    __contains__ = lambda self, key: self.config_dict.__contains__(key.encode() if type(key) == str else key)

    __iter__ = lambda self: _CfgIter(iter(self.config_dict))

    def save(self):
        file = open_file(self.path, "wb")
        file.writelines(self.content)
        file.close()

class Database(_UnencodedDict):
    def __init__(self, path, comment_char=";", escape_char="\\", section_only=False, no_decode=False):
        file = open_file(path, "rb")
        self.content = to_bytes(file.read())
        file.close()

        self.path = path

        self.comment_char = comment_char
        self.escape_char = escape_char

        self.dict = {}

        self.section_only = section_only

        self.no_decode = no_decode

        if not section_only: self._interpret()
        else: self._interpret_section_only()

    def _remove_comments(self, text, return_escape_char = True):
        ignore = False
        out = b""
        for char in text:
            char = bytes((char,))
            if ignore:
                out += char
                ignore = False
                continue
            
            if char == self.escape_char:
                if return_escape_char:
                    out += char
                ignore = True
                continue
            
            if char == self.comment_char:
                return out

            out += char
        return out

    def _interpret_section_only(self):
        section = None
        for line in self.content:
            line_strip = self._remove_comments(line).strip()
            if len(line_strip) >= 2 and line_strip[0] == b"["[0] and line_strip[-1] == b"]"[0]: # new section
                section = line_strip[1:-1]
                
                if section in self.dict:
                    raise SyntaxError("section {} redefinition.".format(section))
                self.dict[section] = []
                continue

            self.dict[section].append(line_strip if self.no_decode else line_strip.decode())

    def _interpret(self):
        section = None
        line_index = -1
        for line in self.content:
            line_index += 1
            line_strip = self._remove_comments(line).strip()
            if len(line_strip) >= 2 and line_strip[0] == b"["[0] and line_strip[-1] == b"]"[0]: # new section
                section = line_strip[1:-1]
                
                if section in self.dict:
                    raise SyntaxError("section {} redefinition.".format(section))
                self.dict[section] = _UnencodedDict()
                continue

            eq_index = line_strip.find(b"=")

            if eq_index != -1: # probably a definition
                left_strip = line_strip[:eq_index].rstrip()

                right_strip = line_strip[eq_index+1:].lstrip()

                self.dict[section][left_strip] = right_strip if self.no_decode else eval(right_strip)

    def save(self):
        out = []
        if self.section_only:
            pass
        else:
            longest_key_length = 0
            for section in self.dict:
                out.append(b"[%b]\n" % (section))
                for key in self.dict[section].dict:
                    value = self.dict[section].dict[key]

                    if type(value) != bytes:
                        value = repr(value).encode()

                    longest_key_length = max(len(key), longest_key_length)

                    out.append(b"%b\t = %b\n" % (key, value))

            longest_key_length = int((longest_key_length // 4 + 1) * 4)
            index = 0
            for line in out:
                if line and line[0] != b"[" and b"=" in line:
                    out[index] = line.replace(b"\t", b"\t" * (int((longest_key_length - line.find(b"\t")) // 4 + 1)), 1)
                index += 1

        file_ = open(self.path, "wb")
        file_.write(b"".join(out))
        file_.close()

if __name__ == "__main__":
    print("inireader by Zuzu_Typ, version {version}\n\n{doc}".format(version=__version__, doc=__doc__))
