
from hypothesis import settings
import six


if six.PY2:
    # Python2 much slower (and inconsistent), so go easy on the fuzz testing.
    settings.register_profile("ci", settings(max_examples=30, deadline=None))
else:
    settings.register_profile("ci", settings(max_examples=50, deadline=300))
settings.load_profile("ci")
