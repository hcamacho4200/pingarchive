# merge to main from feature branch
- bin/pre-commit-checks.sh
- git checkout main
- git pull - to make sure main is updated locally
- git merge --squash <branch_name>

- GO
brew install golandci-lint
