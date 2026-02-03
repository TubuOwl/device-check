window.addEventListener("DOMContentLoaded", async () => {

  function getUser(){
    let f=document.cookie.match(/id\.chatango\.com=([^;]+)/);
    return f?f[1]:"Anon";
  }

  function canvasFP(){
    const c=document.createElement("canvas");
    const ctx=c.getContext("2d");
    ctx.fillText("fp",2,2);
    return c.toDataURL();
  }

  async function hash(str){
    const buf=new TextEncoder().encode(str);
    const h=await crypto.subtle.digest("SHA-256",buf);
    return [...new Uint8Array(h)].map(b=>b.toString(16).padStart(2,"0")).join("");
  }

  const raw=navigator.userAgent+screen.width+screen.height+canvasFP();
  const deviceID=await hash(raw);

  fetch("/api/check",{
    method:"POST",
    headers:{"Content-Type":"application/json"},
    body:JSON.stringify({
      name:getUser(),
      id:deviceID,
      ua:navigator.userAgent
    })
  });

  document.body.innerHTML="Device recorded ✔";
});
