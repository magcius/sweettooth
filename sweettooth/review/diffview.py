
import pygments.formatters

from review.diffutils import get_chunks, split_lines

# Stolen from ReviewBoard
# See the top of diffutils.py for details
class NoWrapperHtmlFormatter(pygments.formatters.HtmlFormatter):
    """An HTML Formatter for Pygments that don't wrap items in a div."""

    def _wrap_div(self, inner):
        # Method called by the formatter to wrap the contents of inner.
        # Inner is a list of tuples containing formatted code. If the first item
        # in the tuple is zero, then it's a wrapper, so we should ignore it.
        for tup in inner:
            if tup[0]:
                yield tup

REGION = u'<span class="%s">%%s</span>'

UNCHANGED_REGION = REGION % (u'inline unchanged',)
CHANGED_REGION = REGION % (u'inline changed',)

EQUAL_REGION = REGION % (u'line equal',)
INSERTED_REGION = REGION % (u'line inserted',)
DELETED_REGION = REGION % (u'line deleted',)
REPLACED_REGION = REGION % (u'line replaced',)

def get_line_region_markup(line, regions):
    if regions == []:
        return [UNCHANGED_REGION % escape(line)]

    parts = []
    last_end = 0
    for start, end in regions:
        parts.append(UNCHANGED_REGION % line[last_end:start])
        parts.append(CHANGED_REGION % line[start:end])
        last_end = end

    parts.append(UNCHANGED_REGION % line[last_end:len(line)])
    return parts

def get_equal_markup(chunk, old, new):
    if chunk['collapsible']:
        return '', ''

    lines = chunk['lines']
    start = lines[0]
    end = lines[-1]
    contents = old[start[1]-1:end[1]]
    markup = [EQUAL_REGION % (L,) for L in contents]
    return markup, markup

def get_inserted_markup(chunk, old, new):
    lines = chunk['lines']
    start = lines[0]
    end = lines[-1]
    contents = new[start[2]-1:end[2]]
    return None, [INSERTED_REGION % (L,) for L in contents]

def get_deleted_markup(chunk, old, new):
    lines = chunk['lines']
    start = lines[0]
    end = lines[-1]
    contents = old[start[1]-1:end[1]]
    return [DELETED_REGION % (L,) for L in contents], None

def get_replaced_markup(chunk, old, new):
    lines = chunk['lines']

    oldlines, newlines = [], []
    for line in lines:
        oldcontent = old[line[1] - 1]
        newcontent = new[line[2] - 1]
        oldregion = line[3]
        newregion = line[4]

        if oldregion is not None:
            oldlines.append(REPLACED_REGION % \
                                (''.join(get_line_region_markup(oldcontent, oldregion)),))
        else:
            oldlines.append(REPLACED_REGION % (oldcontent,))

        if newregion is not None:
            newlines.append(REPLACED_REGION % \
                                (''.join(get_line_region_markup(newcontent, newregion)),))
        else:
            newlines.append(REPLACED_REGION % (newcontent,))

    return oldlines, newlines

OPCODES = dict(equal   = get_equal_markup,
               insert  = get_inserted_markup,
               delete  = get_deleted_markup,
               replace = get_replaced_markup)

def get_chunks_html(old, new):
    oldchunks, newchunks = [], []
    for chunk in get_chunks(old, new):
        opcode = chunk['change']
        oldchunk, newchunk = OPCODES[opcode](chunk, old, new)

        if oldchunk is not None:
            oldchunks.extend(oldchunk)

        if newchunk is not None:
            newchunks.extend(newchunk)

    return oldchunks, newchunks
