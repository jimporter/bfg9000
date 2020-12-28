from verspec.python import Version

from bfg9000.app_version import version as version_str


def define_env(env):
    version = Version(version_str)
    tree = 'master' if version.is_prerelease else 'v{}'.format(version)
    repo_src_url = '{}tree/{}/'.format(env.conf['repo_url'], tree)
    env.variables.repo_src_url = repo_src_url
