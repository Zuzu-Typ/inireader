import sys
if sys.version_info[0] < 3:
    from codecs import open

__doc__ = """This script helps to handle configuration files (*.ini)

cfg = Config(file_path[, comment_char, escape_char])

value = cfg[<section>][<key>]

value = cfg[<section>, <key>]

cfg[<section>][<key>] = value

cfg.save()"""

__version__ = 1.7

class _StringType:
    def _stoi(self, string): # converts a string to an int
        return int(string)

    def _stof(self, string): # converts a string to a float
        return float(string.replace("f", ""))

    def _stod(self, string): # converts a string to a dict
        string = string[1:-1] # remove parenthesis
        items = []
        depth = 0
        index = 0
        last_index = 0
        for char in string:
            if char in ["(", "[", "{"]:
                depth += 1
            elif char in [")", "]", "}"]:
                depth -= 1
            elif char == "," and not depth:
                items.append(string[last_index:index])
                last_index = index + 1
            index += 1
        items.append(string[last_index:index])

        dictionary = {}

        for item in items:
            key, value = item.split(":")

            dictionary[self.decode(key)] = self.decode(value)

        return dictionary

    def _stot(self, string): # converts a string to a tuple
        string = string[1:-1] # remove parenthesis
        items = []
        depth = 0
        index = 0
        last_index = 0
        for char in string:
            if char in ["(", "[", "{"]:
                depth += 1
            elif char in [")", "]", "}"]:
                depth -= 1
            elif char == "," and not depth:
                items.append(string[last_index:index])
                last_index = index + 1
            index += 1
        items.append(string[last_index:index])

        output = []

        for item in items:
            output.append(self.decode(item))

        return tuple(output)

    def _stol(self, string): # converts a string to a list
        string = string[1:-1] # remove parenthesis
        items = []
        depth = 0
        index = 0
        last_index = 0
        for char in string:
            if char in ["(", "[", "{"]:
                depth += 1
            elif char in [")", "]", "}"]:
                depth -= 1
            elif char == "," and not depth:
                items.append(string[last_index:index])
                last_index = index + 1
            index += 1
        items.append(string[last_index:index])

        output = []

        for item in items:
            output.append(self.decode(item))

        return output

    def _stos(self, string): # converts a string to a set
        string = string[1:-1] # remove parenthesis
        items = []
        depth = 0
        index = 0
        last_index = 0
        for char in string:
            if char in ["(", "[", "{"]:
                depth += 1
            elif char in [")", "]", "}"]:
                depth -= 1
            elif char == "," and not depth:
                items.append(string[last_index:index])
                last_index = index + 1
            index += 1
        items.append(string[last_index:index])

        output = set()

        for item in items:
            output.add(self.decode(item))

        return output

    def _stob(self, string): # converts a string to a bool
        string_ = string.strip().lower()
        if string_ == "false":
            return False
        elif string_ == "true":
            return True
        elif string_ == "none":
            return None
        else:
            return string

    def decode(self, string):
        string = string.strip()
        if len(string) >= 2:
            if string[0] == "(" and string[-1] == ")":
                return self._stot(string)
            if string[0] == "[" and string[-1] == "]":
                return self._stol(string)
            if string[0] == "{" and string[-1] == "}":
                if ":" in string:
                    return self._stod(string)
                else:
                    return self._stos(string)
            if string[0] in ["\"", "'"] and string[-1] in ["\"", "'"]:
                return string[1:-1]
            if "." in string:
                return self._stof(string)
        asB = self._stob(string)
        if type(asB) != str:
            return asB
        else:
            return self._stoi(string)
        
__st = _StringType()

def _decode(string):
    global __st
    try:
        return __st.decode(string)
    except:
        return string

# encodings for files
encodings = [None, "ascii", "ansi", "utf-8", "utf-16"]

def open_file(path, mode="r"):
    for encoding in encodings:
        try:
            return open(path, mode, encoding=encoding)
        except: continue
    raise IOError("'{}' couldn't be read".format(path))


class _Pointer:
    def __init__(self, line, from_, text, config):
        self.line = line
        self.from_ = from_
        self.to = from_ + len(text)
        self.config = config

    def set(self, value):
        text = str(value)
        self.config.content[self.line] = self.config.content[self.line][:self.from_] + text + self.config.content[self.line][self.to:]
        self.to = self.from_ + len(text)

    def __call__(self):
        return self.config.content[self.line][self.from_:self.to]

class _Section:
    def __init__(self, dict_):
        self.dict = dict_

    def __getitem__(self, key):
        return _decode(self.dict[key]())

    def __setitem__(self, key, value):
##        if not key in self.dict: # new
##            self.key =
        self.dict[key].set(value)
        
    __contains__ = lambda self, key: self.dict.__contains__(key)

class Config:
    def __init__(self, path, comment_char=";", escape_char="\\"):
        file = open_file(path, "r")
        self.content = file.readlines()
        file.close()

        self.path = path

        self.comment_char = comment_char
        self.escape_char = escape_char

        self.config_dict = {}

        self._interpret()

    def _escape(self, text):
        ignore = False
        out = ""
        for char in text:
            if ignore:
                out += char
                ignore = False
                continue
            
            if char == self.escape_char:
                ignore = True
                continue

            out += char
        return out

    def _remove_comments(self, text, return_escape_char = True):
        ignore = False
        out = ""
        for char in text:
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

    def _interpret(self):
        section = None
        line_index = -1
        for line in self.content:
            line_index += 1
            line_strip = line.strip()
            if len(line_strip) >= 2 and line_strip[0] == "[" and line_strip[-1] == "]": # new section
                section = line_strip[1:-1]
                
                if section in self.config_dict:
                    raise SyntaxError("section {} redefinition.".format(section))
                self.config_dict[section] = {}
                continue
            
            line_without_comments = self._remove_comments(line)

            eq_index = line_without_comments.find("=")

            if eq_index != -1: # probably a definition
                left_strip = line_without_comments[:eq_index].strip()
                
                left = left_strip

                right_strip = line_without_comments[eq_index+1:].strip()
                right_index = line.index(right_strip)
                
                right = _Pointer(line_index, right_index, right_strip, self)

                self.config_dict[section][left] = right

    def __getitem__(self, key):
        if type(key) in (slice, tuple):
            if len(key) == 2:
                return _Section(self.config_dict[key[0]])[key[1]]
            raise IndexError(key)
        return _Section(self.config_dict[key])

    def __setitem__(self, key, value):
        if type(key) in (slice, tuple):
            if len(key) == 2:
                _Section(self.config_dict[key[0]])[key[1]] = value
                return
                
        raise IndexError(key)
        
    __contains__ = lambda self, key: self.config_dict.__contains__(key)

    def save(self):
        file = open_file(self.path, "w")
        file.writelines(self.content)
        file.close()

if __name__ == "__main__":
    print("inireader by Zuzu_Typ, version {version}\n\n{doc}".format(version=__version__, doc=__doc__))
