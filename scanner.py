# PyQt5 imports for GUI components
from PyQt5.QtGui import QTextCursor, QFont, QPixmap, QFontMetrics, QColor
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import QGraphicsEllipseItem, QGraphicsTextItem, QGraphicsScene, QGraphicsRectItem, QMessageBox, QFileDialog
from PyQt5.QtGui import QPen, QBrush
from PyQt5.QtCore import Qt, QPointF

import sys  # Import sys module for system-specific parameters and functions

# Import custom modules
from gui import Ui_MainWindow  # Import the GUI layout from gui.py (assumed to be generated from Qt Designer)
from parser import Parser, ParserError, Node  # Import Parser, ParserError, and Node classes from parser.py


# Define a class for drawing the syntax tree
class SyntaxTreeDrawer:
    def __init__(self, graphicsView, root_node):
        # Initialize the drawer with the QGraphicsView and the root node of the tree
        self.graphicsView = graphicsView  # The graphics view where the tree will be displayed
        self.root_node = root_node  # The root node of the syntax tree
        self.scene = QGraphicsScene()  # Create a new graphics scene
        self.graphicsView.setScene(self.scene)  # Set the scene to the graphics view
        # Set spacing parameters for drawing the tree
        self.vertical_spacing = 100  # Vertical spacing between nodes
        self.horizontal_spacing = 70  # Horizontal spacing between nodes
        self.text_padding = 10  # Padding around the text in nodes

    def clear_scene(self):
        """Clears the QGraphicsScene and ensures all items are removed."""
        # Remove all items from the scene
        for item in self.scene.items():
            self.scene.removeItem(item)
        self.scene.clear()  # Clear the scene

    def display_message(self, message):
        """Displays a message on the QGraphicsView."""
        self.clear_scene()  # Properly clear the scene
        text_item = QGraphicsTextItem(message)  # Create a text item with the message
        text_item.setDefaultTextColor(Qt.red)  # Set text color to red
        text_item.setFont(QFont("Arial", 16))  # Set font to Arial, size 16
        text_item.setPos(10, 10)  # Position the text in the scene
        self.scene.addItem(text_item)  # Add the text item to the scene
        # Adjust the scene rectangle to fit the items
        self.graphicsView.setSceneRect(self.scene.itemsBoundingRect())

    def draw_tree(self):
        """Draws the syntax tree on the QGraphicsScene."""
        self.scene.clear()  # Clear any existing items in the scene
        # Determine the positions of all nodes in the tree
        positions = {}
        self._calculate_positions(self.root_node, 0, 0, positions)
        # Draw the tree based on calculated positions
        self._draw_tree(self.root_node, positions)
        # Adjust the scene rectangle to fit the items
        self.graphicsView.setSceneRect(self.scene.itemsBoundingRect())

    def _calculate_positions(self, node, x, y, positions):
        """Recursively calculates positions for each node in the tree."""
        if not node:
            return 0  # No width contribution for empty nodes

        # Calculate width required for children first
        children_width = 0
        child_positions = []
        for child in node.children:
            # Calculate positions for child nodes
            child_width = self._calculate_positions(child, x + children_width, y + self.vertical_spacing, positions)
            child_positions.append((child, x + children_width))
            children_width += child_width + self.horizontal_spacing  # Update total width

        # Calculate position for the current node
        node_width = max(children_width - self.horizontal_spacing, self.horizontal_spacing)
        node_x = x + (children_width - node_width) // 2  # Center the node based on children
        positions[node] = QPointF(node_x, y)  # Store the position of the current node

        # Adjust sibling positions
        if node.sibling:
            # Calculate positions for sibling nodes
            sibling_width = self._calculate_positions(node.sibling, x + node_width + self.horizontal_spacing + 10, y, positions)
            node_width += sibling_width  # Update the width to include sibling

        return node_width  # Return the total width occupied by this node and its siblings

    def _draw_tree(self, node, positions):
        """Recursively draws each node and its connections on the scene."""
        if not node:
            return  # Base case: do nothing for empty nodes

        # Retrieve the position of the current node
        position = positions[node]
        x, y = position.x(), position.y()

        # Calculate size of the node based on text content
        text_item = QGraphicsTextItem(node.name)  # Create a text item with the node's name
        font_metrics = QFontMetrics(text_item.font())  # Get font metrics
        text_width = font_metrics.horizontalAdvance(node.name)  # Width of the text
        text_height = font_metrics.height()  # Height of the text
        shape_width = text_width + self.text_padding * 2  # Total width including padding
        shape_height = text_height + self.text_padding * 2  # Total height including padding

        # Draw the current node based on its shape
        if node.shape == "oval":
            # Draw an ellipse (oval) for the node
            node_item = QGraphicsEllipseItem(x - shape_width / 2, y - shape_height / 2,
                                             shape_width, shape_height)
        elif node.shape == "rectangle":
            # Draw a rectangle for the node
            node_item = QGraphicsRectItem(x - shape_width / 2, y - shape_height / 2,
                                          shape_width, shape_height)
        else:
            raise ValueError(f"Unsupported shape: {node.shape}")  # Handle unexpected shapes

        # Set appearance of the node
        node_item.setBrush(QBrush(QColor(200, 230, 255)))  # Light blue background color for nodes
        self.scene.addItem(node_item)  # Add the node to the scene

        # Add text inside the node
        text_item.setDefaultTextColor(Qt.black)  # Set text color to black
        text_item.setPos(x - text_width / 2, y - text_height / 2)  # Position the text centered in the node
        self.scene.addItem(text_item)  # Add the text item to the scene

        # Draw connections to children
        for child in node.children:
            child_position = positions[child]
            # Draw a line from current node to child node
            self.scene.addLine(x, y + shape_height / 2,
                               child_position.x(), child_position.y() - shape_height / 2,
                               QPen(QColor(0, 128, 0), 2))  # Green edges with width 2
            self._draw_tree(child, positions)  # Recursive call for children

        # Draw connection to sibling
        if node.sibling:
            sibling_position = positions[node.sibling]
            # Draw a line from current node to sibling node
            self.scene.addLine(x + shape_width / 2, y,
                               (sibling_position.x() - shape_width / 2) + 40, y,
                               QPen(QColor(255, 69, 0), 2))  # Orange edges with width 2
            self._draw_tree(node.sibling, positions)  # Recursive call for sibling

