# TopScript

TopScript es un compilador académico para un lenguaje de dominio específico de presupuestos personales. Analiza programas, valida tipos y ámbitos, genera cuádruplos, aplica optimizaciones y permite ejecutarlos con un intérprete de referencia o generar ensamblador NASM x86 de 32 bits.

Repositorio: [22161258-cmd/automasII](https://github.com/22161258-cmd/automasII).

## Requisitos

- Python 3.8 o posterior.
- PLY, instalado desde `requirements.txt`.
- Para ensamblar y ejecutar código objeto: NASM y GNU `ld` en Linux o WSL. El ensamblador generado usa llamadas al sistema Linux de 32 bits; no se ejecuta de forma nativa en Windows.

## Instalación

Desde la raíz del proyecto:

```bash
python -m pip install -r requirements.txt
```

Comprueba que el compilador funciona con el ejemplo incluido:

```bash
python main.py tests/execution/presupuesto_basico.top
```

## Ejemplo mínimo

```topscript
presupuesto "Octubre" {
  decimal ingreso = 5000.00;
  categoria comida limite 1000.00 {
    gasto 450.50 descripcion "supermercado";
    gasto 620.00 descripcion "comida y cena";
  }
  si (comida.gastado > comida.limite) {
    alerta("Limite de comida excedido");
  } sino {
    mostrar("Comida dentro del limite");
  }
  mostrar("Gastado: " + comida.gastado);
  mostrar("Disponible: " + (ingreso - comida.gastado));
}
```

Guárdalo como `ejemplo.top` y ejecútalo con:

```bash
python main.py ejemplo.top
```

## Línea de comandos

```text
python main.py ARCHIVO.top [opciones]
```

| Opción | Descripción |
|---|---|
| `--tokens` | Muestra los tokens del lexer. |
| `--ast` | Muestra el árbol sintáctico con tipos y conversiones implícitas. |
| `--tabla` | Muestra la tabla de símbolos y direcciones. |
| `--cuadruplos` | Muestra el código intermedio. |
| `--notacion` | Muestra expresiones en notación infija, prefija y postfija. |
| `--opt` | Ejecuta optimizaciones antes de mostrar/ejecutar el programa. |
| `--costos` | Compara métricas de código antes y después de optimizar. |
| `--asm ARCHIVO.asm` | Escribe ensamblador x86 NASM. |
| `--correr-asm` | Ensambla, enlaza y ejecuta; compara la salida con el intérprete. |
| `--sin-registros` | Genera ensamblador sin asignación de variables a registros. |
| `--no-ejecutar` | Compila sin ejecutar el intérprete de referencia. |

Las opciones de inspección se pueden combinar. Por ejemplo:

```bash
python main.py ejemplo.top --tabla --cuadruplos --opt --costos
python main.py ejemplo.top --asm ejemplo.asm
python main.py ejemplo.top --correr-asm
```

## Pruebas

Ejecuta la suite disponible desde la raíz del proyecto:

```bash
python run_tests.py
```

Incluye pruebas unitarias y programas de ejemplo organizados por fase. Algunas pruebas de ensamblador requieren NASM, `ld` y Linux/WSL.

## Estructura del proyecto

| Archivo o carpeta | Responsabilidad |
|---|---|
| `main.py` | Interfaz de línea de comandos y coordinación de fases. |
| `lexer.py`, `parser.py`, `ast_nodes.py` | Análisis léxico, sintáctico y nodos del AST. |
| `semantico.py`, `tabla_simbolos.py`, `errores.py` | Tipos, ámbitos, símbolos y diagnósticos. |
| `codigo_intermedio.py`, `notaciones.py` | Generación de cuádruplos y notaciones de expresiones. |
| `optimizador.py` | Pases de optimización e informe de costos. |
| `interprete.py` | Intérprete de referencia de los cuádruplos. |
| `codigo_objeto.py`, `ensamblar.py` | Generación y ejecución de ensamblador x86 en Linux. |
| `pruebas_unitarias.py`, `run_tests.py`, `tests/` | Pruebas y programas de muestra. |
| `requirements.txt` | Dependencias de Python. |

## Limitaciones conocidas

| Limitación | Detalle |
|---|---|
| Iteración `para cada` | No está implementada. Se puede usar `mientras`. |
| Conversiones explícitas | El parser no tiene sintaxis como `entero(x)` o `texto(x)`. Las conversiones internas incluyen `DEC_A_ENT`, pero no se pueden solicitar desde un programa fuente con casting explícito. |
| Aritmética decimal entre intérprete y ensamblador | El intérprete usa `float`; el ensamblador representa decimales como centavos enteros y redondea multiplicación/división al centavo. En cadenas largas de operaciones puede diferir el último centavo. |
| Rango de enteros en ensamblador | Enteros con signo de 32 bits: −2³¹ a 2³¹−1. Las constantes fuera de rango se rechazan al generar ensamblador. El intérprete emula el desbordamiento de 32 bits en asignaciones y operaciones enteras. |
| Rango decimal en ensamblador | Aproximadamente ±21,474,836.47, por la representación en centavos de 32 bits. |
| Texto en ensamblador | Los buffers de conversión/concatenación admiten hasta 255 caracteres y truncan texto más largo. |
| Identificadores internos | Nombres de usuario con patrón `t<N>` o `L<N>` se renombran para evitar colisiones con temporales y etiquetas generados. |
| Palabras reservadas | Palabras del lenguaje como `limite`, `mientras`, `y` y `no` no pueden usarse como identificadores. |
| Recuperación sintáctica | El parser informa el primer error sintáctico para evitar mensajes en cascada; no continúa recuperando múltiples errores en una misma compilación. |
| Métricas de escrituras | `Memoria.escrituras` es atributo de clase; al medir varias ejecuciones en el mismo proceso las escrituras pueden acumularse. |
| Plataforma de ensamblador | La salida es NASM ELF de 32 bits para Linux y requiere `nasm` + `ld`; en Windows se debe usar WSL. |

## Formato y BOM UTF-8

Los archivos fuente usan extensión `.top` y codificación UTF-8. El lexer ignora un BOM UTF-8 inicial, por lo que también acepta archivos guardados con ese marcador en Windows.
