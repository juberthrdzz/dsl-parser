import re
import sys
from dataclasses import dataclass
from typing import List, Optional, Tuple

# ----------------------------
# Token model
# ----------------------------

@dataclass
class Token:
    type: str
    value: str
    line: int
    col: int

class DSLParseError(Exception):
    pass

# ----------------------------
# Lexer (Scanner)
# ----------------------------

RESERVED = {
    "CARRUSEL", "PRODUCTO", "ESPACIOS", "CAPACIDAD",
    "PRECIO", "MINIMO", "MAXIMO", "CRITICIDAD",
    "ALTA", "MEDIA", "BAJA",
    "SIMULAR", "TRANSACCIONES",
    "RETIRAR", "RESURTIR", "CONTAR",
    "ESTADO", "ESTADISTICAS", "REPORTE",
}

SYMBOLS = {
    "{": "LBRACE",
    "}": "RBRACE",
    "(": "LPAREN",
    ")": "RPAREN",
    "[": "LBRACKET",
    "]": "RBRACKET",
    ":": "COLON",
    ",": "COMMA",
    ";": "SEMI",
}

# Regex patterns (ordered)
RE_WHITESPACE = re.compile(r"[ \t]+")
RE_NEWLINE = re.compile(r"\n")
RE_COMMENT = re.compile(r"#.*")
RE_DECIMAL = re.compile(r"\d+\.\d+")
RE_INT = re.compile(r"\d+")
RE_STRING = re.compile(r"\"([^\"\\]|\\.)*\"")  # allows escaped chars
RE_ID = re.compile(r"[A-Za-z][A-Za-z0-9_]*")

def tokenize(text: str) -> List[Token]:
    tokens: List[Token] = []
    i = 0
    line, col = 1, 1
    n = len(text)

    def advance(matched: str):
        nonlocal i, line, col
        for ch in matched:
            if ch == "\n":
                line += 1
                col = 1
            else:
                col += 1
        i += len(matched)

    while i < n:
        chunk = text[i:]

        # newline
        m = RE_NEWLINE.match(chunk)
        if m:
            tokens.append(Token("NL", "\\n", line, col))
            advance(m.group(0))
            continue

        # whitespace
        m = RE_WHITESPACE.match(chunk)
        if m:
            advance(m.group(0))
            continue

        # comment
        m = RE_COMMENT.match(chunk)
        if m:
            # ignore comments (or keep them if you want)
            advance(m.group(0))
            continue

        # symbols
        ch = chunk[0]
        if ch in SYMBOLS:
            tokens.append(Token(SYMBOLS[ch], ch, line, col))
            advance(ch)
            continue

        # string
        m = RE_STRING.match(chunk)
        if m:
            tokens.append(Token("STRING", m.group(0), line, col))
            advance(m.group(0))
            continue

        # decimal (must be before int)
        m = RE_DECIMAL.match(chunk)
        if m:
            tokens.append(Token("DECIMAL", m.group(0), line, col))
            advance(m.group(0))
            continue

        # int
        m = RE_INT.match(chunk)
        if m:
            tokens.append(Token("INT", m.group(0), line, col))
            advance(m.group(0))
            continue

        # id/reserved
        m = RE_ID.match(chunk)
        if m:
            val = m.group(0)
            ttype = "KW" if val in RESERVED else "ID"
            tokens.append(Token(ttype, val, line, col))
            advance(val)
            continue

        # unknown character
        raise DSLParseError(f"Error léxico en línea {line}, col {col}: carácter inválido '{chunk[0]}'")

    tokens.append(Token("EOF", "", line, col))
    return tokens

# ----------------------------
# Parser (Recursive Descent)
# ----------------------------

