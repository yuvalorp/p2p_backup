import logging

def get_config(peer_id):
    return {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'logzioFormat': {
                'format': '{ "peer ip + port": "' + peer_id + '" }',
                'validate': False
            },
            'brief': {
                'format': '%(asctime)s | %(name)s | %(levelname)s | %(message)s'
            }
        },
        'handlers': {
            'logzio': {
                'class': 'logzio.handler.LogzioHandler',
                'level': 'INFO',
                'formatter': 'logzioFormat',
                'token': 'edONiuAgxXfbIgTlOwAHPEhFGYOETObT',
                'logs_drain_timeout': 5,
                'url': 'https://listener.logz.io:8071'
            },
            'console': {
                'class': 'logging.StreamHandler',
                'formatter': 'brief',
                'level': 'INFO',
                'stream': 'ext://sys.stdout'
            }
        },
        'loggers': {
            '': {
                'level': 'DEBUG',
                'handlers': ['logzio', 'console'],
                'propagate': True
            }
        }
    }
