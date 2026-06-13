Set-Location 'C:\Users\kitap\.openclaw\workspace\live2d-fork'
git add build_pages_dist.py
git diff --cached --stat
git commit -m 'fix(csp): add cdn.jsdelivr.net to script-src + connect-src' -m 'esm.run 301-redirects to cdn.jsdelivr.net when fetching web-llm ES module. CSP must allow the final URL not just the entry URL.' 2>&1 | Select-Object -First 5
