"""Catch mismatched explicit closing tags in the maintained public HTML sources."""
from html.parser import HTMLParser
from pathlib import Path

VOID = set('area base br col embed hr img input link meta param source track wbr'.split())
class StructureParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.stack = []
        self.errors = []
    def handle_starttag(self, tag, attrs):
        if tag not in VOID:
            self.stack.append((tag, self.getpos()[0]))
    def handle_startendtag(self, tag, attrs):
        pass
    def handle_endtag(self, tag):
        if tag in VOID:
            return
        if not self.stack or self.stack[-1][0] != tag:
            self.errors.append(f'line {self.getpos()[0]}: unexpected </{tag}>, open={self.stack[-1:] or "none"}')
            # Continue checking after the closest matching ancestor.
            indexes=[i for i,item in enumerate(self.stack) if item[0]==tag]
            if indexes:self.stack=self.stack[:indexes[-1]]
        else:
            self.stack.pop()

if __name__ == '__main__':
    root=Path(__file__).resolve().parents[1]
    files=list((root/'docs').glob('*.html'))
    errors=[]
    for file in files:
        parser=StructureParser();parser.feed(file.read_text(encoding='utf-8-sig'))
        errors.extend(f'{file.name}: {message}' for message in parser.errors)
        errors.extend(f'{file.name}: unclosed <{tag}> at line {line}' for tag,line in parser.stack)
    if errors:
        print('HTML_STRUCTURE_FAIL\n'+'\n'.join(errors));raise SystemExit(1)
    print(f'HTML_STRUCTURE_PASS files={len(files)}')
