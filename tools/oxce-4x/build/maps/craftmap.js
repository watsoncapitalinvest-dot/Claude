// usage: node craftmap.js <name> [preview]
const {chromium}=require('playwright'); const fs=require('fs');
const name=process.argv[2], O=JSON.parse(fs.readFileSync('craftmaps.json'))[name];
(async()=>{const b=await chromium.launch({args:['--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader']});
const p=await b.newPage(); p.on('pageerror',e=>console.log('err',e.message)); await p.goto('http://127.0.0.1:8765/craftmap.html'); await p.waitForFunction('window.ready===true');
await p.evaluate(o=>window.init(o),O); const dir=`cm_${name}`; fs.mkdirSync(dir,{recursive:true});
const save=(n,u)=>fs.writeFileSync(n,Buffer.from(u.split(',')[1],'base64'));
save(`${dir}/all.png`,await p.evaluate(a=>window.renderAll(...a),[O.W,O.L]));
if(process.argv[3]!=='preview') for(let k=0;k<O.Z;k++) for(let j=0;j<O.L;j++) for(let i=0;i<O.W;i++) save(`${dir}/c_${i}_${j}_${k}.png`,await p.evaluate(a=>window.renderCell(...a),[i,j,k]));
await b.close();})();
