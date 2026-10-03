const CACHE='kep-v31';
const CORE=['./','./index.html','./app.html','./app-shell.css','./app-runtime.js','./manifest.webmanifest','./icon.svg','./privacy.html','./data/id_e9_manufacturing_2026.json','./data/id_e9_manufacturing_2026_rules.json','./data/id_e9_manufacturing_2026_id.json','./data/slc_guardian_2026.json','./data/workplace_reality_v1.json','./data/document_packs_2026.json','./data/exact_answer_rules_v1.json','./data/document_examples_v1.json','./data/freshness_policy_v1.json','./data/broker_question_catalog_v1.json','./data/form_wizards_2026.json','./data/form_lineage_2026.json','./data/source_review_status.json','./data/official_help_channels_v1.json'];
self.addEventListener('install',event=>event.waitUntil(caches.open(CACHE).then(cache=>cache.addAll(CORE))));
self.addEventListener('activate',event=>event.waitUntil(caches.keys().then(keys=>Promise.all(keys.filter(k=>k!==CACHE).map(k=>caches.delete(k))))));
self.addEventListener('fetch',event=>{
  if(event.request.method!=='GET')return;
  event.respondWith(fetch(event.request).then(response=>{
    const clone=response.clone();
    caches.open(CACHE).then(cache=>cache.put(event.request,clone));
    return response;
  }).catch(()=>caches.match(event.request).then(r=>r||caches.match('./app.html'))));
});