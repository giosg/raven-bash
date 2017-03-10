from unittest import TestCase
from logger import raven_logger
import tempfile


class TestRavenLogger(TestCase):
    def test_process_sourcefile_parses_context(self):
        TEST_SCRIPT = """#!/bin/bash
source raven-bash  # best sentry reporting tool ever

echo "Hello world!"
echo "This will produce an error" | grep "success"
echo "Should see this 1"
echo "Should see this 2"
echo "Should see this 3"
echo "Should see this 4"
echo "Should see this 5"
echo "Should see this 6"
echo "Should see this 7"
echo "Should see this 8"
echo "Should see this 9"
echo "Should see this 10"
echo "Should not see this"
"""
        with tempfile.NamedTemporaryFile() as testfile:
            testfile.write(TEST_SCRIPT)
            testfile.seek(0)
            parsed_context = raven_logger.process_sourcefile(testfile.name, 5)
            self.assertItemsEqual(parsed_context.pre_context, [
                '#!/bin/bash',
                '',
                'source raven-bash  # best sentry reporting tool ever',
                'echo "Hello world!"'
            ])
            self.assertEqual(parsed_context.context, 'echo "This will produce an error" | grep "success"')
            self.assertItemsEqual(parsed_context.post_context, [
                'echo "Should see this 1"',
                'echo "Should see this 2"',
                'echo "Should see this 3"',
                'echo "Should see this 4"',
                'echo "Should see this 5"',
                'echo "Should see this 6"',
                'echo "Should see this 7"',
                'echo "Should see this 8"',
                'echo "Should see this 9"',
                'echo "Should see this 10"',
            ])

    def test_parse_variables(self):
        parsed = raven_logger.parse_variables("""
declare -- BASH="/usr/local/bin/bash"
declare -r BASHOPTS="cmdhist:complete_sourcepath"
declare -ir BASHPID
declare -A BASH_ALIASES=()
declare -a BASH_ARGC=([0]="4")
declare -a BASH_ARGV=([0]="--foo=bar" [1]="params" [2]="cool" [3]="some")
declare -A BASH_CMDS=()
declare -- BASH_COMMAND="grep \"success\""
declare -a BASH_LINENO=([0]="6" [1]="0")
declare -a BASH_SOURCE=([0]="raven-bash" [1]="foo.sh")
declare -x VIRTUALENVWRAPPER_PROJECT_FILENAME=".project"
declare -x VIRTUALENVWRAPPER_SCRIPT="/usr/local/bin/virtualenvwrapper.sh"
declare -x XPC_FLAGS="0x0"
declare -x XPC_SERVICE_NAME="0"
declare -- _="exec"
declare -x __CF_USER_TEXT_ENCODING="0x1F5:0x0:0x0"
declare -- foo="bar"
""")

        # ENV variables (declare -x) should be ignored, everything else captured
        self.assertDictContainsSubset({
            'BASH': '/usr/local/bin/bash',
            'BASHOPTS': 'cmdhist:complete_sourcepath',
            'BASH_ALIASES': '()',
            'BASH_ARGC': '([0]="4")',
            'BASH_ARGV': '([0]="--foo=bar" [1]="params" [2]="cool" [3]="some")',
            'BASH_CMDS': '()',
            'BASH_COMMAND': 'grep \"success\"',
            'BASH_LINENO': '([0]="6" [1]="0")',
            'BASH_SOURCE': '([0]="raven-bash" [1]="foo.sh")',
            '_': 'exec',
            'foo': 'bar',
        }, parsed)

    def test_get_captured_exception(self):
        pass
