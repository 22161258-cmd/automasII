"""Conversión entre notaciones infija, prefija y postfija (Tema 2).

Dos formas de trabajar:
  1. Sobre el ÁRBOL de expresión del programa (recorrido postorden / preorden).
  2. Sobre LISTAS DE TOKENS con los algoritmos clásicos (pila / shunting-yard):
        infija -> postfija      postfija -> infija
        postfija -> prefija     prefija  -> postfija
Uso suelto:   python notaciones.py "(a + b) * c - 2"
Nota: 'neg' es el operador menos unario (para no confundirlo con la resta).
"""
import re
import sys
from ast_nodes import (Programa, Declaracion, Asignacion, Categoria, Gasto, Si, Mientras,
                       Accion, Funcion, Retornar, Binario, Unario, Literal, Variable,
                       Acceso, Llamada, Conversion)

# Precedencia: mayor número = se evalúa primero (coincide con la gramática de TopScript)
PREC = {'o': 1, 'y': 2, '<': 4, '>': 4, '<=': 4, '>=': 4, '==': 4, '!=': 4,
        '+': 5, '-': 5, '*': 6, '/': 6}
UNARIOS = {'no': 3, 'neg': 7}
RELACIONALES = {'<', '>', '<=', '>=', '==', '!='}

_TOKEN = re.compile(r'\s*("[^"]*"|\d+\.\d+|\d+|[A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)?'
                    r'|<=|>=|==|!=|[-+*/<>()])')


def _prec(op):
    return PREC[op] if op in PREC else UNARIOS[op]


# ====================== algoritmos sobre listas de tokens ======================
def tokenizar(texto):
    texto, pos, tokens = texto.strip(), 0, []
    while pos < len(texto):
        m = _TOKEN.match(texto, pos)
        if not m:
            raise ValueError(f"carácter no válido en la posición {pos}: {texto[pos]!r}")
        tokens.append(m.group(1))
        pos = m.end()
    return tokens


def infija_a_postfija(tokens):
    """Algoritmo de la estación de maniobras (shunting-yard) con operadores unarios."""
    salida, pila, anterior_operando = [], [], False
    for t in tokens:
        if t == '(':
            pila.append(t)
            anterior_operando = False
        elif t == ')':
            while pila and pila[-1] != '(':
                salida.append(pila.pop())
            if not pila:
                raise ValueError("paréntesis de cierre sin apertura")
            pila.pop()
            anterior_operando = True
        elif t == 'no' or (t == '-' and not anterior_operando):
            pila.append('no' if t == 'no' else 'neg')     # prefijo: no desapila nada
            anterior_operando = False
        elif t in PREC:
            while pila and pila[-1] != '(' and _prec(pila[-1]) >= PREC[t]:
                salida.append(pila.pop())
            pila.append(t)
            anterior_operando = False
        else:
            salida.append(t)
            anterior_operando = True
    while pila:
        op = pila.pop()
        if op == '(':
            raise ValueError("paréntesis de apertura sin cierre")
        salida.append(op)
    return salida


def postfija_a_prefija(tokens):
    pila = []
    for t in tokens:
        if t in PREC:
            if len(pila) < 2:
                raise ValueError("expresión postfija mal formada")
            b, a = pila.pop(), pila.pop()
            pila.append([t] + a + b)
        elif t in UNARIOS:
            if not pila:
                raise ValueError("expresión postfija mal formada")
            pila.append([t] + pila.pop())
        else:
            pila.append([t])
    if len(pila) != 1:
        raise ValueError("expresión postfija mal formada")
    return pila[0]


def prefija_a_postfija(tokens):
    pila = []
    for t in reversed(tokens):                      # se lee de derecha a izquierda
        if t in PREC:
            if len(pila) < 2:
                raise ValueError("expresión prefija mal formada")
            a, b = pila.pop(), pila.pop()
            pila.append(a + b + [t])
        elif t in UNARIOS:
            if not pila:
                raise ValueError("expresión prefija mal formada")
            pila.append(pila.pop() + [t])
        else:
            pila.append([t])
    if len(pila) != 1:
        raise ValueError("expresión prefija mal formada")
    return pila[0]


