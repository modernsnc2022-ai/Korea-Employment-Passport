const form = document.getElementById('betaForm');
form.addEventListener('submit', (event) => {
  event.preventDefault();
  if (!document.getElementById('consent').checked) return;
  const role = document.getElementById('role').value;
  const stage = document.getElementById('stage').value;
  const name = document.getElementById('name').value.trim();
  const contact = document.getElementById('contact').value.trim();
  const source = document.getElementById('source').value;
  const subject = encodeURIComponent('[KEP Beta] Pendaftaran tester Indonesia');
  const body = encodeURIComponent(
    'Halo Korea Employment Passport Beta,\n\n' +
    'Nama panggilan: ' + name + '\n' +
    'Peran: ' + role + '\n' +
    'Tahap saat ini: ' + stage + '\n' +
    'Kontak: ' + contact + '\n' +
    'Sumber: ' + source + '\n\n' +
    'Saya bersedia dihubungi untuk uji beta / wawancara.'
  );
  window.location.href = 'mailto:modernsnc2022@gmail.com?subject=' + subject + '&body=' + body;
});
