# AnimeAttire Release Commands

The repository already contains a `.git` directory in the current workspace. If starting from a fresh folder, initialize it first:

```powershell
git init
```

Add the GitHub remote:

```powershell
git remote add origin https://github.com/Zeronez/cloth_web_site.git
```

If the remote already exists, update it:

```powershell
git remote set-url origin https://github.com/Zeronez/cloth_web_site.git
```

Create the first phase commit:

```powershell
git add .
git commit -m "chore: initialize AnimeAttire platform architecture"
```

Push to `main`:

```powershell
git branch -M main
git push -u origin main
```
