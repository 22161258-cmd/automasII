"""Generación de código objeto: x86 de 32 bits para Linux, sintaxis NASM (Tema 4, versión 1).

ALCANCE ACTUAL
  Soportado: entero, decimal, logico y texto; + - * /, comparaciones (incluye == y != entre textos),
             Y O NO, NEG, asignación, saltos (SALTA, SI_FALSO, LABEL), conversiones (ENT_A_DEC,
             DEC_A_ENT, ENT_A_TXT, DEC_A_TXT, LOG_A_TXT), CONCAT, MOSTRAR_/ALERTA_ de ENT, DEC, LOG y TXT,
             categorías (son variables 'cat.limite', 'cat.gastado', 'cat.nombre') y funciones
             (FUNC, PARAM, CALL, RETORNAR) con recursión.
REPRESENTACIÓN DE LOS DECIMALES  (punto fijo: enteros en CENTAVOS)
  Un decimal se guarda como entero de 32 bits = valor * 100  (12.34 -> 1234).  Así + - y las
  comparaciones son las mismas instrucciones que para enteros. Solo * y / necesitan rutinas
  (mul_dec, div_dec) que usan un producto de 64 bits y redondean al centavo (mitad hacia afuera).
  Límites: rango +-21 474 836.47; las constantes con más de 2 decimales se redondean al centavo;
  en cadenas de operaciones se redondea en cada paso (el intérprete usa float), por lo que el
  último centavo puede diferir en casos extremos.
FUNCIONES
  Todas las variables viven en memoria (.bss). Para permitir recursión, quien llama guarda en la pila
  las variables de la función llamada (parámetros, locales, temporales), copia los argumentos a los
  parámetros, hace 'call' y al volver las restaura; el resultado viaja en EAX.
TEXTO
  Un texto es un puntero a una cadena terminada en 0. Los resultados de CONCAT y de las conversiones
  usan un buffer propio de 256 bytes (se truncan a 255 caracteres).
ASIGNACIÓN DE REGISTROS  (registros=True por omisión; registros=False deja todo en memoria)
  Disponibles para variables y temporales: EBX, ESI, EDI y EBP (todas las rutinas de apoyo los
  preservan). EAX, ECX y EDX quedan como temporales de cada instrucción.
  1. Se calcula el intervalo de vida de cada variable/temporal (primer a último cuádruplo que la usa).
  2. Ciclos: si un salto vuelve hacia atrás, toda variable que viva dentro del ciclo y llegue de fuera
     (o se lea antes de escribirse) conserva su registro durante todo el ciclo.
  3. Funciones: todo lo que toca el cuerpo de una función ("fijo") se considera vivo en todo el
     programa, así ninguna otra variable comparte su registro y una llamada no destruye valores
     del que llama.
  4. Barrido lineal (linear scan): los intervalos que no se solapan comparten registro. Si faltan
     registros se deja en memoria la variable de menor peso (usos, x10 por cada ciclo anidado).
  Además: las operaciones usan el registro de la variable directamente (sin pasar por EAX cuando se
  puede) y una comparación seguida de SI_FALSO se fusiona en  cmp + salto condicional.
SALIDA
  Sin libc: usa llamadas al sistema de Linux (int 0x80) y una pequeña rutina propia para
  imprimir enteros. Se ensambla con:
      nasm -f elf32 programa.asm -o programa.o && ld -m elf_i386 programa.o -o programa
  Nota: entero = 32 bits con signo (el intérprete de referencia usa enteros sin límite).
"""
import re
from decimal import Decimal, ROUND_HALF_UP
from codigo_intermedio import Const


class NoSoportadoAsm(NotImplementedError):
    """La construcción aún no tiene traducción a ensamblador."""


