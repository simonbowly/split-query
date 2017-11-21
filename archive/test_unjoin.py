
import pytest

from octo_spork.query import Column


col1a = Column('table1', 'columna')
col1b = Column('table1', 'columnb')
col1c = Column('table1', 'columnc')
col2x = Column('table2', 'columnx')
col2y = Column('table2', 'columny')
col2z = Column('table2', 'columnz')


@pytest.mark.xfail
def test_main_filter():
    # Filtering on a column in the main table limits the inner joined query.
    # Joining values.
    query = Query(
        table='table1',
        join=(col1a, col2x),
        select=[col1b, col1c, col2y, col2z],
        where=EQ(col1b, 'value'))
    assert query.tables == {'table1', 'table2'}

    # Preliminary results.
    expect_main_query = Query(
        table='table1',
        select=[col1a, col1b, col1c],
        where=EQ(col1b, 2))
    assert expect_main_query.tables == {'table1'}

    expect_joined_query = Query(
        table='table2',
        select=[col2x, col2y, col2z],
        where=DelayedConstraint(col2x, 'some_id'))
    assert expect_joined_query.tables == {'table2'}

    # After main is run, returing col2x in {1, 2, 3}.
    # DelayedConstraint is replaced, needs some sort of id marker.
    expect_joined_query = Query(
        table='table2',
        select=[col2x, col2y, col2z],
        where=In(col2x, [1, 2, 3]))
    assert expect_joined_query.tables == {'table2'}

    # Results are joined. NB there is no need to do a local refine on the
    # join table result since this is implicit to the 'inner' op.
    engine.join(main_result, join_result, how='inner')



@pytest.mark.xfail
def test_join_filter():
    # Filtering on a column in the main table limits the inner joined query.
    # Joining values.
    query = Query(
        table='table1',
        join=(col1a, col2x),
        select=[col1b, col1c, col2y, col2z],
        where=EQ(col2y, 'value'))
    assert query.tables == {'table1', 'table2'}

    # Preliminary results.
    expect_main_query = Query(
        table='table1',
        select=[col1a, col1b, col1c],
        where=DelayedConstraint(col1a))
    assert expect_main_query.tables == {'table1'}

    expect_joined_query = Query(
        table='table2',
        select=[col2x, col2y, col2z],
        where=EQ(col2y, 'value'))
    assert expect_joined_query.tables == {'table2'}

    # After joined is run, returing col1a in {1, 2, 3}.
    # DelayedConstraint is replaced, needs some sort of id marker.
    expect_main_query = Query(
        table='table1',
        select=[col1a, col1b, col1c],
        where=In(col1a, [1, 2, 3]))
    assert expect_main_query.tables == {'table1'}

    # Results are joined. NB there is no need to do a local refine on the
    # join table result since this is implicit to the 'inner' op.
    engine.join(main_result, join_result, how='inner')
