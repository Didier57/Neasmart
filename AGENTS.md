# AGENTS.md

## Release workflow (automatic)

After finishing any code change, automatically perform the full release
workflow below, without waiting to be asked:

1. Bump `"version"` in `custom_components/neasmart/manifest.json` using
   semantic versioning (patch for fixes, minor for features, major for
   breaking changes).
2. Add a matching entry at the top of `CHANGELOG.md`:
   `## [x.y.z] - YYYY-MM-DD`, with a `### Ajouté` / `### Modifié` /
   `### Corrigé` subsection as appropriate. Keep the link references at the
   bottom of the file up to date.
3. Stage the intended files only and commit with a concise message matching
   the existing repo style (`feat:`, `fix:`, `docs:`, `chore:` ...).
4. Push to `origin` (`main`).
5. Create the GitHub release with `gh release create vX.Y.Z` and a short
   release note.

Only skip a step if it truly cannot be done (for example no changes to
release). Do not bump the version for documentation-only changes unless a
release is still expected.

## Project

- Integration name: Nea Smart, HACS custom integration for Home Assistant.
- Domain: `neasmart`. Source: `custom_components/neasmart/`.
- Lint: Ruff (config in `pyproject.toml`). Run Ruff before committing.
- Remote: `origin` -> https://github.com/Didier57/Neasmart.git (branch `main`).
