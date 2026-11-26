/** Apply the author's three PDF comments to existing native slide objects. */
export function reviseScenarioBoardsV2(p, root) {
  if(p.slides.items.length!==3)throw Error('Expected the reviewed three-slide deck');
  const titles=['Один молодой взрослый дома','Пара: вместе или по очереди','Семья: разные действия в одной комнате'];
  for(let i=0;i<3;i++) {
    if(String(p.slides.items[i].shapes.getItem('title').text)!==titles[i])throw Error('Reviewed deck changed');
    for(const name of ['eyebrow','footer','page-number'])if(!p.slides.items[i].shapes.getItem(name))throw Error('Expected service label: '+name);
  }
  let removed=0;
  for(const slide of p.slides.items) {
    for(const name of ['eyebrow','footer','page-number']) {slide.shapes.getItem(name).delete();removed++;}
    slide.speakerNotes.text=String(slide.speakerNotes.text)+'\n\nD-017: по комментариям автора убраны служебные надписи сверху и снизу. Ограничения и происхождение сохранены в заметках и исследовательских файлах.';
  }
  p.slides.items[2].images.items[0].replace({path:root+'/research/assets/scenarios-2026-10-30/03_family_v2.png',alt:'Семья: шесть действий; коврик в подготовке исправлен на один слой',fit:'contain'});
  return {slides:3,removedServiceLabels:removed,replacedIllustrations:1};
}
