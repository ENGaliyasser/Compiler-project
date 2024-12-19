import sys
import time
import os

# PyQt5 imports
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QGraphicsScene, QFileDialog, QMessageBox
from PyQt5.QtCore import QRectF

# Third-party library imports
from graphviz import Digraph

# Local module imports
from gui import Ui_MainWindow
from parser import Parser, Node

def draw_tree(root):
    """
    Draws a syntax tree using Graphviz with a hierarchical layout.

    Args:
        root (Node): The root node of the syntax tree.
    """
    dot = Digraph(format='png', graph_attr={'rankdir': 'TB'})  # Top-to-Bottom layout

    def traverse(node, parent_id=None):
        if not node:
            return

        node_id = str(id(node))
        dot.node(node_id, label=node.name, shape=node.shape)

        if parent_id:
            dot.edge(parent_id, node_id)

        # Handle sibling nodes
        sibling_group = []
        current_sibling = node
        while current_sibling:
            sibling_id = str(id(current_sibling))
            dot.node(sibling_id, label=current_sibling.name, shape=current_sibling.shape)
            sibling_group.append(sibling_id)
            current_sibling = current_sibling.sibling

        # Ensure siblings are properly aligned
        if len(sibling_group) > 1:
            with dot.subgraph() as s:
                s.attr(rank="same")
                for sibling_id in sibling_group:
                    s.node(sibling_id)
            # Connect siblings with horizontal edges
            for i in range(len(sibling_group) - 1):
                dot.edge(sibling_group[i], sibling_group[i + 1], constraint="false")

        # Recursively process children
        current_sibling = node
        while current_sibling:
            for child in current_sibling.children:
                traverse(child, str(id(current_sibling)))
            current_sibling = current_sibling.sibling

    traverse(root)

    # Render the syntax tree to a PNG file
    try:
        filepath = dot.render('tree', view=True)
        print(f"Syntax tree generated successfully: {filepath}")
    except Exception as e:
        print(f"Error generating syntax tree: {e}")

class Back_End_Class(QtWidgets.QWidget, Ui_MainWindow):
    """
    Main application backend class handling UI interactions and processing.
    """

    def __init__(self):
        super().__init__()
        self.setupUi(MainWindow)
        self.thread = {}

        # Connect UI elements to their respective functions
        self.scan.clicked.connect(self.Scan)
        self.Browse.clicked.connect(self.browse_file)
        self.parse.clicked.connect(self.parser)

    def browse_file(self):
        """Handles file selection and loads it into the input text area."""
        options = QFileDialog.Options()
        file_name, _ = QFileDialog.getOpenFileName(
            self,
            "Open Code File",
            "",
            "Text Files (*.txt);;All Files (*)",
            options=options
        )
        if file_name:
            with open(file_name, 'r') as file:
                self.input.setPlainText(file.read())
                self.Browseline.setText(str(file_name))

    def Scan(self):
        """Performs lexical analysis on the input code."""
        user_input = self.input.toPlainText().splitlines()
        user_code = "\n".join(user_input)

        # Check if the input code is empty
        if not user_code.strip():
            # Display an error message
            QMessageBox.warning(
                self,
                "Input Error",
                "No input provided. Please enter code in the input area or select a file."
            )
            return  # Exit the method early since there's nothing to scan

        self.scanner = Scanner()
        self.scanner.scan(user_code)
        self.scanner.output()

        # Display the results
        output_content = self._format_scanner_output()
        self.output.setPlainText("".join(output_content))

    def parser(self):
        """Generates and displays the syntax tree."""

        # Check if there are tokens available
        if not hasattr(self, 'scanner') or not self.scanner.tokens:
            QMessageBox.warning(
                self,
                "Parsing Error",
                "No tokens available for parsing. Please perform scanning first."
            )
            return

        self.scanner.draw_syntax_tree()
        time.sleep(0.5)  # Small delay to ensure the image is generated

        # Load and display the syntax tree image
        scene = QGraphicsScene()
        pixmap = QPixmap("tree.png")
        scene.addPixmap(pixmap)
        scene.setSceneRect(QRectF(pixmap.rect()))

        self.graphicsView.setScene(scene)
        self.graphicsView.fitInView(scene.sceneRect(), mode=1)  # Keep aspect ratio

    def _format_scanner_output(self):
        """Formats scanner output for display."""
        output = []
        output.append("Tokens:\n")
        output.append(f"{'Line':<5} {'Token':<12} {'Type':<12}\n")
        output.append(f"{'====':<5} {'====':<12} {'=====':<12}\n")

        for line_number, token, token_type in self.scanner.tokens:
            output.append(f"{line_number:<5} {token:<12} {token_type:<12}\n")

        if self.scanner.errors:
            output.append("\nErrors:\n")
            for line_number, error in self.scanner.errors:
                output.append(f"Line {line_number}: {error}\n")

        return output

