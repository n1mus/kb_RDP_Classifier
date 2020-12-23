
class NoWorkspaceReferenceException(Exception): pass
class ParamsException(Exception): pass



def row_attr_map_desc(create_row_attr_map, overwrite, attribute):
    description=(
        '%s%s attribute `%s`'
        % (
            (
                'Created. ' if create_row_attr_map else ''
            ), (
                'Added' if not overwrite else 'Overwrote'
            ),
            attribute
        )
    )
    return description
