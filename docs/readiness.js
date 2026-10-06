'use strict';
(async()=>{
  const summaryEl=document.getElementById('summary');
  const listEl=document.getElementById('readiness');
  const esc=value=>String(value??'').replace(/[&<>"']/g,ch=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[ch]));
  try{
    const response=await fetch('./data/country_readiness_dashboard_2026.json',{cache:'no-store'});
    if(!response.ok) throw new Error('readiness data '+response.status);
    const data=await response.json();
    const s=data.summary||{};
    const summary=[
      ['EPS sending countries',s.sendingCountries],
      ['Registered Manufacturing packs',s.registeredCountryPacks],
      ['Beta HOLD',s.betaHold],
      ['Research HOLD',s.researchHold],
      ['Pending Manufacturing verification',s.pendingManufacturingVerification],
      ['Beta-ready',s.betaReady]
    ];
    summaryEl.innerHTML=summary.map(([label,value])=>'<article class="summary-card"><span>'+esc(label)+'</span><strong>'+esc(value)+'</strong></article>').join('');

    const rank=row=>{
      if(row.nextReview?.type==='dated_official_review') return 0;
      if(row.packState==='beta_hold') return 1;
      if(row.packState==='research_hold') return 2;
      return 3;
    };
    const rows=[...(data.rows||[])].sort((a,b)=>{
      const ar=rank(a),br=rank(b);
      if(ar!==br) return ar-br;
      const ad=a.nextReview?.date||'9999-99-99',bd=b.nextReview?.date||'9999-99-99';
      if(ad!==bd) return ad.localeCompare(bd);
      return String(a.countryName).localeCompare(String(b.countryName));
    });
    listEl.innerHTML=rows.map(row=>{
      const state=row.packState||'unknown';
      const badgeClass=row.nextReview?.type==='dated_official_review'?'dated':state==='pending_manufacturing_verification'?'pending':state==='beta_hold'?'beta':'';
      const date=row.nextReview?.date?'<div class="trigger-date">Review date: '+esc(row.nextReview.date)+'</div>':'';
      const blockers=(row.blockers||[]).map(x=>'<li>'+esc(x)+'</li>').join('');
      const sources=(row.nextReview?.officialSources||[]).map(url=>'<a href="'+esc(url)+'" rel="noopener">'+esc(url)+'</a>').join('');
      const details=row.detailsPage?'<p><a href="'+esc(row.detailsPage)+'">Open verification details</a></p>':'';
      return '<article class="readiness-card" data-country="'+esc(row.country)+'">'+
        '<span class="badge '+badgeClass+'">'+esc(state)+'</span>'+
        '<h3>'+esc(row.countryName)+' · '+esc(row.country)+'</h3>'+
        (row.routeId?'<p>'+esc(row.routeId)+'</p>':'<p>No promoted Manufacturing routeId</p>')+
        '<ul>'+blockers+'</ul>'+
        '<div class="trigger">'+date+'<strong>'+esc(row.nextReview?.subject||'Official evidence review')+'</strong>'+
        '<div class="source-links">'+sources+'</div>'+details+'</div>'+
      '</article>';
    }).join('');
  }catch(error){
    document.body.dataset.readinessError='true';
    summaryEl.textContent='Readiness data unavailable.';
    listEl.textContent='Unable to load the readiness dashboard.';
    console.error(error);
  }
})();