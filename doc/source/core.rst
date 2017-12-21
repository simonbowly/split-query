Core Expressions API
====================

.. currentmodule:: split_query.core

Building
~~~~~~~~

.. autoclass:: And
.. autoclass:: Or
.. autoclass:: Not

Simplifying
~~~~~~~~~~~

.. autofunction:: simplify_tree
.. autofunction:: simplify_domain
.. autoexception:: SimplifyError
.. autofunction:: expand_dnf

Altering/Rebuilding
~~~~~~~~~~~~~~~~~~~

.. autofunction:: traverse_expression

Serialisation
~~~~~~~~~~~~~

.. autofunction:: default
.. autofunction:: object_hook
