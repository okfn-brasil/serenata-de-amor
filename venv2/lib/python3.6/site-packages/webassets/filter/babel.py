from webassets.filter import ExternalTool

class Babel(ExternalTool):
    """Processes ES6+ code into ES5 friendly code using `Babel <https://babeljs.io/>`_.

    Requires the babel executable to be available externally.
    To install it, you might be able to do::

        $ npm install --global babel-cli

    You probably also want some presets::

        $ npm install --global babel-preset-es2015

    Example python bundle:

    .. code-block:: python

        es2015 = get_filter('babel', presets='es2015')
        bundle = Bundle('**/*.js', filters=es2015)

    Example YAML bundle:

    .. code-block:: yaml

        es5-bundle:
            output: dist/es5.js
            config:
                BABEL_PRESETS: es2015
            filters: babel
            contents:
                - file1.js
                - file2.js

    Supported configuration options:

    BABEL_BIN
        The path to the babel binary. If not set the filter will try to run
        ``babel`` as if it's in the system path.

    BABEL_PRESETS
        Passed straight through to ``babel --presets`` to specify which babel
        presets to use

    BABEL_EXTRA_ARGS
        A list of manual arguments to be specified to the babel command

    BABEL_RUN_IN_DEBUG
        May be set to False to make babel not run in debug
    """
    name = 'babel'
    max_debug_level = None

    options = {
        'binary': 'BABEL_BIN',
        'presets': 'BABEL_PRESETS',
        'extra_args': 'BABEL_EXTRA_ARGS',
        'run_in_debug': 'BABEL_RUN_IN_DEBUG',
    }

    def setup(self):
        super(Babel, self).setup()
        if self.run_in_debug is False:
            # Disable running in debug mode for this instance.
            self.max_debug_level = False

    def input(self, _in, out, **kw):
        args = [self.binary or 'babel']
        if self.presets:
            args += ['--presets', self.presets]
        if self.extra_args:
            args.extend(self.extra_args)
        return self.subprocess(args, out, _in)

