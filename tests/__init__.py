
from hypothesis import settings

settings.register_profile("ci", settings(max_examples=10))
settings.load_profile("ci")
