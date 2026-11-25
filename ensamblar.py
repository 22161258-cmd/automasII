"""Ensambla, enlaza y ejecuta un programa .asm (requiere nasm y ld; Linux o WSL)."""
import os
import shutil
import subprocess
import tempfile


class HerramientasNoDisponibles(RuntimeError):
    pass


def herramientas_disponibles():
    return shutil.which('nasm') is not None and shutil.which('ld') is not None


def texto_esperado(lineas):
    """Lo que imprime el programa ensamblado para las líneas que da el intérprete de referencia."""
    return "".join(l + "\n" for l in lineas)


def ensamblar_y_correr(asm_texto, timeout=10):
    """Devuelve la salida estándar (texto) del programa ensamblado."""
    if not herramientas_disponibles():
        raise HerramientasNoDisponibles("se necesitan 'nasm' y 'ld' (en Windows, úsalos desde WSL)")
    with tempfile.TemporaryDirectory() as d:
        asm, obj, exe = (os.path.join(d, n) for n in ('p.asm', 'p.o', 'p'))
        with open(asm, 'w', encoding='utf-8') as f:
            f.write(asm_texto)
        for cmd in (['nasm', '-f', 'elf32', asm, '-o', obj], ['ld', '-m', 'elf_i386', obj, '-o', exe]):
            r = subprocess.run(cmd, capture_output=True, text=True)
            if r.returncode != 0:
                raise RuntimeError(f"falló {cmd[0]}:\n{r.stderr}")
        r = subprocess.run([exe], capture_output=True, timeout=timeout)
        return r.stdout.decode('utf-8')
