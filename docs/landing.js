(()=>{
  const raw=String(new URLSearchParams(location.search).get('src')||'').trim().toLowerCase();
  if(!/^[a-z0-9_]{1,64}$/.test(raw))return;
  const workerSourceCodes=new Set(['ut_korea_pmi','wongrow_pmi_korea','kbri_seoul_pmi','sbmi_korea_worker_referral','pcim_korea_referral','kp2mi_departure_worker_referral','korea_indonesia_center_referral']);
  if(workerSourceCodes.has(raw)){
    location.replace('beta.html?src='+encodeURIComponent(raw)+'#worker-panel');
    return;
  }
  document.querySelectorAll('a[href="beta.html"]').forEach(link=>{
    link.href='beta.html?src='+encodeURIComponent(raw);
  });
})();
