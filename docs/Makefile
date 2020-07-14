#   Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#
#   Licensed under the Apache License, Version 2.0 (the "License").
#   You may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
SRC = sources
HTML_DEPS += $(SRC)/head1.html
HTML_DEPS += $(SRC)/style.css
HTML_DEPS += $(SRC)/head2.html
HTML_DEPS += $(SRC)/index.tmp.html
HTML_DEPS += $(SRC)/foot.html

index.html: $(HTML_DEPS)
	cat $(HTML_DEPS) > $@

.INTERMEDIATE: $(SRC)/index.tmp.html
$(SRC)/index.tmp.html: $(SRC)/index.md
	markdown $^ > $@

open: index.html
	open index.html