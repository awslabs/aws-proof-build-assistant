# AWS Proof Assistant

## Overview

AWS Proof Assistant automatically finds build-related information such as *file dependencies*, *included directories* and *defines* for source files within a `c` code base.
It accumulates this information inside an internal JSON representation, which is used to generate a `Makefile` containing all the relevant information *for a given source file*.
AWS Proof Assistant simplifies the task of proof developers by automatically generating a ready-to-use `Makefile` containing information that developers previously had to find manually.
In order to use the generated `Makefile`, developers must simply include it in another custom (and possibly trivial) `Makefile` and run `make` on it.
It's ease of use makes AWS Proof Assistant ideal for local proof implementation and building as well as part of CI.

## Requirements

* Python 3
* [Cmake](https://cmake.org/) : 
  * `apt-get install cmake`
  * `brew install cmake`
* [Ninja](https://ninja-build.org/) : 
  * `apt-get install ninja-build`
  * `brew install ninja`
* [Cflow](https://www.gnu.org/software/cflow/) : 
  * `apt-get install cflow`
  * `brew install cflow`
* [Dataclasses](https://pypi.org/project/dataclasses/) : 
  * `pip3 install dataclasses`
* [Voluptuous](https://pypi.org/project/voluptuous/)
  * `pip3 install voluptuous`