DEFINEN = {'=', '+', '-', '*', '/', '<', '>', '<=', '>=', '==', '!=', 'Y', 'O', 'NEG', 'NO',
           'ENT_A_DEC', 'DEC_A_ENT', 'ENT_A_TXT', 'DEC_A_TXT', 'LOG_A_TXT', 'CONCAT', 'CALL'}
SALIDAS = {f"{c}_{t}" for c in ('MOSTRAR', 'ALERTA') for t in ('ENT', 'DEC', 'LOG', 'TXT')}
SOPORTADAS = DEFINEN | SALIDAS | {'LABEL', 'SALTA', 'SI_FALSO', 'FUNC', 'PARAM', 'RETORNAR'}
INSTR = {'+': 'add', '-': 'sub', '*': 'imul', 'Y': 'and', 'O': 'or'}
SETCC = {'<': 'setl', '>': 'setg', '<=': 'setle', '>=': 'setge', '==': 'sete', '!=': 'setne'}
MIN32, MAX32 = -2 ** 31, 2 ** 31 - 1
REGS = ['ebx', 'esi', 'edi', 'ebp']       # registros asignables a variables
CC_INV = {'<': 'jge', '>': 'jle', '<=': 'jg', '>=': 'jl', '==': 'jne', '!=': 'je'}   # salta si la condición es falsa
BUF = 256                                    # tamaño del buffer de cada texto calculado


def centavos(valor):
    """Valor decimal -> entero en centavos (redondeo mitad hacia arriba, sin errores de float)."""
    return int((Decimal(str(valor)) * 100).quantize(Decimal(1), rounding=ROUND_HALF_UP))


def _tipos(tabla, tipos_temp):
    t = dict(tipos_temp)
    for s in tabla.todos:
        if s.clase == 'categoria':
            t[f"{s.id_unico}.limite"] = t[f"{s.id_unico}.gastado"] = 'decimal'
            t[f"{s.id_unico}.nombre"] = 'texto'
        elif s.clase != 'funcion':
            t[s.id_unico] = s.tipo
    return t


def _leidos(q):
    if q.op in ('LABEL', 'SALTA', 'FUNC', 'CALL'):       # CALL: arg1 es el nombre de la función
        return []
    return [a for a in (q.arg1, q.arg2) if a is not None]


def _tipo(x, tipos):
    return x.tipo if isinstance(x, Const) else tipos[x]


def _validar(q, tipos):
    if q.op not in SOPORTADAS:
        raise NoSoportadoAsm(f"la operación {q.op} aún no tiene traducción a ensamblador: {q}")
    for x in _leidos(q) + ([q.res] if q.op in DEFINEN else []):
        if isinstance(x, Const) and x.tipo == 'entero' and not (MIN32 <= x.valor <= MAX32):
            raise NoSoportadoAsm(f"constante fuera del rango de 32 bits: {x}")
        if isinstance(x, Const) and x.tipo == 'decimal' and not (MIN32 <= centavos(x.valor) <= MAX32):
            raise NoSoportadoAsm(f"constante decimal fuera de rango (+-21 474 836.47): {x}")


def _etq(nombre):
    return "v_" + nombre.replace('.', '__')


def _bytes(texto):
    datos = list(texto.encode('utf-8')) + [0]
    return ", ".join(str(b) for b in datos)


