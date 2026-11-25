"""Pruebas automáticas de los módulos nuevos. Se ejecutan desde run_tests.py."""
import glob
import random

import notaciones as N
from errores import ERRORES


def pruebas_notaciones():
    """Devuelve (ok, detalle)."""
    # 1) Casos fijos: (infija, postfija esperada, prefija esperada)
    casos = [
        ("a + b * c", "a b c * +", "+ a * b c"),
        ("(a + b) * c", "a b + c *", "* + a b c"),
        ("a - b - c", "a b - c -", "- - a b c"),
        ("a - (b - c)", "a b c - -", "- a - b c"),
        ("-a * b", "a neg b *", "* neg a b"),
        ("no a y b", "a no b y", "y no a b"),
        ("no a > b", "a b > no", "no > a b"),
        ("a o b y c", "a b c y o", "o a y b c"),
        ("x * (p + q) / 2", "x p q + * 2 /", "/ * x + p q 2"),
        ('"hola" + "mundo"', '"hola" "mundo" +', '+ "hola" "mundo"'),
        ("c.gastado <= c.limite", "c.gastado c.limite <=", "<= c.gastado c.limite"),
        ("- - 3", "3 neg neg", "neg neg 3"),
    ]
    for infija, post, pre in casos:
        toks = N.tokenizar(infija)
        got_post = " ".join(N.infija_a_postfija(toks))
        got_pre = " ".join(N.infija_a_prefija(toks))
        if got_post != post or got_pre != pre:
            return False, f"'{infija}': postfija={got_post!r} (esperada {post!r}), prefija={got_pre!r} (esperada {pre!r})"
        if " ".join(N.prefija_a_postfija(pre.split())) != post:
            return False, f"prefija->postfija falla en '{infija}'"
        re_toks = N.tokenizar(N.postfija_a_infija(post.split()))
        if N.infija_a_postfija(re_toks) != post.split():
            return False, f"ida y vuelta infija falla en '{infija}'"

    # 2) Errores esperados
    for malo in ["a + ", "(a + b", "a + b)"]:
        try:
            N.infija_a_postfija(N.tokenizar(malo))
            if malo == "a + ":
                N.postfija_a_prefija(N.infija_a_postfija(N.tokenizar(malo)))
            return False, f"debió rechazar {malo!r}"
        except ValueError:
            pass

    # 3) Expresiones aleatorias: ida y vuelta entre las tres notaciones
    rnd = random.Random(7)
    binops = list(N.PREC)

    def gen(prof):
        if prof == 0 or rnd.random() < 0.25:
            return rnd.choice(["a", "b", "c", "x1", "7", "2.5"])
        if rnd.random() < 0.2:
            return (rnd.choice(["neg", "no"]), gen(prof - 1))
        return (rnd.choice(binops), gen(prof - 1), gen(prof - 1))

    def toks(t):
        if isinstance(t, str):
            return [t]
        if len(t) == 2:
            return ["(", "-" if t[0] == "neg" else "no"] + toks(t[1]) + [")"]
        return ["("] + toks(t[1]) + [t[0]] + toks(t[2]) + [")"]

    def post(t):
        if isinstance(t, str):
            return [t]
        return post(t[1]) + post(t[2]) + [t[0]] if len(t) == 3 else post(t[1]) + [t[0]]

    for i in range(400):
        arbol = gen(4)
        esperado = post(arbol)
        if N.infija_a_postfija(toks(arbol)) != esperado:
            return False, f"aleatoria {i}: shunting-yard difiere del árbol"
        pre = N.postfija_a_prefija(esperado)
        if N.prefija_a_postfija(pre) != esperado:
            return False, f"aleatoria {i}: prefija->postfija difiere"
        if N.infija_a_postfija(N.tokenizar(N.postfija_a_infija(esperado))) != esperado:
            return False, f"aleatoria {i}: la infija mínima cambia el significado"

    # 4) Todas las expresiones de los programas de prueba
    from main import compilar
    total = 0
    for ruta in sorted(glob.glob("tests/*/*.top")) + sorted(glob.glob("ejemplos_pendientes/*.top")):
        r = compilar(open(ruta, encoding="utf-8").read())
        ERRORES.limpiar() if not r.prog else None
        if r.prog is None or r.tabla is None:
            continue
        for _, _, e in N.expresiones_del_programa(r.prog.sentencias):
            N.verificar(e)
            total += 1
    return True, f"{len(casos)} casos fijos, 400 aleatorias, {total} expresiones de programas"


