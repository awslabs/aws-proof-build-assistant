<header id="title">
  <h1>AWS Proof Build Assistant</h1>
  <p id="subtitle">arpa command-line Reference</p>
</header>


AWS Proof Build Assistant automatically finds build-related information such as *file dependencies*, *included directories* and *defines* for source files within a `c` code base.
Users can access the AWS Proof Build Assistant through `arpa`, the command-line interface.
This document serves as a reference for using `arpa` and integrating it into your project.

`arpa` accumulates build information for a complete `c` code base inside an internal JSON representation which is used to generate a `Makefile` containing all the relevant information *for a given source file*.
`arpa` simplifies the task of proof developers by automatically generating a ready-to-use `Makefile` containing information that developers previously had to find manually.
In order to use the generated `Makefile`, developers must simply include it in another custom (and possibly trivial) `Makefile` and run `make` on it.
It's ease of use makes AWS Proof Build Assistant ideal for local proof implementation and building as well as part of CI.

[Source code repository](path/to/aws-proof-assistant)

## Overview
Consider the following `c` file:

    #include "api/s2n.h"
    #include "stuffer/s2n_stuffer.h"
    #include <assert.h>
    #include <cbmc_proof/proof_allocators.h>
    #include <cbmc_proof/make_common_datastructures.h>

    void s2n_stuffer_alloc_harness() {
        struct s2n_stuffer *stuffer = 
            can_fail_malloc(sizeof(*stuffer));
        struct s2n_blob* in = cbmc_allocate_s2n_blob();

        if (s2n_stuffer_init(stuffer, in) == S2N_SUCCESS){
            assert(s2n_stuffer_is_valid(stuffer));
            assert(s2n_blob_is_valid(in));
        };
    }

As any source file in a code base, the above file has source file dependencies. This information can be found through a static analysis tool applied on the entire code base (for this purpose, AWS Proof Build Assistant uses `cflow`, which generates a function-level call graph). 

The above file, along with the source files it depends on, also require certain directories to be included and certain variables to be defined for proper compilation. Compile commands for each source file in a code base are obtained by using the `-DCMAKE_EXPORT_COMPILE_COMMANDS=1` flag when calling `cmake` on the code base.

AWS Proof Build Assistant runs the relevant commands, parses the outputs and gathers all the build information for a specified source file within an easy-to-read and easy-to-integrate `Makefile`. Users can run the following command:

<pre class="command"><code>arpa run                       \
    -ha path/to/file.c            \
    -cc path/to/compile/commands  \
    -r path/to/project/root/dir
</code></pre>

Doing so generates the following `Makefile`, which contains all the relevant build information for the above source file:

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




## Motivation
Although `arpa` is capable of generating valuable `Makefile`s for any source file of a code base, it's main use case is in the context of running CBMC proofs. Generally speaking, running a CBMC proof requires users to create a *harness* (a `c` source file containing the CBMC call) and a corresponding *Makefile*. This `Makefile` should contain all the required build information and should include a `Makefile.common` that contains all the `make` rules. `arpa` is useful in this context as it generates a `Makefile.arpa` that contains all the build information (excluding customizations) that can be included directly in a custom `Makefile`.

`arpa` would be ideal for code bases that already contain CBMC proofs. In this context, `arpa` would be integrated as a submodule inside these code bases and would simplify the development of additional CBMC proofs. Currently, we can envision `arpa` to be integrated in the following five AWS projects: 

