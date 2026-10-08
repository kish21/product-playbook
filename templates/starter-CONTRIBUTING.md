# Contributing to {product}

1. Follow `README.md` to install the tools and the dependencies from the lockfile.
2. Copy `.env.example` to `.env` and replace every `CHANGE_ME` value; the app refuses to start while one remains.
   Never commit `.env`.
3. Before adding a file, read `STRUCTURE.md`, "Where does a new file go?". A new folder updates `STRUCTURE.md`
   in the same commit.
4. Run {check} before every push; the commit hooks run the linter, the secret scan and the structure check.
5. Settings go through the one config loader; secrets live in `.env`, never in a code file.{prompts}
6. One small pull request per change, with its tests, and one line under `[Unreleased]` in `CHANGELOG.md`.
