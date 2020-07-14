# AWS Proof Build Assistant

## Project Description

AWS Proof Build Assistant automatically extracts build information needed to build proofs.
The tool then generates a proof-specific `Makefile` that developers can include in their own proof `Makefile`s. 
This significantly simplifies proof development and keeps proof builds consistent with code builds as the source tree evolves.
An example of a `Makefile` generated by AWS Proof Build Assistant is shown below:

    SRCDIR = /path/to/source/dir
    HELPERDIR = /path/to/helper/dir

    DEFINES += -DS2N_HAVE_EXECINFO
    DEFINES += -DS2N_NO_PQ_ASM
    DEFINES += -D_POSIX_C_SOURCE=200809L

    INCLUDES += -I$(SRCDIR)
    INCLUDES += -I$(SRCDIR)/api

    DEPENDENCIES += $(HELPERDIR)/source/make_common_datastructures.c
    DEPENDENCIES += $(HELPERDIR)/source/proof_allocators.c
    DEPENDENCIES += $(SRCDIR)/stuffer/s2n_stuffer.c
    DEPENDENCIES += $(SRCDIR)/utils/s2n_blob.c

## Repository Overview

* **Source Code**: AWS Proof Build Assistant is implemented in a single python script, [`arpa`](placeholderarpa).
* **Testing**: Tests can be found in the [`test/`](placeholder/test) directory. Testing the AWS Proof Build Assistant involves checking the well-formedness of generated JSON files.
* **Documentation**: Documentation can be found in the [`doc/`](placeholder/doc) directory which contains artifacts that can be built using `make` to generate an `index.html`.

## Requirements

* Python 3
* [Cmake](https://cmake.org/) : 
  * `apt-get install cmake`
  * `brew install cmake`
* [GNU cflow](https://www.gnu.org/software/cflow/) : 
  * `apt-get install cflow`
  * `brew install cflow`
* [Voluptuous](https://pypi.org/project/voluptuous/)
  * `python3 -m pip install voluptuous`