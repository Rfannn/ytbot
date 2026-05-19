from jinja2 import Environment, FileSystemLoader
from pathlib import Path

_env = Environment(loader=FileSystemLoader(Path(__file__).parent / "templates"), autoescape=True)


def render(name: str, **context):
    t = _env.get_template(name)
    return t.render(**context)
