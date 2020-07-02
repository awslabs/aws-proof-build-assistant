# AWS Proof Assistant

## Testing

The testing approach for AWS Proof Assistant involves running the tool on various AWS projects included as submodules (each submodule corresponds to a test case). 
The test suite simply runs the tool on each submodule and AWS Proof Assistant's built-in data validator ensure that the internal JSON representation is well-formed. 
Currently, there are no tests pertaining to the generation of `Makefile`s.

## Included Submodules

* [S2N](https://github.com/awslabs/s2n)
* [AWS-C-Common](https://github.com/awslabs/aws-c-common)