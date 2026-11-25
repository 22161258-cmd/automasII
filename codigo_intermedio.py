"""Generación de código intermedio, cuádruplos del tema 2

     Los operandos son:
  - str   : variable, temporal (t1, t2...) o atributo de categoría ('comida.gastado')
  - Const : literal con su tipo
  - None  : no se usa  (se imprime como '_')
Los saltos usan etiquetas:  (LABEL,_,_,L1)  (SALTA,_,_,L1)  (SI_FALSO,t1,_,L1)

Funciones (el cuerpo se emite en línea, rodeado por un SALTA para que el flujo normal lo esquive):
  (SALTA,_,_,L9)
  (FUNC, nombre, (params...), (locales...))   <- inicio; 'locales' = params + variables + temporales
  ... cuerpo ...                                     de la función (el intérprete/asm los guardan y
  (RETORNAR, valor)                                  restauran en cada llamada, lo que permite recursión)
  (LABEL,_,_,L9)
Llamada:  (PARAM, a) ... (PARAM, z)  (CALL, nombre, num_args, t)   """


from dataclasses import dataclass
from ast_nodes import *


@dataclass(frozen=True)
class Const:
    valor: object
    tipo: str

    def __repr__(self):
        if self.tipo == 'texto':
            return f'"{self.valor}"'
        if self.tipo == 'logico':
            return 'verdadero' if self.valor else 'falso'
        return repr(self.valor)


class Quad:
    def __init__(self, op, arg1=None, arg2=None, res=None):
        self.op, self.arg1, self.arg2, self.res = op, arg1, arg2, res

    def __repr__(self):
        f = lambda x: '_' if x is None else repr(x) if isinstance(x, Const) else str(x)
        return f"({self.op}, {f(self.arg1)}, {f(self.arg2)}, {f(self.res)})"


def formatear(quads):
    return "\n".join(f"{i + 1:>3}  {q}" for i, q in enumerate(quads))


CONV = {('entero', 'decimal'): 'ENT_A_DEC', ('entero', 'texto'): 'ENT_A_TXT',
        ('decimal', 'texto'): 'DEC_A_TXT', ('logico', 'texto'): 'LOG_A_TXT'}
ABREV = {'entero': 'ENT', 'decimal': 'DEC', 'texto': 'TXT', 'logico': 'LOG'}
DEFECTO = {'entero': Const(0, 'entero'), 'decimal': Const(0.0, 'decimal'),
           'texto': Const('', 'texto'), 'logico': Const(False, 'logico')}
OPS = {'y': 'Y', 'o': 'O'}


def _declaradas(stmts):
    """id_unico de las variables declaradas dentro de un cuerpo de función (incluye bloques anidados)."""
    out = []
    for s in stmts:
        if isinstance(s, Declaracion) and s.simbolo is not None:
            out.append(s.simbolo.id_unico)
        elif isinstance(s, Si):
            out += _declaradas(s.entonces) + _declaradas(s.sino or [])
        elif isinstance(s, Mientras):
            out += _declaradas(s.cuerpo)
    return out


