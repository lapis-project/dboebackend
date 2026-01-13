# API examples

see also 
* https://dboe-backend.acdh-dev.oeaw.ac.at/api/schema/swagger-ui/
* https://dboe-backend.acdh-dev.oeaw.ac.at/api/?format=json
* https://dboe-backend.acdh-dev.oeaw.ac.at/data-model

be aware that the swagger-ui is automatically derived from the datamodel and most likely needs some manual curation

## authentication
via auth-token

### get-auth-token

```JavaScript
const options = {
  method: 'POST',
  headers: {'Content-Type': 'application/json', 'User-Agent': 'insomnia/12.2.0'},
  body: '{"password":"password","username":"username"}'
};

fetch('https://dboe-backend.acdh-dev.oeaw.ac.at/api-token-auth', options)
  .then(response => response.json())
  .then(response => console.log(response))
  .catch(err => console.error(err));

  // response
  {
	"token": "sometoken"
  }
```

## collections

### collection list view

```JavaScript
const options = {method: 'GET', headers: {'User-Agent': 'insomnia/12.2.0'}};

fetch('https://dboe-backend.acdh-dev.oeaw.ac.at/api/collections', options)
  .then(response => response.json())
  .then(response => console.log(response))
  .catch(err => console.error(err));
```

### collection detail view

```JavaScript
const options = {
  method: 'GET',
  headers: {
    'User-Agent': 'insomnia/12.2.0',
  }
};

fetch('https://dboe-backend.acdh-dev.oeaw.ac.at/api/collections/36', options)
  .then(response => response.json())
  .then(response => console.log(response))
  .catch(err => console.error(err));
```

### create new collection

```JavaScript
const options = {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'User-Agent': 'insomnia/12.2.0',
    Authorization: 'Token sometoken'
  },
  body: '{"title":"sumsibumsi","beleg":["d144_153_qdbn-d16e1057","d144_153_qdbn-d16e107","d144_153_qdbn-d16e1080"]}'
};

fetch('https://dboe-backend.acdh-dev.oeaw.ac.at/api/collections/', options)
  .then(response => response.json())
  .then(response => console.log(response))
  .catch(err => console.error(err));
```

### update existing collection
```JavaScript
const options = {
  method: 'PATCH',
  headers: {
    'Content-Type': 'application/json',
    'User-Agent': 'insomnia/12.2.0',
    Authorization: 'Token sometoken'
  },
  body: '{"beleg":["d144_153_qdbn-d16e1057"],"title":"created vi insomnia"}'
};

fetch('https://dboe-backend.acdh-dev.oeaw.ac.at/api/collections/45630/', options)
  .then(response => response.json())
  .then(response => console.log(response))
  .catch(err => console.error(err));
```

## belege
replacing Es_Documents

### beleg list view

```JavaScript
const options = {method: 'GET', headers: {'User-Agent': 'insomnia/12.2.0'}};

fetch('https://dboe-backend.acdh-dev.oeaw.ac.at/api/belege-elastic-search/', options)
  .then(response => response.json())
  .then(response => console.log(response))
  .catch(err => console.error(err));
```

### belege detail view

```JavaScript
const options = {method: 'GET', headers: {'User-Agent': 'insomnia/12.2.0'}};

fetch('https://dboe-backend.acdh-dev.oeaw.ac.at/api/belege-elastic-search/', options)
  .then(response => response.json())
  .then(response => console.log(response))
  .catch(err => console.error(err));
```

### belege-filter-by-collection

```JavaScript
const options = {method: 'GET', headers: {'User-Agent': 'insomnia/12.2.0'}};

fetch('https://dboe-backend.acdh-dev.oeaw.ac.at/api/belege-elastic-search?collection=1564', options)
  .then(response => response.json())
  .then(response => console.log(response))
  .catch(err => console.error(err));
```

### update beleg

Adding, deleting of tags works with key `[modify_tag]` which excpects the primary keys of the tags

```JavaScript
const options = {
  method: 'PATCH',
  headers: {
    'Content-Type': 'application/json',
    'User-Agent': 'insomnia/12.2.0',
    Authorization: 'Token ffce9a31e22aca2c4b666347b935cf9a93dae7b1'
  },
  body: '{"hl":"Puse (geändert)","modify_tag":[141,142,143]}'
};

fetch('https://dboe-backend.acdh-dev.oeaw.ac.at/api/belege-elastic-search/b120_qdbn-d16e2/', options)
  .then(response => response.json())
  .then(response => console.log(response))
  .catch(err => console.error(err));

// returns the full object
```

