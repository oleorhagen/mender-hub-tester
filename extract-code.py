
import re

from mistune import mistune


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
    IS_TREE = True

    IGNORE_NEXT_CODE_BLOCK = False

    def __init__(self, output_file=None):
        if output_file is not None:
            self.output_file = output_file


    # Hidden documentation automation commands
    AUTOMATION_EXECUTE_REGEXP = "<!---\s*AUTOMATION: execute=`(.*)`\s*-->"
    AUTOMATION_IGNORE_REGEXP = "<!---\s*AUTOMATION: ignore=`(.*)`\s*-->"
    AUTOMATION_TEST_REGEXP = "<!---\s*AUTOMATION: test=`(.*)`\s*-->"

    def block_html(self, children):
        # Check if it is an automation comment.
        #
        # Type: execute
        #
        me = re.match(self.AUTOMATION_EXECUTE_REGEXP, children)
        if me:
            self.output_file.write("\n# Added as an automation comment\n")
            self.output_file.write(str(me.group(1))+"\n\n")
            return None
        #
        # Type: Ignore
        #
        me = re.match(self.AUTOMATION_IGNORE_REGEXP, children)
        if me:
            self.IGNORE_NEXT_CODE_BLOCK = True
            self.output_file.write("\n# Ignoring the next code block...\n")
            return None
        #
        # Type: test
        #
        me = re.match(self.AUTOMATION_TEST_REGEXP, children)
        if me:
            self.output_file.write("\n# Test code block\n")
            self.output_file.write(str(me.group(1))+"\n\n")
            return None
        return None


    def block_code(self, children, info=None):
        """Only render a block of code if it is bash marked, and it is not ignored"""
        if info == "bash":
          if self.IGNORE_NEXT_CODE_BLOCK:
              self.IGNORE_NEXT_CODE_BLOCK = False
              self.output_file.write("# Ignoring...\n")
              for line in children.split("\n"):
                  self.output_file.write("# {}\n".format(line))
              return None
          self.output_file.write(children)
        return None

code_blocks = []

with open("article.md", mode="r") as af:

    data = af.read()

    try:
      output_file = open("test-script", mode="w")
    except Exception as e:
        print("Error opening file: {}".format(e))

    renderer = DocumentationCodeRenderer(output_file)

    # Generate AST tokens instead of html
    markdown = mistune.create_markdown(renderer=renderer)

    markdown(data)

    output_file.close()

