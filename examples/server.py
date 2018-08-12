''' Serve/mirror an existing dataset. '''

import logging
logging.basicConfig(level=logging.INFO)
from aemo import AEMOCauserPays5min

AEMOCauserPays5min().serve_zmq(port=5566)
