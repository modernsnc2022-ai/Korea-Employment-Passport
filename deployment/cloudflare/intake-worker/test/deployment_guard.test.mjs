import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {test} from 'node:test';
import {fileURLToPath} from 'node:url';
import {dirname,resolve} from 'node:path';

const root=resolve(dirname(fileURLToPath(import.meta.url)),'..');
const intake=readFileSync(resolve(root,'wrangler.toml.example'),'utf8');
const verifier=readFileSync(resolve(root,'email-verifier','wrangler.resend.toml.example'),'utf8');

function setting(source,key) {
  const found=source.match(new RegExp('^'+key+'\\s*=\\s*(.+)$','m'));
  assert.ok(found,'missing '+key);
  return found[1].trim();
}

test('intake Wrangler template remains disabled with both public routes off',()=>{
  assert.equal(setting(intake,'workers_dev'),'false');
  assert.equal(setting(intake,'preview_urls'),'false');
  assert.equal(setting(intake,'INTAKE_ENABLED'),'"false"');
  assert.equal(setting(intake,'keep_vars'),'true');
});
test('private verifier template remains disabled with both public routes off',()=>{
  assert.equal(setting(verifier,'workers_dev'),'false');
  assert.equal(setting(verifier,'preview_urls'),'false');
  assert.equal(setting(verifier,'VERIFIER_ENABLED'),'"false"');
});
test('service binding and database binding names match actual application code',()=>{
  assert.match(intake,/binding\s*=\s*"EMAIL_VERIFIER"\s*\r?\nservice\s*=\s*"kep-beta-email-verifier"/);
  assert.match(intake,/binding\s*=\s*"KEP_BETA_DB"/);
  assert.match(verifier,/binding\s*=\s*"OTP_DB"/);
  assert.doesNotMatch(intake,/TURNSTILE_SECRET\s*=\s*"[^"]+"/);
});
