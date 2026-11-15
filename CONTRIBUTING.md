# How we change code (5 people, one repo)

**Rule: nobody pushes to `main`. Everything goes through a short branch + pull request.**

## Every time you start working
```bash
git checkout main
git pull                      # get everyone's latest
git checkout -b <you>/<what>  # e.g. sean/infrared-tint
```

## While working (at least every few hours)
```bash
git add -A && git commit -m "what changed"
git pull --rebase origin main # take others' new work now, not in 2 days
git push -u origin HEAD
```
If `pull --rebase` says CONFLICT: open the file, keep both people's lines, `git add <file>`, `git rebase --continue`. Stuck → `git rebase --abort` and ask in the chat.

## When a piece is done
1. Open a pull request into `main` on GitHub.
2. Wait for the green tick (the **check** builds the web app and loads the engine).
3. Merge it yourself. Delete the branch.

Small PRs, merged the same day, cause almost no conflicts. Branches older than a day cause most of them.

## Who owns what (edit others' areas only after telling them)
| Folder | Owner |
|---|---|
| `data/`, `science/` | Yasen + Sean |
| `processing/`, `backend/` | Quirce + Giorgi |
| `web/` | Niklas |

## Never commit
`.env`, keys, passwords, `node_modules/`, `web/dist/`, caches, big zips. Large NASA files stay out of git.
