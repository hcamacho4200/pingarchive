# check alembic
alembic current

# create new schema revision
alembic revision --autogenerate -m "message/notes"
alembic revision --autogenerate -m "initial schema" --rev-id 001

# apply revision(s)
alembic upgrade head

# merge to main from feature branch
- bin/pre-commit-checks.sh
- git checkout main
- git pull - to make sure main is updated locally
- git merge --squash <branch_name>

- GO
brew install golandci-lint
