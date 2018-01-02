Core Expressions API
====================

The ``core`` module provides a collection of objects for describing a query and a set of functions for manipulating, simplifying, and serialising the query objects.
For example, an expression may be defined as follows::

    expression = And([
        In(Attribute('sensor_id'), [1, 2, 3]),
        Ge(Attribute('date'), datetime(2017, 1, 2)),
        Le(Attribute('date'), datetime(2017, 1, 4))
        ])

A function processing this query should return any records from a target dataset which satisfy the described condition (in this case, data from 2017-01-02 to 2017-01-04 for sensors 1, 2 and 3).
Note that the expression objects provided are not meant to be particularly user friendly; the intention is to provide a consistent language to be read by functions.
Handling user-friendly-ness is the job of the ``interfaces`` module.

Expression objects are equality-comparable, immutable and hashable, so they can be used to store data in dictionary-like structures to retrieve associated results::

    cache[expression] = query_result

Serialisation hooks ``default`` and ``object_hook`` are provided to serialise expressions for storing in databases or passing messages between services.
For example, a string encoding can be produced using Python's native ``json``::

    json_string = json.dumps(expression, default=default)
    recovered = json.loads(expression, object_hook=object_hook)

Or a bytes encoding can be written using the ``msgpack`` library::

    msgpack_bytes = msgpack.packb(
        expression, default=default, use_bin_type=True)
    recovered = msgpack.unpackb(
        expression, object_hook=object_hook, encoding='utf-8')

Functions are included which perform simplifications of expressions, returning new expressions representing the same query.

* ``simplify_tree`` for reducing complicated And/Or/Not logic trees.
* ``simplify_domain`` for reducing combinations of filters on attributes.
* ``expand_dnf`` for converting an expression to disjunctive normal form (DNF).

The combination of these simplification steps is quite powerful.
In particular, performing a DNF expansion followed by domain simplification will always decide correctly whether two queries intersect, or if the result of one query can be entirely recovered from the result of another query without requesting more data.
This functionality is extremely useful when designing data caching implementations.

Finally, user-defined query manipulations can be performed by traversing the logic tree of an expression and replacing components.
Simple examples include renaming/remapping an attribute::

    >>> def hook(obj):
    >>>    if isinstance(obj, In) and obj.attribute == Attribute('sensor_id'):
    >>>        new_values = ['item_{}'.format(v) for v in obj.valueset]
    >>>        return In(Attribute('sensor_name'), new_values)
    >>>    return obj

    >>> traverse_expression(expression, hook=hook)
    And([
        In(Attribute('sensor_name'), ['sensor_1', 'sensor_2', 'sensor_3']),
        Ge(Attribute('date'), datetime(2017, 1, 2)),
        Le(Attribute('date'), datetime(2017, 1, 4))])

or sanitising a query::

    def hook(obj):
        if isinstance(obj, Attribute):
            if obj.name not in ['sensor_name', 'date']:
                raise Exception()
        return obj

    traverse_expression(expression, hook=hook)
    # Raises Exception if the expression contains attributes other than those named.


.. currentmodule:: split_query.core

Expression Components
~~~~~~~~~~~~~~~~~~~~~

.. autoclass:: Attribute
.. autoclass:: And
.. autoclass:: Or
.. autoclass:: Not
.. autoclass:: Eq
.. autoclass:: Le
.. autoclass:: Lt
.. autoclass:: Ge
.. autoclass:: Gt
.. autoclass:: Eq
.. autoclass:: In

Simplifying
~~~~~~~~~~~

.. autofunction:: simplify_tree
.. autofunction:: simplify_domain
.. autofunction:: expand_dnf
.. autoexception:: SimplifyError

Altering/Rebuilding
~~~~~~~~~~~~~~~~~~~

.. autofunction:: traverse_expression

Serialisation
~~~~~~~~~~~~~

.. autofunction:: default
.. autofunction:: object_hook
