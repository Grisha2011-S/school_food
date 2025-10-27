import re
import sys
p='c:\\Users\\Game_PC\\Documents\\__SITE__\\flask_app.py'
with open(p,'r', encoding='utf-8') as f:
    lines=f.readlines()

issues=[]
for i,l in enumerate(lines, start=1):
    # detect tabs
    if '\t' in l:
        issues.append((i, 'TAB', l.rstrip('\n')))
    else:
        m=re.match(r'^( +)\S', l)
        if m:
            spaces=len(m.group(1))
            # if spaces not multiple of 4, flag
            if spaces%4!=0:
                issues.append((i, f'SPACES({spaces})', l.rstrip('\n')))

print('Checked file:', p)
print('Total lines:', len(lines))
if not issues:
    print('No indentation issues found (no tabs, spaces multiple of 4).')
else:
    print('Found issues:')
    for it in issues[:200]:
        print(f'Line {it[0]:4d}: {it[1]}: {it[2][:200]!s}')

if issues:
    sys.exit(2)
else:
    sys.exit(0)
