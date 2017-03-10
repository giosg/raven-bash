import argparse
import re
import sys
import os
from collections import namedtuple
from raven import Client
from raven.transport.requests import RequestsHTTPTransport

# For python 2 compatibility since it does not have FileNotFoundError
try:
    FileNotFoundError
except NameError:
    FileNotFoundError = IOError


def parse_variables(declare_output):
    """Parses the output from declare -p and returns a dict that contains the variables"""
    parser = re.compile(r'declare .[^x] (?P<name>[^=]+)=(?P<value>\S.*)')

    res = {}
    for match in parser.finditer(declare_output):
        group = match.groupdict()

        # Trim leading and trailing "
        # TODO: This could be cleaner if we did it in the regex
        if group['value'].endswith('"'):
            group['value'] = group['value'][:-1]
        if group['value'].startswith('"'):
            group['value'] = group['value'][1:]

        res[group['name']] = group['value']

    return res


def process_sourcefile(file_path, line_number, context_lines=10):
    FileContext = namedtuple('FileContext', ['pre_context', 'context', 'post_context'])

    start = max(line_number - context_lines, 0)
    stop = line_number + context_lines

    pre_context = []
    post_context = []
    context = None

    with open(file_path, 'r') as f:
        for i, line in enumerate(f):
            current_line = i + 1
            if current_line < start:
                continue
            elif current_line > stop:
                break

            if current_line < line_number:
                pre_context.append(line.rstrip('\n'))
            elif current_line == line_number:
                context = line.rstrip('\n')
            else:
                post_context.append(line.rstrip('\n'))

    return FileContext(pre_context, context, post_context)


def get_extra_info(shell_args):
    # add ENV vars and stderr if provided
    extra = {}
    if shell_args.env:
        extra['environment'] = dict([item.split('=', 1) for item in shell_args.env.split('\n')])

    if shell_args.stderr:
        extra['stderr'] = shell_args.stderr

    return extra


def get_captured_exception(shell_args):
    frame = {
        'filename': shell_args.script,
        'function': shell_args.function or 'main',
        'lineno': shell_args.lineno,
        'module': shell_args.command,
        'vars': {},
    }

    if shell_args.pwd:
        abspath = os.path.abspath(os.path.join(shell_args.pwd, shell_args.script))
        filename = os.path.basename(abspath)

        try:
            srcfile = process_sourcefile(abspath, shell_args.lineno)
            if shell_args.declares:
                frame['vars'] = parse_variables(shell_args.declares)
            frame.update(
                filename=filename,
                abs_path=abspath,
                pre_context=srcfile.pre_context,
                context_line=srcfile.context,
                post_context=srcfile.post_context
            )

        except FileNotFoundError:
            sys.stderr.write('Could not process file "{}"\n'.format(abspath))

    data = {
        'exception': {
            'values': [{
                'module': 'builtins',
                'stacktrace': {
                    'frames': [frame]
                },
                'type': shell_args.script,
                'value': 'error on line {}'.format(shell_args.lineno) if not shell_args.function else "error in '{}' on line {}".format(shell_args.function, shell_args.lineno)
            }]
        },
    }
    return data


def main():
    dsn = os.environ.get('SENTRY_DSN')
    if not dsn:
        sys.stderr.write('Missing SENTRY_DSN')
        sys.exit(1)

    parser = argparse.ArgumentParser(description='Send error to Sentry')

    parser.add_argument('--env', help='Script environment')
    parser.add_argument('--cmdline-args', help='Command line arguments')
    parser.add_argument('--stderr', help='Standard error output')
    parser.add_argument('--pwd', help='Working directory')
    parser.add_argument('--function', help='Error function')
    parser.add_argument('--declares', help='declare -p output')

    parser.add_argument('script', help='Source script')
    parser.add_argument('command', help='Error command')
    parser.add_argument('lineno', type=int, help='Error line number')

    args = parser.parse_args()

    # Use RequestsHTTPTransport here so it works with Lets encrypt certs
    client = Client(dsn=dsn, context={}, transport=RequestsHTTPTransport)

    client.capture(
        'raven.events.Message',
        message="raven-bash captured error in %s" % args.script,
        data=get_captured_exception(args),
        extra=get_extra_info(args),
    )

if __name__ == '__main__':
    main()
