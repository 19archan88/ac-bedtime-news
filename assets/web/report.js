/* Bedtime News local presentation layer. No telemetry, fetch, or remote assets. */
(() => {
  'use strict';
  const config = JSON.parse(document.getElementById('report-settings').textContent);
  const markdownBytes = Uint8Array.from(atob(config.markdownBase64), c => c.charCodeAt(0));
  const markdown = new TextDecoder('utf-8').decode(markdownBytes).replace(/^\uFEFF/, '');
  const escape = value => String(value).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const renderer = new marked.Renderer();
  // Reports are data. Never execute raw Markdown HTML or active link schemes.
  renderer.html = ({text}) => escape(text);
  renderer.link = function({href, title, tokens}) {
    const text = this.parser.parseInline(tokens);
    let safe = false;
    try { safe = ['https:', 'http:'].includes(new URL(href).protocol); } catch (_) {}
    if (!safe) return text;
    return `<a href="${escape(href)}" target="_blank" rel="noopener noreferrer"${title ? ` title="${escape(title)}"` : ''}>${text}</a>`;
  };
  renderer.image = ({href, text}) => `<span class="image-reference">[图像：${escape(text || '未命名')}；${escape(href)}]</span>`;
  const holder = document.createElement('div');
  holder.innerHTML = marked.parse(markdown, {renderer, gfm:true});
  if (holder.firstElementChild?.tagName === 'H1') holder.firstElementChild.remove();
  document.getElementById('headline').textContent = config.headline;
  document.getElementById('date').textContent = config.dateLabel;
  document.getElementById('kind').textContent = config.kind;
  document.getElementById('report-id').textContent = config.reportId;
  document.getElementById('footer-version').textContent = `${config.reportId} · ${config.version}`;
  if (config.audience === 'child') {
    document.getElementById('audience-note').textContent = '留给未来的成长回忆录';
    document.getElementById('audience-badge').textContent = '成长回忆录 · 珍藏版';
  }
  const toc = document.getElementById('toc');
  const chapters = document.getElementById('chapters');
  let target = document.getElementById('opening');
  let index = 0;
  for (const node of [...holder.childNodes]) {
    if (node.nodeType === 1 && node.tagName === 'H2') {
      index++;
      const label = node.textContent.replace(/^[一二三四五六七八九十]+[、.．]\s*/, '');
      target = document.createElement('section');
      target.className = 'chapter';
      if (/今日金句/.test(label)) target.classList.add('quotes');
      if (/孩子分析|成长观察|看见孩子/.test(label)) target.classList.add('analysis');
      if (/家长复盘|父母复盘|照见父母/.test(label)) target.classList.add('reflection');
      if (/通道健康|健康信号/.test(label)) target.classList.add('signals');
      if (/姿态建议/.test(label)) target.classList.add('posture');
      if (/红旗与沉淀/.test(label)) target.classList.add('sediment');
      target.id = `section-${index}`;
      const heading = document.createElement('div');
      heading.className = 'chapter-heading';
      const number = document.createElement('span');
      number.className = 'chapter-number'; number.setAttribute('aria-hidden','true');
      number.textContent = String(index).padStart(2,'0');
      const title = document.createElement('h2'); title.textContent = label;
      heading.append(number, title); target.append(heading); chapters.append(target);
      const link = document.createElement('a'); link.href = `#${target.id}`;
      const navNumber = document.createElement('span'); navNumber.textContent = number.textContent;
      link.append(navNumber, document.createTextNode(label)); toc.append(link);
    } else target.append(node);
  }
  const introParagraphs = [...document.querySelectorAll('#opening > p')];
  if (introParagraphs.length > 1 && introParagraphs.at(-1).querySelector('strong')) {
    introParagraphs.at(-1).classList.add('reading-lead');
    introParagraphs.at(-1).dataset.label=({D:'今夜的注脚',W:'本周的注脚',M:'本月的注脚',Y:'这一年的注脚'})[config.reportId[0]] || '阅读提要';
  }
  if (introParagraphs[0]?.querySelector('br')) {
    const details=document.createElement('div');details.className='record-details';
    let line=document.createElement('span');line.className='detail-line';details.append(line);
    for(const node of [...introParagraphs[0].childNodes]){
      if(node.nodeName==='BR'){line=document.createElement('span');line.className='detail-line';details.append(line);}
      else line.append(node);
    }
    introParagraphs[0].replaceWith(details);
  }
  // Preserve all three source columns, while presenting narrative records as a timeline.
  const dialogue = [...chapters.children].find(s => /对话记录/.test(s.querySelector('h2')?.textContent));
  const table = dialogue?.querySelector('table');
  if (table && table.querySelectorAll('thead th').length === 3) {
    const key = document.createElement('div'); key.className = 'timeline-key';
    table.closest('.chapter')?.classList.add('has-timeline');
    key.textContent = [...table.querySelectorAll('thead th')].map(c => c.textContent).join(' / ');
    const timeline = document.createElement('ol'); timeline.className = 'timeline';
    for (const row of table.querySelectorAll('tbody tr')) {
      const cells = row.querySelectorAll('td');
      if (cells.length !== 3) continue;
      const item = document.createElement('li'); item.className = 'moment';
      const heading = document.createElement('div'); heading.className = 'moment-title';
      const timeMatch = cells[0].textContent.match(/^(\d{1,2}:\d{2}\s*[–—~\-至]\s*\d{1,2}:\d{2})\s*(.*)$/);
      if (timeMatch) {
        const time = document.createElement('time'); time.textContent = timeMatch[1];
        const title = document.createElement('strong'); title.textContent = timeMatch[2];
        item.append(time);heading.append(title);
      } else {
        item.classList.add('without-time');
        heading.innerHTML = cells[0].innerHTML;
      }
      const body = document.createElement('p'); body.innerHTML = cells[1].innerHTML;
      const tags = document.createElement('p'); tags.className = 'moment-tags'; tags.innerHTML = cells[2].innerHTML;
      const copy=document.createElement('div');copy.className='moment-copy';copy.append(heading,body,tags);
      item.append(copy); timeline.append(item);
    }
    table.replaceWith(key,timeline);
  }
  // Preserve the original quote/note columns only when both parts exist.
  for (const item of chapters.querySelectorAll('.quotes > ul > li')) {
    if (item.children.length === 1 && item.firstElementChild.tagName === 'P') {
      const paragraph = item.firstElementChild;
      paragraph.replaceWith(...paragraph.childNodes);
    }
    const quote = item.querySelector(':scope > strong');
    if (!quote) continue;
    const before = [...item.childNodes].slice(0, [...item.childNodes].indexOf(quote));
    if (before.some(node => node.textContent.trim())) continue;
    before.forEach(node => node.remove());
    const note = document.createElement('div'); note.className = 'quote-note';
    while (quote.nextSibling) note.append(quote.nextSibling);
    if (note.textContent.trim()) {
      item.classList.add('split-quote'); item.append(note);
    } else item.append(...note.childNodes);
  }
  // Standard Markdown headings define groups; no inference or rewritten source text.
  for (const chapter of chapters.children) {
    let subsection = chapter;
    let group = chapter;
    for (const node of [...chapter.childNodes]) {
      if (node.nodeType === 1 && node.tagName === 'H3') {
        subsection = document.createElement('section');
        subsection.className = 'subsection surface-light';
        const label = node.textContent.trim();
        if (/安全知识校准|事实校准|内容审计|新红旗|在飘红旗|紧急|重要提醒|警示/.test(label)) subsection.classList.add('is-critical');
        if (/转写|边界|说明|口径/.test(label)) subsection.classList.add('is-meta');
        chapter.insertBefore(subsection,node);
        subsection.append(node); group = subsection;
      } else if (node.nodeType === 1 && node.tagName === 'H4') {
        group = document.createElement('section'); group.className = 'topic';
        const label = node.textContent.trim();
        if (/安全|风险|红旗|校准|边界|警示/.test(label)) group.classList.add('is-key');
        subsection.append(group); group.append(node);
      } else if (group !== chapter) group.append(node);
    }
  }
  for (const list of chapters.querySelectorAll('.posture > ol')) {
    list.style.counterReset = `posture ${list.start - 1}`;
    for (const item of list.children) {
      if (item.hasAttribute('value')) item.style.counterSet = `posture ${item.value}`;
    }
  }
  const sourceLink = document.getElementById('save-markdown');
  sourceLink.href = `data:text/markdown;charset=utf-8;base64,${config.markdownBase64}`;
  sourceLink.download = config.sourceName;
  const navLinks = [...toc.querySelectorAll('a')];
  const sections = [...chapters.children];
  function updateProgress() {
    const range = document.documentElement.scrollHeight - window.innerHeight;
    document.getElementById('progress').style.width = `${range > 0 ? Math.min(100,Math.max(0,window.scrollY/range*100)) : 100}%`;
    let active = sections[0];
    for (const section of sections) if (section.getBoundingClientRect().top <= 160) active = section;
    navLinks.forEach(link => {
      const selected = link.hash === `#${active?.id}`;
      link.classList.toggle('active',selected);
      if(selected) link.setAttribute('aria-current','location'); else link.removeAttribute('aria-current');
    });
  }
  window.addEventListener('scroll', updateProgress, {passive:true}); updateProgress();
  const status = document.getElementById('export-status');
  let statusTimer;
  function notify(text, sticky=false) {
    clearTimeout(statusTimer); status.textContent = text; status.hidden=false;
    if(!sticky) statusTimer=setTimeout(()=>{status.hidden=true;},7000);
  }
  const printButton = document.getElementById('save-pdf');
  printButton.addEventListener('click', async () => {
    await document.fonts.ready;
    const title = document.title;
    document.title = config.reportId;
    notify('请在打印窗口选择“另存为 PDF”。推荐 A4、默认缩放，关闭浏览器页眉和页脚。');
    try { window.print(); } catch (error) { notify('无法打开打印窗口，请在系统浏览器打开此 HTML 后重试。'); }
    finally { document.title=title; }
  });
  const pngButton = document.getElementById('save-png');
  let previousDownloadURL;
  function download(blob,name){
    if(previousDownloadURL)URL.revokeObjectURL(previousDownloadURL);
    previousDownloadURL=URL.createObjectURL(blob);
    const link=document.createElement('a');link.href=previousDownloadURL;link.download=name;
    document.body.append(link);link.click();link.remove();
  }
  pngButton.addEventListener('click',async()=>{
    if(pngButton.disabled)return;
    pngButton.disabled=true;printButton.disabled=true;
    const originalLabel=pngButton.innerHTML;pngButton.textContent='正在生成长图…';
    notify('正在生成一张完整长图…',true);
    const stage=document.createElement('iframe');stage.className='export-stage';stage.setAttribute('aria-hidden','true');
    stage.tabIndex=-1;stage.style.width='1280px';stage.style.height='900px';stage.style.border='0';
    const markup=document.getElementById('report').cloneNode(true);
    let encoder;
    try{
      await new Promise((resolve,reject)=>{
        stage.onload=resolve;stage.onerror=()=>reject(new Error('Export viewport failed'));
        stage.srcdoc='<!doctype html><html lang="zh-CN" data-report-ready="true"><head><meta charset="utf-8"><style>'+
          document.querySelector('style').textContent+
          '.paper{width:900px!important;max-width:none;margin:0;box-shadow:none}body{margin:0;background:var(--paper)}</style></head><body>'+
          markup.outerHTML+'</body></html>';
        document.body.append(stage);
      });
      const doc=stage.contentDocument;
      await doc.fonts.ready;
      await Promise.all([...doc.images].map(img=>img.decode()));
      const clone=doc.querySelector('.paper'),width=900,scale=2;
      const height=Math.ceil(clone.getBoundingClientRect().height);
      encoder=BedtimePNG.create(width*scale,height*scale);
      // Small canvases feed consecutive rows into ONE PNG stream. No giant canvas,
      // no image splitting, no reduced quality, and no gaps at internal tile boundaries.
      const tileHeight=768;
      for(let y=0;y<height;y+=tileHeight){
        const rows=Math.min(tileHeight,height-y);
        notify('正在生成完整长图 '+Math.round(y/height*100)+'%…',true);
        const canvas=await html2canvas(clone,{scale,backgroundColor:'#fcf9f3',logging:false,
          width,height:rows,y,windowWidth:1280,windowHeight:900,scrollX:0,scrollY:0,
          allowTaint:false,useCORS:false,removeContainer:true});
        try{
          const pixels=canvas.getContext('2d').getImageData(0,0,canvas.width,canvas.height);
          await encoder.addRows(pixels.data,canvas.height);
        }finally{canvas.width=0;canvas.height=0;}
      }
      notify('正在保存完整长图…',true);
      const blob=await encoder.finish();encoder=null;
      download(blob,config.reportId+'.png');
      notify('完整长图已生成，浏览器已开始保存。');
      document.dispatchEvent(new CustomEvent('bedtime-export-complete',{detail:{format:'png',parts:1,width:width*scale,height:height*scale}}));
    }catch(error){
      console.error('PNG export failed',error);
      notify('长图生成失败，请关闭其他页面后重试，或用新版 Edge、Chrome 打开本文件。报告不会被拆分或截断。',true);
    }finally{
      if(encoder)await encoder.abort();
      stage.remove();pngButton.disabled=false;printButton.disabled=false;pngButton.innerHTML=originalLabel;
    }
  });
  document.documentElement.dataset.reportReady='true';
})();
