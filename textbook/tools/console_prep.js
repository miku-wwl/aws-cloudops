// 控制台截图前的页面内脱敏 + 版面统一（只读，不修改任何 AWS 资源）。
//
// 用法：每次整页加载后，把下面这段粘贴到浏览器开发者工具的 Console（或自动化工具的 javascript 执行）中运行。
//   1) 把账户号 / 账户别名 / 邮箱 / IAM 用户名替换成 AWS 文档示例值（覆盖文本节点、输入框、
//      shadow DOM 与同源 iframe，并每 300 ms 重扫一次，懒加载的内容也会被替换）；
//   2) 用根元素 CSS zoom 把版面统一成约 1400 px 宽，截图更清晰。
//
// 使用前：把本文件复制为 console_prep.local.js（已被 .gitignore 忽略），在副本里填入你自己的真实值。
// 真实值只留在本机，不要提交到仓库。本书统一替换为 111122223333 / cloudops-lab / ops@example.com / ops-admin。
// 需要时可以在 map 里追加访问密钥（AKIA/ASIA…）与公网 IP 的规则，例如：
//   [/\bA(KI|SI)A[A-Z0-9]{16}\b/g, 'AKIAEXAMPLEEXAMPLE1'], [/\b198\.51\.100\.7\b/g, '203.0.113.10']
(()=>{const map=[[/123456789012/g,'111122223333'],[/1234-5678-9012/g,'1111-2222-3333'],[/your-account-alias/gi,'cloudops-lab'],[/you@example\.com/gi,'ops@example.com'],[/your-iam-user/g,'ops-admin']];const fix=n=>{let v=n.nodeValue,o=v;for(const[a,b]of map)v=v.replace(a,b);if(v!==o)n.nodeValue=v;};const scan=root=>{if(!root)return;const w=document.createTreeWalker(root,5);let n=w.currentNode;while(n){if(n.nodeType===3)fix(n);else if(n.nodeType===1){if(n.shadowRoot)scan(n.shadowRoot);if(n.tagName==='IFRAME'){try{const d=n.contentDocument;if(d&&d.body)scan(d.body);}catch(e){}}if((n.tagName==='INPUT'||n.tagName==='TEXTAREA')&&n.value){let v=n.value,o=v;for(const[a,b]of map)v=v.replace(a,b);if(v!==o)n.value=v;}}n=w.nextNode();}};window.__scan=scan;scan(document.body);if(!window.__scanT)window.__scanT=setInterval(()=>scan(document.body),300);document.documentElement.style.zoom=(innerWidth/1400).toFixed(3);return 'prepped';})()
