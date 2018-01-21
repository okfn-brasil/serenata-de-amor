import tokenize
import warnings

from django import template
from django_assets import Bundle
from django_assets.env import get_env

from webassets import six
from webassets.exceptions import ImminentDeprecationWarning


def parse_debug_value(value):
    """Django templates do not know what a boolean is, and anyway we need to
    support the 'merge' option."""
    if isinstance(value, bool):
        return value
    try:
        from webassets.env import parse_debug_value
        return parse_debug_value(value)
    except ValueError:
        raise template.TemplateSyntaxError(
            '"debug" argument must be one of the strings '
            '"true", "false" or "merge", not "%s"' % value)


class AssetsNode(template.Node):

    # For testing, to inject a mock bundle
    BundleClass = Bundle

    def __init__(self, filters, depends, output, debug, files, childnodes):
        self.childnodes = childnodes
        self.output = output
        self.files = files
        self.depends = depends
        self.filters = filters
        self.debug = debug

    def resolve(self, context={}):
        """We allow variables to be used for all arguments; this function
        resolves all data against a given context.

        This is a separate method as the management command must have
        the ability to check if the tag can be resolved without a context.
        """
        def resolve_var(x):
            if x is None:
                return None
            else:
                try:
                    return template.Variable(x).resolve(context)
                except template.VariableDoesNotExist:
                    # Django seems to hide those; we don't want to expose
                    # them either, I guess.
                    raise
        def resolve_depends(x):
            # Adapter to parse django template tags for depends.
            # into a webassets compabitble list if multiple depends is passed.
            # Django templates support depends in a (comma delimited form. e.g.,
            #
            # {% assets filters="jsmin", output="path/to/file.js", depends="watchfile.js,second/watch/file.js" "projectfile.js" %}
            value = resolve_var(x)
            if isinstance(value, six.text_type):
                value = value.split(',')
            return value
        def resolve_bundle(name):
            # If a bundle with that name exists, use it. Otherwise,
            # assume a filename is meant.
            try:
                return get_env()[name]
            except KeyError:
                return name


        return self.BundleClass(
            *[resolve_bundle(resolve_var(f)) for f in self.files],
            **{'output': resolve_var(self.output),
            'filters': resolve_var(self.filters),
            'depends': resolve_depends(self.depends),
            'debug': parse_debug_value(resolve_var(self.debug))})

    def render(self, context):
        bundle = self.resolve(context)

        result = u""
        with bundle.bind(get_env()):
            for url in bundle.urls():
                context.update({'ASSET_URL': url, 'EXTRA': bundle.extra})
                try:
                    result += self.childnodes.render(context)
                finally:
                    context.pop()
        return result


def assets(parser, token):
    filters = None
    output = None
    debug = None
    depends = None
    files = []

    # parse the arguments
    args = token.split_contents()[1:]
    for arg in args:
        # Handle separating comma; for backwards-compatibility
        # reasons, this is currently optional, but is enforced by
        # the Jinja extension already.
        if arg[-1] == ',':
            arg = arg[:-1]
            if not arg:
                continue

        # determine if keyword or positional argument
        arg = arg.split('=', 1)
        if len(arg) == 1:
            name = None
            value = arg[0]
        else:
            name, value = arg

        # handle known keyword arguments
        if name == 'output':
            output = value
        elif name == 'debug':
            debug = value
        elif name == 'filters':
            filters = value
        elif name == 'filter':
            filters = value
            warnings.warn('The "filter" option of the {% assets %} '
                          'template tag has been renamed to '
                          '"filters" for consistency reasons.',
                            ImminentDeprecationWarning)
        elif name == 'depends':


            depends = value
        # positional arguments are source files
        elif name is None:
            files.append(value)
        else:
            raise template.TemplateSyntaxError('Unsupported keyword argument "%s"'%name)

    # capture until closing tag
    childnodes = parser.parse(("endassets",))
    parser.delete_first_token()
    return AssetsNode(filters, depends, output, debug, files, childnodes)



# If Coffin is installed, expose the Jinja2 extension
try:
    from coffin.template import Library as CoffinLibrary
except ImportError:
    register = template.Library()
else:
    register = CoffinLibrary()
    from webassets.ext.jinja2 import AssetsExtension
    from django_assets.env import get_env
    register.tag(AssetsExtension, environment={'assets_environment': get_env()})

# expose the default Django tag
register.tag('assets', assets)