## Tags
Tags are n:n connected to Belege

### tag list view

```javascript
const options = {method: 'GET', headers: {'User-Agent': 'insomnia/12.2.0'}};

fetch('https://dboe-backend.acdh-dev.oeaw.ac.at/api/tags', options)
  .then(response => response.json())
  .then(response => console.log(response))
  .catch(err => console.error(err));
```

### filter tags by beleg

```javascript
const options = {method: 'GET', headers: {'User-Agent': 'insomnia/12.2.0'}};

fetch('https://dboe-backend.acdh-dev.oeaw.ac.at/api/tags?belege=f236_qdb-d1e36765', options)
  .then(response => response.json())
  .then(response => console.log(response))
  .catch(err => console.error(err));
```

### tag detail view

```javascript
const options = {method: 'GET', headers: {'User-Agent': 'insomnia/12.2.0'}};

fetch('https://dboe-backend.acdh-dev.oeaw.ac.at/api/tags', options)
  .then(response => response.json())
  .then(response => console.log(response))
  .catch(err => console.error(err));
```

### tag create view

```javascript
const options = {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'User-Agent': 'insomnia/12.2.0',
    Authorization: 'Token asdfadsfsafs'
  },
  body: '{"name":"Sumsiisthebest","color":"blue"}'
};

fetch('https://dboe-backend.acdh-dev.oeaw.ac.at/api/tags/', options)
  .then(response => response.json())
  .then(response => console.log(response))
  .catch(err => console.error(err));

// returns

{
	"id": 7842,
	"name": "Sumsiisthebest",
	"url": "https://dboe-backend.acdh-dev.oeaw.ac.at/api/tags/7842/",
	"color": "blue",
	"meta": null
}
```

### tag update view

```javascript
const options = {
  method: 'PATCH',
  headers: {
    'Content-Type': 'application/json',
    'User-Agent': 'insomnia/12.2.0',
    Authorization: 'Token asdfsdafdsafds'
  },
  body: '{"name":"but hansi is better","color":"blue"}'
};

fetch('https://dboe-backend.acdh-dev.oeaw.ac.at/api/tags/7842/', options)
  .then(response => response.json())
  .then(response => console.log(response))
  .catch(err => console.error(err));

// returns
{
	"id": 7842,
	"name": "but hansi is better",
	"url": "https://dboe-backend.acdh-dev.oeaw.ac.at/api/tags/7842/",
	"belege_count": 0,
	"color": "blue",
	"meta": null,
	"belege_ids": [
		null
	]
}
```

## Siglen

### siglen list view

```javascript
const options = {method: 'GET', headers: {'User-Agent': 'insomnia/12.2.0'}};

fetch('https://dboe-backend.acdh-dev.oeaw.ac.at/api/siglen/', options)
  .then(response => response.json())
  .then(response => console.log(response))
  .catch(err => console.error(err));
```

### filter siglen list view (by kind and name)

```javascript
const options = {method: 'GET', headers: {'User-Agent': 'insomnia/12.2.0'}};

fetch('https://dboe-backend.acdh-dev.oeaw.ac.at/api/siglen/?kind=ort&name=im', options)
  .then(response => response.json())
  .then(response => console.log(response))
  .catch(err => console.error(err));
```

### siglen detail view

```javascript
const options = {method: 'GET', headers: {'User-Agent': 'insomnia/12.2.0'}};

fetch('https://dboe-backend.acdh-dev.oeaw.ac.atapi/siglen/1A.1a01/', options)
  .then(response => response.json())
  .then(response => console.log(response))
  .catch(err => console.error(err));
```

### sigle create

```javascript
const options = {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'User-Agent': 'insomnia/12.2.0',
    Authorization: 'Token asfsdfasf'
  },
  body: '{"sigle":"T2","kind":"bl","name":"Südtirol"}'
};

fetch('https://dboe-backend.acdh-dev.oeaw.ac.at/api/siglen/', options)
  .then(response => response.json())
  .then(response => console.log(response))
  .catch(err => console.error(err));
```

### sigle update

```javascript
const options = {
  method: 'PATCH',
  headers: {
    'Content-Type': 'application/json',
    'User-Agent': 'insomnia/12.2.0',
    Authorization: 'Token asfsdfasf'
  },
  body: '{"sigle":"T2","kind":"gr","name":"Südtirol west","bl":"1A"}'
};

fetch('https://dboe-backend.acdh-dev.oeaw.ac.at/api/siglen/T2/', options)
  .then(response => response.json())
  .then(response => console.log(response))
  .catch(err => console.error(err));
```