def postfija_a_infija(tokens):
    """Reconstruye la expresión con los paréntesis mínimos necesarios."""
    pila = []                                       # (texto, precedencia)
    for t in tokens:
        if t in PREC:
            if len(pila) < 2:
                raise ValueError("expresión postfija mal formada")
            (b, pb), (a, pa) = pila.pop(), pila.pop()
            p = PREC[t]
            if pa < p or (t in RELACIONALES and pa == p):
                a = f"({a})"
            if pb <= p:
                b = f"({b})"
            pila.append((f"{a} {t} {b}", p))
        elif t in UNARIOS:
            if not pila:
                raise ValueError("expresión postfija mal formada")
            x, px = pila.pop()
            p = UNARIOS[t]
            if px < p:
                x = f"({x})"
            pila.append((f"-{x}" if t == 'neg' else f"no {x}", p))
        else:
            pila.append((t, 99))
    if len(pila) != 1:
        raise ValueError("expresión postfija mal formada")
    return pila[0][0]


def infija_a_prefija(tokens):
    return postfija_a_prefija(infija_a_postfija(tokens))


def prefija_a_infija(tokens):
    return postfija_a_infija(prefija_a_postfija(tokens))


# ====================== recorridos sobre el árbol de expresión ======================
def _sin_conv(n):
    """Las conversiones implícitas (casting) las inserta el compilador; no las escribió el usuario."""
    while isinstance(n, Conversion):
        n = n.expr
    return n


def _atomo(n):
    if isinstance(n, Literal):
        if n.tipo == 'texto':
            return f'"{n.valor}"'
        if n.tipo == 'logico':
            return 'verdadero' if n.valor else 'falso'
        return str(n.valor)
    if isinstance(n, Variable):
        return n.nombre
    if isinstance(n, Acceso):
        return f"{n.obj}.{n.attr}"
    raise TypeError(f"nodo sin notación: {type(n).__name__}")


def _op_unario(n):
    return 'no' if n.op == 'no' else 'neg'


def tiene_llamada(n):
    n = _sin_conv(n)
    if isinstance(n, Llamada):
        return True
    if isinstance(n, Binario):
        return tiene_llamada(n.izq) or tiene_llamada(n.der)
    if isinstance(n, Unario):
        return tiene_llamada(n.expr)
    return False


def postfija_arbol(n):
    """Recorrido postorden: hijos y al final el operador."""
    n = _sin_conv(n)
    if isinstance(n, Binario):
        return postfija_arbol(n.izq) + postfija_arbol(n.der) + [n.op]
    if isinstance(n, Unario):
        return postfija_arbol(n.expr) + [_op_unario(n)]
    if isinstance(n, Llamada):
        out = []
        for a in n.args:
            out += postfija_arbol(a)
        return out + [f"{n.nombre}/{len(n.args)}"]
    return [_atomo(n)]


def prefija_arbol(n):
    """Recorrido preorden: el operador y después los hijos."""
    n = _sin_conv(n)
    if isinstance(n, Binario):
        return [n.op] + prefija_arbol(n.izq) + prefija_arbol(n.der)
    if isinstance(n, Unario):
        return [_op_unario(n)] + prefija_arbol(n.expr)
    if isinstance(n, Llamada):
        out = [f"{n.nombre}/{len(n.args)}"]
        for a in n.args:
            out += prefija_arbol(a)
        return out
    return [_atomo(n)]


def infija_arbol(n):
    if tiene_llamada(n):
        return _infija_con_llamadas(n)
    return postfija_a_infija(postfija_arbol(n))


