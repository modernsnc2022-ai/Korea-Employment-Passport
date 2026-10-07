const DEFAULT_ORIGIN='https://modernsnc2022-ai.github.io';
const JSON_HEADERS={'Content-Type':'application/json; charset=utf-8','Cache-Control':'no-store','X-Content-Type-Options':'nosniff'};

function allowedOrigins(env){
  return String(env.ALLOWED_ORIGINS||DEFAULT_ORIGIN)
    .split(',')
    .map(value=>value.trim())
    .filter(Boolean);
}

function corsHeaders(origin,env){
  if(!origin||!allowedOrigins(env).includes(origin))return {};
  return {
    'Access-Control-Allow-Origin':origin,
    'Access-Control-Allow-Methods':'POST,OPTIONS',
    'Access-Control-Allow-Headers':'Content-Type,Accept',
    'Access-Control-Max-Age':'600',
    'Vary':'Origin'
  };
}

function json(body,status=200,extra={}){
  return new Response(JSON.stringify(body),{status,headers:{...JSON_HEADERS,...extra}});
}

function cleanString(value,max){
  const text=String(value??'').trim();
  return text.length<=max?text:'';
}

function validEmail(value){
  return value.length>3&&value.length<=254&&/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value);
}

function validCycle(value){
  return value==='unknown'||/^20\d{2}$/.test(value);
}

function retentionSeconds(env){
  const parsed=Number.parseInt(String(env.RETENTION_DAYS||'90'),10);
  const days=Number.isFinite(parsed)?Math.min(365,Math.max(7,parsed)):90;
  return days*24*60*60;
}

export default {
  async fetch(request,env){
    const url=new URL(request.url);
    const origin=request.headers.get('Origin')||'';
    const cors=corsHeaders(origin,env);

    if(request.method==='GET'&&url.pathname==='/health'){
      return json({ok:true,service:'kep-beta-intake'},200,{'Cache-Control':'no-store'});
    }

    if(request.method==='OPTIONS'){
      if(!origin||!allowedOrigins(env).includes(origin))return json({error:'origin_not_allowed'},403);
      return new Response(null,{status:204,headers:cors});
    }

    if(request.method!=='POST'||url.pathname!=='/v1/beta/applicant'){
      return json({error:'not_found'},404,cors);
    }

    if(!origin||!allowedOrigins(env).includes(origin)){
      return json({error:'origin_not_allowed'},403);
    }

    if(!env.KEP_BETA_APPLICATIONS){
      return json({error:'storage_unavailable'},503,cors);
    }

    const type=String(request.headers.get('Content-Type')||'').toLowerCase();
    if(!type.startsWith('application/json')){
      return json({error:'content_type_required'},415,cors);
    }

    const length=Number.parseInt(request.headers.get('Content-Length')||'0',10);
    if(Number.isFinite(length)&&length>4096){
      return json({error:'payload_too_large'},413,cors);
    }

    let body;
    try{body=await request.json()}catch{return json({error:'invalid_json'},400,cors)}

    if(cleanString(body.website,120)){
      return json({ok:true,submissionId:'accepted'},202,cors);
    }

    const email=cleanString(body.contactEmail,254).toLowerCase();
    const stageId=cleanString(body.stageId,64);
    const stageTitle=cleanString(body.stageTitle,180);
    const cycle=cleanString(body.cycle,16);
    const sourceCode=cleanString(body.sourceCode,96);

    if(body.kind!=='active_applicant')return json({error:'invalid_kind'},400,cors);
    if(!validEmail(email))return json({error:'invalid_email'},400,cors);
    if(!/^[a-z0-9_]{2,64}$/.test(stageId))return json({error:'invalid_stage'},400,cors);
    if(!stageTitle)return json({error:'invalid_stage_title'},400,cors);
    if(!validCycle(cycle))return json({error:'invalid_cycle'},400,cors);
    if(!/^[a-z0-9_]{2,96}$/.test(sourceCode))return json({error:'invalid_source'},400,cors);
    if(body.activeProcess!==true||body.feedbackAgreement!==true){
      return json({error:'confirmations_required'},400,cors);
    }

    const uuid=crypto.randomUUID();
    const submissionId='KEP-I-'+uuid.slice(0,8).toUpperCase();
    const now=new Date().toISOString();
    const record={
      schemaVersion:1,
      submissionId,
      kind:'active_applicant',
      contactEmail:email,
      stageId,
      stageTitle,
      cycle,
      sourceCode,
      activeProcess:true,
      feedbackAgreement:true,
      receivedAt:now
    };
    const day=now.slice(0,10);
    await env.KEP_BETA_APPLICATIONS.put(
      'applicant:'+day+':'+uuid,
      JSON.stringify(record),
      {expirationTtl:retentionSeconds(env)}
    );
    return json({ok:true,submissionId},201,cors);
  }
};
