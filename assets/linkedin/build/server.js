const http = require('http');
const fs = require('fs');
const path = require('path');
const root = path.resolve(__dirname, '..', '..', '..');
const mime = {'.html':'text/html','.jpg':'image/jpeg','.png':'image/png','.svg':'image/svg+xml','.css':'text/css'};
function handler(req,res){
  let p = decodeURIComponent(req.url.split('?')[0]);
  let fp = path.join(root, p);
  fs.readFile(fp, (err,data)=>{
    if(err){ res.writeHead(404); res.end('not found: '+fp); return; }
    const ext = path.extname(fp);
    res.writeHead(200, {'Content-Type': mime[ext]||'application/octet-stream'});
    res.end(data);
  });
}
const ports = [8935,8936,8937,8938,8939,8940,8941,8942];
ports.forEach(port=>{
  http.createServer(handler).listen(port, ()=>console.log('serving', root, 'on', port));
});