def _infija_con_llamadas(n):
    n = _sin_conv(n)
    if isinstance(n, Llamada):
        return f"{n.nombre}({', '.join(_infija_con_llamadas(a) for a in n.args)})"
    if isinstance(n, Binario):
        return f"({_infija_con_llamadas(n.izq)} {n.op} {_infija_con_llamadas(n.der)})"
    if isinstance(n, Unario):
        return f"({'-' if n.op == '-' else 'no '}{_infija_con_llamadas(n.expr)})"
    return _atomo(n)


def tokens_infijos_arbol(n):
    """Infija totalmente parentizada, construida directo del árbol (sirve de verificación)."""
    n = _sin_conv(n)
    if isinstance(n, Binario):
        return ['('] + tokens_infijos_arbol(n.izq) + [n.op] + tokens_infijos_arbol(n.der) + [')']
    if isinstance(n, Unario):
        return ['(', 'no' if n.op == 'no' else '-'] + tokens_infijos_arbol(n.expr) + [')']
    return [_atomo(n)]


def verificar(n):
    """Comprueba que el recorrido del árbol y los algoritmos de pila den lo mismo."""
    if tiene_llamada(n):
        return
    post = postfija_arbol(n)
    assert infija_a_postfija(tokens_infijos_arbol(n)) == post, "postfija: árbol y shunting-yard difieren"
    assert prefija_arbol(n) == postfija_a_prefija(post), "prefija: árbol y conversión difieren"
    assert prefija_a_postfija(prefija_arbol(n)) == post, "prefija -> postfija no regresa a la original"


# ====================== recorrido del programa ======================
def _es_atomo(n):
    return isinstance(_sin_conv(n), (Literal, Variable, Acceso))


def expresiones_del_programa(sentencias, salida=None):
    """Lista de (línea, etiqueta, nodo) con todas las expresiones no triviales del programa."""
    salida = [] if salida is None else salida

    def anota(linea, etiqueta, e):
        if e is not None and not _es_atomo(e):
            salida.append((linea, etiqueta, e))

    for s in sentencias:
        if isinstance(s, Declaracion):
            anota(s.linea, f"declaración de {s.nombre}", s.expr)
        elif isinstance(s, Asignacion):
            anota(s.linea, f"asignación a {s.nombre}", s.expr)
        elif isinstance(s, Categoria):
            anota(s.linea, f"límite de {s.nombre}", s.limite)
            expresiones_del_programa(s.cuerpo, salida)
        elif isinstance(s, Gasto):
            anota(s.linea, "monto de gasto", s.monto)
        elif isinstance(s, Si):
            anota(s.linea, "condición de si", s.cond)
            expresiones_del_programa(s.entonces, salida)
            expresiones_del_programa(s.sino or [], salida)
        elif isinstance(s, Mientras):
            anota(s.linea, "condición de mientras", s.cond)
            expresiones_del_programa(s.cuerpo, salida)
        elif isinstance(s, Accion):
            anota(s.linea, s.clase, s.expr)
        elif isinstance(s, Retornar):
            anota(s.linea, "retornar", s.expr)
        elif isinstance(s, Funcion):
            expresiones_del_programa(s.cuerpo, salida)
    return salida


def informe_notaciones(prog):
    lineas = []
    for linea, etiqueta, e in expresiones_del_programa(prog.sentencias):
        lineas.append(f"línea {linea:<3} {etiqueta}")
        lineas.append(f"    infija  : {infija_arbol(e)}")
        lineas.append(f"    postfija: {' '.join(postfija_arbol(e))}")
        lineas.append(f"    prefija : {' '.join(prefija_arbol(e))}")
    return "\n".join(lineas) if lineas else "(el programa no tiene expresiones compuestas)"


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print('Uso: python notaciones.py "a + b * (c - 2)"')
        sys.exit(1)
    try:
        toks = tokenizar(" ".join(sys.argv[1:]))
        post = infija_a_postfija(toks)
        print("infija  :", postfija_a_infija(post))
        print("postfija:", " ".join(post))
        print("prefija :", " ".join(postfija_a_prefija(post)))
    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)
