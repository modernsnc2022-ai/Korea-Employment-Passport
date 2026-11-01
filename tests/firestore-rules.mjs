import {after, before, beforeEach, test} from 'node:test';
import {readFile} from 'node:fs/promises';
import {initializeTestEnvironment, assertFails, assertSucceeds} from '@firebase/rules-unit-testing';
import {deleteDoc, doc, getDoc, serverTimestamp, setDoc} from 'firebase/firestore';

let env;
const projectId='kep-rules-test';
const ownerUid='owner-uid';
const otherUid='other-uid';
const goodPayload={
  kind:'kep-progress-backup',
  schemaVersion:2,
  routeKey:'id-e9-manufacturing-2026',
  betaTesterId:null,
  progress:{
    done:['eligibility'],
    docs:['passport-copy'],
    scopeSelections:{registration:'official-2026'},
    formWizard:{formId:'visa-form',index:2},
    wizardReviewed:['registration|default|visa-form|name'],
    quickSetup:true
  }
};

before(async()=>{
  const rules=await readFile(new URL('../deployment/gcp/firestore.rules',import.meta.url),'utf8');
  env=await initializeTestEnvironment({projectId,firestore:{rules,host:'127.0.0.1',port:8088}});
});
beforeEach(async()=>env.clearFirestore());
after(async()=>env.cleanup());

function progressRef(context,uid=ownerUid){return doc(context.firestore(),'kep_progress',uid)}
function record(payload=goodPayload){return {payload,updatedAt:serverTimestamp()}}

test('verified owner can create, read, update and delete only their progress',async()=>{
  const owner=env.authenticatedContext(ownerUid,{email:'owner@example.org',email_verified:true});
  await assertSucceeds(setDoc(progressRef(owner),record()));
  await assertSucceeds(getDoc(progressRef(owner)));
  await assertSucceeds(setDoc(progressRef(owner),record({...goodPayload,progress:{...goodPayload.progress,quickSetup:false}})));
  await assertSucceeds(deleteDoc(progressRef(owner)));
});

test('anonymous, unverified and another verified user cannot access owner progress',async()=>{
  await env.withSecurityRulesDisabled(async context=>setDoc(progressRef(context),record()));
  const anonymous=env.unauthenticatedContext();
  const unverified=env.authenticatedContext(ownerUid,{email:'owner@example.org',email_verified:false});
  const other=env.authenticatedContext(otherUid,{email:'other@example.org',email_verified:true});
  await assertFails(getDoc(progressRef(anonymous)));
  await assertFails(getDoc(progressRef(unverified)));
  await assertFails(getDoc(progressRef(other)));
  await assertFails(setDoc(progressRef(other),record()));
  await assertFails(deleteDoc(progressRef(other)));
});

test('rules reject unexpected collections and unsafe progress shapes',async()=>{
  const owner=env.authenticatedContext(ownerUid,{email:'owner@example.org',email_verified:true});
  await assertFails(setDoc(doc(owner.firestore(),'other_collection','x'),{ok:true}));
  await assertFails(setDoc(progressRef(owner),record({...goodPayload,routeKey:'../../identity-record'})));
  await assertFails(setDoc(progressRef(owner),record({...goodPayload,progress:{...goodPayload.progress,formWizard:{formId:'visa-form',index:'2'}}})));
  await assertFails(setDoc(progressRef(owner),{...record(),privateNote:'must not be stored'}));
});
