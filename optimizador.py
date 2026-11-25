"""Módulo de optimización (Tema 3).

Trabaja sobre la lista de cuádruplos y NUNCA debe cambiar lo que el programa muestra.
Cada PASE es una función  pase(quads) -> quads  (devuelve una lista nueva).
Los pases se repiten hasta que ya no hay cambios (punto fijo).

Pases implementados
  1. pase_local ............. dentro de cada bloque básico: propagación de constantes y de copias,
                              plegado de constantes, simplificación algebraica y reducción de fuerza.
  2. pase_saltos ............ peephole: código inalcanzable, 'SALTA L' seguido de 'L:' y etiquetas sin uso.
  3. pase_temporales_constantes  temporales de una sola asignación constante se sustituyen en todo el programa.
  4. pase_invariantes ....... optimización de ciclos: saca del bucle los cálculos que no cambian.
  5. pase_codigo_muerto ..... elimina asignaciones cuyo resultado nadie lee.
  (+) pase_copias_adyacentes  peephole: (op,a,b,t) + (=,t,_,x) se fusionan en (op,a,b,x).

Para añadir una técnica: escribir la función y agregarla a PASES. La salida debe seguir idéntica;
run_tests.py y las pruebas aleatorias lo verifican.
"""
import re
from codigo_intermedio import Quad, Const
from interprete import BIN, UNA, ErrorEjecucion, Interprete

BINARIAS = set(BIN)                                   # + - * / < > <= >= == != Y O CONCAT
UNARIAS = set(UNA)                                    # NEG NO ENT_A_DEC ENT_A_TXT DEC_A_TXT LOG_A_TXT
PURAS = (BINARIAS - {'/'}) | UNARIAS | {'='}          # sin efectos laterales ('/' puede fallar con 0)
CONOCIDAS = BINARIAS | UNARIAS | {'=', 'LABEL', 'SALTA', 'SI_FALSO', 'FUNC', 'PARAM', 'CALL', 'RETORNAR'}
ERRORES_CALCULO = (ErrorEjecucion, ArithmeticError, TypeError, ValueError)


# ----------------------------- utilidades -----------------------------
def _conocida(op):
    return op in CONOCIDAS or op.startswith(('MOSTRAR_', 'ALERTA_'))


def _es_temporal(n):
    return isinstance(n, str) and re.fullmatch(r't\d+', n) is not None


def _define(q):
    """Nombre que escribe la instrucción (o None)."""
    return q.res if (q.op in BINARIAS or q.op in UNARIAS or q.op in ('=', 'CALL')) else None


def _lee(q):
    """Nombres (no constantes) que lee la instrucción."""
    if q.op in ('LABEL', 'SALTA', 'FUNC', 'CALL'):       # CALL: arg1 es el nombre de la función
        return []
    return [a for a in (q.arg1, q.arg2) if isinstance(a, str)]


def _es_pura(q):
    if q.op in PURAS:
        return True
    return q.op == '/' and isinstance(q.arg2, Const) and q.arg2.valor != 0


def _copia(q):
    return Quad(q.op, q.arg1, q.arg2, q.res)


def _firma(quads):
    return tuple((q.op, q.arg1, q.arg2, q.res) for q in quads)


def _const_de(v):
    if isinstance(v, bool):
        return Const(v, 'logico')
    if isinstance(v, int):
        return Const(v, 'entero')
    if isinstance(v, float):
        return Const(v, 'decimal')
    return Const(v, 'texto')


def _es_num(c, n):
    return isinstance(c, Const) and c.tipo in ('entero', 'decimal') and c.valor == n


def _es_entero(c, n):
    return isinstance(c, Const) and c.tipo == 'entero' and c.valor == n


