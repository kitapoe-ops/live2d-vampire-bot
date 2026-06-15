#!/usr/bin/env python3
import sys, codecs
sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer)

with open('widget.html', 'r', encoding='utf-8', errors='replace') as f:
    content = f.read()

print('File loaded, size:', len(content))

# Find title
t1 = content.find('<title>')
t2 = content.find('</title>')
print('Title:', repr(content[t1:t2+8]))

# Find micBtn setAttribute
m1 = content.find("micBtn.setAttribute('aria-label'")
print('micBtn aria-label:', repr(content[m1:m1+150]))

# Count literal ? chars
print('Literal ? count (U+003F):', content.count('\u003f'))

# Show a few lines with ?
lines_with_q = [(i+1, line) for i, line in enumerate(content.split('\n')) if '\u003f' in line]
print(f'\nLines with literal ?: {len(lines_with_q)}')
for ln, line in lines_with_q[:5]:
    print(f'  Line {ln}: {line[:100]}')
