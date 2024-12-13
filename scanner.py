import time

from PyQt5.QtGui import QTextCursor, QFont, QPixmap
import PyQt5.QtWidgets
import os
import numpy as np
import pandas as pd
from graphviz import Digraph

from gui import Ui_MainWindow
from PyQt5 import QtCore, QtGui, QtWidgets
import sys
from parser import Parser
from parser import Node
from PyQt5.QtWidgets import QGraphicsScene
from PyQt5.QtGui import QPen, QBrush
from PyQt5.QtCore import Qt, QRectF
from parser import Node
import graphviz
from PIL import Image
import matplotlib.pyplot as plt
import networkx as nx

from graphviz import Digraph

def draw_tree(root):
    """
    Draw the syntax tree structure using Graphviz.

    Parameters:
        root (Node): The root node of the tree.
    """
    dot = Digraph(format='png')  # Create a Graphviz Digraph

    def traverse(node, parent_id=None):
        if node is None:
            return

        # Add the current node to the graph
        dot.node(node.name, label=node.name, shape=node.shape)

        # If there's a parent, add an edge
        if parent_id:
            dot.edge(parent_id, node.name)

        # Recursively add children
        for child in node.children:
            traverse(child, node.name)

        # Process siblings
        sibling = node.sibling
        while sibling:
            traverse(sibling, parent_id)
            sibling = sibling.sibling

    # Start traversal from the root
    traverse(root)

    # Render the tree
    try:
        filepath = dot.render('tree', view=True)
        print(f"Syntax tree generated successfully: {filepath}")
    except Exception as e:
        print(f"Error while generating the syntax tree: {e}")


class Back_End_Class(QtWidgets.QWidget, Ui_MainWindow):

    def __init__(self):
        QtWidgets.QWidget.__init__(self)
        self.setupUi(MainWindow)
        self.thread = {}

        self.scan.clicked.connect(self.Scan)
        self.Browse.clicked.connect(self.browse_file)  # Connect the browse button to the browse function
        self.parse.clicked.connect(self.parser)  # Connect the browse button to the browse function
        # Assuming you already have an instance of QGraphicsView, named self.graphicsView
        # Assuming you have an existing QGraphicsView (self.graphicsView)





    def browse_file(self):
        options = QtWidgets.QFileDialog.Options()
        file_name, _ = QtWidgets.QFileDialog.getOpenFileName(self, "Open Code File", "",
                                                             "Text Files (*.txt);;All Files (*)", options=options)
        if file_name:
            # Read the content of the file

            with open(file_name, 'r') as file:
                file_content = file.read()
            # Set the content of the file in the input QTextEdit

            self.input.setPlainText(file_content)
            self.Browseline.setText(str(file_name))  # Set the text of the line edit to the selected file name (file_name)



    def Scan(self):

        user_input = self.input.toPlainText().splitlines()
        user_code = "\n".join(user_input)

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


        # # Create a simple tree
        # dot = graphviz.Digraph()
        # dot.node('A', 'Root')
        # dot.node('B', 'Child 1')
        # dot.node('C', 'Child 2')
        # dot.edges(['AB', 'AC'])

        # Save the tree as a PNG image
        # dot.render('tree', format='png', cleanup=True)
    def parser(self):
        # Load the tree image
        # Create a scene if it doesn't exist already
        self.scanner.draw_syntax_tree()
        time.sleep(0.5)  # Delay for half a second

        if self.graphicsView.scene() is None:
            scene = QGraphicsScene()  # Create a new scene
            self.graphicsView.setScene(scene)  # Set the scene to the view
        else:
            scene = self.graphicsView.scene()  # Use the existing scene
        scene.clear()  # Clear the previous content
        pixmap = QPixmap("tree.png")
        scene.addPixmap(pixmap)

        scene.setSceneRect(QRectF(pixmap.rect()))  # Pass QRect directly to QRectF constructor

        self.graphicsView.fitInView(QRectF(pixmap.rect()), mode=1)  # 1 corresponds to Qt.KeepAspectRatio




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

    def draw_syntax_tree(self):
        """
        Draws the syntax tree using Graphviz.

        Args:
            root (Node): The root of the syntax tree.
            scanner (Scanner): The scanner object containing tokens.
        """
        # Extract the token list from the Scanner instance


        globall_tokens_list = [(token, token_type) for _, token, token_type in self.tokens]

        parser = Parser(globall_tokens_list)
        try:
            tree_root = parser.program()
            print("The input program is valid. Syntax Tree:")
            print(tree_root)

            # Draw the tree using the draw_tree function
            dot = draw_tree(tree_root)
            dot.render("tree", format="png", cleanup=True)  # Generates 'tree.png'
        except Exception as e:
            print(f"Error while generating the syntax tree: {e}")

        # # Initialize a Digraph object
        # dot = Digraph(format='png')
        # dot.attr(rankdir='TB')  # Tree style (top-to-bottom)
        #
        # def traverse(node, parent_name=None):
        #     """
        #     Recursively traverse the tree and add nodes/edges to the Graphviz graph.
        #
        #     Args:
        #         node (Node): Current node in the tree.
        #         parent_name (str): Name of the parent node.
        #     """
        #     if node is None:
        #         return
        #
        #     # Add the current node to the graph
        #     dot.node(node.name, node.name)
        #
        #     # Add an edge from the parent to the current node
        #     if parent_name:
        #         dot.edge(parent_name, node.name)
        #
        #     # Add child nodes
        #     for child in node.children:
        #         traverse(child, node.name)
        #
        #     # Traverse siblings
        #     if node.sibling:
        #         traverse(node.sibling, parent_name)
        #
        # # Start the traversal from the root
        # traverse(root)
        #
        # # Render the graph to a file and display it
        # dot.render('syntax_tree', view=True)

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