# ----------------------------- simplificación de UNA instrucción -----------------------------
def _simplificar(q):
    """Devuelve la instrucción simplificada, o None si se puede eliminar."""
    op, a, b = q.op, q.arg1, q.arg2

    def asigna(x):
        return Quad('=', x, None, q.res)

    if op == 'SI_FALSO' and isinstance(a, Const):
        return None if a.valor else Quad('SALTA', None, None, q.res)
    if op in UNA and isinstance(a, Const):                         # plegado de constantes (unarias)
        try:
            return asigna(_const_de(UNA[op](a.valor)))
        except ERRORES_CALCULO:
            return q
    if op in BIN and isinstance(a, Const) and isinstance(b, Const):  # plegado (binarias)
        try:
            return asigna(_const_de(BIN[op](a.valor, b.valor)))
        except ERRORES_CALCULO:                                    # p. ej. división entre cero: se deja
            return q
    # simplificación algebraica (las de decimales evitan el caso -0.0 para no alterar la salida)
    if op == '+':
        if _es_entero(b, 0):
            return asigna(a)
        if _es_entero(a, 0):
            return asigna(b)
    elif op == '-':
        if _es_num(b, 0):
            return asigna(a)
    elif op == '*':
        if _es_num(b, 1):
            return asigna(a)
        if _es_num(a, 1):
            return asigna(b)
        if _es_entero(b, 0):
            return asigna(b)
        if _es_entero(a, 0):
            return asigna(a)
        if _es_num(b, 2):                                          # reducción de fuerza: x*2 -> x+x
            return Quad('+', a, a, q.res)
        if _es_num(a, 2):
            return Quad('+', b, b, q.res)
    elif op == '/':
        if _es_num(b, 1):
            return asigna(a)
    elif op == 'Y':
        if isinstance(b, Const):
            return asigna(a if b.valor else b)
        if isinstance(a, Const):
            return asigna(b if a.valor else a)
    elif op == 'O':
        if isinstance(b, Const):
            return asigna(b if b.valor else a)
        if isinstance(a, Const):
            return asigna(a if a.valor else b)
    return q


# ----------------------------- PASE 1: local (por bloque básico) -----------------------------
def pase_local(quads):
    out, env = [], {}           # env: nombre -> Const | nombre del que es copia

    def invalidar(n):
        env.pop(n, None)
        for k in [k for k, v in env.items() if v == n]:
            del env[k]

    def sust(x):
        return env.get(x, x) if isinstance(x, str) else x

    for q in quads:
        if q.op in ('LABEL', 'FUNC'):                              # entra un nuevo bloque: se olvida todo
            env.clear()
            out.append(q)
            continue
        if q.op == 'SALTA':
            out.append(q)
            env.clear()
            continue
        if q.op == 'CALL':                                         # la función puede cambiar globales
            out.append(q)
            env.clear()
            continue
        if q.op == 'RETORNAR':
            out.append(Quad(q.op, sust(q.arg1), None, None))
            env.clear()
            continue
        nq = _simplificar(Quad(q.op, sust(q.arg1), sust(q.arg2), q.res))
        if nq is None:
            continue
        if nq.op == '=' and nq.arg1 == nq.res:                     # x = x
            continue
        out.append(nq)
        d = _define(nq)
        if d is not None:
            invalidar(d)
            if nq.op == '=' and nq.arg1 != d:
                env[d] = nq.arg1
    return out


# ----------------------------- PASE 2: saltos y código inalcanzable -----------------------------
def pase_saltos(quads):
    out, vivo = [], True
    for q in quads:                                                # 1) nada es alcanzable tras SALTA / RETORNAR
        if q.op in ('LABEL', 'FUNC'):
            vivo = True
        if vivo:
            out.append(q)
        if q.op in ('SALTA', 'RETORNAR'):
            vivo = False
    quads, out = out, []
    for i, q in enumerate(quads):                                  # 2) SALTA L seguido de L:
        if q.op == 'SALTA':
            j, siguientes = i + 1, set()
            while j < len(quads) and quads[j].op == 'LABEL':
                siguientes.add(quads[j].res)
                j += 1
            if q.res in siguientes:
                continue
        out.append(q)
    usadas = {q.res for q in out if q.op in ('SALTA', 'SI_FALSO')}  # 3) etiquetas sin referencias
    return [q for q in out if not (q.op == 'LABEL' and q.res not in usadas)]


# ----------------------------- PASE 2b: copia de temporal adyacente (peephole) -----------------------------
def pase_copias_adyacentes(quads):
    """(op, a, b, tN) seguido de (=, tN, _, x), con tN usado solo ahí  ->  (op, a, b, x)."""
    cuenta = _definiciones(quads)
    lecturas = {}
    for q in quads:
        for n in _lee(q):
            lecturas[n] = lecturas.get(n, 0) + 1
    out, i = [], 0
    while i < len(quads):
        q = quads[i]
        if (i + 1 < len(quads) and _define(q) is not None and _es_temporal(q.res)
                and cuenta[q.res] == 1 and lecturas.get(q.res) == 1):
            n = quads[i + 1]
            if n.op == '=' and n.arg1 == q.res and n.res != q.res:
                out.append(Quad(q.op, q.arg1, q.arg2, n.res))
                i += 2
                continue
        out.append(q)
        i += 1
    return out


# ----------------------------- PASE 3: temporales constantes (global) -----------------------------
def _definiciones(quads):
    cuenta = {}
    for q in quads:
        d = _define(q)
        if d is not None:
            cuenta[d] = cuenta.get(d, 0) + 1
    return cuenta


