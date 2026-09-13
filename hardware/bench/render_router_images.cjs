// Close-ups of every retained router corner, from the generated panel drawing.
const fs=require('fs'),path=require('path');
const [here,sharpPath]=process.argv.slice(2),sharp=require(sharpPath);
(async()=>{
  const manifest=JSON.parse(fs.readFileSync(path.join(here,'panel-manifest.json'),'utf8'));
  const source=fs.readFileSync(path.join(here,'panel-mechanical.svg'),'utf8');
  const out=path.join(here,'router-images');fs.mkdirSync(out,{recursive:true});
  const records=[];let i=0;
  for(const opening of manifest.router.openings) for(const patch of opening.retained_patches){
    const [x0,y0,x1,y1]=patch.bounds_mm,cx=(x0+x1)/2,cy=(y0+y1)/2;
    const name=`corner-${String(++i).padStart(2,'0')}`;
    const svg=source.replace(/width="151mm" height="139mm" viewBox="0 0 151 139"/,
      `width="700" height="700" viewBox="${cx-2} ${cy-2} 4 4"`);
    fs.writeFileSync(path.join(out,name+'.svg'),svg);
    await sharp(Buffer.from(svg)).png().toFile(path.join(out,name+'.png'));
    records.push({name,opening:opening.index,centre_mm:[cx,cy]});
  }
  fs.writeFileSync(path.join(out,'index.html'),`<!doctype html><meta charset="utf-8"><title>Router corner review</title><style>body{font:16px sans-serif}main{display:grid;grid-template-columns:repeat(4,1fr)}img{width:100%}article{padding:10px}</style><h1>2 mm cutter / 1 mm radius</h1><p>Panel SHA256: ${manifest.panel_sha256}</p><p>All ${records.length} retained corner patches; 4 × 4 mm views. Pale green is retained material; white is routed away. Factory CAM approval remains pending.</p><main>${records.map(r=>`<article><h2>${r.name}, opening ${r.opening}</h2><a href="${r.name}.png?rev=${manifest.panel_sha256}"><img src="${r.name}.png?rev=${manifest.panel_sha256}"></a></article>`).join('')}</main>`);
  fs.writeFileSync(path.join(out,'sources.json'),JSON.stringify({panel_sha256:manifest.panel_sha256,records},null,2));
  console.log('Rendered',records.length,'router corner patches');
})().catch(e=>{console.error(e);process.exit(1)});
