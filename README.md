# ACA-PY - AFJ Interop

This project enables quick, automated, and hackable testing interactions between ACA-Py and AFJ.

This is heavily inspired by the [ACA-Py Minimal Example][AME] project as well as the [Aries Agent Test Harness][AATH].

The goal of this project is to be able to quickly iterate on changes made to either ACA-Py or AFJ to validate interoperability.

[AME]: https://github.com/Indicio-tech/acapy-minimal-example
[AATH]: https://github.com/hyperledger/aries-agent-test-harness

## How it works

ACA-Py has a built in Admin API that it presents over an HTTP REST interface. AFJ does not have a built in Admin style API but there is an extension available. Unforunately, at the time of this project's creation, the REST extension is not up to date with the most recent version of AFJ. To work around this, I have thrown together a minimal JSON-RPC over TCP API. This API is not intended to be generally consumable. I intend to only add methods to it as I have reason to test them.

The [`docker-compose.yml`](./docker-compose.yml) script is the key entrypoint. To run the current set of tests:

```sh
$ docker-compose build
$ docker-compose run runner
$ docker-compose down -v
```

The runner is running `pytest`. The usual arguments apply; e.g.:

```sh
$ docker-compose run runner -k oob --pdb -x
```