# ======================= generador de programas aleatorios (solo enteros / lógicos / texto) =======================
class GeneradorAleatorio:
    INTS = ['a', 'b', 'c', 'd']
    BOOLS = ['p', 'q']
    REL = ['<', '>', '<=', '>=', '==', '!=']
    TEXTOS = ['uno', 'dos', 'límite ñ', 'x y z']

    def __init__(self, rnd):
        self.r, self.n = rnd, 0

    def entero(self, prof):
        r = self.r
        if prof <= 0 or r.random() < 0.3:
            return r.choice([str(r.randint(0, 9)), r.choice(self.INTS), r.choice(self.INTS)])
        k = r.random()
        if k < 0.25:
            return f"({self.entero(prof - 1)} + {self.entero(prof - 1)})"
        if k < 0.45:
            return f"({self.entero(prof - 1)} - {self.entero(prof - 1)})"
        if k < 0.65:
            return f"({self.entero(prof - 1)} * {self.entero(prof - 1)})"
        if k < 0.75:
            return f"(-{self.entero(prof - 1)})"
        return f"({self.entero(prof - 1)} {r.choice(['+', '*', '-'])} {r.choice(['0', '1', '2'])})"

    def logico(self, prof):
        r = self.r
        if prof <= 0 or r.random() < 0.25:
            return r.choice(['verdadero', 'falso', 'p', 'q'])
        k = r.random()
        if k < 0.45:
            return f"({self.entero(prof - 1)} {r.choice(self.REL)} {self.entero(prof - 1)})"
        if k < 0.65:
            return f"({self.logico(prof - 1)} y {self.logico(prof - 1)})"
        if k < 0.85:
            return f"({self.logico(prof - 1)} o {self.logico(prof - 1)})"
        return f"(no {self.logico(prof - 1)})"

    def sentencias(self, cuantas, prof):
        return "\n".join(self.sentencia(prof) for _ in range(cuantas))

    def sentencia(self, prof):
        r, k = self.r, self.r.random()
        if k < 0.22:
            return f"{r.choice(self.INTS)} = {self.entero(2)};"
        if k < 0.32:
            return f"{r.choice(self.BOOLS)} = {self.logico(2)};"
        if k < 0.48:
            return f"mostrar({self.entero(2)});"
        if k < 0.54:
            return f"mostrar({self.logico(2)});"
        if k < 0.58:
            return f'mostrar("{r.choice(self.TEXTOS)}");'
        if k < 0.62:
            return f'alerta("{r.choice(self.TEXTOS)}");'
        if k < 0.78 and prof > 0:
            sino = f" sino {{\n{self.sentencias(r.randint(1, 2), prof - 1)}\n}}" if r.random() < 0.6 else ""
            return f"si ({self.logico(2)}) {{\n{self.sentencias(r.randint(1, 3), prof - 1)}\n}}{sino}"
        if k < 0.9 and prof > 0:
            self.n += 1
            c = f"k{self.n}"
            cuerpo = self.sentencias(r.randint(1, 3), prof - 1)
            return f"entero {c} = 0;\nmientras ({c} < {r.randint(0, 4)}) {{\n{cuerpo}\n{c} = {c} + 1;\n}}"
        self.n += 1
        v = f"v{self.n}"
        return f"entero {v} = {self.entero(2)};\nmostrar({v} + {r.choice(self.INTS)});"

    def programa(self):
        r = self.r
        cab = "\n".join(f"entero {v} = {r.randint(0, 6)};" for v in self.INTS)
        cab += f"\nlogico p = {r.choice(['verdadero', 'falso'])};\nlogico q = {r.choice(['verdadero', 'falso'])};"
        cuerpo = self.sentencias(r.randint(5, 9), 2)
        cola = "\n".join(f"mostrar({v});" for v in self.INTS + self.BOOLS)
        return f'presupuesto "Aleatorio" {{\n{cab}\n{cuerpo}\n{cola}\n}}\n'


def _desborda(mem):
    return any(isinstance(v, int) and not isinstance(v, bool) and abs(v) >= 2 ** 31 for v in mem.values())


