[![Test](https://github.com/lapis-project/dboebackend/actions/workflows/test.yml/badge.svg)](https://github.com/lapis-project/dboebackend/actions/workflows/test.yml)
[![flake8 Lint](https://github.com/lapis-project/dboebackend/actions/workflows/lint.yml/badge.svg)](https://github.com/lapis-project/dboebackend/actions/workflows/lint.yml)
[![workflows starter](https://github.com/lapis-project/dboebackend/actions/workflows/starter.yaml/badge.svg)](https://github.com/lapis-project/dboebackend/actions/workflows/starter.yaml)
# dboebackend

REST-Service to expose, curate and enrich DBÖ-Belegzettel

## Technical setup

The application is implemented using Python, [Django](https://www.djangoproject.com/) and [Django Rest Framework](https://www.django-rest-framework.org/).
It stores the data in PostgreSQL database using PostgreSQL's native XML field to store TEI/XML modelled Belegzettel. See [sample_entries.xml](sample_entries.xml).

### install

The project uses [uv](https://docs.astral.sh/uv/).

- clone the repo
- create a PostgreSQL database `dboebackend`
- provide database credentials e.g. via

```shell
DATABASE_URL=postgres://dboeannotation:dboeannotation@localhost:5432/dboeannotation
```

- run the usual django-commands

```shell
uv run manage.py migrate
uv run manage.py runserver
```

### data import

In case you have access to the DBOE-TEI/XML files you can populate the database by adapting [belege/management/commands/import.py](belege/management/commands/import.py) and running

```shell
uv run manage.py import
```

After this is done, run

```shell
uv run manage.py update
```

populates OpenSearch index (and dump data as json) (default batch-size is 5000)
```shell
uv run manage.py index
uv run manage.py index --batch-size 200
uv run manage.py index --batch-size 200 --dump
```

## implementation details

### XMLField

The project implements a custom [XMLField](belege/fields.py) to store valid XML data into PostgreSQL's XML Field. This ensures well formed XML snippets.

### custom properties for models fields

It is possible to declare custom properties to Django's model fields, e.g. like

```python
definition = models.TextField(
    blank=True, null=True, verbose_name="definition"
).set_extra(xpath="./tei:def", node_type="text")
```

### customized save methods for some classes

The classes `Belege` and `Citation` have customized save methods. On save, given some parameters are set, information from the XMLField are extracted and saved in their respective fields.

## Docker

### building the image

```shell
docker build -t dboeannotation:latest .
```

### running the image

```shell
docker run -it --network="host" --rm --env-file .env dboeanntoation:latest
```


