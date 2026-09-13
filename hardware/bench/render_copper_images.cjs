// Render KiCad's actual saved copper plots; do not change or refill source boards.
const fs = require('fs');
const path = require('path');
const [out, sharpPath] = process.argv.slice(2);
const sharp = require(sharpPath);
const entries = JSON.parse(fs.readFileSync(path.join(out, 'sources.json'), 'utf8').replace(/^\uFEFF/, ''));
(async () => {
  for (const item of entries) {
    const source = path.join(out, `${item.stem}.svg`);
    const image = sharp(source, { density: 1200, limitInputPixels: false });
    await image.resize(6000, 6000, {fit: 'inside'}).flatten({background:'#ffffff'}).png().toFile(path.join(out, `${item.stem}.png`));
    await sharp(path.join(out, `${item.stem}.png`)).resize(900, 900, {fit:'inside'}).png().toFile(path.join(out, `${item.stem}-preview.png`));
  }
  for (const [name, source, x, y, w, h] of [
    ['Main-U16-pad-via', path.join(out,'Main-F.Cu.svg'),11.5,84.8,9.5,8.5],
    ['Main-encoder-MOSI', path.join(out,'Main-B.Cu.svg'),19.6,30.8,3.8,4.7],
    ['Wheel-ADC2-MISO', path.join(out,'Wheel-F.Cu.svg'),36.2,5.9,3.3,3.6],
    ['Main-U6-coil-via', path.join(out,'Main-F.Cu.svg'),63.35,44.5,2.1,1.5],
    ['Main-pictured-corner', path.join(out,'Main-F.Cu.svg'),49.55,65.25,3.1,3.1],
    ['Panel-relocated-tabs',path.join(out,'../panel-mechanical.svg'),81,69,24,19]]) {
    let svg=fs.readFileSync(source,'utf8').replace(/width="[\d.]+mm" height="[\d.]+mm" viewBox="[^"]+"/,
      `width="1200" height="1200" viewBox="${x} ${y} ${w} ${h}"`);
    fs.writeFileSync(path.join(out,name+'.svg'),svg);
    await sharp(Buffer.from(svg)).flatten({background:'#ffffff'}).png().toFile(path.join(out,name+'.png'));
  }
  const cards = entries.map(e => `<article><h2>${e.board} — ${e.layer}</h2><p>Source <code>${e.sha256.slice(0,16)}</code></p><a href="${e.stem}.png?rev=${e.sha256}"><img src="${e.stem}-preview.png?rev=${e.sha256}" alt="${e.board} ${e.layer} copper"></a><p><a href="${e.stem}.png?rev=${e.sha256}">Full-resolution PNG</a> · <a href="${e.stem}.svg?rev=${e.sha256}">Vector SVG</a></p></article>`).join('\n');
  fs.writeFileSync(path.join(out,'index.html'), `<!doctype html><html lang="en"><meta charset="utf-8"><title>MagMouse copper layers</title><style>body{font:16px system-ui;background:#edf1f4;color:#15212d;margin:24px}main{display:grid;grid-template-columns:repeat(4,minmax(200px,1fr));gap:16px}article{background:white;padding:16px;border:1px solid #bbc5ce}img{width:100%;height:480px;object-fit:contain}h2{font-size:18px}a{color:#155e9e}@media(max-width:1000px){main{grid-template-columns:repeat(2,1fr)}}</style><h1>MagMouse: copper layer review</h1><p>Click a preview for the full-resolution image (up to 6000 pixels), or open the SVG for unrestricted zoom.</p><p>All layers are viewed from the TOP, without mirroring, so positions line up between layers. B.Cu is a through-board view, not an underside photograph. Plots include saved filled zones, tracks, pads, actual drill openings and Edge.Cuts; they exclude solder mask and silkscreen.</p><p><strong>Panel note:</strong> this is the current working geometry, updated after the JLC submission. The Main-right and Encoder-top replacement tabs now connect across their full width to both board and frame. Images are for manual review, not replacement fabrication files.</p><p>Gallery generated ${new Date().toISOString()}. Source hashes below identify the board geometry; refresh older open image tabs.</p><p><a href="../router-images/index.html">All router corner close-ups</a></p><p>Detail views: <a href="Main-U16-pad-via.png?rev=${entries.find(e=>e.board==='Main').sha256}">U16 pad and via entries</a> · <a href="Main-encoder-MOSI.png?rev=${entries.find(e=>e.board==='Main').sha256}">Main B.Cu repair</a> · <a href="Wheel-ADC2-MISO.png?rev=${entries.find(e=>e.board==='Wheel').sha256}">Wheel MISO simplification</a> · <a href="Main-U6-coil-via.png?rev=${entries.find(e=>e.board==='Main').sha256}">U6 coil via entry</a> · <a href="Main-pictured-corner.png?rev=${entries.find(e=>e.board==='Main').sha256}">repaired pictured corner</a> · <a href="Panel-relocated-tabs.png?rev=${entries.find(e=>e.board==='Panel').sha256}">both relocated tabs</a>.</p><p>Source identities: <a href="sources.json">SHA-256 manifest</a>. No source board was edited or refilled by this export.</p><main>${cards}</main></html>`);
  console.log(`Rendered ${entries.length} copper layers into ${out}`);
})().catch(err => { console.error(err); process.exit(1); });
