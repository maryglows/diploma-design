/** Build the revised first A3 board from research/board-1-content.json.
 * Requires the bundled @oai/artifact-tool and presentations skill finalizer.
 * Example PowerShell: & $runtimeNode tools/build_first_board.mjs `
 *   --runtime-modules $runtimeModules --skill-dir $presentationSkill `
 *   --python-executable $runtimePython
 * Existing output files are never overwritten. Set --stem for a new revision.
 */
import fs from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';
import { createRequire } from 'node:module';
import { spawnSync } from 'node:child_process';

const args = Object.fromEntries(process.argv.slice(2).reduce((pairs, value, index, all) => {
  if (index % 2 === 0) pairs.push([value.replace(/^--/, ''), all[index + 1]]);
  return pairs;
}, []));
for (const name of ['runtime-modules', 'skill-dir', 'python-executable']) {
  if (!args[name]) throw new Error(`Missing --${name}`);
}
const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const build = path.join(root, '.codex-build', 'board1-2026-10-24');
const stem = args.stem ?? 'Research_board_01_2026-10-24';
if (!/^[A-Za-z0-9_-]+$/.test(stem)) throw new Error('Invalid output stem');
const output = path.join(root, 'outputs', 'current');
const pptxPath = path.join(output, `${stem}.pptx`);
const pdfPath = path.join(output, `${stem}.pdf`);
for (const file of [pptxPath, pdfPath]) {
  try { await fs.access(file); throw new Error(`Refusing to overwrite ${file}`); }
  catch (error) { if (error.code !== 'ENOENT') throw error; }
}
await fs.mkdir(build, { recursive: true });
const requireRuntime = createRequire(path.join(path.resolve(args['runtime-modules']), '_resolver.cjs'));
process.env.RUNTIME_NODE_MODULES = path.resolve(args['runtime-modules']);
const { Presentation, PresentationFile } = await import(pathToFileURL(requireRuntime.resolve('@oai/artifact-tool')).href);
const { finalizePresentation } = await import(pathToFileURL(path.join(args['skill-dir'], 'container_tools', 'artifact_tool_utils.mjs')).href);
const data = JSON.parse(await fs.readFile(path.join(root, 'research', 'board-1-content.json'), 'utf8'));

// A3 landscape, CSS px at 96 DPI. Retain the original board's paper size and palette.
const width = 420 / 25.4 * 96;
const height = 297 / 25.4 * 96;
const presentation = Presentation.create({ slideSize: { width, height } });
const slide = presentation.slides.add();
const C = { paper: '#F5F4EF', ink: '#24343A', teal: '#177D79', muted: '#65787E', pale: '#DFE7E3' };
const pdfElements=[];
slide.background.fill = C.paper;
function text(name, value, x, y, w, h, size = 19, bold = false, color = C.ink) {
  const shape = slide.shapes.add({ geometry: 'textbox', name,
    position: { left:x, top:y, width:w, height:h }, fill:'none',
    line: { fill:'none', width:0 } });
  shape.text = value;
  shape.text.style = { typeface:'Arial', fontSize:size, bold, color,
    insets:0, autoFit:'none', verticalAlignment:'top', wrap:'square' };
  pdfElements.push({kind:'text',name,value,x,y,w,h,size,bold,color});
  return shape;
}
text('project-label', 'ДИПЛОМ / ПРОМЫШЛЕННЫЙ ДИЗАЙН', 48, 24, 1400, 25, 17, true, C.teal);
text('board-title', data.title, 48, 65, 1460, 62, 46, true);
text('board-subtitle', data.subtitle, 48, 128, 1488, 28, 19, false, C.muted);
text('comparison-heading', 'СРАВНЕНИЕ ПОЛЬЗОВАТЕЛЕЙ', 48, 174, 1488, 28, 20, true, C.teal);

const values = [data.tableHeaders, ...data.tableRows];
const table = slide.tables.add({ rows:5, columns:4, left:48, top:213,
  width:1491.4, height:302, columnWidths:[245, 355, 395, 496.4], values });
