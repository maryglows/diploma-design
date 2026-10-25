/** Build 3 A3 age-group boards from one JSON, preserving all earlier versions.
 * Arguments: --runtime-modules PATH --skill-dir PATH --python-executable PATH
 * Optional: --stem Age_group_boards_YYYY-MM-DD_v2
 */
import fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath,pathToFileURL} from 'node:url';
import {createRequire} from 'node:module';
import {spawnSync} from 'node:child_process';
const args=Object.fromEntries(process.argv.slice(2).reduce((a,v,i,all)=>{if(i%2===0)a.push([v.replace(/^--/,''),all[i+1]]);return a;},[]));
for(const key of ['runtime-modules','skill-dir','python-executable'])if(!args[key])throw new Error('Missing --'+key);
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const build=path.join(root,'.codex-build','groups-2026-10-24');
const out=path.join(root,'outputs/current');
const stem=args.stem??'Age_group_boards_2026-10-24_v3';
if(!/^[A-Za-z0-9_-]+$/.test(stem))throw new Error('Invalid stem');
const data=JSON.parse(await fs.readFile(path.join(root,'research/age-group-boards.json'),'utf8'));
const sourceMarkdown=await fs.readFile(path.join(root,'research/age-group-sources.md'),'utf8');
const sourceUrls=new Map([...sourceMarkdown.matchAll(/\*\*(G-\d+)\.\*\*([\s\S]*?)(?=\n\*\*G-|\n##|$)/g)].map(m=>[m[1],[...m[2].matchAll(/https?:\/\/[^\s)]+/g)].map(u=>u[0])]));
const files=[`${stem}.pptx`,`${stem}.pdf`,...data.boards.map(b=>`${stem}_${b.id}.pdf`)];
for(const file of files){try{await fs.access(path.join(out,file));throw new Error('Refusing to overwrite '+file);}catch(e){if(e.code!=='ENOENT')throw e;}}
await fs.mkdir(build,{recursive:true});
process.env.RUNTIME_NODE_MODULES=path.resolve(args['runtime-modules']);
const rr=createRequire(path.join(args['runtime-modules'],'_resolver.cjs'));
const {Presentation,PresentationFile,FileBlob}=await import(pathToFileURL(rr.resolve('@oai/artifact-tool')).href);
const {finalizePresentation}=await import(pathToFileURL(path.join(args['skill-dir'],'container_tools/artifact_tool_utils.mjs')).href);
const width=420/25.4*96,height=297/25.4*96;
const p=Presentation.create({slideSize:{width,height}});
const C={paper:'#F5F4EF',ink:'#24343A',teal:'#177D79',muted:'#65787E',pale:'#DFE7E3'};
const pdfCandidates=[];
for(let number=0;number<data.boards.length;number++){
  const board=data.boards[number],slide=p.slides.add(),elements=[];
  slide.background.fill=C.paper;
  function text(name,value,x,y,w,h,size=19,bold=false,color=C.ink){
    const shape=slide.shapes.add({geometry:'textbox',name,position:{left:x,top:y,width:w,height:h},fill:'none',line:{fill:'none',width:0}});
    shape.text=value;
    shape.text.style={typeface:'Arial',fontSize:size,bold,color,insets:0,autoFit:'none',verticalAlignment:'top',wrap:'square'};
    elements.push({kind:'text',name,value,x,y,w,h,size,bold,color});
  }
  text('project-label','ДИПЛОМ / ИССЛЕДОВАНИЕ ПОЛЬЗОВАТЕЛЕЙ',48,24,1450,24,17,true,C.teal);
  text('board-title',String(number+1).padStart(2,'0')+'  '+board.title,48,62,1490,62,46,true);
  text('board-subtitle',board.subtitle,48,125,1490,30,22,false,C.muted);
  text('anthropometry-heading',board.anthroTitle,48,176,600,28,21,true,C.teal);
  const values=[board.anthroHeaders,...board.anthroRows];
  const table=slide.tables.add({rows:values.length,columns:3,left:48,top:216,width:590,height:values.length*31,columnWidths:[244,173,173],values});
  table.styleOptions={headerRow:false,bandedRows:false};
  table.cells.block({row:0,column:0,rowCount:values.length,columnCount:3}).assign({fill:C.paper,textStyle:{typeface:'Arial',fontSize:18,color:C.ink},margins:{top:5,bottom:4,left:8,right:8},anchor:'top'});
  table.borders.assign({fill:C.pale,width:0.7,style:'solid'});
  for(let r=0;r<values.length;r++){
    table.rows[r].height=31;
    for(let c=0;c<3;c++)if(r===0){table.getCell(r,c).fill=C.teal;table.getCell(r,c).text.style={typeface:'Arial',fontSize:17,bold:true,color:'#FFFFFF'};}
  }
  elements.push({kind:'table',values,x:48,y:216,widths:[244,173,173],heights:values.map(()=>31),size:18,headerSize:17,marginTop:5,marginBottom:4,marginLeft:8,marginRight:8});
  text('anthropometry-note',board.anthroNote,48,values.length===5?380:326,590,36,14,false,C.muted);
  text('activity-heading',board.activityTitle,696,176,844,30,23,true,C.teal);
  text('activity-summary',board.activity,696,218,844,90,20);
  text('platform-summary',board.platform,696,310,844,84,19);
  for(let index=0;index<board.exercises.length;index++){
    const e=board.exercises[index],col=index%3,row=Math.floor(index/3),x=48+col*507,y=445+row*320,w=477;
    text('exercise-'+index+'-title',e.title,x,y,w,33,23,true);
    const gap=8,photoW=(w-gap*(e.images.length-1))/e.images.length;
    for(let im=0;im<e.images.length;im++){
      const relative=path.join('research/assets/age-groups',e.images[im]);
      const absolute=path.join(root,relative),ext=path.extname(absolute).toLowerCase();
      const pos={left:x+im*(photoW+gap),top:y+43,width:photoW,height:160};
      slide.images.add({blob:new Uint8Array(await fs.readFile(absolute)),contentType:ext==='.png'?'image/png':'image/jpeg',alt:e.title+' / исходное фото '+(im+1),fit:'contain',position:pos});
      elements.push({kind:'image',path:relative,x:pos.left,y:pos.top,w:pos.width,h:pos.height});
    }
    text('exercise-'+index+'-focus',e.focus,x,y+211,w,27,18,true,C.teal);
    text('exercise-'+index+'-cue',e.cue,x,y+242,w,43,17);
    text('exercise-'+index+'-zone',e.zone,x,y+290,w,22,16,true);
  }
  // Keep source lists off the board as requested. Full provenance stays in notes
  // and research/age-group-sources.md, including the limits of clinical examples.
  text('footer',board.footer,48,1093,1490,22,13,false,C.muted);
  slide.speakerNotes.text=[
    board.title+'. '+data.date+'. '+data.ageNote,
    'Источники и изображения: research/age-group-sources.md. Идентификаторы: '+board.sources.join(', '),
    ...board.sources.map(id=>id+': '+(sourceUrls.get(id)??[]).join(' ; ')),
    'Границы возраста предложены помощником для структуры показа. Это не утверждённая аудитория продукта.',
    'Медианы роста и массы описывают выборку США 2021–2023. Они не являются минимальным/максимальным размером пользователя, допустимой нагрузкой или нормой здоровья.',
    'Все зоны пола — предложенная разметка для начального макета. Они не взяты из медицинских страниц, не измерены и не задают минимум безопасного пространства. Размер платформы и свободная зона помещения различаются.',
    ...board.exercises.map(e=>e.title+'; '+e.source+'; '+e.zone+' (гипотеза); Акцент: '+e.focus),
    board.id==='03_older_adults'?'G-10 Chair Stand включает подготовку корпуса из положения сидя. Его описание не следует переносить на любое вставание со стула. Поворот корпуса показан как подвижность, а не сила.':''
  ].filter(Boolean).join('\n\n');
  const preview=await p.export({slide,format:'png',scale:1.5});
  await fs.writeFile(path.join(build,board.id+'.png'),new Uint8Array(await preview.arrayBuffer()));
  const layoutPath=path.join(build,board.id+'.json');
  await fs.writeFile(layoutPath,JSON.stringify({width,height,C,title:board.title,elements}));
  const pdfPath=path.join(build,board.id+'.pdf');
  const pdf=spawnSync(args['python-executable'],[path.join(root,'tools/render_first_board_pdf.py'),layoutPath,pdfPath],{encoding:'utf8'});
  if(pdf.status!==0)throw new Error(pdf.stdout+'\n'+pdf.stderr);
  pdfCandidates.push(pdfPath);
}
const candidate=path.join(build,'candidate.pptx');
await(await PresentationFile.exportPptx(p)).save(candidate);
await finalizePresentation({workspaceDir:root,candidatePath:candidate,finalPath:path.join(out,stem+'.pptx'),
  explicitTotalSlideCount:3,requiredNativeTableOwnerSlides:[1,2,3],
  pythonExecutable:args['python-executable'],
  integrityValidatorPath:path.join(args['skill-dir'],'container_tools/inspect_presentation_package_integrity.py'),
  layoutValidatorPath:path.join(args['skill-dir'],'container_tools/inspect_presentation_layout_geometry.py'),
  layoutArgs:['--expected-slide-size-emu','15120000,10692000','--validate-heading-fit',...['1','2','3'].flatMap(n=>['--require-native-table-slide',n])],
  fontPolicy:{basis:'design',families:['Arial']},verifyArtifactToolImport:true,receiptPath:path.join(build,stem+'.validation.json')});
// Verify the actual exported file, with all images embedded, after finalization.
const final=await PresentationFile.importPptx(await FileBlob.load(path.join(out,stem+'.pptx')));
for(let i=0;i<3;i++){
  const b=await final.export({slide:final.slides.items[i],format:'png',scale:1.5});
  await fs.writeFile(path.join(build,'final-'+data.boards[i].id+'.png'),new Uint8Array(await b.arrayBuffer()));
  await fs.copyFile(pdfCandidates[i],path.join(out,`${stem}_${data.boards[i].id}.pdf`),fs.constants.COPYFILE_EXCL);
}
const merge=spawnSync(args['python-executable'],['-c','from pypdf import PdfWriter; import sys; w=PdfWriter(); [w.append(p) for p in sys.argv[2:]]; w.write(sys.argv[1])',path.join(out,stem+'.pdf'),...pdfCandidates],{encoding:'utf8'});
if(merge.status!==0)throw new Error(merge.stderr);
console.log(JSON.stringify({files:files.map(f=>path.join(out,f)),slides:final.slides.items.length}));
