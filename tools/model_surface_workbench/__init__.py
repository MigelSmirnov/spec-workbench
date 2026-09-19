"""Model surface workbench: the closed field surface of every model and class.

Two lenses over one index:

- ``fields``: the State 1 model sections (``01_models_*.md``) and the model
  closures (``60_model_closure*.json``) must declare the same fields. The
  projection reads the closure; a field that lives only in the design text
  reaches neither the assembled specification nor the generator.
- ``attributes``: a State 7 note that reads ``value.attribute`` must name an
  attribute the value's declared type actually has. The generator implements
  notes literally; an attribute the model lacks becomes an AttributeError at
  runtime or a refused candidate at generation.
"""
