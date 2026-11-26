"""Hack Assembler (K = 76, K mod 3 = 1 -> clear error messages with line numbers)
Usage: python assembler.py Prog.asm   ->  writes Prog.hack
"""
import sys

DEST = {"": "000", "M": "001", "D": "010", "MD": "011", "A": "100",
        "AM": "101", "AD": "110", "AMD": "111"}
JUMP = {"": "000", "JGT": "001", "JEQ": "010", "JGE": "011",
        "JLT": "100", "JNE": "101", "JLE": "110", "JMP": "111"}
COMP = {  # a-bit + c1..c6
    "0": "0101010", "1": "0111111", "-1": "0111010", "D": "0001100",
    "A": "0110000", "!D": "0001101", "!A": "0110001", "-D": "0001111",
    "-A": "0110011", "D+1": "0011111", "A+1": "0110111", "D-1": "0001110",
    "A-1": "0110010", "D+A": "0000010", "D-A": "0010011", "A-D": "0000111",
    "D&A": "0000000", "D|A": "0010101",
    "M": "1110000", "!M": "1110001", "-M": "1110011", "M+1": "1110111",
    "M-1": "1110010", "D+M": "1000010", "D-M": "1010011", "M-D": "1000111",
    "D&M": "1000000", "D|M": "1010101",
}

def predefined():
    t = {"SP": 0, "LCL": 1, "ARG": 2, "THIS": 3, "THAT": 4,
         "SCREEN": 16384, "KBD": 24576}
    for i in range(16):
        t["R%d" % i] = i
    return t

class AsmError(Exception):
    pass

def clean(line):
    return line.split("//")[0].replace(" ", "").replace("\t", "").strip()

def assemble(lines):
    symbols = predefined()
    errors = []
    # ---------- PASS 1: labels ----------
    rom = 0
    for n, raw in enumerate(lines, 1):
        line = clean(raw)
        if not line:
            continue
        if line.startswith("("):
            if not line.endswith(")") or len(line) < 3:
                errors.append("Line %d: invalid label '%s'" % (n, line)); continue
            name = line[1:-1]
            if name in symbols:
                errors.append("Line %d: label '%s' already defined" % (n, name))
            else:
                symbols[name] = rom
        else:
            rom += 1
    # ---------- PASS 2: translate ----------
    out, next_var = [], 16
    for n, raw in enumerate(lines, 1):
        line = clean(raw)
        if not line or line.startswith("("):
            continue
        try:
            if line.startswith("@"):
                sym = line[1:]
                if sym == "":
                    raise AsmError("empty A-instruction")
                if sym.isdigit():
                    val = int(sym)
                    if val > 32767:
                        raise AsmError("address %d too large (max 32767)" % val)
                else:
                    if sym[0].isdigit():
                        raise AsmError("invalid symbol '%s'" % sym)
                    if sym not in symbols:
                        symbols[sym] = next_var
                        next_var += 1
                    val = symbols[sym]
                out.append(format(val, "016b"))
            else:
                dest, comp, jump = "", line, ""
                if "=" in comp:
                    dest, comp = comp.split("=", 1)
                if ";" in comp:
                    comp, jump = comp.split(";", 1)
                if dest not in DEST:
                    raise AsmError("invalid dest '%s'" % dest)
                if comp not in COMP:
                    raise AsmError("invalid instruction")
                if jump not in JUMP:
                    raise AsmError("invalid jump '%s'" % jump)
                out.append("111" + COMP[comp] + DEST[dest] + JUMP[jump])
        except AsmError as e:
            errors.append("Line %d: %s" % (n, e))
    return out, errors, symbols

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python assembler.py file.asm"); sys.exit(1)
    with open(sys.argv[1]) as f:
        lines = f.readlines()
    out, errors, _ = assemble(lines)
    if errors:
        print("\n".join(errors)); sys.exit(1)
    path = sys.argv[1].rsplit(".", 1)[0] + ".hack"
    with open(path, "w") as f:
        f.write("\n".join(out) + "\n")
    print("Wrote %s (%d instructions)" % (path, len(out)))