RUNTIME = """
; ---------------- rutinas de apoyo (convención cdecl: el que llama limpia la pila) ----------------
print_nl:                       ; imprime un salto de línea
    push ebx
    mov eax, 4
    mov ebx, 1
    mov ecx, nl
    mov edx, 1
    int 0x80
    pop ebx
    ret

print_str:                      ; [esp+4] = dirección de una cadena terminada en 0
    push ebp
    mov ebp, esp
    push ebx
    mov ecx, [ebp+8]
    xor edx, edx
.largo:
    cmp byte [ecx+edx], 0
    je .escribe
    inc edx
    jmp .largo
.escribe:
    mov eax, 4
    mov ebx, 1
    int 0x80
    pop ebx
    pop ebp
    ret

print_int:                      ; [esp+4] = entero con signo
    push ebp
    mov ebp, esp
    push ebx
    push esi
    mov eax, [ebp+8]
    xor esi, esi                ; esi = 1 si el número es negativo
    test eax, eax
    jns .sigue
    neg eax
    mov esi, 1
.sigue:
    mov ebx, 10
    mov ecx, numbuf+11          ; se escriben los dígitos de derecha a izquierda
.digito:
    xor edx, edx
    div ebx
    add dl, '0'
    dec ecx
    mov [ecx], dl
    test eax, eax
    jnz .digito
    test esi, esi
    jz .escribe
    dec ecx
    mov byte [ecx], '-'
.escribe:
    mov edx, numbuf+11
    sub edx, ecx                ; longitud
    mov eax, 4
    mov ebx, 1
    int 0x80
    pop esi
    pop ebx
    pop ebp
    ret
print_dec:                      ; [esp+4] = decimal en centavos; imprime  [-]ent.dd
    push ebp
    mov ebp, esp
    push dword [ebp+8]
    push dword fmtbuf
    call fmt_dec
    add esp, 8
    push dword fmtbuf
    call print_str
    add esp, 4
    pop ebp
    ret

str_copy_n:                     ; [ebp+8]=destino [ebp+12]=origen [ebp+16]=máximo de caracteres
    push ebp                    ; copia y termina en 0; devuelve en EAX la dirección de ese 0
    mov ebp, esp
    push esi
    push edi
    mov edi, [ebp+8]
    mov esi, [ebp+12]
    mov ecx, [ebp+16]
.sigue:
    test ecx, ecx
    jz .fin
    mov al, [esi]
    test al, al
    jz .fin
    mov [edi], al
    inc esi
    inc edi
    dec ecx
    jmp .sigue
.fin:
    mov byte [edi], 0
    mov eax, edi
    pop edi
    pop esi
    pop ebp
    ret

str_cat:                        ; [ebp+8]=destino [ebp+12]=a [ebp+16]=b  ->  destino = a + b
    push ebp
    mov ebp, esp
    push dword 255
    push dword [ebp+12]
    push dword scratch
    call str_copy_n
    add esp, 12
    push dword 255
    push dword [ebp+16]
    push eax
    call str_copy_n
    add esp, 12
    push dword 255
    push dword scratch
    push dword [ebp+8]
    call str_copy_n
    add esp, 12
    pop ebp
    ret

str_eq:                         ; [ebp+8]=a [ebp+12]=b  ->  EAX = 1 si son iguales
    push ebp
    mov ebp, esp
    push esi
    push edi
    mov esi, [ebp+8]
    mov edi, [ebp+12]
.cmp:
    mov al, [esi]
    cmp al, [edi]
    jne .no
    test al, al
    jz .si
    inc esi
    inc edi
    jmp .cmp
.si:
    mov eax, 1
    jmp .out
.no:
    xor eax, eax
.out:
    pop edi
    pop esi
    pop ebp
    ret

fmt_int:                        ; [ebp+8]=destino [ebp+12]=entero  ->  escribe su texto en destino
    push ebp
    mov ebp, esp
    push ebx
    push esi
    mov eax, [ebp+12]
    xor esi, esi
    test eax, eax
    jns .abs
    neg eax
    mov esi, 1
.abs:
    mov ebx, 10
    mov ecx, decbuf+23
.dig:
    xor edx, edx
    div ebx
    add dl, '0'
    dec ecx
    mov [ecx], dl
    test eax, eax
    jnz .dig
    test esi, esi
    jz .copia
    dec ecx
    mov byte [ecx], '-'
.copia:
    push dword 255
    push ecx
    push dword [ebp+8]
    call str_copy_n
    add esp, 12
    pop esi
    pop ebx
    pop ebp
    ret

fmt_dec:                        ; [ebp+8]=destino [ebp+12]=centavos  ->  escribe "[-]ent.dd" en destino
    push ebp
    mov ebp, esp
    push ebx
    push esi
    push edi
    mov eax, [ebp+12]
    xor esi, esi
    test eax, eax
    jns .abs
    neg eax
    mov esi, 1
.abs:
    mov ebx, 100
    xor edx, edx
    div ebx                     ; eax = parte entera, edx = centavos
    mov edi, eax
    mov ecx, decbuf+23
    mov eax, edx
    mov ebx, 10
    xor edx, edx
    div ebx                     ; eax = decenas, edx = unidades
    add dl, '0'
    dec ecx
    mov [ecx], dl
    add al, '0'
    dec ecx
    mov [ecx], al
    dec ecx
    mov byte [ecx], '.'
    mov eax, edi
.ent:
    xor edx, edx
    div ebx
    add dl, '0'
    dec ecx
    mov [ecx], dl
    test eax, eax
    jnz .ent
    test esi, esi
    jz .copia
    dec ecx
    mov byte [ecx], '-'
.copia:
    push dword 255
    push ecx
    push dword [ebp+8]
    call str_copy_n
    add esp, 12
    pop edi
    pop esi
    pop ebx
    pop ebp
    ret

mul_dec:                        ; [ebp+8]*[ebp+12] en centavos, redondeado al centavo -> EAX
    push ebp
    mov ebp, esp
    push ebx
    push esi
    xor esi, esi                ; esi = 1 si el resultado es negativo
    mov eax, [ebp+8]
    test eax, eax
    jns .a
    neg eax
    xor esi, 1
.a:
    mov ecx, [ebp+12]
    test ecx, ecx
    jns .b
    neg ecx
    xor esi, 1
.b:
    mul ecx                     ; edx:eax = |a| * |b|   (centavos al cuadrado)
    add eax, 50                 ; redondeo
    adc edx, 0
    mov ebx, 100
    div ebx
    test esi, esi
    jz .fin
    neg eax
.fin:
    pop esi
    pop ebx
    pop ebp
    ret

div_dec:                        ; [ebp+8] / [ebp+12] en centavos, redondeado al centavo -> EAX
    push ebp
    mov ebp, esp
    push ebx
    push esi
    xor esi, esi
    mov ecx, [ebp+12]
    test ecx, ecx
    jz .cero
    jns .d1
    neg ecx
    xor esi, 1
.d1:
    mov eax, [ebp+8]
    test eax, eax
    jns .d2
    neg eax
    xor esi, 1
.d2:
    mov ebx, 100
    mul ebx                     ; edx:eax = |a| * 100
    mov ebx, ecx
    shr ebx, 1                  ; |b| / 2  (redondeo)
    add eax, ebx
    adc edx, 0
    div ecx
    test esi, esi
    jz .fin
    neg eax
.fin:
    pop esi
    pop ebx
    pop ebp
    ret
.cero:                          ; división entre cero: mensaje a stderr y salida con código 3
    mov eax, 4
    mov ebx, 2
    mov ecx, txt_divcero
    mov edx, txt_divcero_len
    int 0x80
    mov eax, 1
    mov ebx, 3
    int 0x80
"""


