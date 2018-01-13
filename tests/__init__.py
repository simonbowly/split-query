
from hypothesis import settings

settings.register_profile("ci", settings(max_examples=50, deadline=300))
settings.load_profile("ci")
