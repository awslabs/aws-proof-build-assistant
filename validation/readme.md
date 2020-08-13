# AWS Proof Build Assistant

## Validation Approach

The validation approach for AWS Proof Build Assistant is implemented for CMBC Proof suites.
It allows to compare the build information found by AWS Proof Build Assistant to the build information currently found in existing CBMC Proof Makefiles.
The approach involves the following steps:
1. Generate a _goto program_ for the existing CBMC Proof build specification (Makefile).
2. Generate a _goto program_ using the build information provided by AWS Proof Build Assistant.
   1. Use AWS Proof Build Assistant to generate build information for the CBMC Proof under test.
   2. Replace existing build information by the build information generated in the previous step.
   3. Generate a _goto program_ using the newly included build information.
3. Compare the _goto programs_ obtained in steps 1 and 2 with each other and evaluate the results.

To obtain the _goto program_, this approach uses the `cbmc --show-goto-functions` command, which emmits a textual representation of the proof specification. \
_Goto programs_ are compared using a simple textual `diff`.

## Running the Validation

Users may run the validation approach using two configurations:
* **Manual Override Configuration**: 
In this configuration, users are allowed to override any validation run that results in a failure. 
Such a configuration is implemented because in some cases, the two generated _goto programs_ are syntactically different despite being semantically equivalent. 
For such cases, automating the validation approach would incorrectly consider the run as a failure. 
Users are thus given the opportunity to manually override such cases to provide more precise validation results.

* **Automated Validation Configuration (Default)**: 
In this configuration, the validation approach is fully automated.
For known proofs where failures must be overridden, as discussed above, users may list them within a file that is added through the `-o` flag.
For these proofs, failures at validation-time will be automatically overridden by successes.
If the `-o` flag is not specified, no proof failures will be overridden

In order to run the validation for a given CBMC test suite, you must run the following command:

`./arpa-test.sh PROOFS_SOURCE_DIR [-m | -o FILE]`

  * `PROOFS_SOURCE_DIR`
    * Directory containing all the CBMC Proofs
  * `-m, --manual-override`
    * Enable the manual override configuration
  * `-o FILE, --override-proofs FILE`
    * Points to a file that contains a list of proofs to be overridden automatically


## Current Assumptions

The current implementation of the validation approach makes the following assumptions:
* The provided proof source directory (`PROOFS_SOURCE_DIR`) is structures as follows:
    ``` 
    PROOF_SOURCE_DIR
    ├── ...
    ├── cbmc_proof_dir_0
    │   ├── Makefile
    │   └── cbmc_proof_dir_0_harness.c
    ├── cbmc_proof_dir_1
    │   ├── Makefile
    │   └── cbmc_proof_dir_1_harness.c
    └── ...
    ```
* The CBMC proof harness is named as follows: `"<PARENT DIR NAME>_harness.c"`


## Future Works

Future works involve the following:
* Generalize with respect to the current assumptions
* Output a JSON log instead of the current textual representation
* Replace the validation script by a Python script
* Generalize the diff between generated build information and existing build information.
  * See the `grep_out` variable in the `get_deps` function. The grep command may not be necessary in this case.