def pase_temporales_constantes(quads):
    cuenta = _definiciones(quads)
    consts = {q.res: q.arg1 for q in quads
              if q.op == '=' and isinstance(q.arg1, Const) and _es_temporal(q.res) and cuenta[q.res] == 1}
    if not consts:
        return quads
    out = []
    for q in quads:
        if q.op in ('LABEL', 'SALTA'):
            out.append(q)
        else:
            a1 = consts.get(q.arg1, q.arg1) if isinstance(q.arg1, str) else q.arg1
            a2 = consts.get(q.arg2, q.arg2) if isinstance(q.arg2, str) else q.arg2
            out.append(Quad(q.op, a1, a2, q.res))
    return out


# ----------------------------- PASE 4: código invariante de ciclos -----------------------------
def pase_invariantes(quads):
    quads = list(quads)
    cuenta = _definiciones(quads)
    movido = True
    while movido:
        movido = False
        etiquetas = {q.res: i for i, q in enumerate(quads) if q.op == 'LABEL'}
        for j, q in enumerate(quads):
            if q.op != 'SALTA' or etiquetas.get(q.res, j) >= j:
                continue                                           # solo saltos hacia atrás = ciclos
            i = etiquetas[q.res]
            if any(k < i for k, x in enumerate(quads) if x.op in ('SALTA', 'SI_FALSO') and x.res == q.res):
                continue                                           # al encabezado entran saltos de fuera
            if any(x.op == 'CALL' for x in quads[i:j + 1]):
                continue                                           # una llamada puede cambiar globales: no se mueve nada
            definidos = {_define(x) for x in quads[i:j + 1]} - {None}
            for k in range(i + 1, j):
                x = quads[k]
                if (_define(x) is not None and _es_temporal(x.res) and cuenta.get(x.res) == 1
                        and x.op != '=' and _es_pura(x) and not any(n in definidos for n in _lee(x))):
                    quads.pop(k)
                    quads.insert(i, x)                             # se ejecuta una vez, antes del ciclo
                    movido = True
                    break
            if movido:
                break
    return quads


# ----------------------------- PASE 5: código muerto -----------------------------
def pase_codigo_muerto(quads):
    while True:
        leidos = {n for q in quads for n in _lee(q)}
        nuevo = [q for q in quads if not (_define(q) is not None and q.res not in leidos and _es_pura(q))]
        if len(nuevo) == len(quads):
            return quads
        quads = nuevo


PASES = [
    ('propagación/plegado local', pase_local),
    ('saltos e inalcanzable', pase_saltos),
    ('copias adyacentes', pase_copias_adyacentes),
    ('temporales constantes', pase_temporales_constantes),
    ('invariantes de ciclo', pase_invariantes),
    ('código muerto', pase_codigo_muerto),
]


def optimizar_con_informe(quads):
    """Devuelve (cuádruplos optimizados, {pase: instrucciones eliminadas})."""
    quads = [_copia(q) for q in quads]
    informe = {nombre: 0 for nombre, _ in PASES}
    if not all(_conocida(q.op) for q in quads):                    # operación desconocida: no se toca
        return quads, informe
    for _ in range(30):
        antes = _firma(quads)
        for nombre, pase in PASES:
            n0 = len(quads)
            quads = pase(quads)
            informe[nombre] += n0 - len(quads)
        if _firma(quads) == antes:
            break
    return quads, informe


def optimizar(quads):
    return optimizar_con_informe(quads)[0]


# ----------------------------- costos antes / después -----------------------------
def medir(quads):
    """Métricas estáticas y dinámicas; ejecuta el programa con el intérprete de referencia."""
    temporales = {n for q in quads for n in (q.arg1, q.arg2, q.res) if _es_temporal(n)}
    vm = Interprete(quads)
    salida = vm.ejecutar()
    return {
        'Instrucciones (sin etiquetas)': sum(1 for q in quads if q.op != 'LABEL'),
        'Temporales distintos': len(temporales),
        'Saltos': sum(1 for q in quads if q.op in ('SALTA', 'SI_FALSO')),
        'Instrucciones ejecutadas': vm.pasos,
        'Accesos a memoria (lecturas + escrituras)': vm.lecturas + vm.mem.escrituras,
    }, salida


def informe_costos(antes, despues):
    ma, sa = medir(antes)
    mb, sb = medir(despues)
    filas = [f"{'Métrica':<44}{'Antes':>8}{'Después':>9}{'Mejora':>9}", '-' * 70]
    for k in ma:
        mejora = f"{100 * (ma[k] - mb[k]) / ma[k]:.1f}%" if ma[k] else "-"
        filas.append(f"{k:<44}{ma[k]:>8}{mb[k]:>9}{mejora:>9}")
    filas.append(f"Salida del programa idéntica: {'sí' if sa == sb else 'NO  <-- ERROR'}")
    return "\n".join(filas)
