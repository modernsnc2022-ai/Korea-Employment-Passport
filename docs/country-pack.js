const COUNTRY_PACK_REGISTRY_URL='data/country_packs_v1.json';

async function loadCountryPackRegistry(){
  const response=await fetch(COUNTRY_PACK_REGISTRY_URL,{cache:'no-store'});
  if(!response.ok)throw new Error('Country Pack registry load failed: '+response.status);
  return response.json();
}

function routeEntryById(registry,routeId){
  return (registry?.routes||[]).find(route=>route.routeId===routeId)||null;
}

async function loadCountryPack(routeId){
  const registry=await loadCountryPackRegistry();
  const entry=routeEntryById(registry,routeId);
  if(!entry)throw new Error('Unsupported KEP route: '+String(routeId||''));
  const [routeResponse,localeResponse]=await Promise.all([
    fetch(entry.routeFile,{cache:'no-store'}),
    fetch(entry.localizationFile,{cache:'no-store'})
  ]);
  if(!routeResponse.ok)throw new Error('Route pack load failed: '+routeResponse.status);
  if(!localeResponse.ok)throw new Error('Route localization load failed: '+localeResponse.status);
  const pack=await routeResponse.json();
  const locale=await localeResponse.json();
  validateCountryPackShape(registry,entry,pack,locale);
  return {registry,entry,pack,locale};
}

function validateCountryPackShape(registry,entry,pack,locale){
  const expected=registry?.commonStageIds||[];
  const actual=(pack?.stages||[]).map(stage=>stage.id);
  if(expected.length!==actual.length||expected.some((id,index)=>actual[index]!==id)){
    throw new Error('Country Pack stage contract mismatch for '+entry.routeId);
  }
  if(pack.country!==entry.country||pack.visa!==entry.visa||pack.sector!==entry.sector){
    throw new Error('Country Pack route metadata mismatch for '+entry.routeId);
  }
  for(const stage of pack.stages||[]){
    if(!stage.id||!stage.title||!stage.authority||!stage.kind||!stage.action||!stage.sourceUrl){
      throw new Error('Country Pack stage is incomplete: '+String(stage.id||'unknown'));
    }
    if(!String(stage.sourceUrl).startsWith('https://')){
      throw new Error('Country Pack source must use HTTPS: '+stage.id);
    }
    if(!locale?.[stage.id]?.title||!locale?.[stage.id]?.action){
      throw new Error('Country Pack localization missing: '+stage.id);
    }
  }
  if(entry.lifecycle==='research_hold'){
    if(entry.publicAvailability!=='preview_only'||pack.publicAvailability!=='preview_only'){
      throw new Error('Research HOLD route cannot be public-open');
    }
    if(pack?.safety?.betaIntakeOpen!==false){
      throw new Error('Research HOLD route cannot open beta intake');
    }
  }
  return true;
}

window.KEPCountryPacks={
  loadRegistry:loadCountryPackRegistry,
  load:loadCountryPack,
  find:routeEntryById,
  validate:validateCountryPackShape
};
