import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync, existsSync } from "node:fs";
import { dirname, resolve, join } from "node:path";
import { fileURLToPath } from "node:url";
const root=resolve(dirname(fileURLToPath(import.meta.url)),"..");
const load=name=>{
  const text=readFileSync(join(root,name),"utf8");
  // Example configs contain standalone comment lines only, not active JS expressions.
  return JSON.parse(text.replace(/^\s*\/\/.*$/gm,""));
};
test("all committed Wrangler templates keep Cron disabled by default",()=>{
  for(const name of ["wrangler.example.jsonc","wrangler.watchdog.example.jsonc","wrangler.operator-alerts.example.jsonc"]){
    const c=load(name);
    assert.deepEqual(c.triggers.crons,[],name);
    assert.equal(c.workers_dev,false);
    assert.equal(c.preview_urls,false);
  }
});
test("operator issue is prepared, but actual notification activation has three separate holds",()=>{
  const c=load("wrangler.operator-alerts.example.jsonc");
  assert.equal(c.vars.GITHUB_ALERT_REPO,"modernsnc2022-ai/Korea-Employment-Passport");
  assert.equal(c.vars.GITHUB_ALERT_ISSUE,"325");
  assert.equal(c.vars.ALERT_DELIVERY_ENABLED,"false");
  assert.equal(c.vars.GITHUB_ALERT_START_UTC,"REPLACE_WITH_OWNER_APPROVED_UTC");
  assert.match(c.d1_databases[0].database_id,/REPLACE_WITH_/);
  assert.equal(Object.hasOwn(c.vars,"GITHUB_ALERT_TOKEN"),false);
});
test("separate source and watchdog monitors remain intentionally off",()=>{
  assert.equal(load("wrangler.example.jsonc").vars.MONITOR_ENABLED,"false");
  assert.equal(load("wrangler.watchdog.example.jsonc").vars.MONITOR_WATCHDOG_ENABLED,"false");
  for(const name of ["wrangler.json","wrangler.jsonc","wrangler.toml"]){
    assert.equal(existsSync(join(root,name)),false,name+" must not exist in unfinished staging");
  }
});
test("reconciliation audit retains no automatic outcome-unknown retries",()=>{
  const code=readFileSync(join(root,"src","operator-alerts.mjs"),"utf8");
  assert.match(code,/APPROVED_OPERATOR_ISSUE=325/);
  assert.match(code,/status='queued'/);
  assert.match(code,/reconcile_required/);
  assert.match(code,/status='sending'/);
  assert.doesNotMatch(code,/ALERT_DELIVERY_ENABLED\s*!==\s*"false"/);
});