class Parser:
    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.pos = 0

        # semantic tracking (simple)
        self.products_defined = set()
        self.carousels_defined = set()

    def current(self) -> Token:
        return self.tokens[self.pos]

    def match(self, ttype: str, value: Optional[str] = None) -> bool:
        tok = self.current()
        if tok.type != ttype:
            return False
        if value is not None and tok.value != value:
            return False
        return True

    def consume(self, ttype: str, value: Optional[str] = None) -> Token:
        tok = self.current()
        if not self.match(ttype, value):
            expected = f"{ttype}" + (f"('{value}')" if value else "")
            got = f"{tok.type}('{tok.value}')"
            raise DSLParseError(f"Error sintáctico en línea {tok.line}, col {tok.col}: esperaba {expected}, llegó {got}")
        self.pos += 1
        return tok

    def skip_nl(self):
        while self.match("NL"):
            self.consume("NL")

    def fin(self):
        # Flexible: ; or NL (one or more NL)
        if self.match("SEMI"):
            self.consume("SEMI")
            self.skip_nl()
        elif self.match("NL"):
            self.skip_nl()
        else:
            tok = self.current()
            raise DSLParseError(f"Error sintáctico en línea {tok.line}, col {tok.col}: esperaba fin de instrucción (';' o salto de línea).")

    # Grammar:
    # programa ::= definiciones simulacion EOF
    def programa(self):
        self.skip_nl()
        self.definiciones()
        self.skip_nl()
        self.simulacion()
        self.skip_nl()
        self.consume("EOF")

    # definiciones ::= (def_carrusel)*
    def definiciones(self):
        while self.match("KW", "CARRUSEL"):
            self.def_carrusel()
            self.skip_nl()

    # def_carrusel ::= 'CARRUSEL' id '{' parametros catalogo '}'
    def def_carrusel(self):
        self.consume("KW", "CARRUSEL")
        cid = self.consume("ID").value
        if cid in RESERVED:
            raise DSLParseError(f"Error semántico: '{cid}' no puede ser ID (es palabra reservada).")
        if cid in self.carousels_defined:
            raise DSLParseError(f"Error semántico: carrusel '{cid}' definido más de una vez.")
        self.carousels_defined.add(cid)

        self.skip_nl()
        self.consume("LBRACE")
        self.skip_nl()

        self.parametros()
        self.skip_nl()

        self.catalogo()
        self.skip_nl()

        self.consume("RBRACE")
        self.skip_nl()

    # parametros ::= 'ESPACIOS' ':' entero fin  'CAPACIDAD' ':' entero fin
    def parametros(self):
        self.consume("KW", "ESPACIOS")
        self.consume("COLON")
        espacios = int(self.consume("INT").value)
        if espacios <= 0:
            raise DSLParseError("Error semántico: ESPACIOS debe ser > 0.")
        self.fin()

        self.consume("KW", "CAPACIDAD")
        self.consume("COLON")
        capacidad = int(self.consume("INT").value)
        if capacidad <= 0:
            raise DSLParseError("Error semántico: CAPACIDAD debe ser > 0.")
        self.fin()

    # catalogo ::= (def_producto)*
    def catalogo(self):
        while self.match("KW", "PRODUCTO"):
            self.def_producto()
            self.skip_nl()

    # def_producto ::= 'PRODUCTO' id '{' PRECIO: decimal fin MINIMO: entero fin MAXIMO: entero fin CRITICIDAD: (ALTA|MEDIA|BAJA) fin '}'
    def def_producto(self):
        self.consume("KW", "PRODUCTO")
        pid = self.consume("ID").value
        if pid in RESERVED:
            raise DSLParseError(f"Error semántico: '{pid}' no puede ser ID (es palabra reservada).")
        if pid in self.products_defined:
            raise DSLParseError(f"Error semántico: producto '{pid}' definido más de una vez.")
        self.products_defined.add(pid)

        self.skip_nl()
        self.consume("LBRACE")
        self.skip_nl()

        self.consume("KW", "PRECIO")
        self.consume("COLON")
        precio = float(self.consume("DECIMAL").value)
        if precio < 0:
            raise DSLParseError("Error semántico: PRECIO debe ser >= 0.")
        self.fin()

        self.consume("KW", "MINIMO")
        self.consume("COLON")
        minimo = int(self.consume("INT").value)
        self.fin()

        self.consume("KW", "MAXIMO")
        self.consume("COLON")
        maximo = int(self.consume("INT").value)
        if minimo > maximo:
            raise DSLParseError("Error semántico: MINIMO debe ser <= MAXIMO.")
        self.fin()

        self.consume("KW", "CRITICIDAD")
        self.consume("COLON")
        # ALTA/MEDIA/BAJA are reserved keywords
        if self.match("KW", "ALTA") or self.match("KW", "MEDIA") or self.match("KW", "BAJA"):
            self.pos += 1
        else:
            tok = self.current()
            raise DSLParseError(f"Error sintáctico en línea {tok.line}, col {tok.col}: CRITICIDAD debe ser ALTA|MEDIA|BAJA.")
        self.fin()

        self.consume("RBRACE")
        self.skip_nl()

    # simulacion ::= 'SIMULAR' '{' bloque_transacciones (consulta fin)* '}'
    def simulacion(self):
        self.consume("KW", "SIMULAR")
        self.skip_nl()
        self.consume("LBRACE")
        self.skip_nl()

        self.bloque_transacciones()
        self.skip_nl()

        while self.match("KW", "ESTADO") or self.match("KW", "ESTADISTICAS") or self.match("KW", "REPORTE"):
            self.consulta()
            self.fin()
            self.skip_nl()

        self.consume("RBRACE")

    # bloque_transacciones ::= 'TRANSACCIONES' ':' '[' lista_tx ']' fin
    def bloque_transacciones(self):
        self.consume("KW", "TRANSACCIONES")
        self.consume("COLON")
        self.consume("LBRACKET")
        self.skip_nl()

        if not self.match("RBRACKET"):
            self.lista_tx()

        self.skip_nl()
        self.consume("RBRACKET")
        # fin after ]
        if self.match("SEMI") or self.match("NL"):
            self.fin()
        else:
            # allow } directly? keep strict: require fin
            tok = self.current()
            raise DSLParseError(f"Error sintáctico en línea {tok.line}, col {tok.col}: falta fin de instrucción después de ']'.")

    # lista_tx ::= tx (',' tx)*
    def lista_tx(self):
        self.tx()
        while self.match("COMMA"):
            self.consume("COMMA")
            self.skip_nl()
            self.tx()

    # tx ::= RETIRAR '(' id ',' entero ')' | RESURTIR '(' id ',' entero ')' | CONTAR '(' id ')'
    def tx(self):
        if self.match("KW", "RETIRAR"):
            self.consume("KW", "RETIRAR")
            self.consume("LPAREN")
            pid = self.consume("ID").value
            self.consume("COMMA")
            qty = int(self.consume("INT").value)
            self.consume("RPAREN")
            self.check_tx_semantics(pid, qty)
            return

        if self.match("KW", "RESURTIR"):
            self.consume("KW", "RESURTIR")
            self.consume("LPAREN")
            pid = self.consume("ID").value
            self.consume("COMMA")
            qty = int(self.consume("INT").value)
            self.consume("RPAREN")
            self.check_tx_semantics(pid, qty)
            return

        if self.match("KW", "CONTAR"):
            self.consume("KW", "CONTAR")
            self.consume("LPAREN")
            pid = self.consume("ID").value
            self.consume("RPAREN")
            # qty not needed
            self.check_tx_semantics(pid, 1)
            return

        tok = self.current()
        raise DSLParseError(f"Error sintáctico en línea {tok.line}, col {tok.col}: se esperaba RETIRAR/RESURTIR/CONTAR.")

    def check_tx_semantics(self, pid: str, qty: int):
        if pid not in self.products_defined:
            raise DSLParseError(f"Error semántico: producto '{pid}' usado en transacción pero no está definido.")
        if qty <= 0:
            raise DSLParseError("Error semántico: cantidad debe ser > 0.")

    # consulta ::= ESTADO | ESTADISTICAS | REPORTE '(' cadena ')'
    def consulta(self):
        if self.match("KW", "ESTADO"):
            self.consume("KW", "ESTADO")
            return
        if self.match("KW", "ESTADISTICAS"):
            self.consume("KW", "ESTADISTICAS")
            return
        if self.match("KW", "REPORTE"):
            self.consume("KW", "REPORTE")
            self.consume("LPAREN")
            self.consume("STRING")
            self.consume("RPAREN")
            return

        tok = self.current()
        raise DSLParseError(f"Error sintáctico en línea {tok.line}, col {tok.col}: consulta inválida.")

# ----------------------------
# CLI / Runner
# ----------------------------

def main():
    if len(sys.argv) != 2:
        print("Uso: python dsl_parser.py <archivo.dsl>")
        sys.exit(1)

    path = sys.argv[1]
    with open(path, "r", encoding="utf-8") as f:
        text = f.read()

    tokens = tokenize(text)
    parser = Parser(tokens)
    parser.programa()

    print("✅ OK: léxico y sintaxis correctos.")

if __name__ == "__main__":
    try:
        main()
    except DSLParseError as e:
        print(f"❌ {e}")
        sys.exit(2)