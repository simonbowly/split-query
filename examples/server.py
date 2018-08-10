''' Serve/mirror an existing dataset. '''

import logging
logging.basicConfig(level=logging.INFO)
from aemo import AEMOCauserPays

AEMOCauserPays().serve_zmq(port=5566)
