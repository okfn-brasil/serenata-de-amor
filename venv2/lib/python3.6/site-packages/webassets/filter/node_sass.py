import os
import subprocess

from webassets.exceptions import FilterError

from .sass import Sass


__all__ = ('NodeSass', )


class NodeSass(Sass):
    """Converts `Scss <http://sass-lang.com/>`_ markup to real CSS.

    This uses node-sass which is a wrapper around libsass.

    This is an alternative to using the ``sass`` or ``scss`` filters,
    which are based on the original, external tools.

    *Supported configuration options:*

    NODE_SASS_DEBUG_INFO (debug_info)
        Include debug information in the output

        If unset, the default value will depend on your
        :attr:`Environment.debug` setting.

    NODE_SASS_LOAD_PATHS (load_paths)
        Additional load paths that node-sass should use.

    NODE_SASS_STYLE (style)
        The style of the output CSS. Can be one of ``nested`` (default),
        ``compact``, ``compressed``, or ``expanded``.

    NODE_SASS_CLI_ARGS (cli_args)
        Additional cli arguments
    """

    name = 'node-sass'
    options = {
        'binary': 'NODE_SASS_BIN',
        'debug_info': 'NODE_SASS_DEBUG_INFO',
        'use_scss': ('scss', 'NODE_SASS_USE_SCSS'),
        'as_output': 'NODE_SASS_AS_OUTPUT',
        'load_paths': 'NODE_SASS_LOAD_PATHS',
        'style': 'NODE_SASS_STYLE',
        'cli_args': 'NODE_SASS_CLI_ARGS',
    }
    max_debug_level = None

    def _apply_sass(self, _in, out, cd=None):
        # Switch to source file directory if asked, so that this directory
        # is by default on the load path. We could pass it via --include-paths, but then
        # files in the (undefined) wd could shadow the correct files.
        old_dir = os.getcwd()
        if cd:
            os.chdir(cd)

        try:
            args = [self.binary or 'node-sass',
                    '--output-style', self.style or 'expanded']

            if not self.use_scss:
                args.append("--indented-syntax")

            if (self.ctx.environment.debug if self.debug_info is None else self.debug_info):
                args.append('--debug-info')
            for path in self.load_paths or []:
                args.extend(['--include-path', path])

            if (self.cli_args):
                args.extend(self.cli_args)

            proc = subprocess.Popen(args,
                                    stdin=subprocess.PIPE,
                                    stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE,
                                    # shell: necessary on windows to execute
                                    # ruby files, but doesn't work on linux.
                                    shell=(os.name == 'nt'))
            stdout, stderr = proc.communicate(_in.read().encode('utf-8'))

            if proc.returncode != 0:
                raise FilterError(('sass: subprocess had error: stderr=%s, '+
                                   'stdout=%s, returncode=%s') % (
                                                stderr, stdout, proc.returncode))
            elif stderr:
                print("node-sass filter has warnings:", stderr)

            out.write(stdout.decode('utf-8'))
        finally:
            if cd:
                os.chdir(old_dir)


class NodeSCSS(NodeSass):
    """Version of the ``node-sass`` filter that uses the SCSS syntax.
    """

    name = 'node-scss'

    def __init__(self, *a, **kw):
        assert not 'scss' in kw
        kw['scss'] = True
        super(NodeSCSS, self).__init__(*a, **kw)
