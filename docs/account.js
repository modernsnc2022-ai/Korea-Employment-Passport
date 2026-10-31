/* KEP optional account frontend. Supabase Auth handles password storage and verification. */
const config=window.KEP_ACCOUNT_CONFIG||{};
const openButton=document.getElementById('accountOpenBtn');
const dialog=document.getElementById('accountDialog');
const status=document.getElementById('accountStatus');
const form=document.getElementById('accountForm');
const emailInput=document.getElementById('accountEmail');
const passwordInput=document.getElementById('accountPassword');
const passwordLabel=document.getElementById('accountPasswordLabel');
const title=document.getElementById('accountTitle');
const submit=document.getElementById('accountSubmit');
const modeLinks=document.getElementById('accountModeLinks');
const signedIn=document.getElementById('accountSignedIn');
let client=null;
let currentUser=null;
let mode='login';
let syncEnabled=false;
let busy=false;
let syncTimer=null;
const validConfig=/^https:\/\/[a-z0-9-]+\.supabase\.co\/?$/i.test(config.url||'') && /^sb_publishable_|^eyJ/.test(config.publishableKey||'');
function notice(message,error=false){status.hidden=false;status.className=error?'result risk':'result safe';status.textContent=message;}
function setMode(next){mode=next;title.textContent=({login:'Masuk akun KEP',signup:'Daftar akun gratis',forgot:'Atur ulang kata sandi',recovery:'Ganti kata sandi'}[next]||'Akun KEP');passwordLabel.hidden=next==='forgot';document.querySelector('.account-consent').hidden=next!=='signup';emailInput.closest('label').hidden=next==='recovery';emailInput.required=next!=='recovery';passwordInput.required=next!=='forgot';passwordInput.autocomplete=next==='signup'?'new-password':'current-password';passwordInput.minLength=next==='signup'||next==='recovery'?12:1;submit.textContent=({login:'Masuk',signup:'Buat akun gratis',forgot:'Kirim email pemulihan',recovery:'Simpan kata sandi baru'}[next]||'Lanjut');modeLinks.hidden=next==='recovery';status.hidden=true;}
function setLoggedIn(user){currentUser=user||null;signedIn.hidden=!user;form.hidden=!!user;modeLinks.hidden=!!user||mode==='recovery';if(user){document.getElementById('accountIdentity').textContent=user.email||'Akun KEP';notice('Login aktif. Pilih simpan progres perangkat atau pulihkan progres cloud. Progres pemerintah tetap perlu dicek di situs resmi.');}else{syncEnabled=false;setMode('login');}}
function apiError(e){return (e&&typeof e.message==='string')?e.message:'Layanan akun tidak tersedia. Periksa koneksi dan coba lagi.';}
function validProgress(){if(!window.KEPAccountProgress?.ready())throw new Error('Panduan belum selesai dimuat. Coba lagi setelah pemuatan selesai.');const backup=window.KEPAccountProgress.backup();if(backup.betaTesterId)throw new Error('Catatan dari mode ID beta lama perlu dipindahkan terlebih dahulu. Simpan backup lokal.');return {kind:backup.kind,schemaVersion:backup.schemaVersion,routeKey:backup.routeKey,betaTesterId:null,progress:backup.progress};}
async function readCloud(){const {data,error}=await client.from('kep_progress').select('payload,updated_at').eq('user_id',currentUser.id).maybeSingle();if(error)throw error;return data;}
async function saveCloud(silent=false){if(!currentUser||busy)return;busy=true;try{const payload=validProgress();const {error}=await client.from('kep_progress').upsert({user_id:currentUser.id,payload,updated_at:new Date().toISOString()},{onConflict:'user_id'});if(error)throw error;syncEnabled=true;if(!silent)notice('Progres berhasil disimpan ke akun KEP. Perubahan berikutnya akan disimpan otomatis selama halaman ini terbuka.');}catch(e){syncEnabled=false;notice('Gagal menyimpan progres: '+apiError(e),true);}finally{busy=false;}}
async function restoreCloud(){if(!currentUser||busy)return;busy=true;try{const row=await readCloud();if(!row?.payload){notice('Belum ada progres cloud untuk akun ini. Gunakan Simpan progres perangkat terlebih dahulu.',true);return;}if(!window.KEPAccountProgress?.ready())throw new Error('Panduan belum selesai dimuat.');const local=validProgress();if(row.payload.routeKey!==local.routeKey)throw new Error('Progres cloud untuk jalur lain. Pemulihan dibatalkan.');if(!confirm('Progres perangkat saat ini akan diganti. Simpan file backup dari menu pengaturan dahulu jika perlu. Lanjutkan?'))return;window.KEPAccountProgress.restore(row.payload);syncEnabled=true;notice('Progres cloud dipulihkan. Tampilan sedang diperbarui.');setTimeout(()=>location.reload(),650);}catch(e){notice('Pemulihan gagal: '+apiError(e),true);}finally{busy=false;}}
function queueSync(){if(!syncEnabled||!currentUser)return;clearTimeout(syncTimer);syncTimer=setTimeout(()=>saveCloud(true),1500);}
window.addEventListener('kep:progress-changed',queueSync);
async function authAction(event){event.preventDefault();if(busy||!client)return;busy=true;submit.disabled=true;try{const email=emailInput.value.trim().toLowerCase(),password=passwordInput.value;
 if(mode!=='recovery'&&!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email))throw new Error('Masukkan alamat email yang valid.');
 if(mode==='signup'){
   if(password.length<12)throw new Error('Gunakan kata sandi minimal 12 karakter.');
   if(!document.getElementById('accountPrivacyConsent').checked)throw new Error('Setujui pemberitahuan akun dan privasi terlebih dahulu.');
   const {error}=await client.auth.signUp({email,password,options:{emailRedirectTo:location.origin+location.pathname}});if(error)throw error;
   setMode('login');notice('Periksa email untuk konfirmasi pendaftaran. Setelah dikonfirmasi, masuk menggunakan email dan kata sandi.');
 }else if(mode==='forgot'){
   const {error}=await client.auth.resetPasswordForEmail(email,{redirectTo:location.origin+location.pathname});if(error)throw error;
   setMode('login');notice('Jika alamat tersebut terdaftar, email pemulihan akan dikirim.');
 }else if(mode==='recovery'){
   if(password.length<12)throw new Error('Kata sandi baru minimal 12 karakter.');
   const {error}=await client.auth.updateUser({password});if(error)throw error;
   setMode('login');notice('Kata sandi berhasil diperbarui.');
 }else{
   const {error}=await client.auth.signInWithPassword({email,password});if(error)throw error;
   const {data:{user},error:userError}=await client.auth.getUser();if(userError||!user)throw userError||new Error('Login belum terverifikasi');setLoggedIn(user);
 }
 }catch(e){notice(apiError(e),true);}finally{busy=false;submit.disabled=false;passwordInput.value='';}}
