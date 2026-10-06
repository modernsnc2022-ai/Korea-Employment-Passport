(()=>{
  const raw=String(new URLSearchParams(location.search).get('src')||'').trim().toLowerCase();
  if(!/^[a-z0-9_]{1,64}$/.test(raw))return;
  document.querySelectorAll('a[href="beta.html"]').forEach(link=>{
    link.href='beta.html?src='+encodeURIComponent(raw);
  });
})();