def programas_validos(cantidad, semilla):
    """Genera programas aleatorios que compilan, terminan y no desbordan 32 bits.
    Devuelve [(texto, r, salida_referencia)]."""
    from main import compilar
    from interprete import Interprete, ErrorEjecucion
    rnd, out, intentos = random.Random(semilla), [], 0
    while len(out) < cantidad and intentos < cantidad * 8:
        intentos += 1
        texto = GeneradorAleatorio(rnd).programa()
        r = compilar(texto)
        if not r.ok:
            raise AssertionError(f"el generador produjo un programa inválido:\n{ERRORES.reporte()}\n{texto}")
        try:
            vm = Interprete(r.quads)
            salida = vm.ejecutar()
        except ErrorEjecucion:
            continue
        if _desborda(vm.mem):
            continue
        out.append((texto, r, salida))
    return out


def pruebas_optimizador_aleatorias(cantidad=150):
    from optimizador import optimizar
    from interprete import Interprete
    programas = programas_validos(cantidad, semilla=2026)
    if len(programas) < cantidad:
        return False, f"solo se generaron {len(programas)} programas válidos"
    antes = despues = 0
    for i, (texto, r, salida) in enumerate(programas):
        opt = optimizar(r.quads)
        try:
            nueva = Interprete(opt).ejecutar()
        except Exception as e:                                     # p. ej. un valor que dejó de existir
            return False, f"el programa aleatorio {i} falla al ejecutarse optimizado ({e}):\n{texto}"
        if nueva != salida:
            return False, f"el programa aleatorio {i} cambió su salida al optimizar:\n{texto}"
        n0, n1 = sum(q.op != 'LABEL' for q in r.quads), sum(q.op != 'LABEL' for q in opt)
        if n1 > n0:
            return False, f"el programa aleatorio {i} creció al optimizar ({n0} -> {n1})"
        antes, despues = antes + n0, despues + n1
    return True, f"{cantidad} programas: salida idéntica; {antes} -> {despues} instrucciones ({100 * (antes - despues) / antes:.0f}% menos)"


def pruebas_asm_aleatorias(cantidad=60):
    from codigo_objeto import generar_asm
    from ensamblar import ensamblar_y_correr, texto_esperado, herramientas_disponibles
    from optimizador import optimizar
    if not herramientas_disponibles():
        return True, "omitida (sin nasm/ld)"
    programas = programas_validos(cantidad, semilla=77)
    if len(programas) < cantidad:
        return False, f"solo se generaron {len(programas)} programas válidos"
    for i, (texto, r, salida) in enumerate(programas):
        esperado = texto_esperado(salida)
        for etiqueta, quads, regs in (("sin optimizar", r.quads, True), ("optimizado", optimizar(r.quads), True),
                                      ("sin optimizar y sin registros", r.quads, False)):
            obtenido = ensamblar_y_correr(generar_asm(quads, r.tabla, r.tipos_temp, registros=regs))
            if obtenido != esperado:
                return False, f"programa aleatorio {i} ({etiqueta}): el .asm imprime algo distinto\n{texto}"
    return True, f"{cantidad} programas, ensamblados sin optimizar, optimizados y sin registros: salida idéntica"


