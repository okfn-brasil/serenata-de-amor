import newrelic.core.config

settings = newrelic.core.config.global_settings

RECORDSQL_OFF = 'off'
RECORDSQL_RAW = 'raw'
RECORDSQL_OBFUSCATED = 'obfuscated'

STRIP_EXCEPTION_MESSAGE = ("Message removed by New Relic "
        "'strip_exception_messages' setting")
