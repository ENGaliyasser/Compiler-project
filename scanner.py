import time

from PyQt5.QtGui import QTextCursor, QFont, QPixmap, QFontMetrics, QColor

from gui import Ui_MainWindow
from PyQt5 import QtCore, QtGui, QtWidgets
import sys
from parser import Parser, ParserError

from graphviz import Digraph
from PyQt5.QtWidgets import QGraphicsEllipseItem, QGraphicsTextItem, QGraphicsScene, QGraphicsRectItem, QMessageBox,QFileDialog
from PyQt5.QtGui import QPen, QBrush
from PyQt5.QtCore import Qt, QPointF
from parser import Node



class SyntaxTreeDrawer:
    def __init__(self, graphicsView, root_node):
        self.graphicsView = graphicsView
        self.root_node = root_node
        self.scene = QGraphicsScene()
        self.graphicsView.setScene(self.scene)
        self.vertical_spacing = 100
        self.horizontal_spacing = 60
        self.text_padding = 10

    def clear_scene(self):
        """Clears the QGraphicsScene and ensures all items are removed."""
        for item in self.scene.items():
            self.scene.removeItem(item)
        self.scene.clear()

    def display_message(self, message):
        """Displays a message on the QGraphicsView."""
        self.clear_scene()  # Properly clear the scene
        text_item = QGraphicsTextItem(message)  # Create a text item
        text_item.setDefaultTextColor(Qt.red)  # Set text color (red as an example)
        text_item.setFont(QFont("Arial", 16))  # Set font and size
        text_item.setPos(10, 10)  # Position the text in the scene
        self.scene.addItem(text_item)  # Add the text item to the scene
        self.graphicsView.setSceneRect(self.scene.itemsBoundingRect())  # Adjust the scene rect

    def draw_tree(self):
        self.scene.clear()
        # Determine the layout of the entire tree
        positions = {}
        self._calculate_positions(self.root_node, 0, 0, positions)
        # Draw the tree based on calculated positions
        self._draw_tree(self.root_node, positions)
        self.graphicsView.setSceneRect(self.scene.itemsBoundingRect())

    def _calculate_positions(self, node, x, y, positions):
        if not node:
            return 0  # No width contribution for empty nodes

        # Calculate width required for children first
        children_width = 0
        child_positions = []
        for child in node.children:
            child_width = self._calculate_positions(child, x + children_width, y + self.vertical_spacing, positions)
            child_positions.append((child, x + children_width))
            children_width += child_width + self.horizontal_spacing

        # Calculate position for the current node
        node_width = max(children_width - self.horizontal_spacing, self.horizontal_spacing)
        node_x = x + (children_width - node_width) // 2
        positions[node] = QPointF(node_x, y)

        # Adjust sibling positions
        if node.sibling:
            sibling_width = self._calculate_positions(node.sibling, x + node_width + self.horizontal_spacing, y, positions)
            node_width += sibling_width

        return node_width

    def _draw_tree(self, node, positions):
        if not node:
            return

        # Retrieve the position of the current node
        position = positions[node]
        x, y = position.x(), position.y()

        # Calculate size of the node based on text
        text_item = QGraphicsTextItem(node.name)
        font_metrics = QFontMetrics(text_item.font())
        text_width = font_metrics.horizontalAdvance(node.name)
        text_height = font_metrics.height()
        shape_width = text_width + self.text_padding * 2
        shape_height = text_height + self.text_padding * 2

        # Draw the current node
        if node.shape == "oval":
            node_item = QGraphicsEllipseItem(x - shape_width / 2, y - shape_height / 2,
                                             shape_width, shape_height)
        elif node.shape == "rectangle":
            node_item = QGraphicsRectItem(x - shape_width / 2, y - shape_height / 2,
                                          shape_width, shape_height)
        else:
            raise ValueError(f"Unsupported shape: {node.shape}")

        node_item.setBrush(QBrush(QColor(200, 230, 255)))  # Light blue background for nodes
        self.scene.addItem(node_item)

        # Add text inside the node
        text_item.setDefaultTextColor(Qt.black)
        text_item.setPos(x - text_width / 2, y - text_height / 2)
        self.scene.addItem(text_item)

        # Draw connections to children
        for child in node.children:
            child_position = positions[child]
            self.scene.addLine(x, y + shape_height / 2,
                               child_position.x(), child_position.y() - shape_height / 2, QPen(QColor(0, 128, 0), 2))  # Green edges with width 2
            self._draw_tree(child, positions)  # Recursive call for children

        # Draw connection to sibling
        if node.sibling:
            sibling_position = positions[node.sibling]
            self.scene.addLine(x + shape_width / 2, y,
                               (sibling_position.x() - shape_width / 2)+ 40, y, QPen(QColor(255, 69, 0), 2))  # Orange edges with width 2
            self._draw_tree(node.sibling, positions)  # Recursive call for sibling

