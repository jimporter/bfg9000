"""Keywords available in build.cfg files.

Note that the values in this module are actually replaced by bfg9000 when a build.cfg is run, so don't rely on these to
act like normal Python attributes.
"""

# It would be better if each of these referred to some object with the correct signature and docstring so that things
# like autocomplete would work naturally in any IDE. I'm not sure if there's a simple way for us to automate that.

# Note that this list of attributes was created by looking at the names that are actually injected into the build.cfg
# namespace. If some of these should not be in here, they can safely be removed. The code that populates this module
# won't add names that aren't already here.

CalledProcessError = None
FindResult = None
InstallRoot = None
PackageResolutionError = None
PackageVersionError = None
Path = None
Root = None
ToolNotFoundError = None
VersionError = None
__bfg9000__ = None
alias = None
argv = None
auto_file = None
bfg9000_required_version = None
bfg9000_version = None
boost_package = None
build_step = None
command = None
copy_file = None
copy_files = None
debug = None
default = None
directory = None
env = None
executable = None
export = None
extra_dist = None
filter_by_platform = None
find_files = None
find_paths = None
framework = None
generated_source = None
generated_sources = None
generic_file = None
global_link_options = None
global_options = None
header_directory = None
header_file = None
info = None
install = None
library = None
module_def_file = None
object_file = None
object_files = None
opts = None
package = None
pkg_config = None
precompiled_header = None
project = None
relpath = None
resource_file = None
safe_format = None
safe_str = None
shared_library = None
source_file = None
static_library = None
submodule = None
system_executable = None
test = None
test_deps = None
test_driver = None
warning = None
whole_archive = None
