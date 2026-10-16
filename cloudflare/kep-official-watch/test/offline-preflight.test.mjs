import test from "node:test";
import assert from "node:assert/strict";
import {readFileSync} from "node:fs";
import {join,dirname,resolve} from "node:path";
import {fileURLToPath} from "node:url";
import {checkOne,inspect,bundle} from "../scripts/offline-preflight.mjs";

const root=resolve(dirname(fileURLToPath(import.meta.url)),"..");
const read=name=>JSON.parse(readFileSync(join(root,name),"utf8").replace(/^\s*\/\/.*$/gm,""));
const role={name:"source",entry:"src/index.mjs",flag:"MONITOR_ENABLED"};
test("all three examples static-off with exactly four reviewed append-only migrations",()=>{
 const status=inspect();
 assert.equal(status.state,"SAFE_TO_BUILD_OFFLINE_NOT_TO_DEPLOY");
 assert.equal(status.roles.length,3);
 assert.equal(status.configuredCrons,0);
 assert.equal(status.plannedCrons,3);
 assert.equal(status.cloudflareFreeCronLimit,5);
 assert.equal(status.cpuAndSubrequestsActualMeasured,false);
 assert.equal(status.betaReleaseAuthorized,false);
 assert.ok(status.blocking.length>=5);
});
test("activated cron or monitor switch blocks even offline bundle generation",()=>{
 const c=read("wrangler.example.jsonc");
 c.triggers.crons=["0 */2 * * *"];
 assert.throws(()=>checkOne(c,role),/SCHEDULE_MUST_BE_OFF/);
 c.triggers.crons=[];
 c.vars.MONITOR_ENABLED="true";
 assert.throws(()=>checkOne(c,role),/RUNTIME_MUST_BE_OFF/);
});
test("public web route, wrong DB, and token in config rejected",()=>{
 const c=read("wrangler.example.jsonc");
 c.workers_dev=true;
 assert.throws(()=>checkOne(c,role),/PUBLIC_ENDPOINT_OR_ENTRY/);
 c.workers_dev=false;
 c.d1_databases[0].database_id="fake-live-id";
 assert.throws(()=>checkOne(c,role),/MUST_REQUIRE_FRESH_D1/);
 c.d1_databases[0].database_id="REPLACE_WITH_NEW_ISOLATED_MONITOR_D1_ID";
 c.vars.GITHUB_ALERT_TOKEN="dont_write_secrets";
 assert.throws(()=>checkOne(c,role),/UNSAFE_SECRETS_OR_ROUTES/);
});
test("GitHub alert example pinned to issue 325 and disabled from real sending",()=>{
 const c=read("wrangler.operator-alerts.example.jsonc");
 const t={name:"operator",entry:"src/operator-alerts.mjs",flag:"ALERT_DELIVERY_ENABLED"};
 assert.equal(checkOne(c,t),true);
 c.vars.GITHUB_ALERT_ISSUE="999";
 assert.throws(()=>checkOne(c,t),/UNAPPROVED_OPERATOR_DESTINATION_OR_CUTOFF/);
});
test("dry-run bundling refuses missing Wrangler CLI before any upload",()=>{
 assert.throws(()=>bundle({wranglerJs:null}),/LOCAL_WRANGLER_CLI_REQUIRED/);
});
