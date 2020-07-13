from . import *


# MSBuild backend doesn't support generated_source yet.
@skip_if_backend('msbuild')
class TestQt(IntegrationTest):
    def run_executable(self, exe):
        if env.host_platform.genus == 'linux':
            output = self.assertPopen([exe], env={'DISPLAY': ''},
                                      returncode='fail')
            self.assertRegex(output,
                             r'QXcbConnection: Could not connect to display')

    def __init__(self, *args, **kwargs):
        env_vars = ({} if env.builder('c++').flavor == 'msvc'
                    else {'CPPFLAGS': ('-Wno-inconsistent-missing-override ' +
                                       env.getvar('CPPFLAGS', ''))})
        super().__init__(os.path.join(examples_dir, '13_qt'), env=env_vars,
                         *args, **kwargs)

    def test_designer(self):
        self.build(executable('qt-designer'))
        self.run_executable(executable('qt-designer'))

    def test_qml(self):
        self.build(executable('qt-qml'))
        self.run_executable(executable('qt-qml'))