# Define the main backend class for the application
class Back_End_Class(QtWidgets.QWidget, Ui_MainWindow):
    def __init__(self):
        # Initialize the parent classes
        QtWidgets.QWidget.__init__(self)
        self.setupUi(MainWindow)  # Set up the UI elements from the generated GUI module
        self.thread = {}  # Placeholder for threading, if used

        # Connect buttons to their respective functions
        self.scan.clicked.connect(self.Scan)
        self.Browse.clicked.connect(self.browse_file)  # Connect the browse button to the browse function
        self.parse.clicked.connect(self.parser)  # Connect the parse button to the parser function

    def browse_file(self):
        """Handles file selection and loads it into the input text area."""
        options = QtWidgets.QFileDialog.Options()
        # Open a file dialog to select a file
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
                    file_content = file.read()  # Read the content of the file
                self.input.setPlainText(file_content)  # Set the content to the input text area
                self.Browseline.setText(str(file_name))  # Display the file path
            except Exception as e:
                # Handle any errors that occur while opening the file
                QMessageBox.critical(
                    self,
                    "File Error",
                    f"An error occurred while opening the file:\n{e}"
                )
        else:
            # Inform the user if no file was selected
            QMessageBox.information(
                self,
                "No File Selected",
                "No file was selected."
            )

    def Scan(self):
        """Performs lexical analysis on the input code."""
        user_input = self.input.toPlainText().splitlines()  # Get the input code as a list of lines
        user_code = "\n".join(user_input)  # Join the lines back into a single string

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
        self.scanner.output()  # Save output to a file

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

        # Join the content and display in the output text area
        self.output.setPlainText("".join(output_content))  # Assuming `output` is a QTextEdit in your UI

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

        # Prepare the global tokens list for the parser
        globall_tokens_list = [(token, token_type) for _, token, token_type in self.scanner.tokens]
        print(self.scanner.tokens)  # Print the tokens for debugging

        if self.scanner.errors:
            # If there are scanner errors, display an error message in the graphics view
            drawer = SyntaxTreeDrawer(self.graphicsView, Node("no", "Rectangle"))
            drawer.display_message(f"Scanner Error: {self.scanner.errors[0]}")
        else:
            # Initialize the parser with the list of tokens
            parser = Parser(globall_tokens_list)
            try:
                # Parse the program and obtain the root of the syntax tree
                root = parser.program()
                # Initialize the drawer with the graphics view and the parsed tree
                drawer = SyntaxTreeDrawer(self.graphicsView, root)
                # Check for parser errors
                if not parser.errors:
                    # No errors, draw the syntax tree
                    drawer.draw_tree()
                else:
                    # Display the first error message in the graphics view
                    drawer.display_message(f"Error: {parser.errors[0]}")

            except ParserError as e:
                # Handle any unexpected termination of parsing
                print(f"Parsing failed: {e}")
                # Display the error message using the drawer
                drawer = SyntaxTreeDrawer(self.graphicsView, None)  # Pass `None` for the tree
                drawer.display_message(f"Error: {str(e)}")

