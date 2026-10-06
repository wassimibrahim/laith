"""Copy only publishable static assets. No source code, secrets or local notes in Pages."""
import shutil
from pathlib import Path
root=Path(__file__).resolve().parents[1]
dest=root/'dist'
if dest.exists(): shutil.rmtree(dest)
dest.mkdir()
for file in ('index.html',): shutil.copy2(root/file,dest/file)
for directory in ('app','data','reports'): shutil.copytree(root/directory,dest/directory)
(dest/'.nojekyll').touch()
print(f'Built {dest}')
