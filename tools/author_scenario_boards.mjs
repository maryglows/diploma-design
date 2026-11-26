/** Author the same A3 layout in Artifact Session with editable native captions. */
export async function authorScenarioBoards(p, fs, root) {
  if (p.slides.items.length !== 0) throw new Error('Use a new empty presentation for these boards');
  const data=JSON.parse(await fs.readFile(root+'/.codex-build/scenarios-2026-10-30/layout.json','utf8'));
  const source=JSON.parse(await fs.readFile(root+'/research/scenarios-2026-10-30.json','utf8'));
  const px=96/25.4;
  for(const [index,page] of data.pages.entries()) {
    const slide=p.slides.add({width:420*px,height:297*px,background:{fill:'#FFFFFF'}});
    slide.background.fill='#FFFFFF';
    for(const el of page.elements) {
      const position={left:el.x*px,top:el.y*px,width:el.w*px,height:el.h*px};
      if(el.kind==='image') {
        slide.images.add({blob:new Uint8Array(await fs.readFile(root+'/'+el.path)),contentType:'image/png',fit:'contain',alt:page.title+' / шесть иллюстрированных действий',position});
      } else if(el.kind==='rect') {
        slide.shapes.add({geometry:'rect',name:'caption-background',position,fill:el.fill,line:{fill:'none',width:0}});
      } else {
        const sh=slide.shapes.add({geometry:'textbox',name:el.name,position,fill:'none',line:{fill:'none',width:0}});
        sh.text=el.value;
        sh.text.style={typeface:'Arial',fontSize:el.size*96/72,bold:el.bold,color:el.color,insets:0,autoFit:'none',verticalAlignment:'top',wrap:'none'};
      }
    }
    slide.speakerNotes.text=[
      'DIP-010. Поручение автора: три А3 с одним человеком, парой и семьёй.',
      'Выбор автора: обычная квартира, существующий инвентарь, цветные рисунки. Будущее изделие не изображено.',
      'Проектная гипотеза, не данные интервью/наблюдений. Изображения созданы встроенным image_gen. Оригиналы и полные промпты: research/scenario-image-prompts-2026-10-30.json.',
      'Основание: meetings/raw/teacher-discussion-02.md 08:11–09:55,10:24–10:58; разбор meetings/reviews/teacher-discussion-02-review.md.',
      'Движения рассматриваются по ранее проверенным источникам: research/age-group-sources.md; тексты детей, молодёжи и пожилых от 30.10.2026. Дозировки не назначаются.',
      'Размеры комнаты, соответствие траекторий и одновременность не проверены. Это сценарный этап, не масштабная схема DIP-004.',
      JSON.stringify(source.pages[index].notes)
    ].join('\n\n');
  }
  return {slides:p.slides.items.length,nativeTextBlocks:data.pages.map(p=>p.elements.filter(e=>e.kind==='text').length)};
}
