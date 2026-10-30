"""Validate the public release explanation without coupling it to old marketing copy."""
from html.parser import HTMLParser

RELEASE_GATES = {
    'manufacturing-evidence': ('Manufaktur Umum', '2026', 'lampiran resmi', 'pasca-Skill Test'),
    'human-review': ('manusia', 'sumber resmi', 'tidak menggantikan'),
    'release-day-review': ('diperiksa ulang', 'hari rilis'),
    'same-version-checks': ('Static check', 'UI smoke', 'HTTPS', 'aset Pages', 'versi commit'),
    'candidate-verification': ('Versi kandidat yang sama', 'situs lama', 'bukan bukti'),
    'manual-open': ('OPEN', 'manual'),
}

class ReleaseCopyParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.in_section = False
        self.section_count = 0
        self.hidden_section = False
        self.current_gate = None
        self.gates = []
        self.text = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'section' and attrs.get('id') == 'releaseGateNote':
            self.in_section = True
            self.section_count += 1
            self.hidden_section |= 'hidden' in attrs or attrs.get('aria-hidden') == 'true'
        if self.in_section and tag == 'li':
            self.current_gate = [attrs.get('data-release-gate', ''), [], 'hidden' in attrs or attrs.get('aria-hidden') == 'true']
            self.gates.append(self.current_gate)

    def handle_data(self, text):
        if self.in_section:
            self.text.append(text)
            if self.current_gate is not None:
                self.current_gate[1].append(text)

    def handle_endtag(self, tag):
        if tag == 'li':
            self.current_gate = None
        if tag == 'section':
            self.in_section = False


def validate_release_gate_copy(html):
    parser = ReleaseCopyParser()
    parser.feed(html)
    errors = []
    if parser.section_count != 1 or parser.hidden_section:
        errors.append('release explanation must have one visible releaseGateNote section')
    keys = [row[0] for row in parser.gates]
    if len(keys) != len(RELEASE_GATES) or set(keys) != set(RELEASE_GATES):
        errors.append('release explanation must include all six distinct release requirements')
    for key, fragments, hidden in parser.gates:
        text = ' '.join(' '.join(fragments).split()).casefold()
        if hidden or any(term.casefold() not in text for term in RELEASE_GATES.get(key, ())):
            errors.append(f'release requirement is hidden or incomplete: {key}')
    text = ' '.join(' '.join(parser.text).split()).casefold()
    for statement in ('tahap lamaran final tetap HOLD', 'pengiriman minat bukan aktivasi akses beta'):
        if statement.casefold() not in text:
            errors.append(f'release explanation must preserve: {statement}')
    return errors
