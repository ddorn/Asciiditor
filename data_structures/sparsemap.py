from typing import Dict

from sortedcontainers.sorteddict import SortedDict


class Map:
    def __init__(self, text: str = ''):
        # self.data[row][col]
        self.data = SortedDict()  # type: Dict[int, Dict[int, str]]

        # they are all included
        self.row_min = 0
        self.col_min = 0
        self.row_max = 0
        self.col_max = 0

        self.set_text(text)

    def __str__(self):
        return f"""<Map(x:{self.row_min} -> {self.row_max}, 
     y:{self.col_min} -> {self.col_max})>"""

    def __getitem__(self, item):

        row, col = item

        if isinstance(row, slice):

            start = row.start or self.row_min
            stop = row.stop or self.row_max + 1
            step = row.step or 1

            return '\n'.join(self[r, col] for r in range(start, stop, step))

        if isinstance(col, slice):

            start = col.start or self.col_min
            stop = col.stop or self.col_max + 1
            step = col.step or 1

            return ''.join(self[row, c] for c in range(start, stop, step))

        if item in self:
            return self.data[row][col]
        return ' '

    def __setitem__(self, item, value):

        if value == ' ':
            del self[item]
            return

        row, col = item

        self.data.setdefault(row, SortedDict())[col] = value

        if row < self.row_min:
            self.row_min = row
        elif row > self.row_max:
            self.row_max = row

        if col < self.col_min:
            self.col_min = col
        elif col > self.col_max:
            self.col_max = col

    def __delitem__(self, key):
        if key in self:
            row, col = key
            del self.data[row][col]
            if not self.data[row]:
                del self.data[row]
        self.update_bounds()

    def __contains__(self, item):
        return item[0] in self.data and item[1] in self.data[item[0]]

    def __iter__(self):
        for row in self.data:
            for col in self.data[row]:
                yield (col, row), self.data[row][col]

    def set_text(self, text: str):
        self.data.clear()

        for row, line in enumerate(text.splitlines()):
            if line.strip() == '':
                continue

            self.data[row] = SortedDict({col: c for (col, c) in enumerate(line) if c != ' '})

        self.update_bounds()

    def update_bounds(self):
        if self.data:
            self.row_min = min(self.data)
            self.row_max = max(self.data)
            self.col_min = min(map(min, self.data.values()))
            self.col_max = max(map(max, self.data.values()))
        else:
            self.row_min = 0
            self.col_min = 0
            self.row_max = 0
            self.col_max = 0

    def suppr(self, item):
        row, col = item

        # we delete the whole line, shifting everything under one to the top
        if row not in self.data:
            # We take the list of the value so we don't modify the dict while looping on it
            for r in list(self.data):
                if r < row:
                    continue

                self.data[r - 1] = self.data[r]
                del self.data[r]

        else:
            row = self.data[row]
            for c in list(row):
                if c < col:
                    continue
                elif c == col:
                    del row[col]
                else:
                    row[c - 1] = row[c]
                    del row[c]

            if not row:
                del self.data[item[0]]

        self.update_bounds()

    def insert(self, pos, value):
        """Insert value at pos and shift everything after."""

        # we want only one char at a time for now
        value = value[0]
        row, col = pos

        if value == '\n':
            col = max(self.col_min, col)

            for r in reversed(self.data):

                if r < row:  # we do nothing before
                    continue
                elif r == row:  # we split the line into to
                    cur_row = SortedDict()
                    next_row = SortedDict()
                    for c, val in self.data[row].items():
                        if c < col:
                            cur_row[c] = val
                        else:
                            next_row[self.col_min + c - col] = val

                    if cur_row:
                        self.data[r] = cur_row
                    else:
                        if r in self.data:
                            del self.data[r]
                    if next_row:
                        self.data[r + 1] = next_row
                    else:
                        if r + 1 in self.data:
                            del self.data[r + 1]

                else:  # we move the line to the bottom
                    self.data[r + 1] = self.data[r]
                    del self.data[r]
        else:
            if row in self.data:
                row = self.data[row]

                for c in reversed(row):
                    # shift to the right evrything if after the insert
                    if c >= col:  # and shift the left
                        row[c + 1] = row[c]
                        del row[c]

            # in the existing or created space, we put our value !
            self[pos] = value






if __name__ == '__main__':
    m = Map()
    m[0 , 0] = '+'
    m[-1, 6] = '1'
    m[3 , 2] = '7'
    m[0 , 5] = '2'
    m[1 , 4] = '3'
    m[5 , 0] = '4'
    m[2 , 2] = '5'
    m[0 , -3] = '6'

    print(m[3, 4]), print(m[3, 2:6])
    print('-'*10)
    print(m[:, :])

    print(m.data)
