
from hypothesis import settings

settings.register_profile("ci", settings(max_examples=1))
settings.load_profile("ci")
