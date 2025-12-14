import zipfile, os, sys
files = ['services/google_credentials.json','instance/config.py']
for f in files:
    if not os.path.exists(f):
        print('Missing:', f)
        sys.exit(2)
with zipfile.ZipFile('sensitive_files.zip','w', compression=zipfile.ZIP_DEFLATED) as z:
    for f in files:
        z.write(f, arcname=f)
print('Created sensitive_files.zip')
