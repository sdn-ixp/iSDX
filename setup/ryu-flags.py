
CONF.register_cli_opts([
    # refmon
    cfg.StrOpt('config', default=None,
               help='path of config file'),
    cfg.StrOpt('flowmodlog', default=None,
               help='path of flowmod log file'),
    cfg.StrOpt('input', default=None,
               help='path of input file'),
    cfg.StrOpt('log', default=None,
               help='path of log file'),
    cfg.BoolOpt('always_ready', default=False,
               help='assume all switches are up and registered with Ryu'),
], group='refmon')
