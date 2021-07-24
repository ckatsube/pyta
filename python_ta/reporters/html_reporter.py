import os
import sys
import webbrowser
from typing import Any

import socket
from http.server import BaseHTTPRequestHandler, HTTPServer
from werkzeug.serving import run_simple
from werkzeug.wrappers import Response, Request

from jinja2 import Environment, FileSystemLoader
from datetime import datetime
from base64 import b64encode

from pygments import highlight
from pygments.lexers import PythonLexer
from pygments.formatters import HtmlFormatter
from pylint.interfaces import IReporter
from pylint.reporters.ureports.nodes import BaseLayout

from .core import PythonTaReporter

import logging
logging.getLogger("werkzeug").disabled = True

TEMPLATES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')


class HTMLReporter(PythonTaReporter):
    """Reporter that displays results in HTML form.

    By default, automatically opens the report in a web browser.
    """
    __implements__ = IReporter
    name = 'HTMLReporter'

    _COLOURING = {
        'black': '<span class="black">',
        'black-line': '<span class="black line-num">',
        'bold': '<span>',
        'code-heading': '<span>',
        'style-heading': '<span>',
        'code-name': '<span>',
        'style-name': '<span>',
        'highlight': '<span class="highlight-pyta">',
        'grey': '<span class="grey">',
        'grey-line': '<span class="grey line-num">',
        'gbold': '<span class="gbold">',
        'gbold-line': '<span class="gbold line-num">',
        'reset': '</span>'
    }

    no_err_message = 'None!'
    no_snippet = 'Nothing here.'
    code_err_title = 'Code Errors or Forbidden Usage (fix: high priority)'
    style_err_title = 'Style or Convention Errors (fix: before submission)'
    OUTPUT_FILENAME = 'pyta_report.html'

    def print_messages(self, level='all'):
        """Do nothing to print messages, since all are displayed in a single HTML file."""

    def display_messages(self, layout: BaseLayout) -> None:
        """Hook for displaying the messages of the reporter

        This will be called whenever the underlying messages
        needs to be displayed. For some reporters, it probably
        doesn't make sense to display messages as soon as they
        are available, so some mechanism of storing them could be used.
        This method can be implemented to display them after they've
        been aggregated.
        """
        grouped_messages = \
            {path: self.group_messages(msgs) for path, msgs in self.messages.items()}

        template_f = self.linter.config.pyta_template_file
        template = Environment(loader=FileSystemLoader(TEMPLATES_DIR)).get_template(template_f)

        # Embed resources so the output html can go anywhere, independent of assets.
        # with open(os.path.join(TEMPLATES_DIR, 'pyta_logo_markdown.png'), 'rb+') as image_file:
        #     # Encode img binary to base64 (+33% size), decode to remove the "b'"
        #     pyta_logo_base64_encoded = b64encode(image_file.read()).decode()

        # Date/time (24 hour time) format:
        # Generated: ShortDay. ShortMonth. PaddedDay LongYear, Hour:Min:Sec
        dt = str(datetime.now().strftime('%a. %b. %d %Y, %I:%M:%S %p'))

        # Render the jinja template
        rendered_template = template.render(date_time=dt, reporter=self,
                                            grouped_messages=grouped_messages)

        # If a filepath was specified, write to the file
        if self.out is not sys.stdout:
            self.writeln(rendered_template)
        else:
            rendered_template = rendered_template.encode('utf8')
            self._open_html_in_browser(rendered_template, dt)

    def _open_html_in_browser(self, html: bytes, dt: str, debug: bool = True) -> None:
        """
        Display html in a web browser without creating a temp file.
        Instantiates a trivial http server and uses the webbrowser module to
        open a URL to retrieve html from that server.

        Adapted from: https://github.com/plotly/plotly.py/blob/master/packages/python/plotly/plotly/io/_base_renderers.py#L655
        """
        host = '127.0.0.1'

        if debug:
            if not (port_str := os.environ.get('PYTA_HTML_PORT')):
                port = _get_open_port(host)
                os.environ['PYTA_HTML_PORT'] = str(port)
                server_url = f"http://{host}:{port}"
                webbrowser.open(server_url, new=2)
                print(f' * Opening on {server_url}', file=sys.stderr)
            else:
                port = int(port_str)
                print(f' * Reloading report at {dt}', file=sys.stderr)

            @Request.application
            def style_report_app(request: Request) -> Any:
                """WSGI application that returns the rendered html template as a response"""
                if request.method == 'GET' and request.path == '/creationTime':
                    return Response(dt)
                return Response(html, mimetype='text/html')

            extra_files = [
                'python_ta/reporters/templates/stylesheet.css',
                'python_ta/reporters/templates/template.html',
                'python_ta/reporters/templates/script.js'
            ]

            run_simple(hostname=host, port=port, application=style_report_app,
                       use_reloader=True, extra_files=extra_files)

        else:
            class OneShotRequestHandler(BaseHTTPRequestHandler):
                def do_GET(self):
                    self.send_response(200)
                    self.send_header("Content-type", "text/html")
                    self.end_headers()

                    buffer_size = 1024 * 1024
                    for i in range(0, len(html), buffer_size):
                        self.wfile.write(html[i: i + buffer_size])

            host = '127.0.0.1'
            server = HTTPServer((host, 0), OneShotRequestHandler)
            webbrowser.open(f"http://{host}:{server.server_port}", new=2)

            server.handle_request()
            server.server_close()

    @classmethod
    def _colourify(cls, colour_class: str, text: str) -> str:
        """Return a colourized version of text, using colour_class.
        """
        colour = cls._COLOURING[colour_class]
        new_text = text.lstrip(' ')
        space_count = len(text) - len(new_text)
        new_text = new_text.replace(' ', cls._SPACE)
        if '-line' not in colour_class:
            new_text = highlight(
                new_text, PythonLexer(),
                HtmlFormatter(nowrap=True, lineseparator='', classprefix='pygments-')
            )

        return (
                (space_count * cls._SPACE) + colour +
                new_text +
                cls._COLOURING['reset']
        )


def _get_open_port(host: str) -> int:
    """Returns a randomly generated available port"""
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((host, 0))
        _, port = s.getsockname()[:2]
        return port
