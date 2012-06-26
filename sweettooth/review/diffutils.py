
# The code in this file is adapted from ReviewBoard, MIT licensed
# https://github.com/reviewboard/reviewboard
# Copyright 2011 Review Board Team

import re
from difflib import SequenceMatcher

class MyersDiffer:
    """
    An implementation of Eugene Myers's O(ND) Diff algorithm based on GNU diff.
    """
    SNAKE_LIMIT = 20

    DISCARD_NONE = 0
    DISCARD_FOUND = 1
    DISCARD_CANCEL = 2

    # The Myers diff algorithm effectively turns the diff problem into a graph
    # search.  It works by finding the "shortest middle snake," which

    class DiffData:
        def __init__(self, data):
            self.data = data
            self.length = len(data)
            self.modified = {}
            self.undiscarded = []
            self.undiscarded_lines = 0
            self.real_indexes = []

    def __init__(self, a, b, ignore_space=False):
        if type(a) != type(b):
            raise TypeError

        self.a = a
        self.b = b
        self.code_table = {}
        self.last_code = 0
        self.a_data = self.b_data = None
        self.ignore_space = ignore_space
        self.minimal_diff = False

        # SMS State
        self.max_lines = 0
        self.fdiag = None
        self.bdiag = None

    def ratio(self):
        self._gen_diff_data()
        a_equals = self.a_data.length - len(self.a_data.modified)
        b_equals = self.b_data.length - len(self.b_data.modified)

        return 1.0 * (a_equals + b_equals) / \
                     (self.a_data.length + self.b_data.length)

    def get_opcodes(self):
        """
        Generator that returns opcodes representing the contents of the
        diff.

        The resulting opcodes are in the format of
        (tag, i1, i2, j1, j2)
        """
        self._gen_diff_data()

        a_line = b_line = 0
        last_group = None

        # Go through the entire set of lines on both the old and new files
        while a_line < self.a_data.length or b_line < self.b_data.length:
            a_start = a_line
            b_start = b_line

            if a_line < self.a_data.length and \
               not self.a_data.modified.get(a_line, False) and \
               b_line < self.b_data.length and \
               not self.b_data.modified.get(b_line, False):
                # Equal
                a_changed = b_changed = 1
                tag = "equal"
                a_line += 1
                b_line += 1
            else:
                # Deleted, inserted or replaced

                # Count every old line that's been modified, and the
                # remainder of old lines if we've reached the end of the new
                # file.
                while a_line < self.a_data.length and \
                      (b_line >= self.b_data.length or \
                       self.a_data.modified.get(a_line, False)):
                    a_line += 1

                # Count every new line that's been modified, and the
                # remainder of new lines if we've reached the end of the old
                # file.
                while b_line < self.b_data.length and \
                      (a_line >= self.a_data.length or \
                       self.b_data.modified.get(b_line, False)):
                    b_line += 1

                a_changed = a_line - a_start
                b_changed = b_line - b_start

                assert a_start < a_line or b_start < b_line
                assert a_changed != 0 or b_changed != 0

                if a_changed == 0 and b_changed > 0:
                    tag = "insert"
                elif a_changed > 0 and b_changed == 0:
                    tag = "delete"
                elif a_changed > 0 and b_changed > 0:
                    tag = "replace"

                    if a_changed != b_changed:
                        if a_changed > b_changed:
                            a_line -= a_changed - b_changed
                        elif a_changed < b_changed:
                            b_line -= b_changed - a_changed

                        a_changed = b_changed = min(a_changed, b_changed)

            if last_group and last_group[0] == tag:
                last_group = (tag,
                              last_group[1], last_group[2] + a_changed,
                              last_group[3], last_group[4] + b_changed)
            else:
                if last_group:
                    yield last_group

                last_group = (tag, a_start, a_start + a_changed,
                              b_start, b_start + b_changed)


        if not last_group:
            last_group = ("equal", 0, self.a_data.length, 0, self.b_data.length)

        yield last_group

    def _gen_diff_data(self):
        """
        Generate all the diff data needed to return opcodes or the diff ratio.
        This is only called once during the liftime of a MyersDiffer instance.
        """
        if self.a_data and self.b_data:
            return

        self.a_data = self.DiffData(self._gen_diff_codes(self.a, False))
        self.b_data = self.DiffData(self._gen_diff_codes(self.b, True))

        self._discard_confusing_lines()

        self.max_lines = self.a_data.undiscarded_lines + \
                         self.b_data.undiscarded_lines + 3

        vector_size = self.a_data.undiscarded_lines + \
                      self.b_data.undiscarded_lines + 3
        self.fdiag = [0] * vector_size
        self.bdiag = [0] * vector_size
        self.downoff = self.upoff = self.b_data.undiscarded_lines + 1

        self._lcs(0, self.a_data.undiscarded_lines,
                  0, self.b_data.undiscarded_lines,
                  self.minimal_diff)
        self._shift_chunks(self.a_data, self.b_data)
        self._shift_chunks(self.b_data, self.a_data)

    def _gen_diff_codes(self, lines, is_modified_file):
        """
        Converts all unique lines of text into unique numbers. Comparing
        lists of numbers is faster than comparing lists of strings.
        """
        codes = []

        linenum = 0

        for line in lines:
            # TODO: Handle ignoring/triming spaces, ignoring casing, and
            #       special hooks

            raw_line = line
            stripped_line = line.lstrip()

            if self.ignore_space:
                # We still want to show lines that contain only whitespace.
                if len(stripped_line) > 0:
                    line = stripped_line

            try:
                code = self.code_table[line]
            except KeyError:
                # This is a new, unrecorded line, so mark it and store it.
                self.last_code += 1
                code = self.last_code
                self.code_table[line] = code

            codes.append(code)

            linenum += 1

        return codes

    def _find_sms(self, a_lower, a_upper, b_lower, b_upper, find_minimal):
        """
        Finds the Shortest Middle Snake.
        """
        down_vector = self.fdiag # The vector for the (0, 0) to (x, y) search
        up_vector   = self.bdiag # The vector for the (u, v) to (N, M) search

        down_k = a_lower - b_lower # The k-line to start the forward search
        up_k   = a_upper - b_upper # The k-line to start the reverse search
        odd_delta = (down_k - up_k) % 2 != 0

        down_vector[self.downoff + down_k] = a_lower
        up_vector[self.upoff + up_k] = a_upper

        dmin = a_lower - b_upper
        dmax = a_upper - b_lower

        down_min = down_max = down_k
        up_min   = up_max   = up_k

        cost = 0
        max_cost = max(256, self._very_approx_sqrt(self.max_lines * 4))

        while True:
            cost += 1
            big_snake = False

            if down_min > dmin:
                down_min -= 1
                down_vector[self.downoff + down_min - 1] = -1
            else:
                down_min += 1

            if down_max < dmax:
                down_max += 1
                down_vector[self.downoff + down_max + 1] = -1
            else:
                down_max -= 1

            # Extend the forward path
            for k in xrange(down_max, down_min - 1, -2):
                tlo = down_vector[self.downoff + k - 1]
                thi = down_vector[self.downoff + k + 1]

                if tlo >= thi:
                    x = tlo + 1
                else:
                    x = thi

                y = x - k
                old_x = x

                # Find the end of the furthest reaching forward D-path in
                # diagonal k
                while x < a_upper and y < b_upper and \
                      self.a_data.undiscarded[x] == self.b_data.undiscarded[y]:
                    x += 1
                    y += 1

                if odd_delta and up_min <= k <= up_max and \
                   up_vector[self.upoff + k] <= x:
                    return x, y, True, True

                if x - old_x > self.SNAKE_LIMIT:
                    big_snake = True

                down_vector[self.downoff + k] = x

            # Extend the reverse path
            if up_min > dmin:
                up_min -= 1
                up_vector[self.upoff + up_min - 1] = self.max_lines
            else:
                up_min += 1

            if up_max < dmax:
                up_max += 1
                up_vector[self.upoff + up_max + 1] = self.max_lines
            else:
                up_max -= 1

            for k in xrange(up_max, up_min - 1, -2):
                tlo = up_vector[self.upoff + k - 1]
                thi = up_vector[self.upoff + k + 1]

                if tlo < thi:
                    x = tlo
                else:
                    x = thi - 1

                y = x - k
                old_x = x

                while x > a_lower and y > b_lower and \
                      self.a_data.undiscarded[x - 1] == \
                      self.b_data.undiscarded[y - 1]:
                    x -= 1
                    y -= 1

                if not odd_delta and down_min <= k <= down_max and \
                   x <= down_vector[self.downoff + k]:
                    return x, y, True, True

                if old_x - x > self.SNAKE_LIMIT:
                    big_snake = True

                up_vector[self.upoff + k] = x

            if find_minimal:
                continue

            # Heuristics courtesy of GNU diff.
            #
            # We check occasionally for a diagonal that made lots of progress
            # compared with the edit distance. If we have one, find the one
            # that made the most progress and return it.
            #
            # This gives us better, more dense chunks, instead of lots of
            # small ones often starting with replaces. It also makes the output
            # closer to that of GNU diff, which more people would expect.

            if cost > 200 and big_snake:
                ret_x, ret_y, best = \
                    self._find_diagonal(down_min, down_max, down_k, 0,
                                        self.downoff, down_vector,
                                        lambda x: x - a_lower,
                                        lambda x: a_lower + self.SNAKE_LIMIT <=
                                                  x < a_upper,
                                        lambda y: b_lower + self.SNAKE_LIMIT <=
                                                  y < b_upper,
                                        lambda i,k: i - k,
                                        1, cost)

                if best > 0:
                    return ret_x, ret_y, True, False

                ret_x, ret_y, best = \
                    self._find_diagonal(up_min, up_max, up_k, best, self.upoff,
                                        up_vector,
                                        lambda x: a_upper - x,
                                        lambda x: a_lower < x <= a_upper -
                                                  self.SNAKE_LIMIT,
                                        lambda y: b_lower < y <= b_upper -
                                                  self.SNAKE_LIMIT,
                                        lambda i,k: i + k,
                                        0, cost)

                if best > 0:
                    return ret_x, ret_y, False, True

            continue # XXX

            # If we've reached or gone past the max cost, just give up now
            # and report the halfway point between our best results.
            if cost >= max_cost:
                fx_best = bx_best = 0

                # Find the forward diagonal that maximized x + y
                fxy_best = -1
                for d in xrange(down_max, down_min - 1, -2):
                    x = min(down_vector[self.downoff + d], a_upper)
                    y = x - d

                    if b_upper < y:
                        x = b_upper + d
                        y = b_upper

                    if fxy_best < x + y:
                        fxy_best = x + y
                        fx_best = x

                # Find the backward diagonal that minimizes x + y
                bxy_best = self.max_lines
                for d in xrange(up_max, up_min - 1, -2):
                    x = max(a_lower, up_vector[self.upoff + d])
                    y = x - d

                    if y < b_lower:
                        x = b_lower + d
                        y = b_lower

                    if x + y < bxy_best:
                        bxy_best = x + y
                        bx_best = x

                # Use the better of the two diagonals
                if a_upper + b_upper - bxy_best < \
                   fxy_best - (a_lower + b_lower):
                    return fx_best, fxy_best - fx_best, True, False
                else:
                    return bx_best, bxy_best - bx_best, False, True


        raise Exception("The function should not have reached here.")

    def _find_diagonal(self, minimum, maximum, k, best, diagoff, vector,
                       vdiff_func, check_x_range, check_y_range,
                       discard_index, k_offset, cost):
        for d in xrange(maximum, minimum - 1, -2):
            dd = d - k
            x = vector[diagoff + d]
            y = x - d
            v = vdiff_func(x) * 2 + dd

            if v > 12 * (cost + abs(dd)):
                if v > best and \
                   check_x_range(x) and check_y_range(y):
                    # We found a sufficient diagonal.
                    k = k_offset
                    x_index = discard_index(x, k)
                    y_index = discard_index(y, k)

                    while self.a_data.undiscarded[x_index] == \
                          self.b_data.undiscarded[y_index]:
                        if k == self.SNAKE_LIMIT - 1 + k_offset:
                            return x, y, v

                        k += 1
        return 0, 0, 0

    def _lcs(self, a_lower, a_upper, b_lower, b_upper, find_minimal):
        """
        The divide-and-conquer implementation of the Longest Common
        Subsequence (LCS) algorithm.
        """
        # Fast walkthrough equal lines at the start
        while a_lower < a_upper and b_lower < b_upper and \
              self.a_data.undiscarded[a_lower] == \
              self.b_data.undiscarded[b_lower]:
            a_lower += 1
            b_lower += 1

        while a_upper > a_lower and b_upper > b_lower and \
              self.a_data.undiscarded[a_upper - 1] == \
              self.b_data.undiscarded[b_upper - 1]:
            a_upper -= 1
            b_upper -= 1

        if a_lower == a_upper:
            # Inserted lines.
            while b_lower < b_upper:
                self.b_data.modified[self.b_data.real_indexes[b_lower]] = True
                b_lower += 1
        elif b_lower == b_upper:
            # Deleted lines
            while a_lower < a_upper:
                self.a_data.modified[self.a_data.real_indexes[a_lower]] = True
                a_lower += 1
        else:
            # Find the middle snake and length of an optimal path for A and B
            x, y, low_minimal, high_minimal = \
                self._find_sms(a_lower, a_upper, b_lower, b_upper,
                               find_minimal)

            self._lcs(a_lower, x, b_lower, y, low_minimal)
            self._lcs(x, a_upper, y, b_upper, high_minimal)

    def _shift_chunks(self, data, other_data):
        """
        Shifts the inserts/deletes of identical lines in order to join
        the changes together a bit more. This has the effect of cleaning
        up the diff.

        Often times, a generated diff will have two identical lines before
        and after a chunk (say, a blank line). The default algorithm will
        insert at the front of that range and include two blank lines at the
        end, but that does not always produce the best looking diff. Since
        the two lines are identical, we can shift the chunk so that the line
        appears both before and after the line, rather than only after.
        """
        i = j = 0
        i_end = data.length

        while True:
            # Scan forward in order to find the start of a run of changes.
            while i < i_end and not data.modified.get(i, False):
                i += 1

                while other_data.modified.get(j, False):
                    j += 1

            if i == i_end:
                return;

            start = i

            # Find the end of these changes
            i += 1
            while data.modified.get(i, False):
                i += 1

            while other_data.modified.get(j, False):
                j += 1

            while True:
                run_length = i - start

                # Move the changed chunks back as long as the previous
                # unchanged line matches the last changed line.
                # This merges with the previous changed chunks.
                while start != 0 and data.data[start - 1] == data.data[i - 1]:
                    start -= 1
                    i -= 1

                    data.modified[start] = True
                    data.modified[i] = False

                    while data.modified.get(start - 1, False):
                        start -= 1

                    j -= 1
                    while other_data.modified.get(j, False):
                        j -= 1

                # The end of the changed run at the last point where it
                # corresponds to the changed run in the other data set.
                # If it's equal to i_end, then we didn't find a corresponding
                # point.
                if other_data.modified.get(j - 1, False):
                    corresponding = i
                else:
                    corresponding = i_end

                # Move the changed region forward as long as the first
                # changed line is the same as the following unchanged line.
                while i != i_end and data.data[start] == data.data[i]:
                    data.modified[start] = False
                    data.modified[i] = True

                    start += 1
                    i += 1

                    while data.modified.get(i, False):
                        i += 1

                    j += 1
                    while other_data.modified.get(j, False):
                        j += 1
                        corresponding = i

                if run_length == i - start:
                    break

            # Move the fully-merged run back to a corresponding run in the
            # other data set, if we can.
            while corresponding < i:
                start -= 1
                i -= 1

                data.modified[start] = True
                data.modified[i] = False

                j -= 1
                while other_data.modified.get(j, False):
                    j -= 1

    def _discard_confusing_lines(self):
        def build_discard_list(data, discards, counts):
            many = 5 * self._very_approx_sqrt(data.length / 64)

            for i, item in enumerate(data.data):
                if item != 0:
                    num_matches = counts[item]

                    if num_matches == 0:
                        discards[i] = self.DISCARD_FOUND
                    elif num_matches > many:
                        discards[i] = self.DISCARD_CANCEL

        def scan_run(discards, i, length, index_func):
            consec = 0

            for j in xrange(length):
                index = index_func(i, j)
                discard = discards[index]

                if j >= 8 and discard == self.DISCARD_FOUND:
                    break

                if discard == self.DISCARD_FOUND:
                    consec += 1
                else:
                    consec = 0

                    if discard == self.DISCARD_CANCEL:
                        discards[index] = self.DISCARD_NONE

                if consec == 3:
                    break

        def check_discard_runs(data, discards):
            i = 0
            while i < data.length:
                # Cancel the provisional discards that are not in the middle
                # of a run of discards
                if discards[i] == self.DISCARD_CANCEL:
                    discards[i] = self.DISCARD_NONE
                elif discards[i] == self.DISCARD_FOUND:
                    # We found a provisional discard
                    provisional = 0

                    # Find the end of this run of discardable lines and count
                    # how many are provisionally discardable.
                    #for j in xrange(i, data.length):
                    j = i
                    while j < data.length:
                        if discards[j] == self.DISCARD_NONE:
                            break
                        elif discards[j] == self.DISCARD_CANCEL:
                            provisional += 1
                        j += 1

                    # Cancel the provisional discards at the end and shrink
                    # the run.
                    while j > i and discards[j - 1] == self.DISCARD_CANCEL:
                        j -= 1
                        discards[j] = 0
                        provisional -= 1

                    length = j - i

                    # If 1/4 of the lines are provisional, cancel discarding
                    # all the provisional lines in the run.
                    if provisional * 4 > length:
                        while j > i:
                            j -= 1
                            if discards[j] == self.DISCARD_CANCEL:
                                discards[j] = self.DISCARD_NONE
                    else:
                        minimum = 1 + self._very_approx_sqrt(length / 4)
                        j = 0
                        consec = 0
                        while j < length:
                            if discards[i + j] != self.DISCARD_CANCEL:
                                consec = 0
                            else:
                                consec += 1
                                if minimum == consec:
                                    j -= consec
                                elif minimum < consec:
                                    discards[i + j] = self.DISCARD_NONE

                            j += 1

                        scan_run(discards, i, length, lambda x,y: x + y)
                        i += length - 1
                        scan_run(discards, i, length, lambda x,y: x - y)

                i += 1

        def discard_lines(data, discards):
            j = 0
            for i, item in enumerate(data.data):
                if self.minimal_diff or discards[i] == self.DISCARD_NONE:
                    data.undiscarded[j] = item
                    data.real_indexes[j] = i
                    j += 1
                else:
                    data.modified[i] = True

            data.undiscarded_lines = j


        self.a_data.undiscarded = [0] * self.a_data.length
        self.b_data.undiscarded = [0] * self.b_data.length
        self.a_data.real_indexes = [0] * self.a_data.length
        self.b_data.real_indexes = [0] * self.b_data.length
        a_discarded = [0] * self.a_data.length
        b_discarded = [0] * self.b_data.length
        a_code_counts = [0] * (1 + self.last_code)
        b_code_counts = [0] * (1 + self.last_code)

        for item in self.a_data.data:
            a_code_counts[item] += 1

        for item in self.b_data.data:
            b_code_counts[item] += 1

        build_discard_list(self.a_data, a_discarded, b_code_counts)
        build_discard_list(self.b_data, b_discarded, a_code_counts)

        check_discard_runs(self.a_data, a_discarded)
        check_discard_runs(self.b_data, b_discarded)

        discard_lines(self.a_data, a_discarded)
        discard_lines(self.b_data, b_discarded)


    def _very_approx_sqrt(self, i):
        result = 1
        i /= 4
        while i > 0:
            i /= 4
            result *= 2

        return result