pdfElements.push({kind:'table',values,x:48,y:213,widths:[245,355,395,496.4],heights:[42,65,65,65,65],size:18.5});
table.styleOptions = { headerRow:false, bandedRows:false, firstColumn:false };
table.cells.block({ row:0,column:0,rowCount:5,columnCount:4 }).assign({
  fill:C.paper, textStyle:{typeface:'Arial',fontSize:18.5,color:C.ink},
  margins:{top:9,bottom:8,left:10,right:14}, anchor:'top',
});
table.borders.assign({ fill:C.pale, style:'solid', width:0.8 });
for (let row=0; row<5; row++) {
  table.rows[row].height = row===0 ? 42 : 65;
  for (let col=0; col<4; col++) {
    if (row===0) {
      table.getCell(row,col).fill=C.teal;
      table.getCell(row,col).text.style={typeface:'Arial',fontSize:18,bold:true,color:'#FFFFFF'};
    } else if (col===0) {
      table.getCell(row,col).text.style={typeface:'Arial',fontSize:18.5,bold:true,color:C.teal};
    }
  }
}
text('source-age-boundary',data.tableFootnote,48,528,1491,43,15,false,C.muted);
text('movement-heading','ПРИМЕРЫ ПОСЛЕДОВАТЕЛЬНОСТЕЙ И ВЫВОДЫ ДЛЯ ПРОЕКТА',48,583,1490,29,20,true,C.teal);
const columns=[48,565];
for (let i=0;i<data.examples.length;i++) {
  const example=data.examples[i], x=columns[i], w=480;
  text(`movement-${i}-title`,example.title,x,629,w,35,24,true);
  slide.images.add({ blob:new Uint8Array(await fs.readFile(path.join(root,example.image))),contentType:'image/jpeg',alt:example.alt,
    fit:'contain',position:{left:x,top:675,width:w,height:218} });
  pdfElements.push({kind:'image',path:example.image,x,y:675,w,h:218});
  text(`movement-${i}-caption`,example.caption,x,906,w,27,16,true);
  text(`movement-${i}-credit`,example.credit,x,937,w,30,13,false,C.muted);
  text(`movement-${i}-source-detail`,example.body,x,974,w,65,17);
}
// The third column carries the design analysis beside the actual source sequences.
let nextY=631;
for (let i=0;i<data.conclusions.length;i++) {
  const [title,body]=data.conclusions[i];
  text(`conclusion-${i}-title`,title,1097,nextY,438,32,23,true,C.teal);
  text(`conclusion-${i}-body`,body,1097,nextY+40,438,90,20);
  nextY+=128;
}
text('sequence-limits','Фотографии NHS показывают примеры движений. Применимость к конкретному человеку и к будущему изделию требует отдельной проверки.',48,1022,1490,28,15,false,C.muted);
// Add the fuller source and design distinctions in editable notes.
slide.speakerNotes.text = [
  'Исследовательский лист 1. Обновлено '+data.date+'.',
  'Описание кадров не является назначением упражнения. Дозировки и нагрузки здесь не задаются.',
  ...data.examples.flatMap(e=>[e.title,e.body,e.question,e.credit]),
  data.limit,
  'ВОЗ, S-01, Overview: физическая активность включает повседневное движение и игру. Этот контекст не определяет конструкцию изделия.',
  'Основания задания: C-01 04:17–05:39, сравнение 14:12–14:24. Личный сценарий автора: 00:10–00:37.',
  'Источники, обращение 24.10.2026:',
  ...data.sources.map(s=>`${s.id}. ${s.title}. ${s.url}`),
  'Изображения NHS сохранены целиком, без перестановки кадров и изменения пропорций. Это иллюстрации внешнего источника, не результаты собственного наблюдения.',
  'Детские M-07/M-08 не подтверждены описаниями конкретных игр в CDC. Источник поддерживает только общий контекст активности по возрасту.',
].join('\n\n');
text('footer-context',data.limit,48,1060,1490,24,15,true,C.teal);
text('footer-sources','C-01: 04:17–05:39, 14:12–14:24. S-04: CDC. S-05/06: NHS. Полные адреса: research/board-1-review.md и заметки PPTX. '+data.date,48,1091,1490,22,13,false,C.muted);

const preview=await presentation.export({slide,format:'png',scale:1.5});
await fs.writeFile(path.join(build,'board-1-preview.png'),new Uint8Array(await preview.arrayBuffer()));
await fs.writeFile(path.join(build,'pdf-layout.json'),JSON.stringify({width,height,C,elements:pdfElements}));
const renderPdf=spawnSync(args['python-executable'],[path.join(root,'tools','render_first_board_pdf.py'),path.join(build,'pdf-layout.json'),path.join(build,'candidate.pdf')],{encoding:'utf8'});
if(renderPdf.status!==0) throw new Error(renderPdf.stdout+'\n'+renderPdf.stderr);
const candidatePath=path.join(build,'candidate.pptx');
await (await PresentationFile.exportPptx(presentation)).save(candidatePath);
const result=await finalizePresentation({workspaceDir:root,candidatePath,finalPath:pptxPath,
  explicitTotalSlideCount:1,requiredNativeTableOwnerSlides:[1],
  pythonExecutable:args['python-executable'],
  integrityValidatorPath:path.join(args['skill-dir'],'container_tools','inspect_presentation_package_integrity.py'),
  layoutValidatorPath:path.join(args['skill-dir'],'container_tools','inspect_presentation_layout_geometry.py'),
  layoutArgs:['--expected-slide-size-emu','15120000,10692000','--validate-heading-fit','--require-native-table-slide','1'],
  fontPolicy:{basis:'design',families:['Arial']},verifyArtifactToolImport:true,
  receiptPath:path.join(build,`${stem}.validation.json`),
});
await fs.copyFile(path.join(build,'candidate.pdf'),pdfPath,fs.constants.COPYFILE_EXCL);
await fs.writeFile(path.join(build,'layout.json'),new Uint8Array(await (await slide.export({format:'layout'})).arrayBuffer()));
console.log(JSON.stringify({pptxPath,pdfPath,result},null,2));
