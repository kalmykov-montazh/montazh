// Лічильник натискань на кнопки (дзвінок, Telegram, соцмережі, маршрут, поділитися). Без cookies
(function(){
  try{
    var q=new URLSearchParams(location.search), s=q.get('src')||q.get('utm_source')||'', r=document.referrer||'';
    var own=r.indexOf('obmen-gagarina.site')>-1;
    if(!own||!sessionStorage.getItem('og_src')) sessionStorage.setItem('og_src', JSON.stringify({r:own?'':r, s:s}));
  }catch(e){}
  function send(kind){
    try{
      var o=JSON.parse(sessionStorage.getItem('og_src')||'{}');
      var d=JSON.stringify({p:'/click/'+kind, r:o.r||'', s:o.s||''});
      if(navigator.sendBeacon) navigator.sendBeacon('/hit.php', new Blob([d],{type:'application/json'}));
      else fetch('/hit.php',{method:'POST',body:d,keepalive:true});
    }catch(e){}
  }
  window.ogTrack=send;
  document.addEventListener('click', function(e){
    var a=e.target.closest&&e.target.closest('a,button'); if(!a) return;
    var h=a.getAttribute('href')||'', k='';
    if(h.indexOf('tel:')===0) k='tel';
    else if(a.classList.contains('bb-call')) k='call-btn';
    else if(a.id==='share-btn') k='share';
    else if(/t\.me\//.test(h)) k='telegram';
    else if(/instagram\.com/.test(h)) k='instagram';
    else if(/facebook\.com/.test(h)) k='facebook';
    else if(/google\.com\/maps/.test(h)) k='route';
    if(k) send(k);
  }, true);
})();
