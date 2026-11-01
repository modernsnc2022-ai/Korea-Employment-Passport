/* KEP optional account: Google Cloud Firebase Authentication + Cloud Firestore. */
const cfg=window.KEP_ACCOUNT_CONFIG||{};
const $account=id=>document.getElementById(id);
const openButton=$account('accountOpenBtn');
const dialog=$account('accountDialog');
const status=$account('accountStatus');
const form=$account('accountForm');
const emailInput=$account('accountEmail');
const passwordInput=$account('accountPassword');
const passwordLabel=$account('accountPasswordLabel');
const title=$account('accountTitle');
const submit=$account('accountSubmit');
const modeLinks=$account('accountModeLinks');
const signedIn=$account('accountSignedIn');
const validConfig=cfg.provider==='firebase' && /^[-a-z0-9]+$/i.test(cfg.projectId||'') && /^[-a-z0-9.]+\.firebaseapp\.com$/i.test(cfg.authDomain||'') && /^AIza[\w-]{20,}$/.test(cfg.apiKey||'') && /^1:\d+:web:[\da-f]+$/i.test(cfg.appId||'');
let fb=null,auth=null,db=null,currentUser=null,mode='login',syncEnabled=false,busy=false,syncTimer=null;
function notice(message,error=false){status.hidden=false;status.className=error?'result risk':'result safe';status.textContent=message;}
function setMode(next){
  mode=next;title.textContent=({login:'Masuk akun KEP',signup:'Daftar akun gratis',forgot:'Atur ulang kata sandi'}[next]||'Akun KEP');
  passwordLabel.hidden=next==='forgot';passwordInput.required=next!=='forgot';passwordInput.autocomplete=next==='signup'?'new-password':'current-password';passwordInput.minLength=next==='signup'?12:1;
  $account('accountPrivacyConsent').closest('label').hidden=next!=='signup';
  submit.textContent=({login:'Masuk',signup:'Buat akun gratis',forgot:'Kirim email pemulihan'}[next]||'Masuk');
  modeLinks.hidden=false;status.hidden=true;
}
function setLoggedIn(user){
  const verified=Boolean(user?.emailVerified);currentUser=verified?user:null;
  signedIn.hidden=!verified;form.hidden=verified;modeLinks.hidden=verified;
  if(verified){$account('accountIdentity').textContent=user.email||'Akun KEP';notice('Anda sudah masuk. Progres cloud hanya disimpan atau dipulihkan jika Anda memilihnya.');}
  else{syncEnabled=false;setMode('login');}
}
function getError(error){
 const code=error?.code||'';
 if(code==='auth/invalid-credential'||code==='auth/wrong-password')return 'Email atau kata sandi tidak cocok.';
 if(code==='auth/email-already-in-use')return 'Email sudah terdaftar. Silakan masuk atau pulihkan kata sandi.';
 if(code==='auth/too-many-requests')return 'Terlalu banyak percobaan. Coba lagi nanti.';
 if(code==='auth/requires-recent-login')return 'Untuk menghapus akun, keluar lalu masuk kembali terlebih dahulu.';
 if(code==='permission-denied')return 'Akses progres ditolak. Hubungi pengelola jika akun telah diverifikasi.';
 return typeof error?.message==='string'?error.message:'Layanan akun tidak tersedia. Coba lagi nanti.';
}
function progressPayload(){
 if(!window.KEPAccountProgress?.ready())throw new Error('Panduan belum selesai dimuat.');
 const data=window.KEPAccountProgress.backup();
 if(data.betaTesterId)throw new Error('Progres ID beta lama belum dapat disinkronkan. Simpan backup lokal terlebih dahulu.');
 return {kind:data.kind,schemaVersion:data.schemaVersion,routeKey:data.routeKey,betaTesterId:null,progress:data.progress};
}
function userDocument(){if(!currentUser?.emailVerified||!db||!fb)throw new Error('Masuk dengan email terverifikasi terlebih dahulu.');return fb.doc(db,'kep_progress',currentUser.uid);}
async function saveCloud(silent=false){
 if(busy||!currentUser)return;busy=true;
 try{const data=progressPayload();await fb.setDoc(userDocument(),{payload:data,updatedAt:fb.serverTimestamp()});syncEnabled=true;if(!silent)notice('Progres tersimpan di akun KEP. Perubahan berikutnya disimpan otomatis saat halaman terbuka.');}
 catch(error){syncEnabled=false;notice('Gagal menyimpan progres: '+getError(error),true)}finally{busy=false;}
}
async function restoreCloud(){
 if(busy||!currentUser)return;busy=true;
 try{const snap=await fb.getDoc(userDocument());if(!snap.exists())throw new Error('Belum ada progres cloud. Simpan progres perangkat terlebih dahulu.');
   const payload=snap.data().payload,local=progressPayload();
   if(payload.routeKey!==local.routeKey)throw new Error('Progres cloud untuk jalur lain. Pemulihan dibatalkan.');
   if(!confirm('Progres perangkat akan diganti. Buat backup JSON lokal terlebih dahulu jika perlu. Lanjutkan?'))return;
   window.KEPAccountProgress.restore(payload);syncEnabled=true;notice('Progres dipulihkan. Tampilan sedang dimuat ulang.');setTimeout(()=>location.reload(),650);
 }catch(error){notice('Pemulihan gagal: '+getError(error),true)}finally{busy=false;}
}
function queueSync(){if(!syncEnabled||!currentUser)return;clearTimeout(syncTimer);syncTimer=setTimeout(()=>saveCloud(true),1800);}
window.addEventListener('kep:progress-changed',queueSync);
async function submitAccount(event){
 event.preventDefault();if(busy||!auth)return;busy=true;submit.disabled=true;
 try{const email=emailInput.value.trim().toLowerCase(),password=passwordInput.value;
   if(!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email))throw new Error('Masukkan alamat email yang benar.');
   if(mode==='signup'){
     if(password.length<12)throw new Error('Kata sandi minimal 12 karakter.');
     if(!$account('accountPrivacyConsent').checked)throw new Error('Setujui kebijakan privasi untuk membuat akun.');
     const result=await fb.createUserWithEmailAndPassword(auth,email,password);
     await fb.sendEmailVerification(result.user,{url:location.origin+location.pathname});
     await fb.signOut(auth);setMode('login');notice('Email verifikasi dikirim. Konfirmasi email terlebih dahulu, lalu masuk.');
   }else if(mode==='forgot'){
     await fb.sendPasswordResetEmail(auth,email);setMode('login');notice('Jika email terdaftar, Anda akan menerima pesan pemulihan.');
   }else{
     const result=await fb.signInWithEmailAndPassword(auth,email,password);
     await fb.reload(result.user);
     if(!result.user.emailVerified){await fb.signOut(auth);throw new Error('Email belum diverifikasi. Buka pesan verifikasi pendaftaran sebelum login.');}
     setLoggedIn(result.user);
   }
 }catch(error){notice(getError(error),true)}finally{busy=false;submit.disabled=false;passwordInput.value='';}
}
form.addEventListener('submit',submitAccount);
modeLinks.addEventListener('click',event=>{const btn=event.target.closest('[data-account-mode]');if(btn)setMode(btn.dataset.accountMode)});
$account('accountLogoutBtn').addEventListener('click',async()=>{clearTimeout(syncTimer);syncEnabled=false;try{await fb.signOut(auth);setLoggedIn(null)}catch(error){notice(getError(error),true)}});
$account('accountSaveBtn').addEventListener('click',()=>saveCloud());
$account('accountRestoreBtn').addEventListener('click',restoreCloud);
$account('accountDeleteProgressBtn').addEventListener('click',async()=>{
 if(!currentUser||!confirm('Hapus progres yang tersimpan di cloud? Data perangkat tidak akan dihapus.'))return;
 try{await fb.deleteDoc(userDocument());syncEnabled=false;notice('Progres cloud berhasil dihapus. Data perangkat tetap ada.')}catch(error){notice(getError(error),true)}
});
$account('accountDeleteAccountBtn').addEventListener('click',async()=>{
 if(!currentUser||!confirm('Hapus akun KEP dan progres cloud secara permanen? Tindakan ini tidak dapat dibatalkan.'))return;
 try{await fb.deleteDoc(userDocument());await fb.deleteUser(auth.currentUser);syncEnabled=false;setLoggedIn(null);notice('Akun KEP dan progres cloud dihapus.')}catch(error){notice('Penghapusan akun belum selesai: '+getError(error),true)}
});
openButton.addEventListener('click',()=>{dialog.showModal();if(!currentUser)emailInput.focus()});
$account('accountCloseBtn').addEventListener('click',()=>dialog.close());
async function boot(){
 if(!validConfig)return;
 try{
  const base='https://www.gstatic.com/firebasejs/12.4.0/';
  const [core,authentication,firestore]=await Promise.all([import(base+'firebase-app.js'),import(base+'firebase-auth.js'),import(base+'firebase-firestore.js')]);
  const app=core.initializeApp({apiKey:cfg.apiKey,authDomain:cfg.authDomain,projectId:cfg.projectId,appId:cfg.appId});
  auth=authentication.getAuth(app);db=firestore.getFirestore(app);fb={...authentication,...firestore};
  authentication.onAuthStateChanged(auth,user=>{if(user?.emailVerified)setLoggedIn(user);else if(!user)setLoggedIn(null);});
  openButton.hidden=false;
 }catch(error){console.warn('KEP account backend not ready:',getError(error));openButton.hidden=true}
}
boot();
