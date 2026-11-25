"""Intérprete de referencia: ejecuta los cuádruplos directamente.
Sirve para comprobar que el compilador es correcto ANTES de generar ensamblador
(y después, para comparar su salida contra la del programa .asm)."""
from codigo_intermedio import Const


class ErrorEjecucion(Exception):
    pass


MIN32, MAX32 = -(2 ** 31), 2 ** 31 - 1


def _entero_32(valor):
    """Emula el desbordamiento con signo de 32 bits del código x86 generado."""
    valor = int(valor) & 0xFFFFFFFF
    return valor - 0x100000000 if valor >= 0x80000000 else valor


def _div(a, b):
    if b == 0:
        raise ErrorEjecucion("división entre cero")
    return a / b


BIN = {
    '+': lambda a, b: _entero_32(a + b), '-': lambda a, b: _entero_32(a - b),
    '*': lambda a, b: _entero_32(a * b), '/': _div,
    '<': lambda a, b: a < b, '>': lambda a, b: a > b, '<=': lambda a, b: a <= b,
    '>=': lambda a, b: a >= b, '==': lambda a, b: a == b, '!=': lambda a, b: a != b,
    'Y': lambda a, b: a and b, 'O': lambda a, b: a or b, 'CONCAT': lambda a, b: a + b,
}
UNA = {
    'NEG': lambda a: _entero_32(-a), 'NO': lambda a: not a,
    'ENT_A_DEC': float, 'ENT_A_TXT': str,
    'DEC_A_TXT': lambda a: f"{a:.2f}", 'LOG_A_TXT': lambda a: 'verdadero' if a else 'falso',
}


def formato(v, sufijo):
    if sufijo == 'DEC':
        return f"{v:.2f}"
    if sufijo == 'LOG':
        return 'verdadero' if v else 'falso'
    return str(v)


class Memoria(dict):
    """Diccionario que cuenta las escrituras (para medir costos)."""
    escrituras = 0

    def __setitem__(self, clave, valor):
        self.escrituras += 1
        super().__setitem__(clave, valor)


class Interprete:
    def __init__(self, quads, max_pasos=1_000_000, max_pila=2_000):
        self.quads, self.max_pasos, self.max_pila, self.mem = quads, max_pasos, max_pila, Memoria()
        self.pasos = 0        # instrucciones ejecutadas (sin contar etiquetas)
        self.lecturas = 0     # lecturas de memoria (operandos que no son constantes)

    def val(self, a):
        if isinstance(a, Const):
            return a.valor
        self.lecturas += 1
        if a not in self.mem:
            raise ErrorEjecucion(f"'{a}' no tiene valor asignado")
        return self.mem[a]

    def ejecutar(self):
        etiquetas = {q.res: i for i, q in enumerate(self.quads) if q.op == 'LABEL'}
        funciones = {q.arg1: i for i, q in enumerate(self.quads) if q.op == 'FUNC'}
        salida, pc, pasos = [], 0, 0
        args, pila = [], []         # argumentos pendientes (PARAM) y pila de llamadas
        while pc < len(self.quads):
            q = self.quads[pc]
            pc += 1
            pasos += 1
            if pasos > self.max_pasos:
                raise ErrorEjecucion("se excedió el máximo de pasos (¿ciclo infinito?)")
            op = q.op
            if op in ('LABEL', 'FUNC'):
                pasos -= 1
                continue
            self.pasos += 1
            if op == 'SALTA':
                pc = etiquetas[q.res]
            elif op == 'SI_FALSO':
                if not self.val(q.arg1):
                    pc = etiquetas[q.res]
            elif op == '=':
                valor = self.val(q.arg1)
                self.mem[q.res] = _entero_32(valor) if isinstance(valor, int) and not isinstance(valor, bool) else valor
            elif op == 'PARAM':
                args.append(self.val(q.arg1))
            elif op == 'CALL':
                if len(pila) >= self.max_pila:
                    raise ErrorEjecucion("desbordamiento de pila (¿recursión infinita?)")
                n = q.arg2
                valores = args[len(args) - n:]
                del args[len(args) - n:]
                ini = funciones[q.arg1]
                params, locales = self.quads[ini].arg2, self.quads[ini].res
                # se guardan los valores de la activación anterior de esta función (recursión)
                guardado = {k: self.mem[k] for k in locales if k in self.mem}
                pila.append((pc, q.res, locales, guardado))
                for nombre, v in zip(params, valores):
                    self.mem[nombre] = v
                pc = ini + 1
            elif op == 'RETORNAR':
                valor = self.val(q.arg1)
                if not pila:
                    raise ErrorEjecucion("'retornar' fuera de una función")
                pc, res, locales, guardado = pila.pop()
                for k in locales:                       # se restaura la activación anterior
                    dict.pop(self.mem, k, None)
                for k, v in guardado.items():
                    self.mem[k] = v
                if res is not None:
                    self.mem[res] = valor
            elif op in BIN:
                self.mem[q.res] = BIN[op](self.val(q.arg1), self.val(q.arg2))
            elif op in UNA:
                self.mem[q.res] = UNA[op](self.val(q.arg1))
            elif op.startswith(('MOSTRAR_', 'ALERTA_')):
                clase, suf = op.split('_')
                txt = formato(self.val(q.arg1), suf)
                salida.append(("ALERTA: " if clase == 'ALERTA' else "") + txt)
            else:
                raise ErrorEjecucion(f"instrucción no soportada por el intérprete: {op}")
        return salida