# List of keywords used in the language
keywords = ['read', 'if', 'then', 'repeat', 'until', 'write', 'end']

global_tokens_list = []  # Initialize a global list for tokens

# Define the Scanner class for lexical analysis
class Scanner:
    # Define scanner states
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
        self.set_state('START')  # Set the initial state to START
        self.tokens = []  # List to store tokens
        self.errors = []  # List to store errors
        self.in_comment_block = False  # Track if inside a multiline comment

    def set_state(self, state):
        """Sets the current state of the scanner."""
        for key in self.STATES:
            self.STATES[key] = False  # Reset all states to False
        self.STATES[state] = True  # Set the specified state to True

    def get_state(self, state):
        """Gets the value of a specific state."""
        return self.STATES[state]

    def scan(self, input_text):
        """Performs lexical analysis on the input text."""
        global comment_line
        lines = input_text.splitlines()  # Split the input text into lines
        stop_parsing = False  # Flag to indicate parsing should stop

        for line_number, line in enumerate(lines, start=1):
            if stop_parsing:
                break  # Stop parsing if the flag is set

            if not self.in_comment_block:
                self.set_state('START')  # Reset to START state at the beginning of each line if not in a comment

            token = ''  # Initialize an empty token
            i = 0  # Character index
            while i < len(line):
                if stop_parsing:
                    break  # Stop parsing if the flag is set

                c = line[i]  # Current character

                if self.in_comment_block:
                    # Handle multiline comments
                    if c == '}':
                        self.in_comment_block = False  # End of comment block
                    elif c == '{':
                        # Nested comments are not allowed
                        self.errors.append((line_number, f"NOT ALLOWED NESTED COMMENT"))
                        stop_parsing = True  # Set the flag to stop parsing
                        break  # Break out of the current loop
                    i += 1  # Move to the next character
                    continue  # Continue to the next iteration

                # Start state
                if self.get_state('START'):
                    if c == '{':
                        # Start of a comment block
                        comment_line = line_number
                        self.in_comment_block = True
                    elif c == ':':
                        # Possible assignment operator
                        if i + 1 == len(line):
                            # ':' at the end of the line is invalid
                            self.errors.append((line_number, f"Invalid token: {c}"))
                            stop_parsing = True  # Set the flag to stop parsing
                            break  # Break out of the current loop
                        self.set_state('IN_ASSIGN')  # Transition to IN_ASSIGN state
                    elif self.is_symbol(c):
                        # Single-character symbol (operator)
                        self.classify(c, line_number)
                    elif self.is_num(c):
                        # Start of a number
                        self.set_state('IN_NUM')
                        token = c  # Initialize the token with the digit
                    elif self.is_str(c):
                        # Start of an identifier
                        self.set_state('IN_ID')
                        token = c  # Initialize the token with the character
                    elif c == ' ':
                        # Ignore spaces
                        pass
                    else:
                        # Invalid character/token
                        self.errors.append((line_number, f"Invalid token: {c}"))
                        stop_parsing = True  # Set the flag to stop parsing
                        break  # Break out of the current loop

                # IN_ASSIGN state
                elif self.get_state('IN_ASSIGN'):
                    if c == '=':
                        # Valid assignment operator ':='
                        self.classify(":=", line_number)
                    else:
                        # Invalid token; standalone ':' is not allowed
                        self.errors.append((line_number, "Invalid token: ':'"))
                        stop_parsing = True  # Set the flag to stop parsing
                        break  # Break out of the current loop
                    self.set_state('START')  # Return to START state

                # IN_NUM state
                elif self.get_state('IN_NUM'):
                    if self.is_num(c):
                        token += c  # Append the digit to the token
                    else:
                        # End of the number token
                        self.classify(token, line_number)  # Classify the number token
                        token = ''  # Reset the token
                        self.set_state('START')  # Return to START state
                        i -= 1  # Decrement `i` to reprocess this character in the next loop

                # IN_ID state
                elif self.get_state('IN_ID'):
                    if self.is_str(c):
                        token += c  # Append the character to the token
                    else:
                        # End of the identifier token
                        self.classify(token, line_number)  # Classify the identifier token
                        token = ''  # Reset the token
                        self.set_state('START')  # Return to START state
                        i -= 1  # Decrement `i` to reprocess this character in the next loop

                i += 1  # Move to the next character

            # Finalize tokens at the end of the line
            if token and not stop_parsing:
                self.classify(token, line_number)  # Classify any remaining token

        if self.in_comment_block and not stop_parsing:
            # Handle unclosed comment blocks
            self.errors.append((comment_line, f"UNCLOSED COMMENT"))

    # Define keywords used in the language
    KEYWORDS = ['else', 'end', 'if', 'repeat', 'then', 'until', 'read', 'write']

    # Define operator symbols and their corresponding token types
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
        """Classifies a token and adds it to the tokens list or records an error."""
        if not token:
            return  # Skip empty tokens
        if self.is_str(token):
            if token in self.KEYWORDS:
                self.tokens.append((line_number, token, token.upper()))  # Token is a keyword
            else:
                self.tokens.append((line_number, token, 'IDENTIFIER'))  # Token is an identifier
        elif self.is_num(token):
            self.tokens.append((line_number, token, 'NUMBER'))  # Token is a number
        elif token in self.OPERATORS:
            self.tokens.append((line_number, token, self.OPERATORS[token]))  # Token is an operator
        else:
            self.errors.append((line_number, f"Invalid token: {token}"))  # Record invalid token

    # Helper functions to check character types
    def is_str(self, token):
        """Checks if a token is composed of alphabetic characters."""
        return token.isalpha()

    def is_num(self, token):
        """Checks if a token is composed of digits."""
        return token.isdigit()

    def is_symbol(self, token):
        """Checks if a character is a valid operator symbol."""
        return token in ['+', '-', '*', '/', '=', '<', ';', '(', ')']

    # Output the tokens and errors to a .txt file
    def output(self, output_file='scanner_output.txt'):
        """Writes the tokens and errors to an output file."""
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

# Entry point of the application
if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)  # Create the main application
    MainWindow = QtWidgets.QMainWindow()  # Create the main window
    ui = Back_End_Class()  # Initialize the backend class which also sets up the UI
    MainWindow.show()  # Show the main window
    sys.exit(app.exec_())  # Start the event loop