# ---------------- programas aleatorios CON FUNCIONES (prueban llamadas, recursión y registros) ----------------
class GeneradorFunciones:
    G = list('abcdefgh')                 # variables globales

    def __init__(self, rnd):
        self.r = rnd

    def ent(self, vs, prof, fns):
        r = self.r
        if prof <= 0 or r.random() < 0.3:
            return r.choice([str(r.randint(0, 9))] + vs * 2)
        k = r.random()
        if k < 0.3:
            return f"({self.ent(vs, prof - 1, fns)} + {self.ent(vs, prof - 1, fns)})"
        if k < 0.5:
            return f"({self.ent(vs, prof - 1, fns)} - {self.ent(vs, prof - 1, fns)})"
        if k < 0.65:
            return f"({self.ent(vs, prof - 1, fns)} * {r.randint(0, 3)})"
        if k < 0.8 and fns:
            nombre, na = r.choice(fns)
            return f"{nombre}({', '.join(self.ent(vs, prof - 1, None) for _ in range(na))})"
        return f"(-{self.ent(vs, prof - 1, fns)})"

    def programa(self):
        r, G = self.r, self.G
        lineas = [f"entero {v} = {r.randint(0, 5)};" for v in G]
        fns = []
        for k in range(r.randint(1, 3)):
            na = r.randint(1, 3)
            ps = [f"p{j}" for j in range(na)]
            loc = ['vx', 'vy']
            c = [f"entero vx = {self.ent(ps + G, 2, fns)};", f"entero vy = {self.ent(ps + G + ['vx'], 2, None)};"]
            if r.random() < 0.6:
                c.append(f"{r.choice(G)} = {r.choice(G)} + {self.ent(ps + loc, 1, None)};")   # modifica una global
            if r.random() < 0.5:
                c += ["entero k = 0;", f"mientras (k < {r.randint(1, 3)}) {{",
                      f"  vx = vx + {self.ent(ps + loc + ['k'], 1, None)};", "  k = k + 1;", "}"]
            if r.random() < 0.4 and k == 0 and na == 1:                  # recursión acotada
                c += [f"si ({ps[0]} <= 0) {{ retornar vx; }}", f"retornar vx + f0({ps[0]} - 1);"]
            else:
                c.append(f"retornar {self.ent(ps + loc, 2, None)};")
            nombre = f"f{k}"
            if k == 0 and "f0(" in c[-1]:
                nombre = "f0"
            lineas.append(f"funcion entero {nombre}({', '.join('entero ' + p for p in ps)}) {{\n  " + "\n  ".join(c) + "\n}")
            fns.append((nombre, na))
        lineas += ["entero i = 0;", f"mientras (i < {r.randint(1, 4)}) {{"]
        for _ in range(r.randint(2, 5)):
            lineas.append(f"  {r.choice(G)} = {self.ent(G + ['i'], 2, fns)};")
            if r.random() < 0.5:
                lineas.append(f"  mostrar({r.choice(G)});")
        lineas += ["  i = i + 1;", "}"] + [f"mostrar({v});" for v in G]
        return 'presupuesto "Funciones aleatorias" {\n' + "\n".join(lineas) + "\n}\n"


def pruebas_funciones_aleatorias(cantidad=60):
    """Programas con funciones (también recursivas): optimizador y ensamblador (con y sin registros)
    deben imprimir lo mismo que el intérprete de referencia."""
    from main import compilar
    from interprete import Interprete, ErrorEjecucion
    from optimizador import optimizar
    from codigo_objeto import generar_asm
    from ensamblar import ensamblar_y_correr, texto_esperado, herramientas_disponibles
    rnd, probados, intentos = random.Random(2024), 0, 0
    while probados < cantidad and intentos < cantidad * 4:
        intentos += 1
        texto = GeneradorFunciones(rnd).programa()
        r = compilar(texto)
        if not r.ok:
            return False, f"el generador produjo un programa que no compila:\n{ERRORES.reporte()}\n{r.pendiente}\n{texto}"
        try:
            vm = Interprete(r.quads, max_pasos=200000)
            salida = vm.ejecutar()
        except ErrorEjecucion:
            continue
        if _desborda(vm.mem):
            continue
        opt = optimizar(r.quads)
        if Interprete(opt, max_pasos=200000).ejecutar() != salida:
            return False, f"el optimizador cambió la salida:\n{texto}"
        if herramientas_disponibles():
            for etiqueta, quads in (("sin optimizar", r.quads), ("optimizado", opt)):
                for regs in (True, False):
                    obtenido = ensamblar_y_correr(generar_asm(quads, r.tabla, r.tipos_temp, registros=regs))
                    if obtenido != texto_esperado(salida):
                        return False, f"el .asm ({etiqueta}, registros={regs}) imprime algo distinto\n{texto}"
        probados += 1
    sufijo = "" if herramientas_disponibles() else " (asm omitido: sin nasm/ld)"
    return True, f"{probados} programas con funciones: optimizador y x86 (con/sin registros) iguales al intérprete" + sufijo


def ejecutar_todas():
    fallos = 0
    for nombre, prueba in [("notaciones", pruebas_notaciones),
                           ("optimizador (programas aleatorios)", pruebas_optimizador_aleatorias),
                           ("ensamblador x86 (programas aleatorios)", pruebas_asm_aleatorias),
                           ("funciones + registros (programas aleatorios)", pruebas_funciones_aleatorias)]:
        try:
            ok, detalle = prueba()
        except Exception as e:
            ok, detalle = False, f"{type(e).__name__}: {e}"
        fallos += 0 if ok else 1
        print(f"[{'OK ' if ok else 'FALLA'}] pruebas unitarias: {nombre:<40} {detalle}")
    return fallos