def _fusionables(quads, tipos):
    """Índices de comparaciones (enteros) que van seguidas de un SI_FALSO sobre su propio temporal,
    y ese temporal no se lee en ningún otro lado: se traducen como  cmp + salto condicional."""
    lecturas = {}
    for q in quads:
        for x in _leidos(q):
            if isinstance(x, str):
                lecturas[x] = lecturas.get(x, 0) + 1
    out = set()
    for i in range(len(quads) - 1):
        q, n = quads[i], quads[i + 1]
        if (q.op in SETCC and n.op == 'SI_FALSO' and isinstance(q.res, str) and n.arg1 == q.res
                and re.fullmatch(r"t\d+", q.res) and lecturas.get(q.res) == 1
                and 'texto' not in (_tipo(q.arg1, tipos), _tipo(q.arg2, tipos))):
            out.add(i)
    return out


def _regiones_funcion(quads):
    """[(inicio, fin)] de cada cuerpo de función: desde FUNC hasta la etiqueta del SALTA que lo rodea."""
    regiones = []
    for i, q in enumerate(quads):
        if q.op == 'FUNC':
            fin = len(quads) - 1
            if i > 0 and quads[i - 1].op == 'SALTA':
                for j in range(i, len(quads)):
                    if quads[j].op == 'LABEL' and quads[j].res == quads[i - 1].res:
                        fin = j
                        break
            regiones.append((i, fin))
    return regiones