class Back_End_Class(QtWidgets.QWidget, Ui_MainWindow):

    def __init__(self):
        QtWidgets.QWidget.__init__(self)
        self.setupUi(MainWindow)
        self.thread = {}

        self.scan.clicked.connect(self.Scan)
        self.Browse.clicked.connect(self.browse_file)  # Connect the browse button to the browse function
        self.parse.clicked.connect(self.parser)  # Connect the browse button to the browse function

    def browse_file(self):
        """Handles file selection and loads it into the input text area."""
        options = QtWidgets.QFileDialog.Options()
        file_name, _ = QtWidgets.QFileDialog.getOpenFileName(
            self,
            "Open Code File",
            "",
            "Text Files (*.txt);;All Files (*)",
            options=options
        )
        if file_name:
            # Check if the selected file has a .txt extension
            if not file_name.lower().endswith('.txt'):
                QMessageBox.warning(
                    self,
                    "File Type Error",
                    "Please select a file with a .txt extension."
                )
                return  # Exit the method since the file is not a .txt file

            try:
                with open(file_name, 'r') as file:
                    file_content = file.read()
                self.input.setPlainText(file_content)
                self.Browseline.setText(str(file_name))
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "File Error",
                    f"An error occurred while opening the file:\n{e}"
                )
        else:
            QMessageBox.information(
                self,
                "No File Selected",
                "No file was selected."
            )

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

        # Initialize scanner and perform scanning
        self.scanner = Scanner()
        self.scanner.scan(user_code)
        self.scanner.output()  # Save output to file

        # Display tokens and errors in the QTextBrowser
        output_content = []
        output_content.append("Tokens:\n")
        output_content.append(f"{'Line':<5} {'Token':<12} {'Type':<12}\n")
        output_content.append(f"{'====':<5} {'====':<12} {'=====':<12}\n")
        for line_number, token, token_type in self.scanner.tokens:
            output_content.append(f"{line_number:<5} {token:<12} {token_type:<12}\n")

        if self.scanner.errors:
            output_content.append("\nErrors:\n")
            for line_number, error in self.scanner.errors:
                output_content.append(f"Line {line_number}: {error}\n")

        # Join the content for display
        self.output.setPlainText("".join(output_content))  # Assuming `output_text` is a QTextBrowser in your UI



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

        globall_tokens_list = [(token, token_type) for _, token, token_type in self.scanner.tokens]
        print(self.scanner.tokens)
        if self.scanner.errors:
            drawer = SyntaxTreeDrawer(self.graphicsView, Node("no","Rectangle"))
            drawer.display_message(f"Scanner Error: {self.scanner.errors[0]}")
        else:
            parser = Parser(globall_tokens_list)
            try:
                # Parse the program
                root = parser.program()
                # Initialize the drawer with the graphics view and the parsed tree
                drawer = SyntaxTreeDrawer(self.graphicsView, root)
                # Check for errors
                if not parser.errors:
                    # No errors, draw the syntax tree
                    drawer.draw_tree()
                else:
                    # Display the first error message
                    drawer.display_message(f"Error: {parser.errors[0]}")
                    
            except ParserError as e:
                # Handle any unexpected termination of parsing
                print(f"Parsing failed: {e}")
                # Display the error message using the drawer
                drawer = SyntaxTreeDrawer(self.graphicsView, None)  # Pass `None` for the tree
                drawer.display_message(f"Error: {str(e)}")





keywords = ['read', 'if', 'then', 'repeat', 'until', 'write', 'end']

