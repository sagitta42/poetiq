# poetiq

Higher level wrapper for poetry for smart install operations and advanced package template creation

```bash
pip install poetiq
```

or for most recent developments:

```bash
pip install git+https://github.com/sagitta42/poetiq.git
```

- [Usage](#usage): command line usage with examples
- [Examples](#examples): examples of templates and functionalities results
- [development notes](#development-notes): notes on how to add new features to `poetiq`

## Usage

```bash
$ poetiq -h
usage: poetiq [-h] {install,add,lock,init,new,update,setup} ...

positional arguments:
  {install,add,lock,init,new,update,setup}
    install             poetry install with advanced options
    add                 poetry add with advanced options
    lock                poetry lock with advanced options
    init                basic no-interaction init
    new                 create new template
    update              update current template as is with new poetiq updates
    setup               setup functionality in existing repo/directory

options:
  -h, --help            show this help message and exit
```

### Install split/local dependencies

```bash
$ poetiq install -h
usage: poetiq install [-h] [--split [DIR]] [--local] package

positional arguments:
  package        Specific package to install in split or local model; otherwise all local/split

options:
  -h, --help     show this help message and exit
  --split [DIR]  Install from split pyproject.toml files (all defined in poetiq.toml or given DIR)
  --local        Install local dependencies defined in poetiq.toml
```

Perform smart poetry install:
- automatically add `--no-root` flag if current directory `pyproject.toml` states `package-mode=false`
- automatically run `poetry lock` if "pyproject.toml changed significantly since poetry.lock was last generated"

Add `--split` flag if you want to install dependencies from multiple `pyproject.toml` files that are part of your codebase (e.g. a web app with separate services). Provide paths to subfolders containing `pyproject.toml` files in `poetiq.toml` file:
```toml
[dependency-groups]
split = [
  "app",
  "db",
]
```

Note: running this way will generate a separate `poetry.lock` file in each provided subdirectory corresponding to each individual `pyproject.toml`, but install all dependencies into the `venv` of your repository (for development mode).

Add `--local` flag if you want to install the dependences in `pyproject.toml` from filepath instead of pyproject information (e.g. a local clone of a dependency, which may be convenient during development)

Provide paths to local dependencies via `poetiq.toml` file. Format:
```toml
[dependency-groups]
local = [
  "my-package @ /path/to/my-package",
  "python-module @ /path/to/my/fork/of/python-module",
]
```
or by running `poetiq add my-package --local /path/to/my-package` (see [Add dependency](#add-dependency) section)

Specify a packge to perform local install with `poetiq install --local my-package` or simply `--local` to perform local install for all dual packages.

See detailed examples in [Install examples](#install-examples)


### Add split/local dependency

```bash
$ poetiq add -h
usage: poetiq add [-h] [--split DIR] [--local PATH] package

positional arguments:
  package       Package source (name, https, git)

options:
  -h, --help    show this help message and exit
  --split DIR   Add to split pyproject.toml file in specified DIR
  --local PATH  Add local dependency to poetiq.toml in given path
```

Running `poetiq add package-name` is equivalent to `poetry add package-name`.

Adding package from a repository, running `poetiq add https://github.com/username/awesome-package` will automatically add `git+` (same for `ssh` hosted `git@...`)

Use `poetiq add awesome-package --split subdir` to add package to `pyproject.toml` and `poetry.lock` in subdirectory of the main project (see [Install](#install) on `poetiq.toml` split dependency group). Note that this will not install the dependency, run `poetiq install --split`.

Use `--local` flag and path to a local clone/repository as `poetiq add package-name --local /path/to/awesome-package` to add local dependency to `poetiq.toml` - see [Install](#install) for `poetiq install --local` usage to handle dual dependencies.

### (Split) poetry lock

```bash
$ poetiq lock -h
usage: poetiq lock [-h] [--split [DIR]]

options:
  -h, --help     show this help message and exit
  --split [DIR]  Update split poetry.lock(s) (all or specified DIR)
```

Running `poetiq lock` is equivalent to `poetry lock`.

Adding `--split` will perform `poetry lock` for each split directory listed in `poetiq.toml` (see above sections for examples).

Specifying directory `--split DIR` will `poetry lock` only in that directory.

### Init template

`poetiq init -h` to init a simple template in current direcotry with most basic no-interaction poetry pyproject init. Will treat current directory name as project name.

### Create template

```bash
$ poetiq new -h
usage: poetiq new [-h] {package,app} ...

positional arguments:
  {package,app}
    package      python package setup
    app          synchronous 3-tier request-response app template setup

options:
  -h, --help     show this help message and exit
```

Main note: `poetry new package-name` complains if directory `package-name` already exists; `poetiq new <template type> project-name` only complains if it is non-empty.

See detailed examples in [Template examples](#templates)

#### package template

```bash
$ poetiq new package -h
usage: poetiq new package [-h] [--no-commit] [--settings] [--progressbar] [--my-base-model] name

positional arguments:
  name             Template/repository name

options:
  -h, --help       show this help message and exit
  --no-commit      Do not commit changes
  --settings       Set up .env Settings class
  --progressbar    Set up progress bar source code
  --my-base-model  Set up MyBaseModel class with tree display() + logger
```

Add `--settings` flag to set up `pydantic_settings` based `Settings` class containing `.env` variables (applies to `package` template only; app template always includes this class / source file)

Add `--progressbar` flag to set up a simple `ProgressBar` util class in a package source file.

#### app template

```bash
$ poetiq new app -h
usage: poetiq new app [-h] [--no-commit] [--db {sqlite,psql,none}] [--pydantic-table] [--dev-sqlite] [--mongodb] name

positional arguments:
  name                  Template/repository name

options:
  -h, --help            show this help message and exit
  --no-commit           Do not commit changes
  --db {sqlite,psql,none}
                        Database type
  --pydantic-table      Set up pydantic-table for alembic migrations
  --dev-sqlite          Development mode switch to SQLite
  --mongodb             Add MongoDB service
```

Add `--db` flag to set up `alembic` migrations and DB of given type (applies to `app` template type only)

Available DB types:
- `sqlite` to set up a local SQLite DB (default)
- `psql` to set up PostgreSQL service in `docker-compose.yml`

Add `--dev-sqlite` flag to set up dual psql/SQLite setup with switch to SQLite via `.env` variables for local development testing.

Add `--mongodb` flag to set up MongoDB service in `docker-compose.yml` and related source files and dependencies in the app code (app only).

### Update template

Run `poetiq update` inside an existing poetiq template to update it after poetiq itself was updated (new functionalities, bugfixes).

The update will create a special separate update branch, run poetiq template setup in it, and then merge the branch into the one you started from. This way, the updates do not all overwrite the changes you made afterwards. Make sure to handle the merge manually anyway, and be able to recover your original setup in case the merge it too complex.

See detailed examples in [Template examples](#templates)

### Set up functionality

Functionality set up in current directory.

If directory is a git repository, will commit changes unless `--no-commit` flag is provided.

See detailed examples in [Functionality setup examples](#functionalities)

```bash
$ poetiq setup -h
usage: poetiq setup [-h] {vscode,gitignore,logger,db} ...

positional arguments:
  {vscode,gitignore,logger,db}
    vscode              vscode setup
    gitignore           gitignore setup
    logger              logger setup
    db                  db setup

options:
  -h, --help            show this help message and exit
```

Usage for standard basic setup types

```bash
$ poetiq setup <type> -h
usage: poetiq setup <type> [-h] [--no-commit]

options:
  -h, --help   show this help message and exit
  --no-commit  Do not commit changes
```

Current basic setups:

- `vscode`: set up `settings.json` and `launch.json` in `.vscode`
- `gitignore`: set up standard python `.gitignore`

#### Logger setup

```bash
$ poetiq setup logger -h
usage: poetiq setup logger [-h] [--no-commit] [--subfolder SUBFOLDER]

options:
  -h, --help            show this help message and exit
  --no-commit           Do not commit changes
  --subfolder SUBFOLDER
```

Additional optional flag `--subfolder` to indicate where logger source file should be set up (default current directory)

#### DB setup

```bash
$ poetiq setup db -h
usage: poetiq setup db [-h] [--no-commit] --db-type {sqlite,psql} [--pydantic-table] [--dev-sqlite]

options:
  -h, --help            show this help message and exit
  --no-commit           Do not commit changes
  --db-type {sqlite,psql}
                        Database type
  --pydantic-table      Set up pydantic-table for alembic migrations
  --dev-sqlite          Development mode switch to SQLite
```

Example:

```bash
poetiq setup db --db psql --dev-sqlite
```

sets up psql DB with dev mode switch to SQLite

## Examples

### Templates

#### `poetiq new package awesome-package --settings --progressbar`

Result

```bash
awesome-package
├── .vscode
│   ├── launch.json # debug test setup
│   └── settings.json # pytest, format on save, pylance, auto-import, ...
├── src
│   └── awesome_package
│       ├── __init__.py # imports * from core.py
│       ├── foo.py # example source file
│       ├── logger.py # log with levels based on .env and color/bold functionalities
│       ├── core.py # everything here is imported in __init__ as core functionality
|       ├── py.typed # empty file that enables import suggestions in IDE
|       ├── progressbar.py # ProgressBar wrapper class if requested
│       └── settings.py # pydantic_settings based Settings class containing .env variables if requested
├── tests
|   ├── __init__.py
│   ├── conftest.py # set up to be able to run tests in dev mode
│   └──  test_unit.py # unit tests of awesome_package.foo and awesome_package.models.MyBaseModel
├── .gitignore # standard comprehensive Python .gitignore
├── .env.template
├── poetry.lock
├── pyproject.toml
├── README.md
└── venv # venv with pyproject.toml dependencies: dotenv; poetry and pytest (dev)
```

#### `poetiq new app awesome-app --db psql --dev-sqlite --mongodb`

Result

```bash
awesome-app
├── .vscode
│   ├── launch.json # debug test setup
│   └── settings.json # pytest, format on save, pylance, auto-import, ...
├── alembic_migrations # migrations for SQLite if requested; adaptation for PostgreSQL coming soon
│   ├── versions
│   ├── env.py # auto DB URL using settings.py - compatible with SQLite/psql via only .env change
│   ├── README
│   └── script.py.mako
├── app
│   ├── api
│   │   ├── routes
│   │   │   └── dummy.py
│   │   └── router.py # main API router that includes dummy router
│   ├── schemas
│   │   └── dummy.py # dummy request and response schemas
│   └── services
│       └── dummy.py # dummy service using dummy core logic
├── core
│   ├── models
│   │   ├── example.py # DeclarativeBase for sqlalchemy session
│   │   └── mongo_document.py
│   ├── db.py # DB session with automatic dual SQLite/psql switch based on .env
│   ├── db_mongo.py # dummy MongoDB client
│   ├── dummy.py # dummy core logic
│   └── mongo_config.py # MongoDB client config using settings.py
├── db
│   └── database.db # initial SQLite DB file, not tracked
├── venv # venv with pyproject.toml dependencies installed: dotenv, fastapi, pydantic, ...
├── .env.template # controls switch from SQLite to psql with just a few variables
├── .gitignore # standard comprehensive Python .gitignore
├── alembic.ini
├── app_info.py # app info extraction from pyproject
├── docker-compose.yml # app, psql, and mongodb services, env variables set based on .env
├── dockerfile # app service dockerfile
├── main.py # main API launcher
├── poetiq.toml.template
├── poetry.lock
├── pyproject.toml
├── README.md
└── settings.py  # pydantic_settings based Settings class containing .env variables for sqlite/psql dual setup and MongoDB; shared by alembic migrations, SQLAlchemy Session, and MongoDB client
```

#### Update template

`poetiq update`

On the first update, will create a branch dedicated to poetiq updates starting from the first commit.

```bash
$ git branch
  dev-poetiq-update
* main
```

The standard setup is run in the update branch, and the differences/additions are committed and merged with the active branch.

```bash
commit cac874d5f2cf07199f00890c4d4cefbb57d3206b (HEAD -> main)
Merge: a01eefc b4bb541
    Merge branch 'dev-poetiq-update'

commit b4bb54109bf78b85618566c3df082128a3f93dd8 (dev-poetiq-update)
    poetiq update
    commit: d68f600af54ae2410557d19a5f72b09ed63aadbe
    message: <last poetiq commit message>

commit a01eefcfe8fff4372c9ad337d40e9ad991b32f9d
    readme update

commit d68f600af54ae2410557d19a5f72b09ed63aadbe
    template made with poetiq
```

### Functionalities

```bash
$ poetiq setup vscode
VSCode update with [poetiq](https://pypi.org/project/poetiq)
├── settings.json
└── launch.json
```

### Install examlpes

Poetiq automatically determines `--no-root` flag analyzing `pyproject.toml` for `package-mode=false`:

```bash
$ poetiq install --local
Local install requested but no dual dependencies found in poetiq.toml
poetiq: poetry install --no-root
Installing dependencies from lock file

No dependencies to install or update
```

Poetiq uninstalls and re-installs dual dependencies:
```bash
$ poetiq install --local
poetiq: poetry install --no-root
Installing dependencies from lock file

No dependencies to install or update
Replacing dual packages with local dependencies
poetiq: pip uninstall python-module
Found existing installation: python-module 2.13.4
Uninstalling python-module-2.13.4:
  Would remove:
    /home/user/path/to/repo/venv/lib/python3.12/site-packages/python-module-2.13.4.dist-info/*
    /home/user/path/to/repo/venv/lib/python3.12/site-packages/python-module/*
Proceed (Y/n)? 

...

poetiq: pip install /path/to/my/fork/of/python-module
Processing /path/to/my/fork/of/python-module

...

Successfully installed python-module-2.14.0a1 ...
```

with `.poetiq.toml`:
```toml
[dependency-groups]
local = [
  "python-module @ /path/to/my/fork/of/python-module",
]
```

## development notes

### implement new independent functionality setup (`setup`)

1. Create new `ActionType` e.g. `ActionType.foo` in `enums`
1. Add `ActionType.foo` to `choices` for `type` argument of the microfunctionality subparser in `add_microfunctionality_arguments()` (`cli/cli.py`)
1. Create setup settings `FooSettings` in `poetiq.settings.setup` inheriting from `BaseSetupSettings` with `type` as `Literal[ActionType.foo]`
1. Add additional settings field if any under `FooSettings` e.g. `field`
1. Create function adding those settings to given CLI parser in `cli/cli.py` e.g. `add_foo_arguments(parser)` utilizing `FooSettings` and `pydantic-parse` to translate them to CLI arguments. Append call to this function under `add_microfunctionality_arguments()`
1. Add `FooSettings` to accepted setup settings ( `settings.options`)
1. Create setup class `FooSetup` in a new source file `poetiq.setup.foo` inheriting from a base setup (e.g. `BaseFunctionalitySetup`, `BaseVenvSetup`, or `BaseDependencySetup` )  with `[FooSettings]` (`Generic`) depending on if setup includes python library dependency setup etc. For convenience, define `__init__()` with `settings=FooSettings()`
1. Define `setup()` method, calling parent `setup()`, and adding specific setup actions for this setup. This method must return `bool` representing whether this setup already existed before.
1. In case of dependency setup, add dependencies in `setup_dependencies()` using `_poetry_add("package-name")`
1. Add `FooSetup` under `ActionSetupClass` enum in `factory`, matching enum name with `ActionType` name (`foo`)

After this, this setup is now usable with `poetiq add foo`

### implement new DB setup

1. Define new `DBType` in `enums` e.g. `DBType.foo`
1. Create DB setup class `FooDBSetup` inheriting from `BaseDBSetup`
1. Define its `setup_db()` method with actions for this DB setup. Return bool representing whether this setup existed before
1. Define DB URL under `db_url` property
1. Add `FooDBSetup` under `DBSetupClass` in `poetiq.setup.db.builder` using the same enum name as defined `DBType` (`foo`)

After this, this setup is now usable with
- `poetiq new awesome-app --db psql`
- `poetiq setup db --db foo`

### `pydantic-parse` adapter

Template and setup settings fields are used to add `argparse` arguments using `pydantic-parse`.

Defined as `ArgModel` and `ArgField` rather than just `BaseModel` and `Field`.
- `default` for `type` is always set
- field type annotation is always set
- field description is always set

### build assets

To run tests locally, need to first run `poetry build` to generate `src/poetiq/_build_assets` (see `build.py`) for non-src assets