form.addEventListener('submit',authAction);
modeLinks.addEventListener('click',event=>{const el=event.target.closest('[data-account-mode]');if(!el)return;setMode(el.dataset.accountMode);});
document.getElementById('accountLogoutBtn').addEventListener('click',async()=>{clearTimeout(syncTimer);syncEnabled=false;const {error}=await client.auth.signOut();if(error)notice(apiError(error),true);else setLoggedIn(null);});
document.getElementById('accountSaveBtn').addEventListener('click',()=>saveCloud());
document.getElementById('accountDeleteProgressBtn').addEventListener('click',async()=>{if(!currentUser||!confirm('Hapus catatan progres cloud untuk akun ini? Progres pada perangkat ini tidak dihapus.'))return;const {error}=await client.from('kep_progress').delete().eq('user_id',currentUser.id);if(error)notice('Gagal menghapus: '+apiError(error),true);else{syncEnabled=false;notice('Catatan progres cloud dihapus. Data di perangkat tetap tersedia.');}});
document.getElementById('accountRestoreBtn').addEventListener('click',restoreCloud);
openButton.addEventListener('click',()=>{dialog.showModal();if(!currentUser)emailInput.focus();});
document.getElementById('accountCloseBtn').addEventListener('click',()=>dialog.close());
async function boot(){if(!validConfig)return;try{
 const {createClient}=await import('https://esm.sh/@supabase/supabase-js@2.58.0?bundle');
 client=createClient(config.url.replace(/\/$/,''),config.publishableKey,{auth:{persistSession:true,autoRefreshToken:true,detectSessionInUrl:true}});
 const {data:{session},error}=await client.auth.getSession();if(error)throw error;
 if(session){const {data:{user},error:userError}=await client.auth.getUser();if(userError)throw userError;setLoggedIn(user)}
 client.auth.onAuthStateChange((type,session)=>{if(type==='PASSWORD_RECOVERY'){setLoggedIn(null);setMode('recovery');dialog.showModal();}else if(type==='SIGNED_OUT'){setLoggedIn(null);}else if(type==='SIGNED_IN'||type==='TOKEN_REFRESHED'){if(session?.user){setLoggedIn(session.user);}}});
 openButton.hidden=false;
 }catch(e){console.warn('KEP account unavailable:',apiError(e));openButton.hidden=true;}}
boot();
