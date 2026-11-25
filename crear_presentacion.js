const pptxgen = require('pptxgenjs');

const pptx = new pptxgen();
pptx.layout = 'LAYOUT_WIDE';
pptx.author = 'Equipo TopScript';
pptx.subject = 'Presentación del compilador TopScript';
pptx.title = 'TopScript | Compilador para presupuestos personales';
pptx.company = 'Tecnológico Nacional de México · Instituto Tecnológico de Oaxaca';
pptx.lang = 'es-MX';
pptx.theme = {
  headFontFace: 'Aptos Display', bodyFontFace: 'Aptos', lang: 'es-MX'
};
pptx.defineSlideMaster({
  title: 'BASE', background: { color: 'F5F7FA' },
  objects: [
    { line: { x: 0.55, y: 7.12, w: 12.2, h: 0, line: { color: 'D9E1EA', width: 0.8 } } },
    { text: { text: 'TOPSCRIPT  /  LENGUAJES Y AUTÓMATAS II', options: { x: 0.62, y: 7.18, w: 8, h: 0.18, fontFace: 'Aptos', fontSize: 8, color: '62748A', charSpacing: 1.2, margin: 0 } } },
    { text: { text: 'ITO · 2026', options: { x: 11.55, y: 7.16, w: 1.1, h: 0.2, align: 'right', fontFace: 'Aptos', fontSize: 8, color: '62748A', margin: 0 } } }
  ],
  slideNumber: { x: 12.78, y: 7.15, w: 0.25, h: 0.2, color: '62748A', fontFace: 'Aptos', fontSize: 8, margin: 0 }
});

const C = { navy:'10243A', blue:'1769AA', cyan:'43C6C8', ink:'172B42', muted:'5E7185', white:'FFFFFF', pale:'E8F1F8', pale2:'E5F7F6', gold:'E9B44C', red:'D9655B', green:'26877D' };
const S = pptx.ShapeType;
function txt(slide, text, x,y,w,h, opts={}) {
  slide.addText(text, {x,y,w,h,fontFace:'Aptos',fontSize:opts.size||16,color:opts.color||C.ink,margin:0,breakLine:false,fit:'shrink',valign:opts.valign||'mid',bold:opts.bold||false,italic:opts.italic||false,align:opts.align||'left',charSpacing:opts.spacing||0,bullet:opts.bullet,paraSpaceAfterPt:opts.after||0, ...opts});
}
function title(slide, kicker, heading, sub='') {
  txt(slide,kicker.toUpperCase(),0.68,0.38,10,0.25,{size:9,bold:true,color:C.blue,charSpacing:2});
  txt(slide,heading,0.68,0.76,12,0.55,{size:29,bold:true,color:C.navy});
  if(sub) txt(slide,sub,0.7,1.39,11.8,0.36,{size:13,color:C.muted});
}
function rect(slide,x,y,w,h,fill, radius=0.12,line=fill) {
  slide.addShape(S.roundRect,{x,y,w,h,rectRadius:radius,fill:{color:fill},line:{color:line,transparency:100},radius});
}
function pill(slide,label,x,y,w,color=C.blue) {
  slide.addShape(S.roundRect,{x,y,w,h:0.3,rectRadius:0.1,fill:{color},line:{color,transparency:100}});
  txt(slide,label,x+0.08,y+0.01,w-0.16,0.26,{size:9,bold:true,color:C.white,align:'center'});
}
function notes(slide, text){slide.addNotes(text);}
function arrow(slide,x1,y1,x2,y2,color='9AB0C3'){
  slide.addShape(S.line,{x:x1,y:y1,w:x2-x1,h:y2-y1,line:{color,width:1.5,beginArrowType:'none',endArrowType:'triangle'}});
}