def asignar_registros(quads, efectos, fijas_extra=()):
    """Barrido lineal con intervalos de vida. Devuelve {variable: registro}.
    efectos(i, q) -> (lee, escribe): conjuntos de nombres que el cuádruplo i lee / escribe."""
    n = len(quads)
    ocurr = {}                                           # var -> [(indice, 'r'|'w'|'rw')]
    for i, q in enumerate(quads):
        lee, esc = efectos(i, q)
        for v in lee | esc:
            ocurr.setdefault(v, []).append((i, ('r' if v in lee else '') + ('w' if v in esc else '')))
    # ciclos: saltos hacia atrás
    etiquetas = {q.res: i for i, q in enumerate(quads) if q.op == 'LABEL'}
    ciclos = [(etiquetas[q.res], j) for j, q in enumerate(quads)
              if q.op in ('SALTA', 'SI_FALSO') and q.res in etiquetas and etiquetas[q.res] <= j]
    profundidad = [sum(1 for a, b in ciclos if a <= i <= b) for i in range(n)]
    peso = {v: sum(10 ** profundidad[i] for i, _ in lst) for v, lst in ocurr.items()}
    # variables "fijas": las que toca el cuerpo de una función viven en todo el programa
    fijas = set(fijas_extra)
    for ini, fin in _regiones_funcion(quads):
        for v, lst in ocurr.items():
            if any(ini <= i <= fin for i, _ in lst):
                fijas.add(v)
    inter = {v: [lst[0][0], lst[-1][0]] for v, lst in ocurr.items()}
    for v in fijas:
        inter.setdefault(v, [0, n])
        inter[v] = [-1, n]
    cambio = True
    while cambio:                                        # extensión por ciclos (hasta punto fijo)
        cambio = False
        for a, b in ciclos:
            for v, (ini, fin) in inter.items():
                if v in fijas or fin < a or ini > b:
                    continue
                dentro = ini >= a and fin <= b
                if dentro:
                    i0, k0 = ocurr[v][0]
                    if i0 == ini and 'r' not in k0:
                        continue                         # nace dentro del ciclo y se escribe primero
                nuevo = [min(ini, a), max(fin, b)]
                if nuevo != [ini, fin]:
                    inter[v] = nuevo
                    cambio = True
    reg, activos, libres = {}, [], list(REGS)
    for v in sorted(inter, key=lambda x: (inter[x][0], x)):
        for u in list(activos):                          # los que ya terminaron liberan su registro
            if inter[u][1] <= inter[v][0]:
                activos.remove(u)
                libres.append(reg[u])
        if libres:
            reg[v] = libres.pop(0)
            activos.append(v)
        else:
            peor = min(activos + [v], key=lambda x: (peso.get(x, 0), x))
            if peor is not v:
                reg[v] = reg.pop(peor)
                activos.remove(peor)
                activos.append(v)
    return reg


