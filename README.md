<div align="center">

# Federation API

[![Coverage Status](https://coveralls.io/repos/github/neurobagel/federation-api/badge.svg?branch=main)](https://coveralls.io/github/neurobagel/federation-api?branch=main)

</div>

Please refer to our [**official documentation**](https://neurobagel.org/federate/) for more information on Neurobagel federation and how to use the federation API.

## Launching the API
### 1. Set the local Neurobagel nodes to federate over
Create a configuration JSON file called `local_nb_nodes.json` containing the URLs and (arbitrary) names of the local nodes you wish to federate over.
Each node must be denoted by a dictionary `{}` with two key-value pairs: `"NodeName"` for the name of the node, and `"ApiURL"` for the url of the API exposed for that node. 
Multiple nodes must be wrapped in a list `[]`.

This repo contains a [template `local_nb_nodes.json`](/local_nb_nodes.json) file that you can edit.

Examples:  

`local_nb_nodes.json` with one local node API running on `http://localhost:8000`
```json
{
    "NodeName": "Local graph",
    "ApiURL": "http://host.docker.internal:8000"
}
```
_**NOTE:** If the local node API(s) you are federating over is running on the same host machine as the federation API (e.g., the node API itself is accessible at `http://localhost:XXXX`), in `local_nb_nodes.json` you **must** replace `localhost` with `host.docker.internal` in the local node's `"ApiURL"`, as shown above._

`local_nb_nodes.json` with two local nodes
```json
[
    {
        "NodeName": "Local graph 1",
        "ApiURL": "http://host.docker.internal:8000"
    },
    {
        "NodeName": "Local graph 2",
        "ApiURL": "http://192.168.0.1"
    }
]
```

### 2. Run the Docker container
```bash
docker pull neurobagel/federation_api

# Run this next command in the same directory where your `local_nb_nodes.json` file is located
docker run -d -v ${PWD}/local_nb_nodes.json:/usr/src/local_nb_nodes.json:ro \
    --add-host=host.docker.internal:host-gateway \
    --name=federation -p 8080:8000 neurobagel/federation_api
```
NOTE: You can replace the port number `8080` for the `-p` flag with any port on the host you wish to use for the API.