# List of keywords used in the language
keywords = ['read', 'if', 'then', 'repeat', 'until', 'write', 'end']

# Global tokens list (currently unused, but kept for potential future use)
global_tokens_list = []

class Scanner:
    """
    A lexical analyzer (scanner) that processes input text and generates tokens.
    Handles comments, identifiers, numbers, and various operators.
    """

    # State definitions for the scanner
    STATES = {
        'START': False,
        'IN_COMMENT': False,
        'IN_ID': False,
        'IN_NUM': False,
        'IN_ASSIGN': False,
        'DONE': False,
        'OTHER': False
    }

    # Language keywords and operators
    KEYWORDS = ['else', 'end', 'if', 'repeat', 'then', 'until', 'read', 'write']
    OPERATORS = {
        '+': 'PLUS',
        '-': 'MINUS',
        '*': 'MULT',
        '/': 'DIV',
        ':=': 'ASSIGN',
        '=': 'EQUAL',
        '<': 'LESSTHAN',
        ';': 'SEMICOLON',
        '(': 'OPENBRACKET',
        ')': 'CLOSEDBRACKET'
    }

    def __init__(self):
        """Initialize the scanner with empty token and error lists, and set the starting state."""
        self.set_state('START')
        self.tokens = []
        self.errors = []
        self.in_comment_block = False  # Flag to track if inside a multiline comment

    def set_state(self, state):
        """Set the current state of the scanner."""
        self.STATES = {k: (k == state) for k in self.STATES}

    def get_state(self, state):
        """Check if the scanner is in a specific state."""
        return self.STATES[state]

    def scan(self, input_text):
        """
        Process the input text and generate tokens.

        Args:
            input_text (str): The input code to scan.
        """
        global comment_line
        lines = input_text.splitlines()
        stop_parsing = False  # Flag to indicate if parsing should stop due to an error

        for line_number, line in enumerate(lines, start=1):
            if stop_parsing:
                break  # Stop parsing if an error occurred

            if not self.in_comment_block:
                self.set_state('START')

            token = ''
            i = 0
            while i < len(line):
                if stop_parsing:
                    break

                c = line[i]

                # Handle multiline comments
                if self.in_comment_block:
                    if c == '}':
                        self.in_comment_block = False
                    elif c == '{':
                        self.errors.append((line_number, "NOT ALLOWED NESTED COMMENT"))
                        stop_parsing = True
                        break
                    i += 1
                    continue

                # Handle different states
                if self.get_state('START'):
                    if c == '{':
                        comment_line = line_number
                        self.in_comment_block = True
                    elif c == ':':
                        if i + 1 == len(line):
                            self.errors.append((line_number, f"Invalid token: {c}"))
                            stop_parsing = True
                            break
                        self.set_state('IN_ASSIGN')
                    elif self.is_symbol(c):
                        self.classify(c, line_number)
                    elif self.is_num(c):
                        self.set_state('IN_NUM')
                        token = c
                    elif self.is_str(c):
                        self.set_state('IN_ID')
                        token = c
                    elif c == ' ':
                        pass  # Ignore spaces
                    else:
                        self.errors.append((line_number, f"Invalid token: {c}"))
                        stop_parsing = True
                        break

                elif self.get_state('IN_ASSIGN'):
                    if c == '=':
                        self.classify(":=", line_number)  # Valid assignment operator
                    else:
                        self.errors.append((line_number, "Invalid token: ':'"))
                        stop_parsing = True
                        break
                    self.set_state('START')

                elif self.get_state('IN_NUM'):
                    if self.is_num(c):
                        token += c  # Continue building the number token
                    else:
                        self.classify(token, line_number)
                        token = ''
                        self.set_state('START')
                        i -= 1  # Reprocess the current character

                elif self.get_state('IN_ID'):
                    if self.is_str(c):
                        token += c  # Continue building the identifier token
                    else:
                        self.classify(token, line_number)
                        token = ''
                        self.set_state('START')
                        i -= 1  # Reprocess the current character

                i += 1

            # Finalize any token at the end of the line
            if token and not stop_parsing:
                self.classify(token, line_number)

        if self.in_comment_block and not stop_parsing:
            self.errors.append((comment_line, "UNCLOSED COMMENT"))

    def classify(self, token, line_number):
        """
        Classify a token and add it to the tokens list.

        Args:
            token (str): The token to classify.
            line_number (int): The line number where the token appears.
        """
        if not token:
            return  # Skip empty tokens

        if self.is_str(token):
            token_type = token.upper() if token in self.KEYWORDS else 'IDENTIFIER'
            self.tokens.append((line_number, token, token_type))
        elif self.is_num(token):
            self.tokens.append((line_number, token, 'NUMBER'))
        elif token in self.OPERATORS:
            self.tokens.append((line_number, token, self.OPERATORS[token]))
        else:
            self.errors.append((line_number, f"Invalid token: {token}"))

    # Helper methods for character classification
    def is_str(self, token):
        """Check if the token is a valid identifier (alphabetic characters)."""
        return token.isalpha()

    def is_num(self, token):
        """Check if the token is a valid number (digits only)."""
        return token.isdigit()

    def is_symbol(self, token):
        """Check if the token is a valid operator symbol."""
        return token in ['+', '-', '*', '/', '=', '<', ';', '(', ')']

    def draw_syntax_tree(self):
        """
        Draws the syntax tree using Graphviz based on the scanned tokens.
        """
        # Extract the token list from the Scanner instance
        globall_tokens_list = [(token, token_type) for _, token, token_type in self.tokens]

        parser = Parser(globall_tokens_list)
        try:
            tree_root = parser.program()
            print("The input program is valid. Syntax Tree:")
            print(tree_root)

            # Additional nodes (example)
            child1 = Node("Child1", "box")
            child2 = Node("Child2", "box")
            grandchild1 = Node("Grandchild1", "circle")
            grandchild2 = Node("Grandchild2", "circle")
            grandchild3 = Node("Grandchild3", "circle")
            grandchild4 = Node("Grandchild4", "circle")
            grandchild3.add_sibling(grandchild4)
            child1.add_sibling(child2)
            child1.add_child(grandchild1)
            child1.add_child(grandchild2)
            child2.add_child(grandchild3)

            # Draw the tree using the draw_tree function
            draw_tree(tree_root)

        except Exception as e:
            print(f"Error while generating the syntax tree: {e}")

    def output(self, output_file='scanner_output.txt'):
        """
        Writes tokens and errors to an output file.

        Args:
            output_file (str): The file path to write the output to.
        """
        with open(output_file, 'w') as file:
            file.write("Tokens:\n")
            file.write(f"{'Line':<5} {'Token':<12} {'Type':<12}\n")
            file.write(f"{'====':<5} {'====':<12} {'=====':<12}\n")
            for line_number, token, token_type in self.tokens:
                file.write(f"{line_number:<5} {token:<12} {token_type:<12}\n")

            if self.errors:
                file.write("\nErrors:\n")
                for line_number, error in self.errors:
                    file.write(f"Line {line_number}: {error}\n")

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    MainWindow = QtWidgets.QMainWindow()
    ui = Back_End_Class()
    MainWindow.show()
    sys.exit(app.exec_())