
from hypothesis import settings

settings.register_profile("ci", settings(max_examples=100))
settings.load_profile("ci")
