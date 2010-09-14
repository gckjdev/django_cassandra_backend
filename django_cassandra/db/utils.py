import time

SORT_ASCENDING = False
SORT_DESCENDING = True

def _cmp_to_key(comparison_function):
    """
    Convert a cmp= function into a key= function.
    This is built in to Python 2.7, but we define it ourselves
    to work with older versions of Python
    """
    class K(object):
        def __init__(self, obj, *args):
            self.obj = obj
        def __lt__(self, other):
            return comparison_function(self.obj, other.obj) < 0
        def __gt__(self, other):
            return comparison_function(self.obj, other.obj) > 0
        def __eq__(self, other):
            return comparison_function(self.obj, other.obj) == 0
        def __le__(self, other):
            return comparison_function(self.obj, other.obj) <= 0
        def __ge__(self, other):
            return comparison_function(self.obj, other.obj) >= 0
        def __ne__(self, other):
            return comparison_function(self.obj, other.obj) != 0
    return K

def _compare_rows(row1, row2, sort_spec_list):
    for sort_spec in sort_spec_list:
        column_name = sort_spec[0]
        reverse = sort_spec[1] if len(sort_spec) > 1 else False
        row1_value = row1.get(column_name, None)
        row2_value = row2.get(column_name, None)
        result = cmp(row1_value, row2_value)
        if result != 0:
            if reverse:
                result = -result
            break;
    else:
        result = 0
    return result

def sort_rows(rows, sort_spec):
    if sort_spec == None:
        return rows

    if (type(sort_spec) != list) and (type(sort_spec) != tuple):
        raise InvalidSortSpecException()
    
    # The sort spec can be either a single sort spec tuple or a list/tuple
    # of sort spec tuple. To simplify the code below we convert the case
    # where it's a single sort spec tuple to a 1-element tuple containing
    # the sort spec tuple here.
    if (type(sort_spec[0]) == list) or (type(sort_spec[0]) == tuple):
        sort_spec_list = sort_spec
    else:
        sort_spec_list = (sort_spec,)
    
    rows.sort(key=_cmp_to_key(lambda row1, row2: _compare_rows(row1, row2, sort_spec_list)))

COMBINE_INTERSECTION = 1
COMBINE_UNION = 2

def combine_rows(rows1, rows2, op, primary_key_column):
    # Handle cases where rows1 and/or rows2 are None or empty
    if not rows1:
        return list(rows2) if rows2 != None else []
    if not rows2:
        return list(rows1)
    
    # We're going to iterate over the lists in parallel and
    # compare the elements so we need both lists to be sorted
    # Note that this means that the input arguments will be modified.
    # We could optionally clone the rows first, but then we'd incur
    # the overhead of the copy. For now, we'll just always sort
    # in place, and if it turns out to be a problem we can add the
    # option to copy
    sort_rows(rows1,(primary_key_column,))
    sort_rows(rows2,(primary_key_column,))
    
    combined_rows = []
    iter1 = iter(rows1)
    iter2 = iter(rows2)
    update1 = update2 = True
    
    while True:
        # Get the next element from one or both of the lists
        if update1:
            try:
                row1 = iter1.next()
            except:
                row1 = None
            value1 = row1.get(primary_key_column, None) if row1 != None else None
        if update2:
            try:
                row2 = iter2.next()
            except:
                row2 = None
            value2 = row2.get(primary_key_column, None) if row2 != None else None
        
        if (op == COMBINE_INTERSECTION):
            # If we've reached the end of either list and we're doing an intersection,
            # then we're done
            if (row1 == None) or (row2 == None):
                break
        
            if value1 == value2:
                combined_rows.append(row1)
        elif (op == COMBINE_UNION):
            if row1 == None:
                if row2 == None:
                    break;
                combined_rows.append(row2)
            elif (row2 == None) or (value1 <= value2):
                combined_rows.append(row1)
            else:
                combined_rows.append(row2)
        else:
            raise InvalidCombineRowsOpException()
        
        update1 = (row2 == None) or (value1 <= value2)
        update2 = (row1 == None) or (value2 <= value1)
    
    return combined_rows

_last_time = None
_last_counter = None
    
def get_next_timestamp():
    # The timestamp is a 64-bit integer
    # We use the top 32 bits for the integral part of time.time()
    # The next 10 bits are the fractional part of time.time() with
    # roughly millisecond precision.
    # The last 22 bits are a counter that is incremented if the current
    # time value from the top 42 bits is the same as the last
    # time value. This guarantees that a new timestamp is always
    # greater than the previous timestamp
    global _last_time, _last_counter
    current_real_time = time.time()
    current_seconds = int(current_real_time)
    current_subsecond = int((current_real_time % current_seconds) * 1024)
    current_time = (current_seconds * 1024) + current_subsecond
    
    if (_last_time == None) or (current_time > _last_time):
        _last_time = current_time
        _last_counter = 0
    else:
        _last_counter += 1
    
    return _last_time * 0x400000 + _last_counter