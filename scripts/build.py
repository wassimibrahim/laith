"""Copy only publishable static assets. No source code, secrets or local notes in Pages."""
import shutil, hashlib
from pathlib import Path
root=Path(__file__).resolve().parents[1]
dest=root/'dist'
if dest.exists(): shutil.rmtree(dest)
dest.mkdir()
for file in ('index.html',): shutil.copy2(root/file,dest/file)
for directory in ('app','data','reports'): shutil.copytree(root/directory,dest/directory)
revision=hashlib.sha256(b''.join(p.read_bytes() for p in sorted((root/'app').glob('*')))).hexdigest()[:12]
app=dest/'app/app.js'
app.write_text(app.read_text().replace('?v=2', '?v='+revision))
index=dest/'index.html'
index.write_text(index.read_text().replace('?v=2', '?v='+revision))
(dest/'.nojekyll').touch()
print(f'Built {dest}')