def generar_asm(quads, tabla, tipos_temp, registros=True):
    tipos = _tipos(tabla, tipos_temp)
    for q in quads:
        _validar(q, tipos)

    fus = _fusionables(quads, tipos)

    def efectos(i, q):
        """Nombres que lee / escribe el cuádruplo (las comparaciones fusionadas no escriben su temporal)."""
        if i in fus:
            return {x for x in (q.arg1, q.arg2) if isinstance(x, str)}, set()
        if i > 0 and (i - 1) in fus and q.op == 'SI_FALSO':
            return set(), set()
        lee = {x for x in _leidos(q) if isinstance(x, str)}
        return lee, ({q.res} if q.op in DEFINEN else set())

    usados = set()
    for i, q in enumerate(quads):
        lee, esc = efectos(i, q)
        usados |= lee | esc
    # nombre -> (params, locales): solo se guardan/restauran los que el programa realmente usa
    funciones = {q.arg1: (q.arg2, tuple(v for v in q.res if v in usados))
                 for q in quads if q.op == 'FUNC'}

    literales, variables, buffers = {}, [], []

    def literal(texto):
        if texto not in literales:
            literales[texto] = f"s{len(literales)}"
        return literales[texto]

    for i, q in enumerate(quads):
        lee, esc = efectos(i, q)
        for x in [*_leidos(q), q.res]:                               # literales de texto
            if isinstance(x, Const) and x.tipo == 'texto':
                literal(x.valor)
        for v in sorted(lee | esc):
            if v not in variables:
                variables.append(v)
        if q.op == 'FUNC':
            for v in funciones[q.arg1][1]:
                if v not in variables:
                    variables.append(v)
        if i not in fus and (q.op in ('CONCAT', 'ENT_A_TXT', 'DEC_A_TXT')
                             or (q.op == '=' and tipos[q.res] == 'texto' and not isinstance(q.arg1, Const))):
            if q.res not in buffers:
                buffers.append(q.res)

    fijas = {v for ps, ls in funciones.values() for v in (*ps, *ls) if v in usados}
    reg = asignar_registros(quads, efectos, fijas) if registros else {}
    reg = {v: r for v, r in reg.items() if v in variables}
    en_memoria = [v for v in variables if v not in reg]

    # ---------- operandos ----------
    def src(x):                      # operando fuente: registro, memoria o inmediato
        if isinstance(x, Const):
            if x.tipo == 'texto':
                return literal(x.valor)
            if x.tipo == 'logico':
                return '1' if x.valor else '0'
            if x.tipo == 'decimal':
                return str(centavos(x.valor))
            return str(x.valor)
        return reg.get(x) or f"dword [{_etq(x)}]"

    def es_reg(o):
        return o in ('eax', 'ecx', 'edx') or o in REGS

    def es_mem(o):
        return o.startswith('dword [')

    def es_imm(o):
        return not es_reg(o) and not es_mem(o)

    def pusha(o):
        o = str(o)
        return f"push {o}" if not es_imm(o) else f"push dword {o}"

    def guarda(v, r='eax'):          # variable <- registro
        R = reg.get(v)
        if R:
            return [] if R == r else [f"mov {R}, {r}"]
        return [f"mov [{_etq(v)}], {r}"]

    def asigna(v, o):                # variable <- operando cualquiera
        R = reg.get(v)
        if R:
            return [] if o == R else [f"mov {R}, {o}"]
        if es_mem(o):
            return [f"mov eax, {o}", f"mov [{_etq(v)}], eax"]
        return [f"mov dword [{_etq(v)}], {o}"]

    def destino(v, *evitar):         # registro donde calcular v: el suyo, o EAX si choca con un operando
        R = reg.get(v)
        return 'eax' if (R is None or R in evitar) else R

    T = []

    def llama(rutina, *args):        # cdecl: se apilan de derecha a izquierda; args = operandos ya en texto
        T.extend(f"    {pusha(a)}" for a in reversed(args))
        T.append(f"    call {rutina}")
        T.append(f"    add esp, {4 * len(args)}")

    def emite(lineas):
        T.extend(f"    {l}" for l in lineas)

    def compara(a, b):               # deja las banderas de a - b
        sa, sb = src(a), src(b)
        if es_reg(sa):
            return [f"cmp {sa}, {sb}"]
        return [f"mov eax, {sa}", f"cmp eax, {sb}"]

    def tipo(x):
        return _tipo(x, tipos)

    n_log = 0
    for i, q in enumerate(quads):
        o, a, b, r = q.op, q.arg1, q.arg2, q.res
        T.append(f"    ; {q}" + ("   [fusionada con el salto siguiente]" if i in fus else ""))
        if i in fus:
            emite(compara(a, b) + [f"{CC_INV[o]} {quads[i + 1].res}"])
        elif i > 0 and (i - 1) in fus and o == 'SI_FALSO':
            pass
        elif o == 'LABEL':
            T.append(f"{r}:")
        elif o == 'SALTA':
            T.append(f"    jmp {r}")
        elif o == 'SI_FALSO':
            sa = src(a)
            if es_reg(sa):
                emite([f"test {sa}, {sa}", f"jz {r}"])
            elif es_mem(sa):
                emite([f"cmp {sa}, 0", f"je {r}"])
            else:
                emite([f"mov eax, {sa}", "test eax, eax", f"jz {r}"])
        elif o == '=':
            if tipos[r] == 'texto' and not isinstance(a, Const):     # el texto se copia al buffer propio
                llama("str_copy_n", f"b_{_etq(r)}", src(a), 255)
                emite(asigna(r, f"b_{_etq(r)}"))
            else:
                emite(asigna(r, src(a)))
        elif o == '*' and 'decimal' in (tipo(a), tipo(b)):
            llama("mul_dec", src(a), src(b))
            emite(guarda(r))
        elif o == '/':
            llama("div_dec", src(a), src(b))
            emite(guarda(r))
        elif o in INSTR:
            sa, sb = src(a), src(b)
            t = destino(r, sb)
            L = [f"mov {t}, {sa}"] if sa != t else []
            L.append(f"imul {t}, {t}, {sb}" if (o == '*' and es_imm(sb)) else f"{INSTR[o]} {t}, {sb}")
            emite(L + (guarda(r) if t == 'eax' else []))
        elif o in SETCC:
            if 'texto' in (tipo(a), tipo(b)):                         # == / != entre textos
                llama("str_eq", src(a), src(b))
                if o == '!=':
                    T.append("    xor eax, 1")
            else:
                emite(compara(a, b) + [f"{SETCC[o]} al", "movzx eax, al"])
            emite(guarda(r))
        elif o in ('NEG', 'NO'):
            t = destino(r)
            sa = src(a)
            emite(([f"mov {t}, {sa}"] if sa != t else []) + [("neg " if o == 'NEG' else "xor ") + t + ("" if o == 'NEG' else ", 1")]
                  + (guarda(r) if t == 'eax' else []))
        elif o == 'ENT_A_DEC':
            sa = src(a)
            if es_imm(sa):
                emite(asigna(r, str(int(sa) * 100)))
            else:
                t = destino(r)
                emite([f"imul {t}, {sa}, 100"] + (guarda(r) if t == 'eax' else []))
        elif o == 'DEC_A_ENT':
            # Los decimales se guardan como centavos: dividir entre 100 trunca hacia cero.
            emite([f"mov eax, {src(a)}", "cdq", "mov ecx, 100", "idiv ecx"] + guarda(r))
        elif o in ('ENT_A_TXT', 'DEC_A_TXT'):
            llama("fmt_int" if o == 'ENT_A_TXT' else "fmt_dec", f"b_{_etq(r)}", src(a))
            emite(asigna(r, f"b_{_etq(r)}"))
        elif o == 'LOG_A_TXT':
            n_log += 1
            emite([f"mov eax, {src(a)}", "test eax, eax", f"jz Lfalso{n_log}", "mov eax, txt_verdadero",
                   f"jmp Lfin{n_log}", f"Lfalso{n_log}:", "mov eax, txt_falso", f"Lfin{n_log}:"] + guarda(r))
        elif o == 'CONCAT':
            llama("str_cat", f"b_{_etq(r)}", src(a), src(b))
            emite(asigna(r, f"b_{_etq(r)}"))
        elif o == 'FUNC':
            T.append(f"f_{a}:")
        elif o == 'PARAM':
            T.append(f"    {pusha(src(a))}")
        elif o == 'RETORNAR':
            sa = src(a)
            emite(([f"mov eax, {sa}"] if sa != 'eax' else []) + ["ret"])
        elif o == 'CALL':
            params, locales = funciones[a]
            m, k = b, len(locales)
            emite([pusha(src(v)) for v in locales])                  # se guarda la activación anterior
            for j, pnom in enumerate(params):                         # argumentos -> parámetros
                if pnom in usados:
                    emite([f"mov eax, [esp+{4 * k + 4 * (m - 1 - j)}]"] + guarda(pnom))
            T.append(f"    call f_{a}")
            emite([f"pop {reg[v]}" if v in reg else f"pop dword [{_etq(v)}]" for v in reversed(locales)])
            emite([f"add esp, {4 * m}"] + guarda(r))
        else:                                                     # MOSTRAR_* / ALERTA_*
            clase, tp = o.split('_')
            if clase == 'ALERTA':
                T += ["    push dword txt_alerta", "    call print_str", "    add esp, 4"]
            if tp in ('ENT', 'DEC', 'TXT'):
                rutina = {'ENT': 'print_int', 'DEC': 'print_dec', 'TXT': 'print_str'}[tp]
                emite([pusha(src(a)), f"call {rutina}", "add esp, 4"])
            else:                                                 # LOG
                n_log += 1
                emite([f"mov eax, {src(a)}", "test eax, eax", f"jz Lfalso{n_log}", "push dword txt_verdadero",
                       f"jmp Lfin{n_log}", f"Lfalso{n_log}:", "push dword txt_falso", f"Lfin{n_log}:",
                       "call print_str", "add esp, 4"])
            T.append("    call print_nl")

    L = ["; TopScript -> x86 (NASM, 32 bits, Linux)",
         "; Ensamblar:  nasm -f elf32 programa.asm -o programa.o",
         "; Enlazar:    ld -m elf_i386 programa.o -o programa",
         "; Decimales: enteros en centavos (valor * 100)",
         "; Registros: " + (", ".join(f"{r}={v}" for v, r in sorted(reg.items(), key=lambda x: x[1])) or "(ninguno)")
         + f"   | variables en memoria: {len(en_memoria)}",
         "", "section .data",
         "nl:             db 10",
         f"txt_verdadero:  db {_bytes('verdadero')}",
         f"txt_falso:      db {_bytes('falso')}",
         f"txt_alerta:     db {_bytes('ALERTA: ')}",
         "txt_divcero:    db '[error de ejecucion] division entre cero', 10",
         "txt_divcero_len equ $ - txt_divcero"]
    for texto, nombre in literales.items():
        L.append(f"{nombre}:".ljust(16) + f"db {_bytes(texto)}")
    L += ["", "section .bss", "numbuf:         resb 12", "decbuf:         resb 24",
          "fmtbuf:         resb 24", f"scratch:        resb {2 * BUF}"]
    for v in en_memoria:
        L.append(f"{_etq(v)}:".ljust(16) + "resd 1")
    for v in buffers:
        L.append(f"b_{_etq(v)}:".ljust(16) + f"resb {BUF}")
    L += ["", "section .text", "    global _start", "", "_start:"]
    L += T
    L += ["", "    ; fin del programa", "    mov eax, 1", "    xor ebx, ebx", "    int 0x80"]
    L.append(RUNTIME)
    return "\n".join(L) + "\n"
