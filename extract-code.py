# from mistune.mistune import mistune
# import mistune.mistune as m

from mistune import mistune

import pprint
import tempfile
import re

# from mistune.renderers import BaseRenderer
# from mistune.mistune import renderers
from mistune.mistune.renderers import BaseRenderer

"""
This tool will parse <file> to extract enclosed ```bash ``` code blocks from markdown,
add it to a shell script, and execute it (with -e -x set).
* Usually when following documentation, some human interaction is required. This can be
  achieved by adding:
      <!-- AUTOMATION: execute=`cmd` -->
  blocks to the markdown file.
* Sometimes, some instructions enclosed in ```bash ``` may not be required and skipped.
  This can be achieved by adding:
      <!-- AUTOMATION: ignore=`reason` -->
* Finally, testing that the instructions executed correctly can be tested using:
      <!-- AUTOMATION: test=`cmd` -->
"""

# Create a code renderer
class DocumentationCodeRenderer(mistune.AstRenderer):
    NAME = 'code'
    IS_TREE = False

    # TODO -- Make the parser handle AUTOMATION HTML comments, like code blocks.
    def block_code(self, code, info=None):
        if info:
            lang = info.strip().split(None, 1)[0]
            lang = escape_html(lang)
            print("Lang: {}".format(lang))
        return "lang: {}"


renderer = DocumentationCodeRenderer()

# Generate AST tokens instead of html
markdown = mistune.create_markdown(renderer="ast")


code_blocks = []

AUTOMATION_EXECUTE_REGEXP = "<!---\s*AUTOMATION: execute=`(.*)`\s*-->"
AUTOMATION_IGNORE_REGEXP = "<!---\s*AUTOMATION: ignore=`(.*)`\s*-->"
AUTOMATION_TEST_REGEXP = "<!---\s*AUTOMATION: test=`(.*)`\s*-->"

# Traverse the AST...
def DFS(node):
    print(node)
    if node["type"] == "block_code":
        code_blocks.append(node)
    # Parse the special cases of AUTOMATION HTML comments
    # Ideally this should be done in the parser, but POC man.
    if node["type"] == "block_html":
        me = re.match(AUTOMATION_EXECUTE_REGEXP, node["text"])
        if me:
            code_blocks.append(
                {
                    "type": "execute",
                    "text": str(me.group(1)+"\n"),
                    "info": "automation"
                })
        me = re.match(AUTOMATION_IGNORE_REGEXP, node["text"])
        if me:
            code_blocks.append(
                {
                    "type": "ignore",
                    "text": str(me.group(1)+"\n"),
                    "info": "automation"
                })
        me = re.match(AUTOMATION_TEST_REGEXP, node["text"])
        if me:
            code_blocks.append(
                {
                    "type": "test",
                    "text": str(me.group(1)+"\n"),
                    "info": "automation"
                })
    if "children" in node:
      for child in node["children"]:
          DFS(child)

with open("article.md") as af:
    data = af.read()
    a = markdown(data)

    for root in a:
        DFS(root)

    code_to_test = []

    print("Extracted code blocks:")
    print(len(code_blocks))
    for block in code_blocks:
        # Strip the sections which should not be executed
        print(block["type"])
        if block["info"] != None:
            code_to_test.append(block)

    print("Code to test:")
    print(code_to_test)

    # Create a script out of the commands
    name = ""
    with open("test-script", "w") as tf:
        name = tf.name
        print(tf)
        tf.write("#! /bin/bash\n")
        tf.write("set -e -x\n")
        command_iter = iter(code_to_test)
        for command in command_iter:
            print ("Running command: ")
            print(command)
            if command["type"] == "ignore":
                tf.write("# Ignoring next command:\n# reason: {}".format(command["text"]))
                nc = next(command_iter)
                tf.write("# {}\n".format(nc["text"]))
                continue
            if command["type"] == "test":
                tf.write("# Documentation test command\n")
            if command["type"] == "execute":
                tf.write("# The next execution step is hidden in the documentation\n")
            tf.write(str(command["text"]))

    print("Tempfile name: {}".format(name))
