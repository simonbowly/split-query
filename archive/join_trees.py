
# Tree resulting from resolving a join.

# NodeJoin -> specified how the engine should join 'main' and 'join' data.
# NodeDelayed -> some dependencies must be run to get the final filter.
#       When run, this will create In filters to be inserted into the unresolved queries.
# NodeValueSet -> take a result, use the engine to get the value set


source1 = Mock()
source2 = Mock()

data_sources = DataSources(
    source_order=[0, 1],
    source_map={0: source1, 1: source2},
    source_tables={0: {'table1'}, 1: {'table2'}})

col1a = Column('table1', 'columna')
col1b = Column('table1', 'columnb')
col1c = Column('table1', 'columnc')
col2x = Column('table2', 'columnx')
col2y = Column('table2', 'columny')
col2z = Column('table2', 'columnz')

query = Query(table='table1', join=(col1a, col2x))

NodeJoin(
    main_column=col1a, join_column=col2x, how='inner',
    main=NodeGet(source=0, query='table1_query'),
    join=NodeDelayed(
        source=1, query=Query(where=DependentIn(col2x, 'key1')),
        dependencies=[('key1', NodeValueSet(
            column=col2x, data=NodeGet(source=0, query='table1_query')))]
        )
    )

# Actually expect two calls, but with temp cache, will be one remote request.
source1.query.assert_called_once_with('table1_query')
# In filter created by NodeValueSet and inserted by NodeDelayed in place of the DependentIn.
source2.query.assert_called_once_with(Query('table2', where=In(col2x, {1, 2, 3, 4})))

# This is the reversed dependency, required when there is a filter on the joined column.
NodeJoin(
    main_column=col1a, join_column=col2x, how='inner',
    main=NodeDelayed(
        source=0, query='some_query_containing_unresolved_parts',
        dependencies=[
            ('dep1', NodeValueSet('col1', NodeGet(source=2, query='some_table2_query'))),
            ]),
    join=NodeGet(source=1, query='some_table2_query'))

# MAKE SURE WE DON'T GET CIRCULAR REFS!!

# TODO - splitting and recombining queries
#   * Replace table2 filters with DependentIn
#   * Replace DependentIn with data.
