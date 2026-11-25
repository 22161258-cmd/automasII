"""TopScript - compilador (CLI).   Uso:  python main.py programa.top [opciones]"""
import argparse
import sys

from errores import ERRORES
from parser import analizar_sintaxis
from lexer import construir_lexer
from semantico import Semantico
from codigo_intermedio import GeneradorCI, formatear
from optimizador import optimizar, optimizar_con_informe, informe_costos
from interprete import Interprete, ErrorEjecucion
from codigo_objeto import generar_asm
from ensamblar import ensamblar_y_correr, texto_esperado, HerramientasNoDisponibles
from ast_nodes import volcar
from notaciones import informe_notaciones


class Resultado:
    prog = tabla = quads = quads_opt = tipos_temp = None
    ok = False
    pendiente = None      # mensaje si alguna fase aún no está implementada


def compilar(texto, usar_opt=False):
    """Ejecuta las fases en orden. Si alguna reporta errores, se detiene."""
    ERRORES.limpiar()
    r = Resultado()
    r.prog = analizar_sintaxis(texto)                  # léxico + sintáctico
    if ERRORES.hay() or r.prog is None:
        return r
    r.tabla = Semantico(ERRORES).analizar(r.prog)       # Tema 1
    if ERRORES.hay():
        return r
    try:
        gen = GeneradorCI()                             # Tema 2
        r.quads, r.tipos_temp = gen.generar(r.prog), gen.tipos_temp
        r.quads_opt = optimizar(r.quads) if usar_opt else r.quads   # Tema 3
        r.ok = True
    except NotImplementedError as e:                    # fase pendiente del equipo
        r.pendiente = str(e)
    return r


def main():
    ap = argparse.ArgumentParser(description="Compilador TopScript")
    ap.add_argument("archivo")
    ap.add_argument("--tokens", action="store_true", help="muestra los tokens")
    ap.add_argument("--ast", action="store_true", help="muestra el árbol anotado")
    ap.add_argument("--tabla", action="store_true", help="muestra la tabla de símbolos y direcciones")
    ap.add_argument("--cuadruplos", action="store_true", help="muestra el código intermedio")
    ap.add_argument("--notacion", action="store_true", help="muestra las expresiones en notación infija, postfija y prefija")
    ap.add_argument("--opt", action="store_true", help="aplica optimizaciones")
    ap.add_argument("--costos", action="store_true", help="compara costos antes y después de optimizar")
    ap.add_argument("--asm", metavar="SALIDA.asm", help="genera el archivo ensamblador")
    ap.add_argument("--correr-asm", action="store_true", help="ensambla (nasm+ld), ejecuta y compara con el intérprete")
    ap.add_argument("--sin-registros", action="store_true", help="el ensamblador deja todas las variables en memoria (sin asignación de registros)")
    ap.add_argument("--no-ejecutar", action="store_true", help="no ejecuta con el intérprete de referencia")
    a = ap.parse_args()

    texto = open(a.archivo, encoding="utf-8").read()
    if a.tokens:
        lx = construir_lexer()
        lx.input(texto)
        for tok in lx:
            print(f"{tok.lineno:>3}  {tok.type:<12} {tok.value!r}")
        print()

    try:
        r = compilar(texto, a.opt)
        if ERRORES.hay():
            print(ERRORES.reporte())
            print(f"\nCompilación fallida: {len(ERRORES.lista)} error(es).")
            return 1
        if a.ast:
            print("\n".join(volcar(r.prog)) + "\n")
        if a.tabla:
            print(r.tabla.como_texto() + "\n")
        if a.notacion:
            print(informe_notaciones(r.prog) + "\n")
        if r.pendiente:
            print(f"[pendiente] {r.pendiente}")
            return 2
        if a.cuadruplos:
            print(formatear(r.quads_opt))
            if a.opt:
                print(f"\nInstrucciones: {len(r.quads)} -> {len(r.quads_opt)}")
            print()
        if a.costos:
            opt, informe = optimizar_con_informe(r.quads)
            print(informe_costos(r.quads, opt))
            print("\nInstrucciones eliminadas por pase: " + ", ".join(f"{k}: {v}" for k, v in informe.items()) + "\n")
        if a.asm:
            open(a.asm, "w", encoding="utf-8").write(generar_asm(r.quads_opt, r.tabla, r.tipos_temp, registros=not a.sin_registros))
            print(f"Ensamblador escrito en {a.asm}")
        if a.correr_asm:
            esperado = texto_esperado(Interprete(r.quads_opt).ejecutar())
            obtenido = ensamblar_y_correr(generar_asm(r.quads_opt, r.tabla, r.tipos_temp, registros=not a.sin_registros))
            print(obtenido, end="")
            print(f"\n[asm] salida idéntica a la del intérprete de referencia: {'sí' if obtenido == esperado else 'NO  <-- ERROR'}")
            return 0 if obtenido == esperado else 1
        if not a.no_ejecutar:
            print("\n".join(Interprete(r.quads_opt).ejecutar()))
        return 0
    except NotImplementedError as e:
        print(f"[pendiente] {e}")
        return 2
    except HerramientasNoDisponibles as e:
        print(f"[asm] {e}")
        return 4
    except ErrorEjecucion as e:
        print(f"[error de ejecución] {e}")
        return 3


if __name__ == "__main__":
    sys.exit(main())
