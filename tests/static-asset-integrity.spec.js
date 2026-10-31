const {test,expect}=require('@playwright/test');
const fs=require('fs');const path=require('path');
const root=path.resolve(__dirname,'../docs');
function files(dir){return fs.readdirSync(dir,{withFileTypes:true}).flatMap(e=>e.isDirectory()?files(path.join(dir,e.name)):[path.join(dir,e.name)]);}
test('every static HTML local asset link resolves inside the published docs tree',()=>{
 const missing=[];let checked=0;
 for(const file of files(root).filter(f=>f.endsWith('.html'))){
  const html=fs.readFileSync(file,'utf8');
  const attrs=html.matchAll(/(?:src|href)\s*=\s*['\"]([^'\"]+)['\"]/gi);
  for(const match of attrs){const raw=match[1];if(/^(?:[a-z][\w+.-]*:|\/\/|#)/i.test(raw))continue;
   const clean=decodeURIComponent(raw.split(/[?#]/)[0]);if(!clean||clean==='/')continue;
   const target=clean.startsWith('/')?path.resolve(root,'.'+clean):path.resolve(path.dirname(file),clean);
   checked++;
   if(!target.startsWith(root+path.sep)||!fs.existsSync(target))missing.push({file:path.relative(root,file),raw});
  }
 }
 expect(checked).toBeGreaterThan(100);expect(missing).toEqual([]);
});