* [AWS C Common](https://github.com/awslabs/aws-c-common/)
* [AWS Encryption sdk](https://github.com/aws/aws-encryption-sdk-c)
* [Amazon FreeRTOS](https://github.com/aws/amazon-freertos/)
* [AWS Iot device sdk](https://github.com/aws/aws-iot-device-sdk-embedded-C)
* [S2n](https://github.com/awslabs/s2n/)

<!-- <table style="width:100%">
  <tr>
    <td><a href="https://github.com/awslabs/aws-c-common/">AWS C Common</a></td>
    <td><a href="https://github.com/aws/aws-encryption-sdk-c">AWS Encryption Sdk</a></td>
    <td><a href="https://github.com/awslabs/s2n/">S2n</a></td>
  </tr>
  <tr>
    <td><a href="https://github.com/aws/amazon-freertos/">Aamazon FreeRTOS</a></td>
    <td><a href="https://github.com/aws/aws-iot-device-sdk-embedded-C">AWS Iot Device Sdk</a></td>
  </tr>
</table> -->

## For Proof Writers
In this section, we provide a step-by-step guide designed to help proof developers integrate AWS Proof Build Assistant into their project and use it for implementation of CBMC Proofs:

### Integrating `arpa` into a project
1. Integrate AWS Proof Build Assistant as a submodule:
    1. Inside your git repository, run:  
    <pre class="command"><code>git submodule add 
            https://github.com/path/to/aws/proof/assistant
    </code></pre>
    2. (Optional) Add the submodule root path to `PATH`:  
    <pre class="command"><code>export PATH=path/to/submodule/root/dir:$PATH
    </code></pre>
2. Install the required dependencies listed below:
    * [Cmake](https://cmake.org/) (for tests) - (`apt-get install cmake` or `brew install cmake`)
    * [GNU cflow](https://www.gnu.org/software/cflow/) - (`apt-get install cflow` or `brew install cflow`)
    * [Voluptuous](https://pypi.org/project/voluptuous/) - (`pip3 install voluptuous`)

### Using `arpa` for writing proofs
3. Generate the build files (including the compilation commands):
    * Run `cmake` on the code base using project-specific flags, if necessary:
    <pre class="command"><code>cmake [--project-specific-flags]       \
            -DCMAKE\_EXPORT\_COMPILE\_COMMANDS=1  \
            -B path/to/build/dir               \
            -S path/to/source/root/dir
    </code></pre>
    * Currently, `arpa` can only handle projects that build with `cmake`.

4. Generate the internal representation *JSON* file:
    1. Move to the root directory of the code base :
    <pre class="command"><code>cd path/to/source/root/dir
    </code></pre>
    2. Run `arpa build`:
    <pre class="command"><code>arpa build                                    \
            -cc path/to/build/dir/compile_commands.json 
    </code></pre>
    3. This generates a *JSON* file containing the internal representation used by `arpa` at `path/to/source/root/dir/internal_rep.json`.
5. Generate a `Makefile` for a given proof harness:
    1. Move to the proof directory which contains a harness source file:
    <pre class="command"><code>cd path/to/proof/dir
    </code></pre>
    2. Run `arpa makefile`:
    <pre class="command"><code>arpa makefile                                   \
            -jp path/to/source/root/dir/internal_rep.json 
    </code></pre>
    3. This generates a `Makefile` at `path/to/proof/dir/Makefile.arpa`.
6. Create a simple `Makefile` that calls `Makefile.arpa`:
    1. In the same directory as the harness, create a simple `Makefile` that:
        * contains variable name adaptations (if required)
        * contains variable customizations (if required)
        * includes `Makefile.arpa`
        * includes `Makefile.common`
    2. Such a `Makefile` may resemble the following:
        <pre><code># Variable name adaptation:
        PROJECT\_SPECIFIC\_VAR\_NAME = $(VAR\_NAME\_USED\_BY\_arpa)
        # ex. INC = $(INCLUDES)  
        # Variable customizations:
        CUSTOM\_VAR = CUSTOM_VAL
        # ex. CHECKFLAGS += --bounds-check  
        include path/to/Makefile.arpa
        include path/to/Makefile.common
        </code></pre>
7. Run CBMC:
    1. While in the directory containing the harness and the `Makefile` created in step 4, run `make` to run CBMC. 
    2. You may run a command such as:
    <pre class="command"><code>make report 
    </code></pre>

## Subtool reference

`arpa` consists of three user-facing commands, where one is a combination of the other two commands:
<ul class="command-list">
<li class="cmd"><code>arpa build</code>:<br>
generate a JSON file containing the internal representation used by <code>arpa</code></li>
<li class="cmd"><code>arpa makefile</code>:<br>
generate a `Makefile` containing build information for a given harness</li>
<li class="cmd"><code>arpa run</code>:<br>
run the above commands successively</li>
</ul>

As mentioned, `arpa build` and `arpa makefile` must be used sequentially. However, these commands can be replaced by a single `arpa run` call. Specifically, both of the following code boxes are equivalent:

<pre class="command"><code>arpa run                                      \
    -cc path/to/build/dir/compile_commands.json  \
    -r path/to/source/root/dir
</code></pre>

<pre class="command"><code>arpa build                                    \
    -cc path/to/build/dir/compile_commands.json  \
    -r path/to/source/root/dir
arpa makefile                                   \
    -jp path/to/source/root/dir/internal_rep.json  
</code></pre>

### `arpa build`
    
<pre class="command"><code>arpa build [-h] -cc F [-r DIR] [-jp F]
</code></pre>

This command generates a JSON file containing the internal representation used by `arpa` from the compilation commands generated through the `cmake` call and from the root directory of the project.

<p class="flag-name">
`-cc F, --compile-commands F`
</p><!-- class="flag-name" -->

<p class="flag-desc">
Path to the `compile_commands.json` file generated during the `cmake` call.
</p><!-- class="flag-desc" -->

<p class="flag-name">
`-r DIR, --root-dir DIR`
</p><!-- class="flag-name" -->

<p class="flag-desc">
Path to the root directory of the project under test. By default, this flag is set to the working directory.
</p><!-- class="flag-desc" -->

<p class="flag-name">
`-jp F, --json_path F`
</p><!-- class="flag-name" -->

<p class="flag-desc">
Output path for the generated JSON file. By default, `arpa` generates an `internal_rep.json` in the working directory.
</p><!-- class="flag-desc" -->

### `arpa makefile`
<pre class="command"><code>arpa makefile [-h] -jp F [-ha F] [-sp F]
                 [-ef V] [-en V] [-sh] 
                 [-def V] [-inc V] [-dep V] 
                 [-xfn V] [-unw V] [-dx EXT] 
                 [-mrn V] [-mrs V] [-mrp DIR] 
                 [-mhn V] [-mhp DIR]
                 [-mpn V] [-mps V]
</code></pre>

This command generates a `Makefile` containing relevant build information for a specified harness given the internal JSON representation generated by `arpa build`.

<p class="flag-name">
`-jp F, --json_path F`
</p><!-- class="flag-name" -->

<p class="flag-desc">
Path to the internal JSON representation file output by `arpa build`.
</p><!-- class="flag-desc" -->

<p class="flag-name">
`-ha F, --harness F`
</p><!-- class="flag-name" -->

<p class="flag-desc">
Path to the harness source file for which a `Makefile.arpa` will be generated. By default, `arpa` will search the working directory for a file that ends with "_harness.c". If the number of such files in the working directory is not exactly 1, `arpa` will throw an error.
</p><!-- class="flag-desc" -->

<p class="flag-name">
`-sp F, --save_path F`
</p><!-- class="flag-name" -->

<p class="flag-desc">
Output path for the generated `Makefile`. By default, `arpa` generates a `Makefile.arpa` in the working directory.
</p><!-- class="flag-desc" -->

<p class="flag-name">
`-ef V, --entry-file V`
</p><!-- class="flag-name" -->

<p class="flag-desc">
Name of the `Makefile` variable containing the *harness file name*. By default, the variable name is "HARNESS_FILE".
</p><!-- class="flag-desc" -->

<p class="flag-name">
`-en V, --entry-name V`
</p><!-- class="flag-name" -->

<p class="flag-desc">
Name of the `Makefile` variable containing the *entry type* for the harness file. By default, the variable name is "HARNESS_ENTRY".
</p><!-- class="flag-desc" -->

<p class="flag-name">
`-sh, --shorten-entry`
</p><!-- class="flag-name" -->

<p class="flag-desc">
Remove the "_harness" suffix from the entry file name when writing to the generated `Makefile`.
</p><!-- class="flag-desc" -->

<p class="flag-name">
`-def V, --define-name V`
</p><!-- class="flag-name" -->

<p class="flag-desc">
Name of the `Makefile` variable containing the *variable definitions* required to compile the harness file. By default, the variable name is "DEFINES".
</p><!-- class="flag-desc" -->

<p class="flag-name">
`-inc V, --include-name V`
</p><!-- class="flag-name" -->

<p class="flag-desc">
Name of the `Makefile` variable containing the *included directories* required to compile the harness file. By default, the variable name is "INCLUDES".
</p><!-- class="flag-desc" -->

<p class="flag-name">
`-dep V, --dependency-name V`
</p><!-- class="flag-name" -->

<p class="flag-desc">
Name of the `Makefile` variable containing the *source file dependencies* for the harness. By default, the variable name is "DEPENDENCIES".
</p><!-- class="flag-desc" -->

<p class="flag-name">
`-xfn V, --exclude-function-name V`
</p><!-- class="flag-name" -->

<p class="flag-desc">
Name of the `Makefile` variable containing the *functions to be excluded by CBMC*. By default, the variable name is "REMOVE_FUNCTION_BODY".
</p><!-- class="flag-desc" -->

<p class="flag-name">
`-unw V, --unwindset-name V`
</p><!-- class="flag-name" -->

<p class="flag-desc">
Name of the `Makefile` variable containing the *undwindset CBMC flag value*. By default, the variable name is "UNWINDSET".
</p><!-- class="flag-desc" -->

<p class="flag-name">
`-dx EXT, --dependency-extension EXT`
</p><!-- class="flag-name" -->

<p class="flag-desc">
Modify the extension of the source file dependencies as they appear in the generated `Makefile`. By default, source file dependency extensions are left intact when writing the `Makefile`. 
</p><!-- class="flag-desc" -->

<p class="flag-name">
`-mrn V, --make-root-name V`
</p><!-- class="flag-name" -->

<p class="flag-desc">
Name of the `Makefile` variable containing the *path to the source root directory*. By default, the variable name is "SRCDIR".
</p><!-- class="flag-desc" -->

<p class="flag-name">
`-mrs V, --make-root-sources V`
</p><!-- class="flag-name" -->

<p class="flag-desc">
Name of the `Makefile` variable containing the *path to the source file under test*, used for CBMC proofs. By default, the variable name is "PROJECT_SOURCES".
</p><!-- class="flag-desc" -->

<p class="flag-name">
`-mrp V, --make-root-path V`
</p><!-- class="flag-name" -->

<p class="flag-desc">
Path to the project root directory as it appears in the generated `Makefile`. By default, the project root directory is extracted from the internal representation and corresponds to the `-r` flag value when running `arpa build`.
</p><!-- class="flag-desc" -->

<p class="flag-name">
`-mhn V, --make-helper-name V`
</p><!-- class="flag-name" -->

<p class="flag-desc">
Name of the `Makefile` variable containing the *path to the helper directory containing all the proof directories*. By default, the variable name is "PROOFDIR".
</p><!-- class="flag-desc" -->


<p class="flag-name">
`-mhp DIR, --make-helper-path DIR`
</p><!-- class="flag-name" -->

<p class="flag-desc">
Relative path from the project source root directory to the directory containing all the proof directories. By default, the relative path is "tests/cbmc".
</p><!-- class="flag-desc" -->

<p class="flag-name">
`-mpn V, --make-proofs-name V`
</p><!-- class="flag-name" -->

<p class="flag-desc">
Name of the `Makefile` variable containing the *path to the proof directory containing the harness file*. By default, the variable name is "PROOFDIR".
</p><!-- class="flag-desc" -->

<p class="flag-name">
`-mps V, --make-proofs-sources V`
</p><!-- class="flag-name" -->

<p class="flag-desc">
Name of the `Makefile` variable containing the *path to the harness file*. By default, the variable name is "PROOF_SOURCES".
</p><!-- class="flag-desc" -->

### `arpa run`

<pre class="command"><code>arpa run [-h] -cc F -r DIR [-ha F]
            [-sp F] [-ef V] [-en V] [-sh] 
            [-def V] [-inc V] [-dep V] 
            [-xfn V] [-unw V] [-dx EXT] 
            [-mrn V] [-mrs V] [-mrp DIR] 
            [-mhn V] [-mhp DIR]
            [-mpn V] [-mps V]
</code></pre>

This command generates a `Makefile` containing relevant build information for a specified source file given the internal JSON representation generated by `arpa build`.

<p class="flag-name">
`-cc F, --compile-commands F`
</p><!-- class="flag-name" -->

<p class="flag-desc">
Path to the `compile_commands.json` file generated during the `cmake` call.
</p><!-- class="flag-desc" -->

<p class="flag-name">
`-r DIR, --root-dir DIR`
</p><!-- class="flag-name" -->

<p class="flag-desc">
Path to the root directory of the project under test. By default, this flag is set to the working directory.
</p><!-- class="flag-desc" -->

<p class="flag-name">
`-ha F, --harness F`
</p><!-- class="flag-name" -->

<p class="flag-desc">
Path to the harness source file for which a `Makefile.arpa` will be generated. By default, `arpa` will search the working directory for a file that ends with "_harness.c". If the number of such files in the working directory is not exactly 1, `arpa` will throw an error.
</p><!-- class="flag-desc" -->

<p class="flag-name">
`-sp F, --save_path F`
</p><!-- class="flag-name" -->

<p class="flag-desc">
Output path for the generated `Makefile`. By default, `arpa` generates a `Makefile.arpa` in the working directory.
</p><!-- class="flag-desc" -->

<p class="flag-name">
`-ef V, --entry-file V`
</p><!-- class="flag-name" -->

<p class="flag-desc">
Name of the `Makefile` variable containing the *harness file name*. By default, the variable name is "HARNESS_FILE".
</p><!-- class="flag-desc" -->

<p class="flag-name">
`-en V, --entry-name V`
</p><!-- class="flag-name" -->

<p class="flag-desc">
Name of the `Makefile` variable containing the *entry type* for the harness file. By default, the variable name is "HARNESS_ENTRY".
</p><!-- class="flag-desc" -->

<p class="flag-name">
`-sh, --shorten-entry`
</p><!-- class="flag-name" -->

<p class="flag-desc">
Remove the "_harness" suffix from the entry file name when writing to the generated `Makefile`.
</p><!-- class="flag-desc" -->

<p class="flag-name">
`-def V, --define-name V`
</p><!-- class="flag-name" -->

<p class="flag-desc">
Name of the `Makefile` variable containing the *variable definitions* required to compile the harness file. By default, the variable name is "DEFINES".
</p><!-- class="flag-desc" -->

<p class="flag-name">
`-inc V, --include-name V`
</p><!-- class="flag-name" -->

<p class="flag-desc">
Name of the `Makefile` variable containing the *included directories* required to compile the harness file. By default, the variable name is "INCLUDES".
</p><!-- class="flag-desc" -->

<p class="flag-name">
`-dep V, --dependency-name V`
</p><!-- class="flag-name" -->

<p class="flag-desc">
Name of the `Makefile` variable containing the *source file dependencies* for the harness. By default, the variable name is "DEPENDENCIES".
</p><!-- class="flag-desc" -->

<p class="flag-name">
`-xfn V, --exclude-function-name V`
</p><!-- class="flag-name" -->

<p class="flag-desc">
Name of the `Makefile` variable containing the *functions to be excluded by CBMC*. By default, the variable name is "REMOVE_FUNCTION_BODY".
</p><!-- class="flag-desc" -->

<p class="flag-name">
`-unw V, --unwindset-name V`
</p><!-- class="flag-name" -->

<p class="flag-desc">
Name of the `Makefile` variable containing the *undwindset CBMC flag value*. By default, the variable name is "UNWINDSET".
</p><!-- class="flag-desc" -->

<p class="flag-name">
`-dx EXT, --dependency-extension EXT`
</p><!-- class="flag-name" -->

<p class="flag-desc">
Modify the extension of the source file dependencies as they appear in the generated `Makefile`. By default, source file dependency extensions are left intact when writing the `Makefile`. 
</p><!-- class="flag-desc" -->

<p class="flag-name">
`-mrn V, --make-root-name V`
</p><!-- class="flag-name" -->

<p class="flag-desc">
Name of the `Makefile` variable containing the *path to the source root directory*. By default, the variable name is "SRCDIR".
</p><!-- class="flag-desc" -->

<p class="flag-name">
`-mrs V, --make-root-sources V`
</p><!-- class="flag-name" -->

<p class="flag-desc">
Name of the `Makefile` variable containing the *path to the source file under test*, used for CBMC proofs. By default, the variable name is "PROJECT_SOURCES".
</p><!-- class="flag-desc" -->

<p class="flag-name">
`-mrp V, --make-root-path V`
</p><!-- class="flag-name" -->

<p class="flag-desc">
Path to the project root directory as it appears in the generated `Makefile`. By default, the project root directory is equivalent to the `-r` flag value.
</p><!-- class="flag-desc" -->

<p class="flag-name">
`-mhn V, --make-helper-name V`
</p><!-- class="flag-name" -->

<p class="flag-desc">
Name of the `Makefile` variable containing the *path to the helper directory containing all the proof directories*. By default, the variable name is "PROOFDIR".
</p><!-- class="flag-desc" -->

<p class="flag-name">
`-mhp DIR, --make-helper-path DIR`
</p><!-- class="flag-name" -->

<p class="flag-desc">
Relative path from the project source root directory to the directory containing all the proof directories. By default, the relative path is "tests/cbmc".
</p><!-- class="flag-desc" -->

<p class="flag-name">
`-mpn V, --make-proofs-name V`
</p><!-- class="flag-name" -->

<p class="flag-desc">
Name of the `Makefile` variable containing the *path to the proof directory containing the harness file*. By default, the variable name is "PROOFDIR".
</p><!-- class="flag-desc" -->

<p class="flag-name">
`-mps V, --make-proofs-sources V`
</p><!-- class="flag-name" -->

<p class="flag-desc">
Name of the `Makefile` variable containing the *path to the harness file*. By default, the variable name is "PROOF_SOURCES".
</p><!-- class="flag-desc" -->