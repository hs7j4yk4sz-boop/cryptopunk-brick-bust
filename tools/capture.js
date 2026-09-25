const {chromium}=require('playwright'); const fs=require('fs');
(async()=>{
const OUT=process.env.OUT||'';
 const mode=process.argv[2]; const a=+process.argv[3]||0, b=+process.argv[4]||0;
 const br=await chromium.launch({args:['--use-angle=swiftshader','--enable-unsafe-swiftshader','--ignore-gpu-blocklist']});
 const p=await br.newPage({viewport:{width:1080,height:1080}});
 p.on('console',m=>console.log('LOG',m.text())); p.on('pageerror',e=>console.log('ERR',e.message));
 await p.goto('http://localhost:8765/'+(process.env.HTML||'render.html')+''); await p.waitForFunction('window.READY',null,{timeout:120000});
 const save=(f,u)=>fs.writeFileSync(f,Buffer.from(u.split(',')[1],'base64'));
 if(mode==='test'){ for(const t of process.argv.slice(3)) save(OUT+`test_${t}.jpg`,await p.evaluate(t=>renderFrame(+t),t)); }
 if(mode==='pages'){ fs.mkdirSync(OUT+'pages',{recursive:true}); const n=await p.evaluate('NPAGES'); for(let i=0;i<n;i++) save(OUT+`pages/p${String(i).padStart(2,'0')}.png`,await p.evaluate(i=>pageURL(i),i)); console.log('pages',n);}
 if(mode==='frames'){ fs.mkdirSync(OUT+'frames',{recursive:true}); for(let f=a;f<b;f++){ save(OUT+`frames/f${String(f).padStart(5,'0')}.jpg`,await p.evaluate(t=>renderFrame(t),f/30)); } }
 if(mode==='dur') console.log(await p.evaluate('DURATION'));
 await br.close();
})();
