#!/usr/bin/env node
// KEP monitoring M9: offline-only review and Wrangler --dry-run compilation.
// No remote deploy, no remote resource creation, no secrets, no beta activation.
import {readFileSync,writeFileSync,mkdtempSync,existsSync,readdirSync,statSync} from "node:fs";
import {tmpdir} from "node:os";
import {join,resolve,dirname,isAbsolute} from "node:path";
import {fileURLToPath} from "node:url";
import {spawnSync} from "node:child_process";
import {createHash} from "node:crypto";

const root=resolve(dirname(fileURLToPath(import.meta.url)),"..");
const roles=[
 {name:"source",template:"wrangler.example.jsonc",entry:"src/index.mjs",flag:"MONITOR_ENABLED"},
 {name:"watchdog",template:"wrangler.watchdog.example.jsonc",entry:"src/watchdog.mjs",flag:"MONITOR_WATCHDOG_ENABLED"},
 {name:"operator",template:"wrangler.operator-alerts.example.jsonc",entry:"src/operator-alerts.mjs",flag:"ALERT_DELIVERY_ENABLED"}
];
const migrations=["0001_init.sql","0002_source_isolation.sql","0003_watchdog.sql","0004_operator_alert_outbox.sql","0005_monotonic_snapshot.sql"];
const load=path=>JSON.parse(readFileSync(path,"utf8").replace(/^\s*\/\/.*$/gm,""));
export function checkOne(obj,role){
 if(obj.main!==role.entry||obj.workers_dev!==false||obj.preview_urls!==false)
  throw Error(role.name+":PUBLIC_ENDPOINT_OR_ENTRY");
 if(!Array.isArray(obj.triggers?.crons)||obj.triggers.crons.length!==0)
  throw Error(role.name+":SCHEDULE_MUST_BE_OFF");
 if(obj.vars?.[role.flag]!=="false")throw Error(role.name+":RUNTIME_MUST_BE_OFF");
 if(obj.d1_databases?.length!==1||obj.d1_databases[0].binding!=="MONITOR_DB"||
    obj.d1_databases[0].database_name!=="kep-official-watch-metadata"||
    !/^REPLACE_WITH_/.test(obj.d1_databases[0].database_id))
  throw Error(role.name+":MUST_REQUIRE_FRESH_D1");
 if("GITHUB_ALERT_TOKEN" in obj.vars || obj.routes || obj.route || obj.zone_id)
  throw Error(role.name+":UNSAFE_SECRETS_OR_ROUTES");
 if(role.name==="operator" && (obj.vars.GITHUB_ALERT_ISSUE!=="325"||
    obj.vars.GITHUB_ALERT_REPO!=="modernsnc2022-ai/Korea-Employment-Passport"||
    obj.vars.GITHUB_ALERT_START_UTC!=="REPLACE_WITH_OWNER_APPROVED_UTC"))
  throw Error("UNAPPROVED_OPERATOR_DESTINATION_OR_CUTOFF");
 return true;
}
export function inspect(base=root){
 for(const n of ["wrangler.json","wrangler.jsonc","wrangler.toml",".dev.vars",".env"]){
   if(existsSync(join(base,n)))throw Error("ACTIVE_CONFIG_OR_SECRET_BLOCKED:"+n);
 }
 for(const role of roles){
   if(!existsSync(join(base,role.entry)))throw Error("ENTRY_MISSING:"+role.entry);
   checkOne(load(join(base,role.template)),role);
 }
 const files=readdirSync(join(base,"migrations")).filter(x=>x.endsWith(".sql")).sort();
 if(JSON.stringify(files)!==JSON.stringify(migrations))throw Error("UNREVIEWED_MIGRATION");
 for(const n of files){
   const sql=readFileSync(join(base,"migrations",n),"utf8");
   if(!/CREATE (?:TABLE|TRIGGER) IF NOT EXISTS/.test(sql)||
      /\b(?:DROP TABLE|TRUNCATE|DELETE FROM)\b/i.test(sql))throw Error("UNSAFE_MIGRATION:"+n);
 }
 return {state:"SAFE_TO_BUILD_OFFLINE_NOT_TO_DEPLOY",
   roles:roles.map(x=>x.name),configuredCrons:0,plannedCrons:3,
   cloudflareFreeCronLimit:5,cloudflareFreeSubrequestLimit:50,
   cpuAndSubrequestsActualMeasured:false,betaReleaseAuthorized:false,
   blocking:["owner deployment approval","real monitor-only D1 UUID",
      "real Cron and origin egress validation","Free 10ms CPU and 50 subrequest evidence",
      "operator GitHub secret and first real notification approval",
      "KP2MI missing intermediate TLS","official source and beta signoffs"]};
}
export function bundle({wranglerJs,base=root}){
 inspect(base);
 if(!wranglerJs||!isAbsolute(wranglerJs)||!existsSync(wranglerJs)||
    !/wrangler\.js$/i.test(wranglerJs))throw Error("LOCAL_WRANGLER_CLI_REQUIRED");
 const tmp=mkdtempSync(join(tmpdir(),"kep-offline-build-"));
 const result=[];
 for(const role of roles){
   const c=load(join(base,role.template));
   delete c.$schema;
   c.name="kep-offline-build-"+role.name;
   c.main=join(base,role.entry).replaceAll("\\","/");
   c.d1_databases[0].database_id="00000000-0000-4000-8000-000000000009";
   c.d1_databases[0].migrations_dir=join(base,"migrations").replaceAll("\\","/");
   const config=join(tmp,role.name+".json");
   const output=join(tmp,role.name+"-out");
   writeFileSync(config,JSON.stringify(c,null,2)+"\n","utf8");
   const args=[wranglerJs,"deploy","--dry-run","--config",config,"--outdir",output];
   if(!args.includes("--dry-run")||args.includes("--remote")||args.includes("--temporary"))
     throw Error("UNSAFE_BUILD_INVOCATION");
   const done=spawnSync(process.execPath,args,{cwd:base,encoding:"utf8",
     timeout:60000,windowsHide:true,env:{...process.env,
       CLOUDFLARE_API_TOKEN:"",CLOUDFLARE_API_KEY:"",CLOUDFLARE_EMAIL:"",
       CF_API_TOKEN:"",WRANGLER_SEND_METRICS:"false",CI:"true"}});
   if(done.error||done.status!==0)throw Error(role.name+"_DRYRUN_FAILED:"+
     String(done.error?.message||done.stderr||done.stdout).slice(-800));
   const built=readdirSync(output).filter(x=>/\.m?js$/.test(x));
   if(built.length!==1)throw Error("DRYRUN_BUNDLE_COUNT:"+role.name);
   const bytes=readFileSync(join(output,built[0]));
   if(bytes.length<100)throw Error("INVALID_BUNDLE");
   result.push({name:role.name,bytes:bytes.length,
     sha256:createHash("sha256").update(bytes).digest("hex")});
 }
 return {status:"THREE_OFFLINE_BUNDLES_PASS",remoteDeploy:false,
   secretsUsed:false,temporaryBuildDir:tmp,bundles:result};
}
if(process.argv[1]&&resolve(process.argv[1])===fileURLToPath(import.meta.url)){
 try{
  const check=inspect();
  if(process.argv.includes("--bundle")){
   console.log(JSON.stringify({check,bundle:bundle({wranglerJs:process.env.KEP_WRANGLER_JS})},null,2));
  }else if(process.argv.length===2||process.argv.includes("--check")){
   console.log(JSON.stringify({check},null,2));
  }else throw Error("USAGE: node scripts/offline-preflight.mjs [--check|--bundle]");
 }catch(e){console.error("KEP_OFFLINE_PREFLIGHT_FAIL",e.message);process.exitCode=2;}
}
