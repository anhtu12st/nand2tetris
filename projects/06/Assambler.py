import sys
import os


class SymbolTable(object):
    def __init__(self):
        self.table = {
            'SP': 0, 'LCL': 1, 'ARG': 2, 'THIS': 3, 'THAT': 4, 'R0': 0,
            'R1': 1, 'R2': 2, 'R3': 3, 'R4': 4, 'R5': 5, 'R6': 6, 'R7': 7,
            'R8': 8, 'R9': 9, 'R10': 10, 'R11': 11, 'R12': 12, 'R13': 13, 'R14': 14,
            'R15': 15, 'SCREEN': 16384, 'KBD': 24576
        }

    def addEntry(self, symbol, address):
        self.table[symbol] = address

    def contains(self, symbol):
        return symbol in self.table

    def getAddress(self, symbol):
        return self.table[symbol]


class Code(object):
    def __init__(self):
        pass

    def dest(self, s):
        dDest = {
            'null': '000', 'M': '001', 'D': '010', 'MD': '011', 'A': '100', 'AM': '101', 'AD': '110', 'AMD': '111'
        }
        return dDest[s]

    def comp(self, s):
        dComp = {
            '0': '0101010', '1': '0111111', '-1': '0111010', 'D': '0001100', 'A': '0110000',
            'M': '1110000', '!D': '0001101', '!A': '0110001', '!M': '1110001', '-D': '0001111',
            '-A': '0110011', '-M': '1110011', 'D+1': '0011111', 'A+1': '0110111', 'M+1': '1110111',
            'D-1': '0001110', 'A-1': '0110010', 'M-1': '1110010', 'D+A': '0000010', 'D+M': '1000010',
            'D-A': '0010011', 'D-M': '1010011', 'A-D': '0000111', 'M-D': '1000111', 'D&A': '0000000',
            'D&M': '1000000', 'D|A': '0010101', 'D|M': '1010101'
        }
        return dComp[s]

    def jump(self, s):
        dJump = {
            'null': '000', 'JGT': '001', 'JEQ': '010', 'JGE': '011',
            'JLT': '100', 'JNE': '101', 'JLE': '110', 'JMP': '111'
        }
        return dJump[s]


class Parser(object):
    def __init__(self, path):
        self.f = open(path, 'r')
        self.rawLines = self.f.readlines()
        self.cleanLines = []
        for line in self.rawLines:
            if (line[:2] == "//") or (line == "\n"):
                continue
            if '//' in line:
                line = line[:line.find('//')]
            line = line.replace(" ", "")
            l = []
            for ch in line:
                if ch not in ['', '\n']:
                    l.append(ch)
            self.cleanLines.append(''.join(l))
        self.addr = -1
        self.command = None
        self.totalCommands = len(self.cleanLines)

    def hasMoreCommands(self):
        return self.addr < self.totalCommands - 1

    def advance(self):
        if self.hasMoreCommands():
            self.addr += 1
            self.command = self.cleanLines[self.addr]

    def commandType(self):
        if self.command[0] == '@':
            return 'A'
        elif self.command[0] == '(':
            return 'L'
        else:
            return 'C'

    def symbol(self):
        if self.commandType() == 'A':
            return self.command[1:]
        elif self.commandType() == 'L':
            return self.command[1:-1]
        else:
            raise ValueError("Command type should be A or L")

    def dest(self):
        if self.commandType() == 'C':
            ind = self.command.find('=')
            if ind != -1:
                return self.command[:ind]
            else:
                return 'null'
        else:
            raise ValueError("Command type should be C")

    def comp(self):
        if self.commandType() == 'C':
            ind1 = self.command.find('=')
            ind2 = self.command.find(';')
            if (ind1 != -1) and (ind2 != -1):
                return self.command[ind1+1:ind2]
            elif (ind1 != -1) and (ind2 == -1):
                return self.command[ind1+1:]
            elif (ind1 == -1) and (ind2 != -1):
                return self.command[:ind2]
            elif (ind1 == -1) and (ind2 == -1):
                return self.command
        else:
            raise ValueError("Command type should be C")

    def jump(self):
        if self.commandType() == 'C':
            ind = self.command.find(';')
            if ind != -1:
                return self.command[ind+1:]
            else:
                return 'null'
        else:
            raise ValueError("Command type should be C")


class Assambler(object):
    def __init__(self, path):
        self.parser = Parser(path)
        self.code = Code()
        self.symbols = SymbolTable()
        idx = path.find('.')
        writefile = path[:idx]
        self.file = open(writefile + '.hack', 'w')

    def execute(self):
        self.firstPass()
        self.secondPass()
        self.createOutput()

    def binary(self, s):
        return '{0:b}'.format(int(s))

    def firstPass(self):
        counter = 0
        while self.parser.hasMoreCommands():
            self.parser.advance()
            commandType = self.parser.commandType()
            if commandType in ['A', 'C']:
                counter += 1
            elif commandType == 'L':
                symbol = self.parser.symbol()
                self.symbols.addEntry(symbol, counter)
            else:
                raise ValueError("Unexpected command type encountered")

    def secondPass(self):
        ramAddress = 16
        self.parser.addr = -1
        while self.parser.hasMoreCommands():
            self.parser.advance()
            commandType = self.parser.commandType()
            if commandType == 'A':
                symbol = self.parser.symbol()
                if (not symbol.isdigit()) and (not self.symbols.contains(symbol)):
                    self.symbols.addEntry(symbol, ramAddress)
                    ramAddress += 1

    def createOutput(self):
        self.parser.addr = -1
        while self.parser.hasMoreCommands():
            self.parser.advance()
            commandType = self.parser.commandType()
            # if A command
            if commandType == 'A':
                symbol = self.parser.symbol()
                if symbol.isdigit():
                    binSymbol = self.binary(symbol)
                else:
                    symAdd = self.symbols.getAddress(symbol)
                    binSymbol = self.binary(symAdd)
                aCmd = '0' * (16 - len(binSymbol)) + binSymbol
                self.file.write(aCmd + '\n')
            elif commandType == 'C':
                destMem = self.parser.dest()
                dest = self.code.dest(destMem)
                compMem = self.parser.comp()
                comp = self.code.comp(compMem)
                jumpMem = self.parser.jump()
                jump = self.code.jump(jumpMem)
                cCmd = '111' + comp + dest + jump
                self.file.write(cCmd + '\n')
            else:
                pass
        self.file.close()


def clearScreen():
    # for mac and linux(here, os.name is 'posix')
    if os.name == 'posix':
        _ = os.system('clear')
    else:
        # for windows platfrom
        _ = os.system('cls')


def main():
    if len(sys.argv) == 2:
        print("Program starting...")
        asm = Assambler(sys.argv[1])
        asm.execute()
        print("Compiled Successful!")
    else:
        while True:
            path = input("Drag or Type .asm file's path here: ")
            path = path[:-1]
            try:
                asm = Assambler(path)
                asm.execute()
                print("Compiled Successful!")
                break
            except:
                clearScreen()
                print('Error occur. Try again!')


if __name__ == "__main__":
    main()
