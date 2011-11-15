
# ./review $ PYTHONPATH=.. python htmldiff.py old new > diff.html

import sys

import pygments.util
import pygments.lexers
import pygments.formatters

from django.utils.html import escape

from review.diffview import get_chunks_html, split_lines, NoWrapperHtmlFormatter

FORMATTER = NoWrapperHtmlFormatter(style="borland", cssclass="code")

def highlight_file(filename, raw):

    try:
        lexer = pygments.lexers.guess_lexer_for_filename(filename, raw)
    except pygments.util.ClassNotFound:
        # released pygments doesn't yet have .json
        # so hack around it here.
        if filename.endswith('.json'):
            lexer = pygments.lexers.get_lexer_by_name('js')
        else:
            lexer = pygments.lexers.get_lexer_by_name('text')

    return pygments.highlight(raw, lexer, FORMATTER)

def htmldiff(oldfile, newfile):
    old, new = open(oldfile, 'r'), open(newfile, 'r')
    oldcontent, newcontent = old.read(), new.read()
    old.close()
    new.close()

    oldmarkup = highlight_file(oldfile, oldcontent)
    newmarkup = highlight_file(newfile, newcontent)

    oldlines = split_lines(oldmarkup)
    newlines = split_lines(newmarkup)

    old_htmls, new_htmls = get_chunks_html(oldlines, newlines)
    old_html, new_html = '\n'.join(old_htmls), '\n'.join(new_htmls)

    return """
<!doctype html>
<html>
  <head>
    <style>
    %s
.code { white-space: pre; }
.code .deleted { background-color: red; }
.code .inserted { background-color: green; }
.code .inline.changed { background-color: lightgreen; }
    </style>
  </head>
  <body>
    <table width="100%%"><tr>
      <td width="50%%"><code class="code">%s</code></td>
      <td width="50%%"><code class="code">%s</code></td>
    </tr></table>
  </body>
</html>
""" % (FORMATTER.get_style_defs(), old_html, new_html)

def main():
    print htmldiff(sys.argv[1], sys.argv[2])

if __name__ == "__main__":
    main()