ALPHANUM_RE = re.compile(r'\w')

def get_line_changed_regions(oldline, newline):
    if oldline is None or newline is None:
        return (None, None)

    # Use the SequenceMatcher directly. It seems to give us better results
    # for this. We should investigate steps to move to the new differ.
    differ = SequenceMatcher(None, oldline, newline)

    # This thresholds our results -- we don't want to show inter-line diffs if
    # most of the line has changed, unless those lines are very short.

    # FIXME: just a plain, linear threshold is pretty crummy here.  Short
    # changes in a short line get lost.  I haven't yet thought of a fancy
    # nonlinear test.
    if differ.ratio() < 0.6:
        return (None, None)

    oldchanges = []
    newchanges = []
    back = (0, 0)

    for tag, i1, i2, j1, j2 in differ.get_opcodes():
        if tag == "equal":
            if (i2 - i1 < 3) or (j2 - j1 < 3):
                back = (j2 - j1, i2 - i1)
            continue

        oldstart, oldend = i1 - back[0], i2
        newstart, newend = j1 - back[1], j2

        if oldchanges != [] and oldstart <= oldchanges[-1][1] < oldend:
            oldchanges[-1] = (oldchanges[-1][0], oldend)
        elif not oldline[oldstart:oldend].isspace():
            oldchanges.append((oldstart, oldend))

        if newchanges != [] and newstart <= newchanges[-1][1] < newend:
            newchanges[-1] = (newchanges[-1][0], newend)
        elif not newline[newstart:newend].isspace():
            newchanges.append((newstart, newend))

        back = (0, 0)

    return (oldchanges, newchanges)

