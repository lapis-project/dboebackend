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