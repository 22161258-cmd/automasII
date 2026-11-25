# TopScript — compilador (modelo base)

Repositorio: [automasII](https://github.com/22161258-cmd/automasII).

Lenguaje de dominio específico para presupuestos personales. Este código es el **modelo base** del compilador:
ya recorre todas las fases, de texto fuente a cuádruplos y ejecución de referencia. Algunas fases están
solo como esqueleto para que las complete cada integrante (ver `TAREAS.md`).

## Cómo correrlo
```
pip install -r requirements.txt          # instala PLY
python main.py tests/execution/presupuesto_basico.top
python main.py programa.top --tokens --ast --tabla --cuadruplos --opt --notacion --costos
python main.py tests/execution/fibonacci.top --correr-asm      # ensambla y ejecuta en x86 real
python notaciones.py "ingreso - (total + 50) * 2"              # convertidor suelto
python run_tests.py                      # corre toda la suite (incluye pruebas aleatorias)
```
| Opción | Qué muestra |
|---|---|
| `--tokens` | tokens del analizador léxico |
| `--ast` | árbol anotado con tipos (incluye las conversiones implícitas) |
| `--tabla` | tabla de símbolos y de direcciones |
| `--cuadruplos` | código intermedio (con `--opt`, ya optimizado) |
| `--opt` | aplica los pases del optimizador |
| `--costos` | tabla de costos antes y después de optimizar (estáticos y de ejecución) |
| `--notacion` | cada expresión en notación infija, postfija y prefija |
| `--asm FILE` | escribe el ensamblador x86 (NASM, 32 bits, Linux) |
| `--correr-asm` | ensambla con `nasm` y `ld`, ejecuta y compara con el intérprete de referencia |

## Fases y módulos
| Fase | Módulo | Estado |
|---|---|---|
| Léxico | `lexer.py` | listo |
| Sintáctico (GLC → árbol) | `parser.py`, `ast_nodes.py` | listo (falta `para cada`) |
| Semántico (Tema 1) | `semantico.py`, `tabla_simbolos.py`, `errores.py` | base lista |
| Código intermedio (Tema 2) | `codigo_intermedio.py`, `notaciones.py` | cuádruplos de expresiones, categorías, `si`, `mientras`, **funciones (FUNC/PARAM/CALL/RETORNAR)**; conversión de notaciones |
| Optimización (Tema 3) | `optimizador.py` | 6 pases + medición de costos; faltan técnicas globales (subexpresiones comunes, etc.) |
| Código objeto (Tema 4) | `codigo_objeto.py`, `ensamblar.py` | x86 real para enteros, **decimales (centavos)**, lógicos, texto y **funciones con recursión**; **asignación de registros (EBX, ESI, EDI, EBP)** |
| Referencia | `interprete.py` | ejecuta los cuádruplos y cuenta costos |
| Pruebas | `run_tests.py`, `pruebas_unitarias.py`, `tests/` | suite fija + programas aleatorios |

Requisito extra para el ensamblador: `nasm` y `ld` (Linux, o WSL en Windows).

## Resumen del lenguaje
```
presupuesto "Octubre" {
  decimal ingreso = 5000.0;
  constante decimal IVA = 0.16;
  categoria comida limite 1000.0 {        // abre un ámbito propio
    gasto 450.50 descripcion "super";     // suma a comida.gastado
  }
  si (comida.gastado > comida.limite) { alerta("Excedido"); } sino { mostrar("OK"); }
  funcion decimal doble(decimal x) { retornar x * 2; }
}
```
- Tipos: `entero`, `decimal`, `texto`, `logico`; `entero → decimal` se convierte solo (casting implícito).
- `+` con un `texto` concatena (convierte el otro operando). `/` siempre da `decimal`.
- Atributos de categoría: `.limite`, `.gastado`, `.nombre`.
- Palabras reservadas, incluidas `y`, `o`, `no`: no se pueden usar como nombres de variable.
- Extensión de los archivos fuente: `.top`.

## Decimales y funciones en el ensamblador (novedades)
- **Decimales = enteros en centavos** (`12.34` -> `1234`). `+ - < > == ...` son las mismas instrucciones que para enteros;
  `*` y `/` usan las rutinas `mul_dec` y `div_dec` (producto de 64 bits, redondeo al centavo). Rango ±21 474 836.47.
  Las constantes con más de 2 decimales se redondean al centavo; el intérprete usa `float`, así que en cadenas largas
  de operaciones el último centavo puede diferir.
- **Funciones**: `(FUNC, nombre, (params), (locales))`, `(PARAM, v)`, `(CALL, nombre, n, t)`, `(RETORNAR, v)`.
  Quien llama guarda las variables de la función llamada (pila) y las restaura al volver; así funciona la recursión
  tanto en el intérprete como en el x86. `tests/execution/factorial_funcion.top`, `funciones.top` y `decimales.top`.
- Texto en x86: `CONCAT`, conversiones a texto y `==`/`!=` entre textos (buffers de 256 bytes).
- **Asignación de registros** (`codigo_objeto.py`, `asignar_registros`): intervalos de vida + barrido lineal sobre EBX/ESI/EDI/EBP;
  las variables que toca una función se consideran vivas en todo el programa; ciclos extienden el intervalo; si faltan
  registros se deja en memoria la de menor peso. Una comparación seguida de `SI_FALSO` se fusiona en `cmp` + salto.
  `--sin-registros` en `main.py` (o `registros=False` en `generar_asm`) deja todo en memoria para comparar. El encabezado del
  `.asm` lista qué variable quedó en qué registro.
- Pendiente: `para (cada x en presupuesto)` (el parser aún no lo tiene; `octubre.top` lo usa).