def new_chunk(lines, collapsable=False, tag='equal', meta=None):
    if not meta:
        meta = {}

    return {
        'lines': lines,
        'change': tag,
        'collapsable': collapsable,
        'meta': meta,
    }

def get_fake_chunk(numlines, tag):
    linenums = xrange(numlines)
    lines = [[n+1, n+1, n+1, [], []] for n in linenums]
    return new_chunk(lines, tag=tag)

def get_chunks(a, b):
    def diff_line(vlinenum, oldlinenum, newlinenum, oldline, newline):
        # This function accesses the variable meta, defined in an outer context.
        if oldline and newline and oldline != newline:
            oldregion, newregion = get_line_changed_regions(oldline, newline)
        else:
            oldregion = newregion = []

        result = [vlinenum, oldlinenum, newlinenum, oldregion, newregion]

        if oldlinenum and oldlinenum in meta.get('moved', {}):
            destination = meta["moved"][oldlinenum]
            result.append(destination)
        elif newlinenum and newlinenum in meta.get('moved', {}):
            destination = meta["moved"][newlinenum]
            result.append(destination)

        return result

    if a is None or b is None:
        if a is not None:
            yield get_fake_chunk(len(a), tag='delete')
        if b is not None:
            yield get_fake_chunk(len(b), tag='insert')
        return

    a_num_lines = len(a)
    b_num_lines = len(b)

    linenum = 1

    ignore_space = True

    differ = MyersDiffer(a, b, ignore_space=ignore_space)

    context_num_lines = 3
    collapse_threshold = 2 * context_num_lines + 3

    for tag, i1, i2, j1, j2, meta in opcodes_with_metadata(differ):
        numlines = max(i2-i1, j2-j1)

        lines = map(diff_line,
                    xrange(linenum, linenum + numlines),
                    xrange(i1 + 1, i2 + 1), xrange(j1 + 1, j2 + 1),
                    a[i1:i2], b[j1:j2])

        if tag == 'equal' and numlines > collapse_threshold:
            last_range_start = numlines - context_num_lines

            if linenum == 1:
                yield new_chunk(lines[:last_range_start], collapsable=True)
                yield new_chunk(lines[last_range_start:numlines])
            else:
                yield new_chunk(lines[:context_num_lines])

                if i2 == a_num_lines and j2 == b_num_lines:
                    yield new_chunk(lines[context_num_lines:numlines], collapsable=True)
                else:
                    yield new_chunk(lines[context_num_lines:last_range_start], collapsable=True)
                    yield new_chunk(lines[last_range_start:numlines])
        else:
            yield new_chunk(lines[:numlines], collapsable=False, tag=tag, meta=meta)

        linenum += numlines

