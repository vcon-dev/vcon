# The Home Repo for vCons and the Conserver

## Introduction
vCons are PDFs for human conversations, defining them so they can be shared, analyzed and secured. The Conserver is a domain specific data platform based on vCons, converting the raw materials of recorded conversations into self-serve data sources for any team. The Conserver represents the most modern set of tools for data engineers to responsibly and scalably use customer conversations in data pipelines. 

The Vcon library consists of two primary components:

  * The Python Vcon package for constructing and operating on Vcon objects
  * The Conserver for storing, managing and manipulating Vcon objects and operation streams on Vcon objects

## Table of Contents

  + [Presentations, Whitepapers and Tutorials](#presentations-whitepapers-and-tutorials)
  + [vCon Library Quick Start for Python](https://github.com/vcon-dev/vcon/wiki/Library-Quick-Start)
  + [Testing the Vcon Package](#testing-the-vcon-package)
  + [Testing the conserver](#testing-the-conserver)

## Presentations, Whitepapers and Tutorials

See the [Birds of a Feather session at IETF 116, Yokohama](https://youtu.be/EF2OMbo6Qj4)

See the [presentation at TADSummit](https://youtu.be/ZBRJ6FcVblc)

See the [presentation at IETF](https://youtu.be/dJsPzZITr_g?t=243)

See the [presentation at IIT](https://youtu.be/s-pjgpBOQqc)

Read the [IETF draft proposal](https://datatracker.ietf.org/doc/html/draft-petrie-vcon-01)

Read the [white paper](https://docs.google.com/document/d/1TV8j29knVoOJcZvMHVFDaan0OVfraH_-nrS5gW4-DEA/edit?usp=sharing)

See the [key note proposal for vCons](https://blog.tadsummit.com/2021/12/08/strolid-keynote-vcons/).


## Testing the Vcon Package
A suite of pytest unit tests exist for the Vcon package in: [tests](tests)

These can be run using the following command in the current directory:

    pytest -v -rP tests


Please also run separately the following unit test as it will check for spurious stdout from the Vcon package that will likely cause the CLI to break:

    pytest -v -rP tests/test_vcon_cli.py

Note: These errors may not show up when you run test_vcon_cli.py with the rest of the unit tests as some stdout may only occur when the Vcon package is first imported and may not get trapped/detected by other unit tests.


## Testing the conserver
A suite of pytest unit tests exist for the conserver in: [server/tests](server/tests)

Running and testing the conserver requires a running instance of Redis.
Be sure to create and edit your server/.env file to reflect your redis server address and port.
It can be generated like the following command line:

    cat <<EOF>.env
    #!/usr/bin/sh
    export AWS_BUCKET=vcon-storage
    export AWS_KEY_ID=aaaaaaaaaaaaaaa
    export AWS_SECRET_KEY=bbbbbbbbbbb
    export DEEPGRAM_KEY=ccccccccccccc
    export ENV=dev
    export HOSTNAME=http://0.0.0.0:8000
    export REDIS_URL=redis://172.17.0.4:6379
    #export MONOREPO_DATABASE_URL=postgresql://password:userid@your.postgres.domain.com:5432/postgres
    EOF

The unit tests for the conserver can be run using the following command in the server directory:

    source .env
    pytest -v -rP tests