global_tokens_list = []
class Scanner:
    STATES = {
        'START': False,
        'IN_COMMENT': False,
        'IN_ID': False,
        'IN_NUM': False,
        'IN_ASSIGN': False,
        'DONE': False,
        'OTHER': False
    }

    def __init__(self):
        self.set_state('START')
        self.tokens = []
        self.errors = []
        self.in_comment_block = False  # Track if inside a multiline comment

    def set_state(self, state):
        for key in self.STATES:
            self.STATES[key] = False
        self.STATES[state] = True

    def get_state(self, state):
        return self.STATES[state]

    def scan(self, input_text):
        global comment_line
        lines = input_text.splitlines()
        stop_parsing = False  # Flag to indicate parsing should stop

        for line_number, line in enumerate(lines, start=1):
            if stop_parsing:
                break  # Stop parsing if the flag is set

            if not self.in_comment_block:
                self.set_state('START')

            token = ''
            i = 0
            while i < len(line):
                if stop_parsing:
                    break  # Stop parsing if the flag is set

                c = line[i]

                if self.in_comment_block:
                    # Handle multiline comments
                    if c == '}':
                        self.in_comment_block = False
                    elif c == '{':
                        self.errors.append((line_number, f"NOT ALLOWED NESTED COMMENT"))
                        stop_parsing = True  # Set the flag to stop parsing
                        break  # Break out of the current loop
                    i += 1
                    continue

                # Start state
                if self.get_state('START'):
                    if c == '{':
                        comment_line = line_number
                        self.in_comment_block = True
                    elif c == ':':
                        if i+1 == len(line):
                            self.errors.append((line_number, f"Invalid token: {c}"))
                            stop_parsing = True  # Set the flag to stop parsing
                            break  # Break out of the current loop
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
                        # Ignore spaces
                        pass
                    else:
                        self.errors.append((line_number, f"Invalid token: {c}"))
                        stop_parsing = True  # Set the flag to stop parsing
                        break  # Break out of the current loop

                # IN_ASSIGN state
                elif self.get_state('IN_ASSIGN'):
                    if c == '=':
                        self.classify(":=", line_number)  # Valid ASSIGN token
                    else:
                        self.errors.append((line_number, "Invalid token: ':'"))  # Standalone `:` is invalid
                        stop_parsing = True  # Set the flag to stop parsing
                        break  # Break out of the current loop
                    self.set_state('START')

                # IN_NUM state (modified)
                elif self.get_state('IN_NUM'):
                    if self.is_num(c):
                        token += c  # Append the numeric character to the token
                    else:
                        # End of the number token
                        self.classify(token, line_number)  # Classify the valid numeric token
                        token = ''  # Reset the token
                        self.set_state('START')  # Go back to the start state

                        # Re-evaluate the current character in the START state
                        i -= 1  # Decrement `i` to reprocess this character in the next loop

                elif self.get_state('IN_ID'):
                    if self.is_str(c):
                        token += c  # Append the valid string character to the token
                    else:
                        # End of the identifier token
                        self.classify(token, line_number)  # Classify the valid identifier token
                        token = ''  # Reset the token
                        self.set_state('START')  # Go back to the start state

                        # Re-evaluate the current character in the START state
                        i -= 1  # Decrement `i` to reprocess this character in the next loop

                i += 1

            # Finalize tokens at the end of the line
            if token and not stop_parsing:
                self.classify(token, line_number)

        if self.in_comment_block and not stop_parsing:
            self.errors.append((comment_line, f"UNCLOSED COMMENT"))

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

    def classify(self, token, line_number):
        if not token:
            return  # Skip empty tokens
        if self.is_str(token):
            if token in self.KEYWORDS:
                self.tokens.append((line_number, token, token.upper()))
            else:
                self.tokens.append((line_number, token, 'IDENTIFIER'))
        elif self.is_num(token):
            self.tokens.append((line_number, token, 'NUMBER'))
        elif token in self.OPERATORS:
            self.tokens.append((line_number, token, self.OPERATORS[token]))
        else:
            self.errors.append((line_number, f"Invalid token: {token}"))

    # Helper functions
    def is_str(self, token):
        return token.isalpha()

    def is_num(self, token):
        return token.isdigit()

    def is_symbol(self, token):
        return token in ['+', '-', '*', '/', '=', '<', ';', '(', ')']





    # Output as .txt file
    def output(self, output_file='scanner_output.txt'):
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