def is_valid_move_range(lines):
    """Determines if a move range is valid and should be included.

    This performs some tests to try to eliminate trivial changes that
    shouldn't have moves associated.

    Specifically, a move range is valid if it has at least one line
    with alpha-numeric characters and is at least 4 characters long when
    stripped.
    """
    for line in lines:
        line = line.strip()

        if len(line) >= 4 and ALPHANUM_RE.search(line):
            return True

    return False


def opcodes_with_metadata(differ):
    """Returns opcodes from the differ with extra metadata.

    This is a wrapper around a differ's get_opcodes function, which returns
    extra metadata along with each range. That metadata includes information
    on moved blocks of code and whitespace-only lines.

    This returns a list of opcodes as tuples in the form of
    (tag, i1, i2, j1, j2, meta).
    """
    groups = []
    removes = {}
    inserts = []

    for tag, i1, i2, j1, j2 in differ.get_opcodes():
        meta = {}
        group = (tag, i1, i2, j1, j2, meta)
        groups.append(group)

        # Store delete/insert ranges for later lookup. We will be building
        # keys that in most cases will be unique for the particular block
        # of text being inserted/deleted. There is a chance of collision,
        # so we store a list of matching groups under that key.
        #
        # Later, we will loop through the keys and attempt to find insert
        # keys/groups that match remove keys/groups.
        if tag == 'delete':
            for i in xrange(i1, i2):
                line = differ.a[i].strip()

                if line:
                    removes.setdefault(line, []).append((i, group))
        elif tag == 'insert':
            inserts.append(group)

    # We now need to figure out all the moved locations.
    #
    # At this point, we know all the inserted groups, and all the individually
    # deleted lines. We'll be going through and finding consecutive groups
    # of matching inserts/deletes that represent a move block.
    #
    # The algorithm will be documented as we go in the code.
    #
    # We start by looping through all the inserted groups.
    for itag, ii1, ii2, ij1, ij2, imeta in inserts:
        # Store some state on the range we'll be working with inside this
        # insert group.
        #
        # i_move_cur is the current location inside the insert group
        # (from ij1 through ij2).
        #
        # i_move_range is the current range of consecutive lines that we'll
        # use for a move. Each line in this range has a corresponding
        # consecutive delete line.
        #
        # r_move_ranges represents deleted move ranges. The key is a
        # string in the form of "{i1}-{i2}-{j1}-{j2}", with those positions
        # taken from the remove group for the line. The value
        # is an array of tuples of (r_start, r_end, r_group). These values
        # are used to quickly locate deleted lines we've found that match
        # the inserted lines, so we can assemble ranges later.
        i_move_cur = ij1
        i_move_range = (i_move_cur, i_move_cur)
        r_move_ranges = {} # key -> [(start, end, group)]

        # Loop through every location from ij1 through ij2 until we've
        # reached the end.
        while i_move_cur <= ij2:
            try:
                iline = differ.b[i_move_cur].strip()
            except IndexError:
                iline = None

            if iline is not None and iline in removes:
                # The inserted line at this location has a corresponding
                # removed line.
                #
                # If there's already some information on removed line ranges
                # for this particular move block we're processing then we'll
                # update the range.
                #
                # The way we do that is to find each removed line that
                # matches this inserted line, and for each of those find
                # out if there's an existing move range that the found
                # removed line immediately follows. If there is, we update
                # the existing range.
                #
                # If there isn't any move information for this line, we'll
                # simply add it to the move ranges.
                for ri, rgroup in removes.get(iline, []):
                    key = "%s-%s-%s-%s" % rgroup[1:5]

                    if r_move_ranges:
                        for i, r_move_range in \
                            enumerate(r_move_ranges.get(key, [])):
                            # If the remove information for the line is next in
                            # the sequence for this calculated move range...
                            if ri == r_move_range[1] + 1:
                                r_move_ranges[key][i] = (r_move_range[0], ri,
                                                         rgroup)
                                break
                    else:
                        # We don't have any move ranges yet, so it's time to
                        # build one based on any removed lines we find that
                        # match the inserted line.
                        r_move_ranges[key] = [(ri, ri, rgroup)]

                # On to the next line in the sequence...
                i_move_cur += 1
            else:
                # We've reached the very end of the insert group. See if
                # we have anything that looks like a move.
                if r_move_ranges:
                    r_move_range = None

                    # Go through every range of lines we've found and
                    # find the longest.
                    #
                    # The longest move range wins. If we find two ranges that
                    # are equal, though, we'll ignore both. The idea is that
                    # if we have two identical moves, then it's probably
                    # common enough code that we don't want to show the move.
                    # An example might be some standard part of a comment
                    # block, with no real changes in content.
                    #
                    # Note that with the current approach, finding duplicate
                    # moves doesn't cause us to reset the winning range
                    # to the second-highest identical match. We may want to
                    # do that down the road, but it means additional state,
                    # and this is hopefully uncommon enough to not be a real
                    # problem.
                    for ranges in r_move_ranges.itervalues():
                        for r1, r2, rgroup in ranges:
                            if not r_move_range:
                                r_move_range = (r1, r2, rgroup)
                            else:
                                len1 = r_move_range[2] - r_move_range[1]
                                len2 = r2 - r1

                                if len1 < len2:
                                    r_move_range = (r1, r2, rgroup)
                                elif len1 == len2:
                                    # If there are two that are the same, it
                                    # may be common code that we don't want to
                                    # see moves for. Comments, for example.
                                    r_move_range = None

                    # If we have a move range, see if it's one we want to
                    # include or filter out. Some moves are not impressive
                    # enough to display. For example, a small portion of a
                    # comment, or whitespace-only changes.
                    if (r_move_range and
                        is_valid_move_range(
                            differ.a[r_move_range[0]:r_move_range[1]])):

                        # Rebuild the insert and remove ranges based on
                        # where we are now and which range we won.
                        #
                        # The new ranges will be actual lists of positions,
                        # rather than a beginning and end. These will be
                        # provided to the renderer.
                        #
                        # The ranges expected by the renderers are 1-based,
                        # whereas our calculations for this algorithm are
                        # 0-based, so we add 1 to the numbers.
                        #
                        # The upper boundaries passed to the range() function
                        # must actually be one higher than the value we want.
                        # So, for r_move_range, we actually increment by 2.
                        # We only increment i_move_cur by one, because
                        # i_move_cur already factored in the + 1 by being
                        # at the end of the while loop.
                        i_move_range = range(i_move_range[0] + 1,
                                             i_move_cur + 1)
                        r_move_range = range(r_move_range[0] + 1,
                                             r_move_range[1] + 2)

                        rmeta = rgroup[-1]
                        rmeta.setdefault('moved', {}).update(
                            dict(zip(r_move_range, i_move_range)))
                        imeta.setdefault('moved', {}).update(
                            dict(zip(i_move_range, r_move_range)))

                # Reset the state for the next range.
                i_move_cur += 1
                i_move_range = (i_move_cur, i_move_cur)
                r_move_ranges = {}

    return groups

def _test(oldfile, newfile):
    old, new = open(oldfile, 'r'), open(newfile, 'r')
    a, b = old.read().splitlines(), new.read().splitlines()

    chunks = list(get_chunks(a, b))
    old.close()
    new.close()

    return chunks

def main():
    import pprint
    import sys

    pprint.pprint(_test(sys.argv[1], sys.argv[2]))

if __name__ == "__main__":
    main()