// 1. Portada institucional
{
 const s=pptx.addSlide(); s.background={color:C.navy};
 s.addShape(S.rect,{x:0,y:0,w:0.18,h:7.5,fill:{color:C.cyan},line:{color:C.cyan}});
 s.addShape(S.ellipse,{x:9.1,y:-1.2,w:5.2,h:5.2,fill:{color:'163B5C'},line:{color:'163B5C'}});
 s.addShape(S.ellipse,{x:10.3,y:3.7,w:4.2,h:4.2,fill:{color:'12314E'},line:{color:'12314E'}});
 pill(s,'PROYECTO INTEGRADOR',0.82,0.7,2.15,C.blue);
 txt(s,'TopScript',0.82,1.52,7.4,0.9,{size:48,bold:true,color:C.white});
 txt(s,'Un compilador para expresar y procesar\npresupuestos personales',0.86,2.56,7.3,1.05,{size:24,color:'D7E6F2',breakLine:true,valign:'top'});
 s.addShape(S.line,{x:0.86,y:4.05,w:6.65,h:0,line:{color:'47617A',width:1}});
 txt(s,'TECNOLÓGICO NACIONAL DE MÉXICO',0.86,4.35,6.8,0.27,{size:12,bold:true,color:C.cyan,charSpacing:1.3});
 txt(s,'Instituto Tecnológico de Oaxaca  ·  Ingeniería en Sistemas Computacionales',0.86,4.75,7.8,0.35,{size:14,color:C.white});
 txt(s,'Lenguajes y Autómatas II  ·  Grupo 7SB',0.86,5.2,7.8,0.32,{size:12,color:'B9CADA'});
 txt(s,'Equipo',0.86,5.82,1.0,0.22,{size:10,bold:true,color:C.cyan,charSpacing:1.3});
 txt(s,'Griselda Juárez Monjaraz  ·  Jorge Núñez Reyes\nOmar Valencia Borja  ·  Gael Velásquez Cruz',0.86,6.1,7.8,0.58,{size:12,color:'D7E6F2',valign:'top',breakLine:true});
 txt(s,'OCTUBRE 2026',10.15,6.78,2.2,0.25,{size:10,bold:true,color:'B9CADA',align:'right',charSpacing:1.3});
 notes(s,'0:30. Presentar la institución, el equipo y el propósito: mostrar cómo construimos un lenguaje pequeño y su compilador para presupuestos personales. La exposición dura 20 minutos; dejar 5 minutos al final para preguntas.');
}
// 2. Introducción y problemática
{
 const s=pptx.addSlide('BASE'); title(s,'01 · Contexto','Del presupuesto cotidiano a un lenguaje ejecutable','La problemática: traducir reglas financieras escritas por una persona a acciones que una computadora pueda validar y ejecutar.');
 rect(s,0.75,2.12,5.55,3.88,C.navy);
 txt(s,'EL RETO',1.08,2.48,1.4,0.25,{size:10,bold:true,color:C.cyan,charSpacing:1.6});
 txt(s,'¿Cómo convertir instrucciones de presupuesto en un programa confiable?',1.08,2.95,4.65,1.22,{size:27,bold:true,color:C.white,valign:'top'});
 txt(s,'Un error de sintaxis, tipo o flujo puede cambiar un cálculo o esconder un gasto fuera de límite.',1.1,4.67,4.65,0.82,{size:15,color:'CFDCE7',valign:'top'});
 const items=[['01','Escribir','Reglas y operaciones en TopScript'],['02','Validar','Estructura, tipos y ámbitos'],['03','Traducir','Cuádruplos, optimización y x86']];
 items.forEach((a,i)=>{let y=2.25+i*1.23; s.addShape(S.ellipse,{x:7.0,y,w:0.58,h:0.58,fill:{color:i===2?C.cyan:C.blue},line:{color:i===2?C.cyan:C.blue}});txt(s,a[0],7.0,y+0.12,0.58,0.25,{size:12,bold:true,color:C.white,align:'center'});txt(s,a[1],7.82,y-0.01,3,0.33,{size:19,bold:true,color:C.navy});txt(s,a[2],7.82,y+0.4,4.1,0.42,{size:13,color:C.muted}); if(i<2) s.addShape(S.line,{x:7.29,y:y+0.61,w:0,h:0.55,line:{color:'B5C9D9',width:1.5}});});
 txt(s,'TopScript',7.82,6.12,2.0,0.28,{size:11,bold:true,color:C.blue});
 notes(s,'2:00. Explicar que un presupuesto contiene datos, reglas, operaciones y decisiones. El proyecto crea un lenguaje de dominio específico para describirlos; el compilador valida el programa y lo conduce por fases hasta poder interpretarlo o generar ensamblador.');
}
// 3. Objetivos y alcance
{
 const s=pptx.addSlide('BASE'); title(s,'02 · Propósito','Qué construimos y hasta dónde llega','Objetivo: implementar el recorrido de un programa TopScript desde el análisis hasta su ejecución de referencia y la generación de x86.');
 rect(s,0.78,2.0,4.05,4.55,C.blue);
 txt(s,'OBJETIVO GENERAL',1.12,2.42,3.4,0.24,{size:10,bold:true,color:'C6F3F1',charSpacing:1.5});
 txt(s,'Diseñar un compilador funcional para un lenguaje de presupuestos personales.',1.12,2.91,3.2,1.35,{size:25,bold:true,color:C.white,valign:'top'});
 txt(s,'Del texto fuente a una salida que se puede analizar, optimizar y ejecutar.',1.12,4.75,3.2,0.95,{size:15,color:'E0EBF4',valign:'top'});
 txt(s,'ALCANCE IMPLEMENTADO',5.35,2.04,5.9,0.25,{size:10,bold:true,color:C.blue,charSpacing:1.5});
 const rows=[['Lenguaje','Variables, constantes, categorías, gasto y expresiones'],['Control','Condiciones, ciclos y funciones'],['Tipos','Entero, decimal, texto y lógico; ámbitos y conversiones'],['Salida','Cuádruplos, optimización, intérprete y ensamblador x86']];
 rows.forEach((a,i)=>{const y=2.55+i*0.91;s.addShape(S.line,{x:5.35,y:y+0.7,w:6.9,h:0,line:{color:'D7E1E9',width:0.8}});txt(s,a[0],5.38,y,1.48,0.3,{size:15,bold:true,color:C.navy});txt(s,a[1],6.95,y,5.15,0.54,{size:13,color:C.muted,valign:'top'});});
 pill(s,'FUERA DEL ALCANCE ACTUAL',5.4,6.28,2.65,C.navy);
 txt(s,'La iteración “para cada” está pendiente; se usa mientras para ciclos.',8.22,6.27,4.1,0.35,{size:11,color:C.muted});
 notes(s,'1:30. Distinguir objetivo general de alcance real. Enumerar funciones soportadas y mencionar con transparencia que “para cada” sigue pendiente, por lo que el trabajo se concentra en las construcciones efectivamente implementadas.');
}
// 4. Arquitectura
{
 const s=pptx.addSlide('BASE'); title(s,'03 · Arquitectura','Un recorrido por fases con responsabilidades claras','Cada módulo recibe una representación, la valida o transforma y entrega el resultado a la siguiente fase.');
 const blocks=[['01','Fuente\nTopScript','main.py'],['02','Léxico y\nsintaxis','lexer.py · parser.py'],['03','Semántica','semantico.py\ntabla_simbolos.py'],['04','Código\nintermedio','codigo_intermedio.py'],['05','Optimización','optimizador.py'],['06','Código objeto','codigo_objeto.py\nensamblar.py']];
 const x0=0.72,gap=0.34,w=1.78,y=2.6;
 blocks.forEach((b,i)=>{const x=x0+i*(w+gap); rect(s,x,y,w,2.0,i===0||i===5?C.navy:(i===3?C.blue:C.white));const color=i===0||i===5?C.white:C.ink;txt(s,b[0],x+0.16,y+0.15,0.45,0.24,{size:10,bold:true,color:i===3?C.cyan:C.blue});txt(s,b[1],x+0.16,y+0.55,w-0.3,0.7,{size:17,bold:true,color,valign:'top'});txt(s,b[2],x+0.16,y+1.47,w-0.3,0.35,{size:9,color:i===0||i===5?'C6D5E2':C.muted,valign:'top'});if(i<blocks.length-1)arrow(s,x+w+0.04,y+1,x+w+gap-0.03,y+1,'8AA2B7');});
 rect(s,1.05,5.35,5.2,0.86,C.pale);txt(s,'Intérprete de referencia',1.32,5.52,2.3,0.25,{size:14,bold:true,color:C.navy});txt(s,'Ejecuta cuádruplos y produce salida observable.',3.52,5.49,2.42,0.4,{size:11,color:C.muted});
 rect(s,7.05,5.35,5.2,0.86,C.pale2);txt(s,'Pruebas',7.32,5.52,1.0,0.25,{size:14,bold:true,color:C.navy});txt(s,'Revisan errores y programas de ejemplo.',8.42,5.49,3.53,0.4,{size:11,color:C.muted});
 txt(s,'Representaciones: texto → tokens/AST → tabla de símbolos → cuádruplos → x86',1.05,6.48,11,0.3,{size:12,bold:true,color:C.blue,align:'center'});
 notes(s,'2:00. Guiar al público de izquierda a derecha. El intérprete de referencia ayuda a observar el comportamiento del programa; el ensamblador es una ruta de salida adicional. Las pruebas automatizadas cubren fases y ejemplos.');
}
// 5. Semántica
{
 const s=pptx.addSlide('BASE'); title(s,'04 · Fase 1','Análisis semántico: validar el significado','Después de reconocer la sintaxis, el compilador comprueba que los nombres, tipos y operaciones tengan sentido.');
 const cards=[['TIPOS','Evita mezclar valores incompatibles. Permite conversión implícita de entero a decimal.'],['ÁMBITOS','La tabla de símbolos registra declaraciones, tipos, clases y alcance. Detecta duplicados en un mismo ámbito.'],['REGLAS DEL DOMINIO','Una sentencia gasto debe pertenecer a una categoría; las categorías mantienen límite y gastado.']];
 cards.forEach((a,i)=>{let x=0.82+i*4.15;rect(s,x,2.32,3.72,2.42,C.white);s.addShape(S.rect,{x,y:2.32,w:3.72,h:0.09,fill:{color:[C.blue,C.cyan,C.gold][i]},line:{color:[C.blue,C.cyan,C.gold][i]}});txt(s,a[0],x+0.25,2.65,3.1,0.25,{size:10,bold:true,color:C.blue,charSpacing:1.4});txt(s,a[1],x+0.25,3.12,3.1,1.15,{size:15,color:C.ink,valign:'top'});});
 rect(s,1.05,5.25,11.15,0.95,C.navy);txt(s,'Ejemplo',1.35,5.53,1.1,0.22,{size:11,bold:true,color:C.cyan});txt(s,'decimal total = 500 + 125.50;',2.6,5.43,4.5,0.42,{fontFace:'Consolas',size:18,bold:true,color:C.white});txt(s,'entero → decimal',8.1,5.51,2.7,0.25,{size:13,bold:true,color:'BCE9E6',align:'right'});
 txt(s,'Si una regla falla, se informa el error antes de generar código intermedio.',1.1,6.48,10.9,0.27,{size:12,color:C.muted,align:'center'});
 notes(s,'2:00. Mostrar que el análisis semántico agrega garantías más allá de la gramática. Explicar tipos, ámbitos y regla financiera; usar la conversión entero a decimal como ejemplo y remarcar que los errores detienen fases posteriores.');
}
// 6. Código intermedio
{
 const s=pptx.addSlide('BASE'); title(s,'05 · Fase 2','Cuádruplos: una forma uniforme de representar operaciones','El árbol sintáctico se traduce a instrucciones pequeñas que simplifican optimización e implementación.');
 rect(s,0.8,2.13,5.75,3.92,C.navy);
 txt(s,'TopScript',1.12,2.47,1.5,0.25,{size:10,bold:true,color:C.cyan,charSpacing:1.5});
 txt(s,'decimal disponible = ingreso - gastos;',1.12,2.95,5.0,0.6,{fontFace:'Consolas',size:16,color:C.white});
 s.addShape(S.line,{x:1.13,y:3.78,w:4.95,h:0,line:{color:'47617A',width:1}});
 txt(s,'Descomposición',1.12,4.04,2.0,0.28,{size:12,bold:true,color:'B9CADA'});
 txt(s,'t1 = ingreso - gastos\ndisponible = t1',1.12,4.48,4.8,0.95,{fontFace:'Consolas',size:18,color:C.white,valign:'top'});
 txt(s,'CUÁDRUPLO',7.08,2.25,2,0.24,{size:10,bold:true,color:C.blue,charSpacing:1.5});
 const cols=[['Operación','-'],['Arg. 1','ingreso'],['Arg. 2','gastos'],['Resultado','t1']];
 cols.forEach((a,i)=>{const y=2.75+i*0.76;txt(s,a[0],7.1,y,1.6,0.3,{size:13,bold:true,color:C.muted});txt(s,a[1],8.95,y,3.2,0.3,{fontFace:'Consolas',size:15,bold:true,color:C.navy});s.addShape(S.line,{x:7.1,y:y+0.48,w:4.6,h:0,line:{color:'D7E1E9',width:0.8}});});
 pill(s,'TEMPORALES t<N>',7.1,6.05,1.83,C.blue);pill(s,'ETIQUETAS L<N>',9.12,6.05,1.82,C.green);
 notes(s,'2:00. Explicar los campos de un cuádruplo y cómo una expresión más grande se divide en pasos. Temporales guardan resultados intermedios; etiquetas modelan saltos y ciclos. El identificador interno evita confundir nombres de usuario con nombres generados.');
}
// 7. Optimización
{
 const s=pptx.addSlide('BASE'); title(s,'06 · Fase 3','Optimización: simplificar sin cambiar el resultado','El optimizador transforma cuádruplos antes de generar código objeto.');
 const before=[['t1 = 4 * 0',''],['t2 = ingreso + 0',''],['t3 = 3 + 5','']];
 const after=[['t1 = 0','simplificación algebraica'],['t2 = ingreso','identidad aditiva'],['t3 = 8','plegado de constantes']];
 txt(s,'ANTES',1.1,2.12,2,0.26,{size:10,bold:true,color:C.muted,charSpacing:1.4});txt(s,'DESPUÉS',7.28,2.12,2,0.26,{size:10,bold:true,color:C.blue,charSpacing:1.4});
 before.forEach((r,i)=>{const y=2.65+i*0.9;rect(s,0.98,y,4.65,0.64,C.white);txt(s,r[0],1.25,y+0.15,4.0,0.31,{fontFace:'Consolas',size:16,color:C.ink});});
 after.forEach((r,i)=>{const y=2.65+i*0.9;rect(s,7.12,y,5.05,0.64,i===2?C.pale2:C.white);txt(s,r[0],7.38,y+0.08,2.45,0.36,{fontFace:'Consolas',size:15,bold:true,color:C.navy});txt(s,r[1],9.85,y+0.1,2.02,0.34,{size:10,color:C.muted});});
 [0,1,2].forEach(i=>arrow(s,5.9,2.96+i*0.9,6.82,2.96+i*0.9,'8AA2B7'));
 rect(s,1.0,5.75,11.15,0.62,C.navy);txt(s,'También elimina código muerto e inalcanzable, copias adyacentes e invariantes de ciclo.',1.28,5.91,10.6,0.28,{size:13,bold:true,color:C.white,align:'center'});
 notes(s,'2:00. Mostrar un antes y después sencillo. Enumerar las seis técnicas disponibles: propagación y plegado de constantes, simplificación algebraica, código inalcanzable, copias adyacentes, invariantes de ciclo y código muerto. La optimización debe preservar el resultado observable.');
}
// 8. Código objeto
{
 const s=pptx.addSlide('BASE'); title(s,'07 · Fase 4','Código objeto: de los cuádruplos a x86','El generador convierte las operaciones soportadas en ensamblador NASM para Linux de 32 bits.');
 const stages=[['Cuádruplo','(+, a, b, t1)',C.navy],['Selección','instrucciones x86',C.blue],['Ensamblado','NASM + ld',C.green]];
 stages.forEach((a,i)=>{let x=0.9+i*4.18;rect(s,x,2.35,3.35,1.62,a[2]);txt(s,a[0].toUpperCase(),x+0.23,2.63,2.8,0.25,{size:10,bold:true,color:'BCE9E6',charSpacing:1.3});txt(s,a[1],x+0.23,3.13,2.9,0.44,{fontFace:i===0?'Consolas':'Aptos',size:17,bold:true,color:C.white});if(i<2)arrow(s,x+3.48,3.15,x+4.02,3.15,'8AA2B7');});
 rect(s,1.0,4.55,5.23,1.25,C.white);txt(s,'DATOS',1.3,4.82,1.0,0.24,{size:10,bold:true,color:C.blue,charSpacing:1.3});txt(s,'Enteros, decimales en centavos, texto y lógico.',2.45,4.75,3.4,0.48,{size:14,color:C.ink});
 rect(s,7.0,4.55,5.23,1.25,C.white);txt(s,'EJECUCIÓN',7.3,4.82,1.25,0.24,{size:10,bold:true,color:C.blue,charSpacing:1.3});txt(s,'El intérprete permite comparar la salida esperada.',8.75,4.7,3.08,0.58,{size:14,color:C.ink});
 txt(s,'Requisito: NASM y ld en Linux o WSL.',1.05,6.25,11.1,0.3,{size:12,bold:true,color:C.muted,align:'center'});
 notes(s,'2:00. Describir que código objeto en este proyecto significa generación de ensamblador x86. Se soportan los tipos y operaciones implementados, decimales con representación de centavos. Para ensamblar y ejecutar se requieren NASM y ld en Linux o WSL; confirmar con la profesora la plataforma aceptada.');
}
// 9. Demo
{
 const s=pptx.addSlide('BASE'); title(s,'08 · Demostración','Un programa, varias etapas visibles','Caso: un presupuesto mensual con categorías, límites y una alerta cuando el gasto excede el tope.');
 rect(s,0.82,2.12,5.05,3.9,C.navy);
 txt(s,'EJEMPLO TOPSCRIPT',1.13,2.42,3.3,0.23,{size:10,bold:true,color:C.cyan,charSpacing:1.5});
 txt(s,'categoria comida limite 1000.0 {\n  gasto 450.50 descripcion "super";\n  gasto 620.00 descripcion "cena";\n}\nsi (comida.gastado > comida.limite) {\n  alerta("Limite excedido");\n}',1.13,2.91,4.45,2.7,{fontFace:'Consolas',size:13,color:C.white,valign:'top',breakLine:true});
 txt(s,'COMANDOS',6.55,2.23,2,0.23,{size:10,bold:true,color:C.blue,charSpacing:1.4});
 const commands=[['1','python main.py demo_presentacion.top'],['2','python main.py demo_presentacion.top --tabla --cuadruplos'],['3','python main.py demo_presentacion.top --opt --costos'],['4','python main.py demo_presentacion.top --correr-asm']];
 commands.forEach((r,i)=>{const y=2.7+i*0.76;s.addShape(S.ellipse,{x:6.55,y,w:0.36,h:0.36,fill:{color:i===3?C.green:C.blue},line:{color:i===3?C.green:C.blue}});txt(s,r[0],6.55,y+0.06,0.36,0.2,{size:10,bold:true,color:C.white,align:'center'});txt(s,r[1],7.1,y-0.03,5.1,0.42,{fontFace:'Consolas',size:11,color:C.ink});});
 rect(s,6.55,5.95,5.55,0.58,C.pale2);txt(s,'Salida del caso: alerta por gasto de 1,070.50',6.8,6.1,5.05,0.28,{size:12,bold:true,color:C.green,align:'center'});
 notes(s,'4:30. Hacer una demostración breve: ejecutar el programa básico, explicar categoría y gasto, mostrar tabla de símbolos y cuádruplos, habilitar optimización/costos, y si NASM/ld están disponibles correr el ensamblador y comparar salidas. Con 450.50 + 620.00 el total es 1,070.50, por encima del límite de 1,000.00. Si no hay Linux/WSL preparado, demostrar el intérprete y la generación del .asm.');
}
// 10. Conclusiones y preguntas
{
 const s=pptx.addSlide(); s.background={color:C.navy};
 s.addShape(S.rect,{x:0,y:0,w:0.18,h:7.5,fill:{color:C.cyan},line:{color:C.cyan}});
 txt(s,'09 · CIERRE',0.82,0.65,3.0,0.26,{size:10,bold:true,color:C.cyan,charSpacing:1.8});
 txt(s,'Conclusiones y aprendizajes',0.82,1.12,10.7,0.6,{size:32,bold:true,color:C.white});
 const lessons=[['01','Un compilador es una cadena de transformaciones; cada fase prepara y valida la siguiente.'],['02','La tabla de símbolos y los tipos hacen posible detectar errores antes de ejecutar.'],['03','Los cuádruplos separan el lenguaje fuente de la optimización y del ensamblador.'],['04','Probar el resultado y comparar salidas ayuda a verificar la generación de código.']];
 lessons.forEach((a,i)=>{const y=2.1+i*0.83;txt(s,a[0],0.88,y,0.55,0.28,{size:11,bold:true,color:C.cyan});txt(s,a[1],1.62,y-0.03,9.9,0.48,{size:16,color:'E4EDF5'});});
 s.addShape(S.line,{x:0.86,y:5.75,w:11.6,h:0,line:{color:'47617A',width:1}});
 txt(s,'Gracias',0.88,6.05,3.5,0.55,{size:29,bold:true,color:C.white});
 txt(s,'Preguntas',9.25,6.12,2.9,0.36,{size:18,bold:true,color:C.cyan,align:'right'});
 txt(s,'20 min exposición  ·  5 min preguntas',0.88,6.78,6.0,0.25,{size:10,color:'B9CADA',charSpacing:0.5});
 notes(s,'1:30. Resumir aprendizajes sobre fases, semántica, representaciones intermedias y validación. Cerrar e invitar preguntas. Reservar 5 minutos para preguntas; el resto de la presentación suma 20 minutos.');
}

if (pptx._slides.length !== 10) throw new Error(`Se esperaban 10 diapositivas, hay ${pptx._slides.length}`);
pptx.writeFile({ fileName: 'TopScript_Presentacion_Profesional.pptx' });