class GeneradorCI:
    def __init__(self):
        self.quads = []
        self.tipos_temp = {}    # temporal -> tipo (lo necesita el generador de código objeto)
        self._t = 0
        self._l = 0

    # ---------- utilidades ----------
    def nueva_temp(self, tipo):
        self._t += 1
        t = f"t{self._t}"
        self.tipos_temp[t] = tipo
        return t

    def nueva_etiqueta(self):
        self._l += 1
        return f"L{self._l}"

    def emitir(self, op, a1=None, a2=None, res=None):
        self.quads.append(Quad(op, a1, a2, res))
        return res

    def generar(self, prog):
        for s in prog.sentencias:
            self.stmt(s)
        return self.quads

    def stmt(self, n):
        getattr(self, 'g_' + type(n).__name__)(n)

    def bloque(self, lista):
        for s in lista:
            self.stmt(s)

    # ---------- expresiones: devuelven el operando donde queda el resultado ----------
    def expr(self, n):
        return getattr(self, 'x_' + type(n).__name__)(n)

    def x_Literal(self, n):
        return Const(n.valor, n.tipo)

    def x_Variable(self, n):
        return n.simbolo.id_unico

    def x_Acceso(self, n):
        return f"{n.simbolo.id_unico}.{n.attr}"

    def x_Conversion(self, n):
        a = self.expr(n.expr)
        t = self.nueva_temp(n.destino)
        return self.emitir(CONV[(n.origen, n.destino)], a, None, t)

    def x_Unario(self, n):
        a = self.expr(n.expr)
        t = self.nueva_temp(n.tipo)
        return self.emitir('NEG' if n.op == '-' else 'NO', a, None, t)

    def x_Binario(self, n):
        a, b = self.expr(n.izq), self.expr(n.der)
        t = self.nueva_temp(n.tipo)
        op = 'CONCAT' if (n.op == '+' and n.tipo == 'texto') else OPS.get(n.op, n.op)
        return self.emitir(op, a, b, t)

    def x_Llamada(self, n):
        args = [self.expr(a) for a in n.args]          # primero se evalúan todos los argumentos...
        for a in args:
            self.emitir('PARAM', a)                    # ...y luego se apilan juntos
        t = self.nueva_temp(n.tipo)
        return self.emitir('CALL', n.simbolo.id_unico, len(args), t)

    # ---------- sentencias ----------
    def g_Declaracion(self, n):
        v = self.expr(n.expr) if n.expr is not None else DEFECTO[n.tipo_decl]
        self.emitir('=', v, None, n.simbolo.id_unico)

    def g_Asignacion(self, n):
        self.emitir('=', self.expr(n.expr), None, n.simbolo.id_unico)

    def g_Categoria(self, n):
        cid = n.simbolo.id_unico
        self.emitir('=', self.expr(n.limite), None, f"{cid}.limite")
        self.emitir('=', Const(0.0, 'decimal'), None, f"{cid}.gastado")
        self.emitir('=', Const(n.nombre, 'texto'), None, f"{cid}.nombre")
        self.bloque(n.cuerpo)

    def g_Gasto(self, n):
        cid = n.simbolo.id_unico
        m = self.expr(n.monto)
        self.emitir('+', f"{cid}.gastado", m, f"{cid}.gastado")

    def g_Si(self, n):
        c = self.expr(n.cond)
        l_else = self.nueva_etiqueta()
        self.emitir('SI_FALSO', c, None, l_else)
        self.bloque(n.entonces)
        if n.sino:
            l_fin = self.nueva_etiqueta()
            self.emitir('SALTA', None, None, l_fin)
            self.emitir('LABEL', None, None, l_else)
            self.bloque(n.sino)
            self.emitir('LABEL', None, None, l_fin)
        else:
            self.emitir('LABEL', None, None, l_else)

    def g_Mientras(self, n):
        l_ini, l_fin = self.nueva_etiqueta(), self.nueva_etiqueta()
        self.emitir('LABEL', None, None, l_ini)
        c = self.expr(n.cond)
        self.emitir('SI_FALSO', c, None, l_fin)
        self.bloque(n.cuerpo)
        self.emitir('SALTA', None, None, l_ini)
        self.emitir('LABEL', None, None, l_fin)

    def g_Accion(self, n):
        v = self.expr(n.expr)
        self.emitir(f"{n.clase.upper()}_{ABREV[n.expr.tipo]}", v)

    def g_Funcion(self, n):
        l_fin = self.nueva_etiqueta()
        self.emitir('SALTA', None, None, l_fin)       # el flujo normal se salta el cuerpo
        params = tuple(p.id_unico for p in n.param_simbolos)
        t_antes, pos = self._t, len(self.quads)
        self.emitir('FUNC', n.simbolo.id_unico, params, ())
        self.bloque(n.cuerpo)
        self.emitir('RETORNAR', DEFECTO[n.tipo_ret])   # por si algún camino llega al final sin 'retornar'
        temporales = [f"t{i}" for i in range(t_antes + 1, self._t + 1)]
        locales = list(params) + _declaradas(n.cuerpo) + temporales
        self.quads[pos].res = tuple(dict.fromkeys(locales))
        self.emitir('LABEL', None, None, l_fin)

    def g_Retornar(self, n):
        self.emitir('RETORNAR', self.expr(n.expr))

    def g_LlamadaSent(self, n):
        self.expr(n.llamada)
